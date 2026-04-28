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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for vehicle_telemetry
CREATE INDEX IF NOT EXISTS idx_vehicle_id ON vehicle_telemetry(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_timestamp ON vehicle_telemetry(timestamp);
CREATE INDEX IF NOT EXISTS idx_vehicle_timestamp ON vehicle_telemetry(vehicle_id, timestamp DESC);

-- Create alerts table
CREATE TABLE IF NOT EXISTS alerts (
    alert_id VARCHAR(255) PRIMARY KEY,
    vehicle_id VARCHAR(50) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for alerts
CREATE INDEX IF NOT EXISTS idx_alerts_vehicle_id ON alerts(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp);

-- Create processed_events table (for audit trail)
CREATE TABLE IF NOT EXISTS processed_events (
    id SERIAL PRIMARY KEY,
    vehicle_id VARCHAR(50) NOT NULL,
    source_timestamp TIMESTAMP NOT NULL,
    processed_at TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL,
    error_message TEXT
);

-- Create indexes for processed_events
CREATE INDEX IF NOT EXISTS idx_processed_events_vehicle_id ON processed_events(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_processed_events_processed_at ON processed_events(processed_at);
