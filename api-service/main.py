"""FastAPI application."""
import logging
from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app
from slowapi import Limiter
from slowapi.util import get_remote_address
from config import Config
from auth import AuthManager, authenticate_user
from models import TokenResponse, UserLogin, TokenData, TelemetryResponse, AlertResponse, VehicleStatusResponse, MetricsResponse
from database import APIDatabase
from cache import CacheManager
from datetime import timedelta
import time

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=Config.API_TITLE,
    version=Config.API_VERSION,
    description="Real-time vehicle telemetry API"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# Prometheus metrics
api_requests = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint'])
api_latency = Histogram('api_latency_seconds', 'API request latency')
api_errors = Counter('api_errors_total', 'Total API errors', ['status_code'])
active_connections = Gauge('api_active_connections', 'Active API connections')

# Initialize database and cache
db = APIDatabase()
cache = CacheManager()


# Dependencies
async def get_current_user(authorization: str = Header(None)) -> TokenData:
    """Get current user from JWT token."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )
    
    token_data = AuthManager.verify_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    
    return token_data


# Middleware for metrics and logging
@app.middleware("http")
async def metrics_middleware(request, call_next):
    """Record metrics for each request."""
    start_time = time.time()
    active_connections.inc()
    
    try:
        response = await call_next(request)
        api_requests.labels(method=request.method, endpoint=request.url.path).inc()
        
        if response.status_code >= 400:
            api_errors.labels(status_code=response.status_code).inc()
        
        elapsed = time.time() - start_time
        api_latency.observe(elapsed)
        
        return response
    finally:
        active_connections.dec()


# Routes

@app.post("/auth/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request, credentials: UserLogin):
    """Authenticate and get JWT token."""
    user = authenticate_user(credentials.username, credentials.password)
    if not user:
        logger.warning(f"Failed login attempt for user: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    access_token = AuthManager.create_access_token(
        data={"sub": user.username}
    )
    
    logger.info(f"User logged in: {user.username}")
    
    return TokenResponse(
        access_token=access_token,
        expires_in=int(Config.JWT_EXPIRATION_DELTA.total_seconds()),
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/vehicles/{vehicle_id}/latest", response_model=TelemetryResponse)
@limiter.limit("100/minute")
async def get_latest_telemetry(request, vehicle_id: str, current_user: TokenData = Depends(get_current_user)):
    """Get latest telemetry for a vehicle."""
    # Try cache first
    cache_key = f"telemetry:{vehicle_id}:latest"
    cached = cache.get(cache_key)
    if cached:
        return TelemetryResponse(**cached)
    
    # Get from database
    result = db.get_latest_telemetry(vehicle_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No telemetry found for vehicle {vehicle_id}",
        )
    
    # Cache the result
    cache.set(cache_key, result, ttl=10)
    
    return TelemetryResponse(**result)


@app.get("/vehicles/{vehicle_id}/history", response_model=list[TelemetryResponse])
@limiter.limit("50/minute")
async def get_telemetry_history(request, vehicle_id: str, limit: int = 100, offset: int = 0, 
                                current_user: TokenData = Depends(get_current_user)):
    """Get telemetry history for a vehicle."""
    limit = min(limit, 500)  # Max 500 records
    
    results = db.get_telemetry_history(vehicle_id, limit=limit, offset=offset)
    
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No history found for vehicle {vehicle_id}",
        )
    
    return [TelemetryResponse(**row) for row in results]


@app.get("/vehicles", response_model=list[str])
@limiter.limit("100/minute")
async def list_vehicles(request, current_user: TokenData = Depends(get_current_user)):
    """List all active vehicles."""
    cache_key = "vehicles:active"
    cached = cache.get(cache_key)
    if cached:
        return cached.get("vehicles", [])
    
    vehicles = db.get_active_vehicles()
    cache.set(cache_key, {"vehicles": vehicles}, ttl=30)
    
    return vehicles


@app.get("/alerts", response_model=list[AlertResponse])
@limiter.limit("100/minute")
async def get_alerts(request, vehicle_id: str = None, limit: int = 100, 
                    current_user: TokenData = Depends(get_current_user)):
    """Get alerts, optionally filtered by vehicle."""
    limit = min(limit, 500)
    
    alerts = db.get_alerts(vehicle_id=vehicle_id, limit=limit)
    
    return [AlertResponse(**alert) for alert in alerts]


@app.get("/metrics", response_model=MetricsResponse)
@limiter.limit("100/minute")
async def get_metrics(request, current_user: TokenData = Depends(get_current_user)):
    """Get system metrics."""
    cache_key = "metrics:system"
    cached = cache.get(cache_key)
    if cached:
        return MetricsResponse(**cached)
    
    metrics = db.get_metrics()
    metrics["average_processing_latency_ms"] = 5.5  # Placeholder
    
    cache.set(cache_key, metrics, ttl=60)
    
    return MetricsResponse(**metrics)


@app.get("/vehicles/{vehicle_id}/status", response_model=VehicleStatusResponse)
@limiter.limit("100/minute")
async def get_vehicle_status(request, vehicle_id: str, 
                             current_user: TokenData = Depends(get_current_user)):
    """Get vehicle status."""
    # Get latest telemetry
    telemetry = db.get_latest_telemetry(vehicle_id)
    if not telemetry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle {vehicle_id} not found",
        )
    
    # Get alert count
    alerts = db.get_alerts(vehicle_id=vehicle_id, limit=1)
    alert_count = len(alerts)
    
    # Determine status
    engine_temp = telemetry.get("engine_temp", 0)
    fuel_level = telemetry.get("fuel_level", 0)
    battery_voltage = telemetry.get("battery_voltage", 0)
    
    if engine_temp > 110 or fuel_level < 10 or battery_voltage < 11.5:
        status_value = "critical"
    elif engine_temp > 100 or fuel_level < 20 or battery_voltage < 12:
        status_value = "warning"
    else:
        status_value = "healthy"
    
    return VehicleStatusResponse(
        vehicle_id=vehicle_id,
        last_telemetry=TelemetryResponse(**telemetry),
        alerts_count=alert_count,
        status=status_value,
    )


# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# Startup and shutdown
@app.on_event("startup")
async def startup():
    """Startup event."""
    logger.info("API service starting")
    logger.info(f"Database: {Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}")
    logger.info(f"Redis: {Config.REDIS_HOST}:{Config.REDIS_PORT}")


@app.on_event("shutdown")
async def shutdown():
    """Shutdown event."""
    db.close()
    cache.close()
    logger.info("API service shutdown")


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    api_errors.labels(status_code=exc.status_code).inc()
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    api_errors.labels(status_code=500).inc()
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )
