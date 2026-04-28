-- Create database
CREATE DATABASE IF NOT EXISTS vehicle_db;

-- Create vehicle_telemetry table
CREATE TABLE IF NOT EXISTS vehicle_telemetry (
    id SERIAL PRIMARY KEY,
    vehicle_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    speed FLOAT NOT NULL,
    rpm INTEGER NOT NULL,
    engine_temp FLOAT NOT NULL,
    fuel_level FLOAT NOT NULL,
    battery_voltage FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_vehicle_id (vehicle_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_vehicle_timestamp (vehicle_id, timestamp DESC)
);

-- Create alerts table
CREATE TABLE IF NOT EXISTS alerts (
    alert_id VARCHAR(255) PRIMARY KEY,
    vehicle_id VARCHAR(50) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_vehicle_id (vehicle_id),
    INDEX idx_severity (severity),
    INDEX idx_timestamp (timestamp)
);

-- Create processed_events table (for audit trail)
CREATE TABLE IF NOT EXISTS processed_events (
    id SERIAL PRIMARY KEY,
    vehicle_id VARCHAR(50) NOT NULL,
    source_timestamp TIMESTAMP NOT NULL,
    processed_at TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    INDEX idx_vehicle_id (vehicle_id),
    INDEX idx_processed_at (processed_at)
);
