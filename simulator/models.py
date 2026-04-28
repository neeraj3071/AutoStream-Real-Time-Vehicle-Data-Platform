"""Data models for vehicle telemetry."""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any
import json


@dataclass
class VehicleSignals:
    """Vehicle CAN-like signals."""
    speed: float  # km/h
    rpm: int  # RPM
    engine_temp: float  # Celsius
    fuel_level: float  # percentage
    battery_voltage: float  # volts


@dataclass
class TelemetryEvent:
    """Vehicle telemetry event."""
    vehicle_id: str
    timestamp: str
    signals: VehicleSignals
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "vehicle_id": self.vehicle_id,
            "timestamp": self.timestamp,
            "signals": {
                "speed": self.signals.speed,
                "rpm": self.signals.rpm,
                "engine_temp": self.signals.engine_temp,
                "fuel_level": self.signals.fuel_level,
                "battery_voltage": self.signals.battery_voltage,
            }
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class VehicleState:
    """Current state of a vehicle for simulation."""
    
    def __init__(self, vehicle_id: str):
        self.vehicle_id = vehicle_id
        self.speed = 0.0
        self.rpm = 0
        self.engine_temp = 80.0
        self.fuel_level = 100.0
        self.battery_voltage = 13.5
        self.last_timestamp = None
    
    def to_signals(self) -> VehicleSignals:
        """Convert state to signals."""
        return VehicleSignals(
            speed=self.speed,
            rpm=self.rpm,
            engine_temp=self.engine_temp,
            fuel_level=self.fuel_level,
            battery_voltage=self.battery_voltage,
        )
