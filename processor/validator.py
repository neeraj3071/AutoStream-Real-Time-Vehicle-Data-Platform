"""Data validation module."""
import logging
from typing import Dict, Any, Tuple, Optional
from models import ValidationError

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates incoming telemetry data."""
    
    REQUIRED_FIELDS = {"vehicle_id", "timestamp", "signals"}
    REQUIRED_SIGNAL_FIELDS = {"speed", "rpm", "engine_temp", "fuel_level", "battery_voltage"}
    
    @staticmethod
    def validate_event(event: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate incoming event structure and values."""
        try:
            # Check required fields
            if not all(field in event for field in DataValidator.REQUIRED_FIELDS):
                missing = DataValidator.REQUIRED_FIELDS - set(event.keys())
                return False, f"Missing required fields: {missing}"
            
            # Check signals structure
            signals = event.get("signals", {})
            if not all(field in signals for field in DataValidator.REQUIRED_SIGNAL_FIELDS):
                missing = DataValidator.REQUIRED_SIGNAL_FIELDS - set(signals.keys())
                return False, f"Missing signal fields: {missing}"
            
            # Validate value ranges
            error = DataValidator._validate_ranges(signals)
            if error:
                return False, error
            
            # Validate vehicle_id format
            vehicle_id = event.get("vehicle_id", "")
            if not vehicle_id or not isinstance(vehicle_id, str):
                return False, "Invalid vehicle_id"
            
            # Validate timestamp format
            timestamp = event.get("timestamp", "")
            if not timestamp:
                return False, "Missing or invalid timestamp"
            
            return True, None
        
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False, str(e)
    
    @staticmethod
    def _validate_ranges(signals: Dict[str, Any]) -> Optional[str]:
        """Validate signal value ranges."""
        speed = signals.get("speed", 0)
        if not isinstance(speed, (int, float)) or speed < 0 or speed > 300:
            return f"Invalid speed: {speed}"
        
        rpm = signals.get("rpm", 0)
        if not isinstance(rpm, (int, float)) or rpm < 0 or rpm > 10000:
            return f"Invalid RPM: {rpm}"
        
        engine_temp = signals.get("engine_temp", 0)
        if not isinstance(engine_temp, (int, float)) or engine_temp < 40 or engine_temp > 150:
            return f"Invalid engine temperature: {engine_temp}"
        
        fuel_level = signals.get("fuel_level", 0)
        if not isinstance(fuel_level, (int, float)) or fuel_level < 0 or fuel_level > 100:
            return f"Invalid fuel level: {fuel_level}"
        
        battery_voltage = signals.get("battery_voltage", 0)
        if not isinstance(battery_voltage, (int, float)) or battery_voltage < 10 or battery_voltage > 15:
            return f"Invalid battery voltage: {battery_voltage}"
        
        return None
