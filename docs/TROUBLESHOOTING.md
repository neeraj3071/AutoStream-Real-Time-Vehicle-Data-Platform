# Troubleshooting Guide

## Common Issues and Solutions

### Issue: Services Won't Start

**Error**: `docker-compose up` fails or services exit immediately

**Debugging Steps**:
```bash
# Check Docker daemon
docker ps

# View service logs
docker-compose logs simulator
docker-compose logs processor
docker-compose logs api

# Rebuild images
docker-compose down --volumes
docker-compose up --build
```

**Solutions**:
1. Ensure Docker Desktop is running
2. Check available disk space: `docker system df`
3. Clear dangling images: `docker system prune`
4. Rebuild specific service: `docker-compose build --no-cache service-name`

---

### Issue: Port Already in Use

**Error**: `Error response from daemon: Ports are not available`

**Solution**:
```bash
# Find what's using the port (macOS/Linux)
lsof -i :8000
lsof -i :5432
lsof -i :6379
lsof -i :9092

# Kill process
kill -9 <PID>

# Or change ports in docker-compose.yml
# ports:
#   - "8001:8000"  # Map 8001 externally to 8000 internally
```

---

### Issue: PostgreSQL Connection Refused

**Error**: `psycopg2.OperationalError: could not connect to server`

**Debugging**:
```bash
# Check if postgres is running
docker ps | grep postgres

# Check postgres logs
docker-compose logs postgres

# Test connection
docker exec autostream-postgres psql -U postgres -c "\l"

# Check network
docker network inspect autostream
```

**Solutions**:
1. Wait for PostgreSQL to be ready (health check)
2. Verify environment variables in processor/.env and api-service/.env
3. Reset database:
   ```bash
   docker-compose down postgres
   docker volume rm autostream_postgres_data
   docker-compose up postgres
   ```

---

### Issue: Kafka Topics Not Created

**Error**: `Exception in thread "main" java.lang.ClassNotFoundException: org.apache.kafka.common.security.JaasConfig`

**Debugging**:
```bash
# Check Kafka logs
docker-compose logs kafka

# Check if kafka-init completed
docker-compose logs kafka-init

# Manually verify topics
docker exec autostream-kafka kafka-topics --bootstrap-server localhost:9092 --list
```

**Solutions**:
1. Wait longer for Kafka to be ready (takes ~30 seconds)
2. Manually create topics:
   ```bash
   docker exec autostream-kafka kafka-topics \
     --create --if-not-exists \
     --bootstrap-server localhost:9092 \
     --topic vehicle.telemetry \
     --partitions 3 \
     --replication-factor 1
   ```
3. Check Zookeeper status:
   ```bash
   docker exec autostream-zookeeper zkServer.sh status
   ```

---

### Issue: API Service Returns 401 Unauthorized

**Error**: `{"detail":"Authorization header missing"}`

**Debugging**:
```bash
# Test without auth (should work)
curl http://localhost:8000/health

# Get token first
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Use token
TOKEN="eyJhbGc..."
curl -X GET http://localhost:8000/vehicles \
  -H "Authorization: Bearer $TOKEN"
```

**Solutions**:
1. Ensure token is obtained from `/auth/login`
2. Check token format: `Bearer YOUR_TOKEN` (space-separated)
3. Verify JWT_SECRET_KEY is same in all services
4. Check token expiration: default is 24 hours
5. Clear browser cache if using web UI

---

### Issue: Database Connection Pool Exhausted

**Error**: `too many connections to psycopg2 connection pool`

**Debugging**:
```bash
# Check active connections
docker exec autostream-postgres psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# Check by connection state
docker exec autostream-postgres psql -U postgres -c \
  "SELECT datname, usename, state, count(*) FROM pg_stat_activity GROUP BY datname, usename, state;"
```

**Solutions**:
1. Increase connection pool size in database.py:
   ```python
   pool.SimpleConnectionPool(1, 50, ...)  # Increase from 10 to 50
   ```
2. Close idle connections:
   ```bash
   docker exec autostream-postgres psql -U postgres -c \
     "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state='idle';"
   ```
3. Restart services to reset connections:
   ```bash
   docker-compose restart processor api
   ```

---

### Issue: Out of Memory

**Error**: `java.lang.OutOfMemoryError` or container killed

**Debugging**:
```bash
# Check memory usage
docker stats

# Check memory limit
docker inspect autostream-kafka | grep -i memory
```

**Solutions**:
1. Increase Docker memory:
   - Docker Desktop Settings → Resources → Memory
   - Set to at least 8GB
2. Reduce batch sizes in processor
3. Reduce data retention in Kafka:
   ```bash
   docker exec autostream-kafka kafka-configs \
     --bootstrap-server localhost:9092 \
     --entity-type topics \
     --entity-name vehicle.telemetry \
     --alter \
     --add-config retention.ms=43200000
   ```

---

### Issue: Slow API Responses

**Error**: Requests taking >1 second

**Debugging**:
```bash
# Check latency metrics
curl http://localhost:9090/api/v1/query?query=api_latency_seconds

# Check database query time
docker exec autostream-postgres psql -U postgres -d vehicle_db -c \
  "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 5;"

# Check Redis hit ratio
docker exec autostream-redis redis-cli INFO stats | grep hits
```

**Solutions**:
1. Increase Redis cache TTL for frequently accessed data
2. Add database indexes:
   ```sql
   CREATE INDEX idx_vehicle_timestamp ON vehicle_telemetry(vehicle_id, timestamp DESC);
   ```
3. Scale API service horizontally:
   ```bash
   # Update docker-compose.yml
   api:
     deploy:
       replicas: 3
   ```
4. Check network latency:
   ```bash
   docker exec autostream-api ping processor
   ```

---

### Issue: High CPU Usage

**Error**: One or more containers using 100% CPU

**Debugging**:
```bash
# Identify hot container
docker stats

# Check top processes in container
docker exec autostream-processor top -b -n 1

# Check for infinite loops in logs
docker-compose logs processor | tail -100
```

**Solutions**:
1. Check for tight loops in code
2. Add exponential backoff to retries
3. Reduce simulation rate:
   ```bash
   # simulator/.env
   SIMULATION_RATE=50  # Reduce from 100
   ```
4. Increase batch size in processor:
   ```python
   messages = consumer.poll(timeout_ms=1000, max_records=500)  # Increase from 100
   ```

---

### Issue: Data Loss

**Error**: Events disappearing from database

**Debugging**:
```bash
# Check Kafka message lag
docker exec autostream-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group vehicle-processor \
  --describe

# Check processor logs for failures
docker-compose logs processor | grep -i error

# Count events at each stage
# In Kafka topic
docker exec autostream-kafka kafka-run-class kafka.tools.JmxTool \
  --object-name kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec

# In database
docker exec autostream-postgres psql -U postgres -d vehicle_db \
  -c "SELECT COUNT(*) FROM vehicle_telemetry;"
```

**Solutions**:
1. Check processor logs for validation errors
2. Review dead-letter queue:
   ```bash
   docker exec autostream-kafka kafka-console-consumer \
     --bootstrap-server localhost:9092 \
     --topic vehicle.dlq \
     --from-beginning
   ```
3. Verify database commits:
   ```python
   # In processor/main.py, ensure manual commit
   self.consumer.commit()  # After successful processing
   ```
4. Increase Kafka retention:
   ```bash
   docker exec autostream-kafka kafka-configs \
     --bootstrap-server localhost:9092 \
     --entity-type topics \
     --entity-name vehicle.telemetry \
     --alter \
     --add-config retention.ms=604800000  # 7 days
   ```

---

### Issue: Prometheus Not Scraping Metrics

**Error**: No metrics in Prometheus dashboard

**Debugging**:
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check specific service metrics
curl http://localhost:8001/metrics  # processor

# Check Prometheus logs
docker-compose logs prometheus
```

**Solutions**:
1. Ensure services expose metrics on correct port:
   ```
   Processor: 8001/metrics
   API: 8000/metrics
   ```
2. Verify prometheus.yml configuration:
   ```yaml
   scrape_configs:
     - job_name: 'processor'
       static_configs:
         - targets: ['processor:8001']  # Use container name, not localhost
   ```
3. Wait 60+ seconds for metrics to be collected
4. Check service logs for metric errors:
   ```bash
   docker-compose logs api | grep -i prometheus
   ```

---

### Issue: Grafana Dashboards Empty

**Error**: Panels showing "No data"

**Debugging**:
```bash
# Verify Prometheus datasource
# In Grafana UI: Configuration → Data Sources → Prometheus → Test

# Check Prometheus queries
curl 'http://localhost:9090/api/v1/query?query=up'
```

**Solutions**:
1. Wait for metrics to be collected (first scrape takes 15+ seconds)
2. Verify Prometheus is running:
   ```bash
   docker-compose logs prometheus
   ```
3. Check datasource URL in Grafana (should be `http://prometheus:9090`)
4. Re-import dashboard:
   - Grafana UI → Dashboards → New → Import
   - Use Postman Collection dashboard template

---

## Performance Tuning

### Simulator Optimization
```bash
# Increase simulation rate
SIMULATION_RATE=1000  # Max theoretical events/sec per instance

# Run multiple instances
docker-compose up --scale simulator=3
```

### Processor Optimization
```bash
# Increase batch size in main.py
messages = consumer.poll(timeout_ms=1000, max_records=1000)

# Increase consumer threads
KAFKA_BOOTSTRAP_SERVERS=localhost:9092 consumer.max.poll.records=500
```

### API Optimization
```bash
# Increase Redis cache TTL
REDIS_CACHE_TTL=7200  # 2 hours

# Increase connection pool
# In database.py: pool.SimpleConnectionPool(1, 50, ...)
```

### Database Optimization
```sql
-- Analyze table statistics
ANALYZE vehicle_telemetry;

-- Vacuum to clean up
VACUUM FULL ANALYZE vehicle_telemetry;

-- Create partial indexes
CREATE INDEX idx_active_vehicles 
ON vehicle_telemetry(vehicle_id) 
WHERE timestamp > NOW() - INTERVAL '5 minutes';
```

---

## Monitoring Commands

```bash
# Watch service logs in real-time
docker-compose logs -f

# Monitor resources
docker stats

# Check network
docker network inspect autostream

# Database connections
docker exec autostream-postgres psql -U postgres -c \
  "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"

# Kafka topics
docker exec autostream-kafka kafka-topics --bootstrap-server localhost:9092 --list --describe

# Consumer lag
docker exec autostream-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --all-groups \
  --describe
```

---

## Getting Help

1. **Check logs**: `docker-compose logs [service]`
2. **Verify connectivity**: `docker exec [container] ping [destination]`
3. **Test manually**: Use curl, Postman, or Python requests
4. **Review metrics**: Check Prometheus at http://localhost:9090
5. **Check documentation**: See [README.md](../README.md) and [ARCHITECTURE.md](ARCHITECTURE.md)

If issues persist:
- Collect logs: `docker-compose logs > logs.txt`
- Run diagnostics: `docker-compose exec processor python -m pdb -m main`
- Reset everything: `docker-compose down -v && docker-compose up`
