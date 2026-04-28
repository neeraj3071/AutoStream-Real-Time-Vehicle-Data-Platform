"""Unit tests for processor module."""
import sys
sys.path.insert(0, '../processor')

import pytest
from validator import DataValidator
from anomaly_detector import AnomalyDetector
from models import AlertType, AlertSeverity


def test_valid_event():
    """Test validation of valid event."""
    event = {
        "vehicle_id": "V001",
        "timestamp": "2024-01-01T00:00:00Z",
        "signals": {
            "speed": 80.0,
            "rpm": 3000,
            "engine_temp": 90.0,
            "fuel_level": 75.0,
            "battery_voltage": 13.2
        }
    }
    
    is_valid, error = DataValidator.validate_event(event)
    assert is_valid
    assert error is None


def test_missing_fields():
    """Test validation with missing fields."""
    event = {
        "vehicle_id": "V001",
        # Missing timestamp and signals
    }
    
    is_valid, error = DataValidator.validate_event(event)
    assert not is_valid
    assert error is not None


def test_invalid_speed():
    """Test validation with invalid speed."""
    event = {
        "vehicle_id": "V001",
        "timestamp": "2024-01-01T00:00:00Z",
        "signals": {
            "speed": 350.0,  # Exceeds max
            "rpm": 3000,
            "engine_temp": 90.0,
            "fuel_level": 75.0,
            "battery_voltage": 13.2
        }
    }
    
    is_valid, error = DataValidator.validate_event(event)
    assert not is_valid


def test_anomaly_overheat():
    """Test anomaly detection for overheating."""
    signals = {
        "speed": 80.0,
        "rpm": 3000,
        "engine_temp": 105.0,  # Above threshold
        "fuel_level": 75.0,
        "battery_voltage": 13.2
    }
    
    alerts = AnomalyDetector.detect_anomalies("V001", signals, "2024-01-01T00:00:00Z")
    
    assert len(alerts) > 0
    assert any(a.alert_type == AlertType.OVERHEAT for a in alerts)


def test_anomaly_low_fuel():
    """Test anomaly detection for low fuel."""
    signals = {
        "speed": 50.0,
        "rpm": 2000,
        "engine_temp": 85.0,
        "fuel_level": 10.0,  # Below threshold
        "battery_voltage": 13.2
    }
    
    alerts = AnomalyDetector.detect_anomalies("V001", signals, "2024-01-01T00:00:00Z")
    
    assert len(alerts) > 0
    assert any(a.alert_type == AlertType.LOW_FUEL for a in alerts)


def test_anomaly_low_battery():
    """Test anomaly detection for low battery."""
    signals = {
        "speed": 50.0,
        "rpm": 2000,
        "engine_temp": 85.0,
        "fuel_level": 50.0,
        "battery_voltage": 11.8  # Below threshold
    }
    
    alerts = AnomalyDetector.detect_anomalies("V001", signals, "2024-01-01T00:00:00Z")
    
    assert len(alerts) > 0
    assert any(a.alert_type == AlertType.LOW_BATTERY for a in alerts)


def test_no_anomalies():
    """Test normal conditions with no anomalies."""
    signals = {
        "speed": 50.0,
        "rpm": 2000,
        "engine_temp": 85.0,
        "fuel_level": 50.0,
        "battery_voltage": 13.2
    }
    
    alerts = AnomalyDetector.detect_anomalies("V001", signals, "2024-01-01T00:00:00Z")
    
    assert len(alerts) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
