"""Configuration module for vehicle simulator."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Simulator configuration."""

    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").split(",")
    KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "vehicle.telemetry")
    
    # Simulation parameters
    SIMULATION_RATE = int(os.getenv("SIMULATION_RATE", "100"))  # events per second
    NUM_VEHICLES = int(os.getenv("NUM_VEHICLES", "5"))
    
    # Signal ranges (realistic CAN-like signals)
    SPEED_MIN = 0
    SPEED_MAX = 200  # km/h
    RPM_MIN = 0
    RPM_MAX = 8000
    ENGINE_TEMP_MIN = 60
    ENGINE_TEMP_MAX = 120  # Celsius
    FUEL_LEVEL_MIN = 0
    FUEL_LEVEL_MAX = 100  # percentage
    BATTERY_VOLTAGE_MIN = 11.0
    BATTERY_VOLTAGE_MAX = 14.5  # volts
    
    # Anomaly thresholds
    TEMP_THRESHOLD = 100  # Celsius
    TEMP_CRITICAL = 110
    RPM_SPIKE_THRESHOLD = 1000  # RPM increase in short period
    SPEED_DROP_THRESHOLD = 50  # km/h sudden drop
    LOW_FUEL_THRESHOLD = 15  # percentage
    LOW_BATTERY_THRESHOLD = 12.0  # volts
    
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
