"""Data models and validation."""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
import json


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertType(str, Enum):
    """Alert types."""
    OVERHEAT = "OVERHEAT"
    TEMPERATURE_CRITICAL = "TEMPERATURE_CRITICAL"
    RPM_SPIKE = "RPM_SPIKE"
    SPEED_DROP = "SPEED_DROP"
    LOW_FUEL = "LOW_FUEL"
    LOW_BATTERY = "LOW_BATTERY"
    VALIDATION_ERROR = "VALIDATION_ERROR"


@dataclass
class ProcessedTelemetry:
    """Processed telemetry data."""
    vehicle_id: str
    timestamp: str
    speed: float
    rpm: int
    engine_temp: float
    fuel_level: float
    battery_voltage: float
    processed_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class Alert:
    """Alert event."""
    alert_id: str
    vehicle_id: str
    alert_type: AlertType
    severity: AlertSeverity
    timestamp: str
    message: str
    triggered_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "vehicle_id": self.vehicle_id,
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp,
            "message": self.message,
            "triggered_at": self.triggered_at,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class ValidationError(Exception):
    """Validation error."""
    pass
