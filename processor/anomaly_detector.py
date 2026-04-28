"""Anomaly detection module."""
import logging
from typing import List, Optional
from datetime import datetime
from models import Alert, AlertType, AlertSeverity
from config import Config
import uuid

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Detects anomalies in vehicle telemetry."""
    
    @staticmethod
    def detect_anomalies(vehicle_id: str, signals: dict, timestamp: str) -> List[Alert]:
        """Detect anomalies and return list of alerts."""
        if not Config.ANOMALY_DETECTION_ENABLED:
            return []
        
        alerts = []
        
        # Engine temperature checks
        engine_temp = signals.get("engine_temp", 0)
        if engine_temp >= Config.TEMP_CRITICAL:
            alerts.append(AnomalyDetector._create_alert(
                vehicle_id=vehicle_id,
                alert_type=AlertType.TEMPERATURE_CRITICAL,
                severity=AlertSeverity.CRITICAL,
                message=f"Engine temperature critical: {engine_temp}°C",
                timestamp=timestamp,
            ))
        elif engine_temp >= Config.TEMP_THRESHOLD:
            alerts.append(AnomalyDetector._create_alert(
                vehicle_id=vehicle_id,
                alert_type=AlertType.OVERHEAT,
                severity=AlertSeverity.WARNING,
                message=f"Engine overheating: {engine_temp}°C",
                timestamp=timestamp,
            ))
        
        # Fuel level check
        fuel_level = signals.get("fuel_level", 0)
        if fuel_level < Config.LOW_FUEL_THRESHOLD:
            alerts.append(AnomalyDetector._create_alert(
                vehicle_id=vehicle_id,
                alert_type=AlertType.LOW_FUEL,
                severity=AlertSeverity.WARNING,
                message=f"Low fuel level: {fuel_level}%",
                timestamp=timestamp,
            ))
        
        # Battery voltage check
        battery_voltage = signals.get("battery_voltage", 0)
        if battery_voltage < Config.LOW_BATTERY_THRESHOLD:
            alerts.append(AnomalyDetector._create_alert(
                vehicle_id=vehicle_id,
                alert_type=AlertType.LOW_BATTERY,
                severity=AlertSeverity.WARNING,
                message=f"Low battery voltage: {battery_voltage}V",
                timestamp=timestamp,
            ))
        
        return alerts
    
    @staticmethod
    def _create_alert(vehicle_id: str, alert_type: AlertType, 
                     severity: AlertSeverity, message: str, 
                     timestamp: str) -> Alert:
        """Create an alert object."""
        return Alert(
            alert_id=str(uuid.uuid4()),
            vehicle_id=vehicle_id,
            alert_type=alert_type,
            severity=severity,
            timestamp=timestamp,
            message=message,
            triggered_at=datetime.utcnow().isoformat() + "Z",
        )
