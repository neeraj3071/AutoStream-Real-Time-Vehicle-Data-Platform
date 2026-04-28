"""Vehicle simulator - generates telemetry data to Kafka."""
import logging
import time
import signal
import sys
from typing import Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError
from config import Config
from vehicle_generator import VehicleDataGenerator

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VehicleSimulator:
    """Vehicle telemetry simulator."""
    
    def __init__(self):
        self.generator = VehicleDataGenerator(num_vehicles=Config.NUM_VEHICLES)
        self.producer: Optional[KafkaProducer] = None
        self.running = False
        self.events_sent = 0
    
    def initialize(self) -> None:
        """Initialize Kafka producer."""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
                client_id='vehicle-simulator',
                acks='all',  # Wait for all replicas
                retries=3,
                value_serializer=lambda v: v.encode('utf-8'),
            )
            logger.info(f"Connected to Kafka: {Config.KAFKA_BOOTSTRAP_SERVERS}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            raise
    
    def send_events(self) -> int:
        """Generate and send events to Kafka."""
        events = self.generator.generate_batch()
        sent_count = 0
        
        for event in events:
            try:
                future = self.producer.send(
                    Config.KAFKA_TOPIC,
                    value=event.to_json(),
                    key=event.vehicle_id.encode('utf-8'),
                    partition=hash(event.vehicle_id) % 3,  # Partition by vehicle_id
                )
                # Optional: Wait for send to complete (can reduce throughput)
                # record_metadata = future.get(timeout=10)
                sent_count += 1
                self.events_sent += 1
            except Exception as e:
                logger.error(f"Error sending event for {event.vehicle_id}: {e}")
        
        return sent_count
    
    def run(self) -> None:
        """Run the simulator."""
        self.running = True
        interval = 1.0 / Config.SIMULATION_RATE if Config.SIMULATION_RATE > 0 else 0.01
        
        logger.info(f"Starting simulator with {Config.NUM_VEHICLES} vehicles")
        logger.info(f"Simulation rate: {Config.SIMULATION_RATE} events/sec")
        logger.info(f"Publishing to topic: {Config.KAFKA_TOPIC}")
        
        try:
            while self.running:
                start_time = time.time()
                
                sent = self.send_events()
                
                elapsed = time.time() - start_time
                sleep_time = max(0, interval - elapsed)
                
                if self.events_sent % 1000 == 0:
                    logger.info(f"Total events sent: {self.events_sent}")
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
        
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Error during simulation: {e}", exc_info=True)
        finally:
            self.shutdown()
    
    def shutdown(self) -> None:
        """Shutdown simulator and cleanup."""
        self.running = False
        if self.producer:
            logger.info("Flushing remaining events...")
            self.producer.flush()
            self.producer.close()
        logger.info(f"Simulator shutdown. Total events sent: {self.events_sent}")


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    logger.info("Signal received, shutting down...")
    sys.exit(0)


def main() -> None:
    """Main entry point."""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    simulator = VehicleSimulator()
    simulator.initialize()
    simulator.run()


if __name__ == "__main__":
    main()
