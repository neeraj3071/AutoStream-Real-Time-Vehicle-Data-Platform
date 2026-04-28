"""Data models for API responses."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class TelemetrySignals(BaseModel):
    """Vehicle telemetry signals."""
    speed: float
    rpm: int
    engine_temp: float
    fuel_level: float
    battery_voltage: float


class TelemetryResponse(BaseModel):
    """Telemetry data response."""
    vehicle_id: str
    timestamp: str
    signals: TelemetrySignals
    processed_at: Optional[str] = None


class AlertResponse(BaseModel):
    """Alert response."""
    alert_id: str
    vehicle_id: str
    alert_type: str
    severity: str
    timestamp: str
    message: str
    triggered_at: str


class VehicleStatusResponse(BaseModel):
    """Vehicle status response."""
    vehicle_id: str
    last_telemetry: TelemetryResponse
    alerts_count: int
    status: str  # "healthy", "warning", "critical"


class MetricsResponse(BaseModel):
    """System metrics response."""
    total_events_processed: int
    total_alerts: int
    alerts_by_severity: Dict[str, int]
    average_processing_latency_ms: float
    active_vehicles: int


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserLogin(BaseModel):
    """User login request."""
    username: str
    password: str


class User(BaseModel):
    """User model."""
    username: str
    email: Optional[str] = None
    disabled: Optional[bool] = False


class TokenData(BaseModel):
    """Token payload data."""
    username: Optional[str] = None
