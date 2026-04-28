"""Configuration for stream processor."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Stream processor configuration."""
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").split(",")
    KAFKA_CONSUMER_TOPIC = os.getenv("KAFKA_CONSUMER_TOPIC", "vehicle.telemetry")
    KAFKA_PROCESSED_TOPIC = os.getenv("KAFKA_PROCESSED_TOPIC", "vehicle.processed")
    KAFKA_ALERTS_TOPIC = os.getenv("KAFKA_ALERTS_TOPIC", "vehicle.alerts")
    KAFKA_DLQ_TOPIC = os.getenv("KAFKA_DLQ_TOPIC", "vehicle.dlq")
    KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "vehicle-processor")
    MAX_RETRIES = 3
    
    # PostgreSQL
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB = os.getenv("POSTGRES_DB", "vehicle_db")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
    
    # Redis
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    
    # Anomaly detection thresholds
    ANOMALY_DETECTION_ENABLED = os.getenv("ANOMALY_DETECTION_ENABLED", "true").lower() == "true"
    TEMP_THRESHOLD = 100
    TEMP_CRITICAL = 110
    RPM_SPIKE_THRESHOLD = 1000
    SPEED_DROP_THRESHOLD = 50
    LOW_FUEL_THRESHOLD = 15
    LOW_BATTERY_THRESHOLD = 12.0
    
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
