"""Unit tests for simulator module."""
import sys
sys.path.insert(0, '../simulator')

import pytest
from vehicle_generator import VehicleDataGenerator
from models import VehicleState, VehicleSignals, TelemetryEvent
from config import Config


def test_vehicle_state_creation():
    """Test vehicle state initialization."""
    vehicle = VehicleState("V001")
    assert vehicle.vehicle_id == "V001"
    assert vehicle.speed == 0.0
    assert vehicle.rpm == 0
    assert vehicle.engine_temp == 80.0
    assert vehicle.fuel_level == 100.0
    assert vehicle.battery_voltage == 13.5


def test_vehicle_signals_generation():
    """Test vehicle signals conversion."""
    vehicle = VehicleState("V001")
    signals = vehicle.to_signals()
    
    assert isinstance(signals, VehicleSignals)
    assert signals.speed == 0.0
    assert signals.rpm == 0


def test_telemetry_event_creation():
    """Test telemetry event creation."""
    signals = VehicleSignals(
        speed=80.0,
        rpm=3000,
        engine_temp=95.0,
        fuel_level=75.0,
        battery_voltage=13.2
    )
    
    event = TelemetryEvent(
        vehicle_id="V001",
        timestamp="2024-01-01T00:00:00Z",
        signals=signals
    )
    
    assert event.vehicle_id == "V001"
    assert event.signals.speed == 80.0
    
    # Test JSON serialization
    json_str = event.to_json()
    assert "V001" in json_str
    assert "80.0" in json_str


def test_data_generator_batch():
    """Test batch event generation."""
    generator = VehicleDataGenerator(num_vehicles=3)
    batch = generator.generate_batch()
    
    assert len(batch) == 3
    assert all(isinstance(event, TelemetryEvent) for event in batch)
    assert len(set(e.vehicle_id for e in batch)) == 3


def test_signal_ranges():
    """Test that signals stay within valid ranges."""
    generator = VehicleDataGenerator(num_vehicles=1)
    
    for _ in range(100):
        batch = generator.generate_batch()
        for event in batch:
            signals = event.signals
            assert Config.SPEED_MIN <= signals.speed <= Config.SPEED_MAX
            assert Config.RPM_MIN <= signals.rpm <= Config.RPM_MAX
            assert Config.ENGINE_TEMP_MIN <= signals.engine_temp <= Config.ENGINE_TEMP_MAX
            assert Config.FUEL_LEVEL_MIN <= signals.fuel_level <= Config.FUEL_LEVEL_MAX
            assert Config.BATTERY_VOLTAGE_MIN <= signals.battery_voltage <= Config.BATTERY_VOLTAGE_MAX


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
