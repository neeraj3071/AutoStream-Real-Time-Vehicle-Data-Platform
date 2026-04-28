# API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication

All endpoints (except `/auth/login` and `/health`) require JWT authentication via Bearer token.

### Login Endpoint

**POST** `/auth/login`

Get JWT access token for API requests.

**Request Body**:
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Usage**:
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

**Default Credentials**:
- Username: `admin`, Password: `admin123`
- Username: `user`, Password: `user123`

---

## Endpoints

### Health Check

**GET** `/health`

Check if API service is running.

**Authentication**: None required

**Response** (200 OK):
```json
{
  "status": "healthy"
}
```

---

### List Vehicles

**GET** `/vehicles`

Get list of all active vehicles (with telemetry in last 5 minutes).

**Authentication**: Required (Bearer token)

**Query Parameters**: None

**Response** (200 OK):
```json
[
  "V000",
  "V001",
  "V002",
  "V003",
  "V004"
]
```

**Example**:
```bash
curl -X GET http://localhost:8000/vehicles \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Get Latest Telemetry

**GET** `/vehicles/{vehicle_id}/latest`

Get the most recent telemetry data for a specific vehicle.

**Authentication**: Required (Bearer token)

**Path Parameters**:
- `vehicle_id` (string, required): Vehicle identifier (e.g., "V000")

**Response** (200 OK):
```json
{
  "vehicle_id": "V000",
  "timestamp": "2024-01-15T10:30:45.123456Z",
  "signals": {
    "speed": 85.5,
    "rpm": 3200,
    "engine_temp": 95.2,
    "fuel_level": 72.5,
    "battery_voltage": 13.4
  },
  "processed_at": "2024-01-15T10:30:45.654321Z"
}
```

**Errors**:
- 404: Vehicle not found
- 401: Unauthorized
- 500: Internal server error

**Example**:
```bash
curl -X GET http://localhost:8000/vehicles/V000/latest \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Get Telemetry History

**GET** `/vehicles/{vehicle_id}/history`

Get historical telemetry data for a vehicle with pagination.

**Authentication**: Required (Bearer token)

**Path Parameters**:
- `vehicle_id` (string, required): Vehicle identifier

**Query Parameters**:
- `limit` (integer, optional): Maximum records to return. Default: 100, Max: 500
- `offset` (integer, optional): Number of records to skip. Default: 0

**Response** (200 OK):
```json
[
  {
    "vehicle_id": "V000",
    "timestamp": "2024-01-15T10:30:45.123456Z",
    "signals": {
      "speed": 85.5,
      "rpm": 3200,
      "engine_temp": 95.2,
      "fuel_level": 72.5,
      "battery_voltage": 13.4
    },
    "processed_at": "2024-01-15T10:30:45.654321Z"
  },
  {
    "vehicle_id": "V000",
    "timestamp": "2024-01-15T10:30:40.123456Z",
    "signals": {
      "speed": 84.2,
      "rpm": 3150,
      "engine_temp": 94.8,
      "fuel_level": 72.6,
      "battery_voltage": 13.3
    },
    "processed_at": "2024-01-15T10:30:40.654321Z"
  }
]
```

**Example**:
```bash
curl -X GET "http://localhost:8000/vehicles/V000/history?limit=50&offset=0" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Get Vehicle Status

**GET** `/vehicles/{vehicle_id}/status`

Get overall status of a vehicle including latest telemetry and alerts.

**Authentication**: Required (Bearer token)

**Path Parameters**:
- `vehicle_id` (string, required): Vehicle identifier

**Response** (200 OK):
```json
{
  "vehicle_id": "V000",
  "last_telemetry": {
    "vehicle_id": "V000",
    "timestamp": "2024-01-15T10:30:45.123456Z",
    "signals": {
      "speed": 85.5,
      "rpm": 3200,
      "engine_temp": 95.2,
      "fuel_level": 72.5,
      "battery_voltage": 13.4
    },
    "processed_at": "2024-01-15T10:30:45.654321Z"
  },
  "alerts_count": 2,
  "status": "warning"
}
```

**Status Values**:
- `healthy`: All signals within normal ranges
- `warning`: One or more signals approaching thresholds
- `critical`: One or more signals exceeding critical thresholds

**Example**:
```bash
curl -X GET http://localhost:8000/vehicles/V000/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Get Alerts

**GET** `/alerts`

Get generated alerts with optional filtering by vehicle.

**Authentication**: Required (Bearer token)

**Query Parameters**:
- `vehicle_id` (string, optional): Filter by specific vehicle
- `limit` (integer, optional): Maximum records to return. Default: 100, Max: 500

**Response** (200 OK):
```json
[
  {
    "alert_id": "550e8400-e29b-41d4-a716-446655440000",
    "vehicle_id": "V000",
    "alert_type": "OVERHEAT",
    "severity": "WARNING",
    "timestamp": "2024-01-15T10:30:45.123456Z",
    "message": "Engine overheating: 105.2°C",
    "triggered_at": "2024-01-15T10:30:45.654321Z"
  },
  {
    "alert_id": "550e8400-e29b-41d4-a716-446655440001",
    "vehicle_id": "V001",
    "alert_type": "LOW_FUEL",
    "severity": "WARNING",
    "timestamp": "2024-01-15T10:29:30.123456Z",
    "message": "Low fuel level: 12.5%",
    "triggered_at": "2024-01-15T10:29:30.654321Z"
  }
]
```

**Alert Types**:
- `OVERHEAT`: Engine temperature warning (80-110°C)
- `TEMPERATURE_CRITICAL`: Engine temperature critical (>110°C)
- `RPM_SPIKE`: Sudden RPM increase
- `SPEED_DROP`: Sudden speed decrease
- `LOW_FUEL`: Fuel level below threshold
- `LOW_BATTERY`: Battery voltage below threshold
- `VALIDATION_ERROR`: Data validation failed

**Severity Levels**:
- `INFO`: Informational
- `WARNING`: Warning level
- `CRITICAL`: Critical level

**Examples**:
```bash
# All alerts
curl -X GET http://localhost:8000/alerts \
  -H "Authorization: Bearer YOUR_TOKEN"

# Alerts for specific vehicle
curl -X GET "http://localhost:8000/alerts?vehicle_id=V000" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Limited results
curl -X GET "http://localhost:8000/alerts?limit=50" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Get Metrics

**GET** `/metrics`

Get system-wide metrics and statistics.

**Authentication**: Required (Bearer token)

**Response** (200 OK):
```json
{
  "total_events_processed": 50000,
  "total_alerts": 245,
  "alerts_by_severity": {
    "INFO": 50,
    "WARNING": 180,
    "CRITICAL": 15
  },
  "active_vehicles": 5,
  "average_processing_latency_ms": 5.5
}
```

**Example**:
```bash
curl -X GET http://localhost:8000/metrics \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Prometheus Metrics

**GET** `/metrics` (Prometheus format)

Get raw Prometheus metrics for monitoring.

**Authentication**: None required

**Response** (200 OK):
```
# HELP api_requests_total Total API requests
# TYPE api_requests_total counter
api_requests_total{endpoint="/vehicles",method="GET"} 1234
api_requests_total{endpoint="/vehicles/V000/latest",method="GET"} 567

# HELP api_latency_seconds API request latency
# TYPE api_latency_seconds histogram
api_latency_seconds_bucket{le="0.01"} 100
api_latency_seconds_bucket{le="0.05"} 500
api_latency_seconds_bucket{le="0.1"} 1100

# HELP api_errors_total Total API errors
# TYPE api_errors_total counter
api_errors_total{status_code="404"} 12
api_errors_total{status_code="401"} 5

# HELP api_active_connections Active API connections
# TYPE api_active_connections gauge
api_active_connections 25
```

---

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Invalid or expired token"
}
```

### 404 Not Found
```json
{
  "detail": "No telemetry found for vehicle V000"
}
```

### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

API endpoints are rate-limited to prevent abuse:

- **Login endpoint**: 5 requests per minute
- **Protected endpoints**: 100 requests per minute
- **Public endpoints**: No limit

When rate limit is exceeded, API returns:
- Status Code: 429 Too Many Requests
- Header: `Retry-After: 60`

---

## Caching

Certain endpoints support caching via Redis to improve performance:

- `/vehicles` - Cached for 30 seconds
- `/vehicles/{vehicle_id}/latest` - Cached for 10 seconds
- `/metrics` - Cached for 60 seconds

Cache is automatically invalidated when new data is processed.

---

## API Versioning

Current API Version: **v1.0.0**

All endpoints are versioned and backward compatibility is maintained for at least one major version.

---

## Examples

### Python Client
```python
import requests
from datetime import datetime

# Login
response = requests.post(
    "http://localhost:8000/auth/login",
    json={"username": "admin", "password": "admin123"}
)
token = response.json()["access_token"]

# Get vehicles
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "http://localhost:8000/vehicles",
    headers=headers
)
vehicles = response.json()

# Get latest telemetry
for vehicle_id in vehicles:
    response = requests.get(
        f"http://localhost:8000/vehicles/{vehicle_id}/latest",
        headers=headers
    )
    telemetry = response.json()
    print(f"{vehicle_id}: Speed {telemetry['signals']['speed']} km/h")
```

### JavaScript/Node.js Client
```javascript
// Login
const loginResponse = await fetch("http://localhost:8000/auth/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ username: "admin", password: "admin123" })
});
const { access_token } = await loginResponse.json();

// Get vehicles
const headers = { "Authorization": `Bearer ${access_token}` };
const vehiclesResponse = await fetch("http://localhost:8000/vehicles", { headers });
const vehicles = await vehiclesResponse.json();

// Get latest telemetry
for (const vehicleId of vehicles) {
  const telemetryResponse = await fetch(
    `http://localhost:8000/vehicles/${vehicleId}/latest`,
    { headers }
  );
  const telemetry = await telemetryResponse.json();
  console.log(`${vehicleId}: Speed ${telemetry.signals.speed} km/h`);
}
```

### cURL Examples

See examples in each endpoint section above.

---

## Swagger Documentation

Interactive API documentation is available at:
```
http://localhost:8000/docs
```

This provides a UI for testing all endpoints with automatic request/response formatting.

Alternative ReDoc documentation:
```
http://localhost:8000/redoc
```
