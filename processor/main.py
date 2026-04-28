"""Stream processor - consumes telemetry, processes, and publishes."""
import logging
import json
import time
from typing import Optional, Dict, Any
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from config import Config
from validator import DataValidator
from anomaly_detector import AnomalyDetector
from models import ProcessedTelemetry, AlertType, AlertSeverity, Alert
from database import DatabaseManager
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
messages_consumed = Counter('processor_messages_consumed_total', 'Total messages consumed')
messages_processed = Counter('processor_messages_processed_total', 'Total messages processed successfully')
messages_failed = Counter('processor_messages_failed_total', 'Total messages failed')
processing_time = Histogram('processor_processing_time_seconds', 'Message processing time')
alerts_generated = Counter('processor_alerts_generated_total', 'Total alerts generated', ['severity'])
processing_lag = Gauge('processor_lag', 'Consumer lag')


class StreamProcessor:
    """Process vehicle telemetry from Kafka."""
    
    def __init__(self):
        self.consumer: Optional[KafkaConsumer] = None
        self.producer: Optional[KafkaProducer] = None
        self.db_manager: Optional[DatabaseManager] = None
        self.running = False
        self.retry_count = 0
    
    def initialize(self) -> None:
        """Initialize Kafka consumer, producer, and database."""
        try:
            # Initialize Kafka consumer
            self.consumer = KafkaConsumer(
                Config.KAFKA_CONSUMER_TOPIC,
                bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
                group_id=Config.KAFKA_GROUP_ID,
                auto_offset_reset='earliest',
                enable_auto_commit=False,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                session_timeout_ms=30000,
            )
            logger.info(f"Connected to Kafka consumer: {Config.KAFKA_BOOTSTRAP_SERVERS}")
            
            # Initialize Kafka producer
            self.producer = KafkaProducer(
                bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
                acks='all',
                retries=3,
                value_serializer=lambda v: v.encode('utf-8'),
            )
            logger.info("Kafka producer initialized")
            
            # Initialize database
            self.db_manager = DatabaseManager()
            logger.info("Database connection established")
        
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            raise
    
    def process_message(self, message: Dict[str, Any]) -> bool:
        """Process a single telemetry message."""
        start_time = time.time()
        
        try:
            messages_consumed.inc()
            
            # Validate
            is_valid, error_msg = DataValidator.validate_event(message)
            if not is_valid:
                logger.warning(f"Validation failed: {error_msg}")
                self._send_alert(message, AlertType.VALIDATION_ERROR, error_msg)
                messages_failed.inc()
                return False
            
            vehicle_id = message["vehicle_id"]
            timestamp = message["timestamp"]
            signals = message["signals"]
            
            # Detect anomalies
            alerts = AnomalyDetector.detect_anomalies(vehicle_id, signals, timestamp)
            for alert in alerts:
                self._publish_alert(alert)
                self.db_manager.save_alert(
                    alert.alert_id,
                    alert.vehicle_id,
                    alert.alert_type.value,
                    alert.severity.value,
                    alert.message,
                    alert.timestamp,
                )
                alerts_generated.labels(severity=alert.severity.value).inc()
            
            # Create processed telemetry
            processed = ProcessedTelemetry(
                vehicle_id=vehicle_id,
                timestamp=timestamp,
                speed=signals.get("speed"),
                rpm=signals.get("rpm"),
                engine_temp=signals.get("engine_temp"),
                fuel_level=signals.get("fuel_level"),
                battery_voltage=signals.get("battery_voltage"),
                processed_at=datetime.utcnow().isoformat() + "Z",
            )
            
            # Save to database
            self.db_manager.save_telemetry(vehicle_id, timestamp, signals)
            
            # Publish to processed topic
            self.producer.send(
                Config.KAFKA_PROCESSED_TOPIC,
                value=processed.to_json(),
                key=vehicle_id.encode('utf-8'),
            )
            
            messages_processed.inc()
            elapsed = time.time() - start_time
            processing_time.observe(elapsed)
            
            return True
        
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            messages_failed.inc()
            return False
    
    def _publish_alert(self, alert: Alert) -> None:
        """Publish alert to Kafka."""
        try:
            self.producer.send(
                Config.KAFKA_ALERTS_TOPIC,
                value=alert.to_json(),
                key=alert.vehicle_id.encode('utf-8'),
            )
        except Exception as e:
            logger.error(f"Error publishing alert: {e}")
    
    def _send_alert(self, message: Dict[str, Any], alert_type: AlertType, details: str) -> None:
        """Send validation error alert."""
        vehicle_id = message.get("vehicle_id", "unknown")
        timestamp = message.get("timestamp", datetime.utcnow().isoformat() + "Z")
        
        alert = Alert(
            alert_id=f"{vehicle_id}-{int(time.time())}",
            vehicle_id=vehicle_id,
            alert_type=alert_type,
            severity=AlertSeverity.WARNING,
            timestamp=timestamp,
            message=details,
            triggered_at=datetime.utcnow().isoformat() + "Z",
        )
        self._publish_alert(alert)
    
    def run(self) -> None:
        """Run the processor."""
        self.running = True
        logger.info(f"Starting processor. Consuming from {Config.KAFKA_CONSUMER_TOPIC}")
        
        try:
            while self.running:
                messages = self.consumer.poll(timeout_ms=1000, max_records=100)
                
                if not messages:
                    continue
                
                for topic_partition, records in messages.items():
                    for record in records:
                        success = self.process_message(record.value)
                        if success:
                            self.consumer.commit()
                        else:
                            logger.error(f"Failed to process message, may retry")
        
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Error during processing: {e}", exc_info=True)
        finally:
            self.shutdown()
    
    def shutdown(self) -> None:
        """Shutdown processor and cleanup."""
        self.running = False
        if self.consumer:
            self.consumer.close()
        if self.producer:
            self.producer.flush()
            self.producer.close()
        if self.db_manager:
            self.db_manager.close()
        logger.info("Processor shutdown complete")


def main() -> None:
    """Main entry point."""
    # Start Prometheus metrics server
    start_http_server(8001)
    logger.info("Prometheus metrics server started on port 8001")
    
    processor = StreamProcessor()
    processor.initialize()
    processor.run()


if __name__ == "__main__":
    main()
