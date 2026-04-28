# Architecture Deep Dive

## System Design Overview

AutoStream is designed with the following architectural principles:

1. **Event-Driven**: Asynchronous message-based communication
2. **Microservices**: Independently deployable, scalable services
3. **Fault-Tolerant**: Built-in retry logic and dead-letter queues
4. **Observable**: Comprehensive metrics and logging
5. **Scalable**: Horizontal scaling via Kafka partitioning

## Component Architecture

### Data Flow

```
Vehicle Simulator
    ↓ (Kafka Producer)
vehicle.telemetry topic
    ↓ (Partitioned by vehicle_id)
Stream Processor
    ├─→ Validation
    ├─→ Transformation
    ├─→ Anomaly Detection
    ├→ PostgreSQL (Storage)
    └→ vehicle.alerts (Kafka)
    └→ vehicle.processed (Kafka)
        ↓
    FastAPI Backend
        ├→ REST API responses
        ├→ Redis cache
        └→ Prometheus metrics
```

## Detailed Component Design

### 1. Vehicle Simulator Service

**Purpose**: Generate realistic vehicle telemetry data

**Key Features**:
- Multi-vehicle simulation
- Physics-based signal changes
- Anomaly injection
- Configurable generation rate

**Scalability**:
- Horizontal scaling: Run multiple instances with different vehicle ranges
- Each instance partitions vehicles independently
- Kafka partitioning by vehicle_id ensures ordering per vehicle

**Performance**:
- 100+ events/sec per instance
- Minimal CPU/RAM overhead
- Lock-free threading model

### 2. Stream Processor Service

**Purpose**: Validate, transform, and detect anomalies in event streams

**Processing Pipeline**:
```
Input Event
    ↓
Deserialization (JSON)
    ↓
Schema Validation
    ↓
Value Range Validation
    ↓
Anomaly Detection
    ├→ Temperature checks
    ├→ Fuel level checks
    ├→ Battery voltage checks
    ├→ RPM spike detection
    └→ Speed drop detection
    ↓
Database Persistence
    ├→ Telemetry table
    └→ Alerts table
    ↓
Kafka Publishing
    ├→ vehicle.processed
    └→ vehicle.alerts
```

**Error Handling**:
- Validation failures → vehicle.alerts (VALIDATION_ERROR)
- Processing errors → Retry up to 3 times
- Persistent errors → vehicle.dlq (dead-letter queue)
- Failed records logged for manual review

**Scalability**:
- Kafka consumer group handles load distribution
- Each processor instance consumes different partitions
- Automatic rebalancing on instance failure

### 3. FastAPI Backend Service

**Purpose**: Provide REST API for querying vehicle data

**Architecture**:
```
HTTP Request
    ↓
CORS Middleware
    ↓
Rate Limiting
    ↓
JWT Authentication
    ↓
Request Routing
    ├→ Public endpoints (health)
    ├→ Auth endpoints (login)
    └→ Protected endpoints
        ↓
        ├→ Cache Check (Redis)
        │   ├→ Cache HIT → Response
        │   └→ Cache MISS → DB Query
        ├→ Database Query (PostgreSQL)
        ├→ Response Serialization
        ├→ Cache Update
        ├→ Response Headers (metrics)
        └→ Response Body
    ↓
Prometheus Metrics Recording
    ↓
HTTP Response
```

**Authentication Flow**:
```
POST /auth/login
    ↓
Credential Validation
    ├→ Check username exists
    ├→ Verify hashed password
    ├→ Generate JWT token
    ├→ Sign with secret key
    └→ Return token + expires_in
    ↓
Subsequent Requests
    ├→ Extract Bearer token
    ├→ Verify JWT signature
    ├→ Check expiration
    ├→ Extract username
    └→ Allow/Deny request
```

**Caching Strategy**:
- Latest telemetry: 10s TTL
- Active vehicles: 30s TTL
- System metrics: 60s TTL
- Cache invalidation: Automatic or manual

**Scalability**:
- Stateless design enables horizontal scaling
- Load balancer distributes requests
- Shared PostgreSQL and Redis backends

### 4. Data Layer

#### PostgreSQL Database

**Schema**:
```sql
-- Telemetry (Time-Series)
vehicle_telemetry
├─ id (PK)
├─ vehicle_id (indexed)
├─ timestamp (indexed)
├─ speed, rpm, engine_temp, fuel_level, battery_voltage
├─ created_at
└─ Composite index: (vehicle_id, timestamp)

-- Alerts
alerts
├─ alert_id (PK)
├─ vehicle_id (indexed)
├─ alert_type
├─ severity (indexed)
├─ message
├─ timestamp
└─ created_at

-- Audit Trail
processed_events
├─ id (PK)
├─ vehicle_id (indexed)
├─ source_timestamp
├─ processed_at (indexed)
├─ status
└─ error_message
```

**Performance Optimization**:
- Partitioning by date for time-series data
- Composite indexes on common queries
- Connection pooling (10-20 connections)
- Prepared statements to prevent SQL injection

**Retention**:
- Telemetry: 30 days (or configurable)
- Alerts: 90 days
- Audit logs: 1 year

#### Redis Cache

**Purpose**: Reduce database load and improve API response times

**Cache Keys**:
```
telemetry:{vehicle_id}:latest       → 10s
vehicles:active                      → 30s
metrics:system                       → 60s
```

**Eviction Policy**: LRU (Least Recently Used)

**Memory Limit**: Configurable (default: 256MB)

### 5. Event Streaming - Apache Kafka

**Topic Design**:
```
vehicle.telemetry (3 partitions)
├─ Raw telemetry events
├─ Retention: 24 hours
├─ Compression: Snappy
└─ Partition key: vehicle_id

vehicle.processed (3 partitions)
├─ Processed and validated data
├─ Retention: 24 hours
├─ Partition key: vehicle_id
└─ For downstream consumers

vehicle.alerts (1 partition)
├─ Alert events only
├─ Retention: 7 days
├─ High priority
└─ Ordered processing

vehicle.dlq (1 partition)
├─ Dead-letter queue
├─ Failed messages for replay
├─ Retention: 7 days
└─ Manual intervention needed
```

**Consumer Groups**:
```
vehicle-processor
├─ Consumes: vehicle.telemetry
├─ Partitions: 0, 1, 2 (distributed)
├─ Processing: Validation + Anomaly detection
└─ Auto-commit: Disabled (manual commit on success)
```

**Partitioning Strategy**:
- Key: vehicle_id → Ensures ordering per vehicle
- Allows parallel processing across vehicles
- Automatic rebalancing on consumer failure

### 6. Observability Stack

#### Prometheus Metrics

**Collected Metrics**:

From Simulator:
```promql
simulator_events_sent_total          # Counter
simulator_anomalies_injected_total   # Counter
```

From Processor:
```promql
processor_messages_consumed_total    # Counter
processor_messages_processed_total   # Counter
processor_messages_failed_total      # Counter
processor_processing_time_seconds    # Histogram
processor_alerts_generated_total     # Counter
processor_lag                        # Gauge
```

From API:
```promql
api_requests_total                   # Counter (by method, endpoint)
api_latency_seconds                  # Histogram
api_errors_total                     # Counter
api_active_connections               # Gauge
```

**Scrape Configuration**:
- Interval: 15 seconds
- Timeout: 10 seconds
- Retention: 30 days

#### Grafana Dashboards

**Key Dashboards**:
1. System Overview
   - Request rate
   - Error rate
   - Latency (p50, p95, p99)
   - Active connections

2. Data Pipeline
   - Events/sec in
   - Processing latency
   - Alert rate
   - DLQ depth

3. Database Performance
   - Query latency
   - Connection pool usage
   - Disk I/O

4. Vehicle Metrics
   - Vehicles per status
   - Alert distribution
   - Processing lag per vehicle

## Design Patterns

### 1. Event Sourcing

Each vehicle's state is reconstructed from the event stream:
```
Initial State + Event1 + Event2 + ... + EventN = Current State
```

### 2. CQRS (Command Query Responsibility Segregation)

- **Commands**: Write operations via Kafka (Simulator, Processor)
- **Queries**: Read operations via REST API (FastAPI)

Separate models optimize for each operation type.

### 3. Circuit Breaker

Implemented in database and cache layers:
- Failed requests → Count
- Threshold exceeded → Open circuit
- Waiting period → Half-open
- Success → Close circuit

### 4. Retry Pattern

```
Request
    ↓
Execute
    ├→ Success → Return
    └→ Failure
        ├→ Retry 1
        ├→ Retry 2
        ├→ Retry 3
        └→ Fail → DLQ
```

## Deployment Topology

### Local Development
```
Docker Desktop
├─ PostgreSQL container
├─ Redis container
├─ Kafka + Zookeeper containers
├─ Simulator container
├─ Processor container
├─ API container
├─ Prometheus container
└─ Grafana container
```

### Production (Kubernetes)
```
Kubernetes Cluster
├─ Stateful Set: PostgreSQL
├─ Stateful Set: Redis
├─ Stateful Set: Kafka Cluster
├─ Deployment: Simulator (3 replicas)
├─ Deployment: Processor (5 replicas)
├─ Deployment: API (3 replicas)
├─ StatefulSet: Prometheus
└─ Deployment: Grafana
```

## Scalability Analysis

### Simulator Scaling
- Linear scaling with instance count
- 100 events/sec per instance
- 1000 events/sec = 10 instances

### Processor Scaling
- Limited by Kafka partitions (max 3 currently)
- Each partition processes ~33 events/sec
- For higher throughput: Increase partitions

### API Scaling
- Stateless design enables unlimited horizontal scaling
- Load balancer distributes requests
- Database becomes bottleneck at scale

### Database Scaling
- Vertical: Increase CPU/RAM
- Horizontal: Replication, sharding
- Read replicas for analytics

## Security Considerations

### Authentication & Authorization
- JWT tokens with expiration
- Password hashing with bcrypt
- Rate limiting per endpoint

### Data Protection
- HTTPS/TLS in production
- Database encryption at rest
- Secrets management (vault)

### API Security
- CORS configuration
- Request validation
- SQL injection prevention (prepared statements)
- XSS protection

## Performance Optimization Techniques

1. **Partitioning**: By vehicle_id for parallelism
2. **Caching**: Redis for frequently accessed data
3. **Connection Pooling**: Reuse DB connections
4. **Batch Processing**: Commit multiple events
5. **Index Optimization**: Composite indexes on queries
6. **Asynchronous Processing**: Non-blocking I/O
7. **Message Compression**: Snappy compression on Kafka

## Monitoring & Alerting

### Key Metrics
- Event ingestion rate
- Processing latency
- Alert generation rate
- API error rate
- Database connection pool usage
- Cache hit ratio

### Alert Rules
```promql
rate(processor_messages_failed_total[5m]) > 10
processor_lag > 1000
api_errors_total > 100
api_latency_seconds > 1
```

## Trade-offs

| Decision | Advantage | Disadvantage |
|----------|-----------|--------------|
| PostgreSQL | ACID compliance, rich queries | Not ideal for extreme scale |
| Kafka | Scalable event streaming | Added operational complexity |
| Redis Caching | Fast responses, reduced DB load | Additional component to manage |
| JWT Auth | Stateless, scalable | No easy token revocation |
| Python | Rapid development, ML integration | Slower than compiled languages |

## Future Enhancements

1. **Kubernetes Support**: Helm charts, auto-scaling
2. **Machine Learning**: Anomaly detection model
3. **Time Series DB**: InfluxDB for better time-series handling
4. **Data Lake**: S3/GCS for long-term storage
5. **Real-time Dashboard**: WebSocket updates
6. **Multi-tenancy**: Support multiple organizations
7. **Compliance**: GDPR, HIPAA compliance features
8. **Advanced Analytics**: Data warehouse integration
