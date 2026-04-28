"""Vehicle telemetry data generator."""
import random
import numpy as np
from datetime import datetime
from typing import List
from config import Config
from models import VehicleState, VehicleSignals, TelemetryEvent


class VehicleDataGenerator:
    """Generate realistic vehicle telemetry data."""
    
    def __init__(self, num_vehicles: int = Config.NUM_VEHICLES):
        self.num_vehicles = num_vehicles
        self.vehicles: List[VehicleState] = [
            VehicleState(f"V{i:03d}") for i in range(num_vehicles)
        ]
    
    def generate_event(self, vehicle: VehicleState) -> TelemetryEvent:
        """Generate a telemetry event for a vehicle."""
        self._update_vehicle_state(vehicle)
        
        timestamp = datetime.utcnow().isoformat() + "Z"
        signals = vehicle.to_signals()
        
        return TelemetryEvent(
            vehicle_id=vehicle.vehicle_id,
            timestamp=timestamp,
            signals=signals,
        )
    
    def _update_vehicle_state(self, vehicle: VehicleState) -> None:
        """Update vehicle state with realistic physics."""
        # Simulate speed with random acceleration/deceleration
        speed_change = random.uniform(-5, 10)  # km/h per update
        vehicle.speed = max(Config.SPEED_MIN, min(
            Config.SPEED_MAX,
            vehicle.speed + speed_change
        ))
        
        # RPM follows speed (rough correlation)
        base_rpm = int(vehicle.speed * 40)
        rpm_noise = random.randint(-200, 200)
        vehicle.rpm = max(Config.RPM_MIN, min(
            Config.RPM_MAX,
            base_rpm + rpm_noise
        ))
        
        # Engine temperature slowly increases with driving, decreases at idle
        if vehicle.speed > 5:
            temp_change = random.uniform(0.1, 0.5)
        else:
            temp_change = random.uniform(-0.5, 0.1)
        
        vehicle.engine_temp = max(
            Config.ENGINE_TEMP_MIN,
            min(Config.ENGINE_TEMP_MAX, vehicle.engine_temp + temp_change)
        )
        
        # Fuel consumption (roughly 0.001% per km)
        fuel_consumption = (vehicle.speed / 1000) * 0.1
        vehicle.fuel_level = max(0, vehicle.fuel_level - fuel_consumption)
        
        # Battery voltage decreases slightly with load, increases at idle
        if vehicle.rpm > 2000:
            voltage_change = random.uniform(-0.02, 0.01)
        else:
            voltage_change = random.uniform(0.01, 0.03)
        
        vehicle.battery_voltage = max(
            Config.BATTERY_VOLTAGE_MIN,
            min(Config.BATTERY_VOLTAGE_MAX, vehicle.battery_voltage + voltage_change)
        )
        
        # Occasionally inject anomalies (10% chance per update)
        if random.random() < 0.1:
            self._inject_anomaly(vehicle)
    
    def _inject_anomaly(self, vehicle: VehicleState) -> None:
        """Randomly inject anomalies into vehicle state."""
        anomaly_type = random.choice([
            "overheat",
            "rpm_spike",
            "speed_drop",
            "low_fuel",
            "low_battery"
        ])
        
        if anomaly_type == "overheat":
            vehicle.engine_temp = random.uniform(105, 115)
        elif anomaly_type == "rpm_spike":
            vehicle.rpm = min(Config.RPM_MAX, vehicle.rpm + random.randint(1000, 2000))
        elif anomaly_type == "speed_drop":
            vehicle.speed = max(0, vehicle.speed - random.uniform(20, 50))
        elif anomaly_type == "low_fuel":
            vehicle.fuel_level = random.uniform(5, 20)
        elif anomaly_type == "low_battery":
            vehicle.battery_voltage = random.uniform(11.0, 11.9)
    
    def generate_batch(self) -> List[TelemetryEvent]:
        """Generate one event per vehicle."""
        return [self.generate_event(vehicle) for vehicle in self.vehicles]
