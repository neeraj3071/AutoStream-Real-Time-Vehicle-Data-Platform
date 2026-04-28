"""Database operations."""
import logging
import psycopg2
from psycopg2 import pool
from psycopg2.extras import execute_values
from typing import Optional
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages PostgreSQL connections and operations."""
    
    def __init__(self):
        self.connection_pool: Optional[pool.SimpleConnectionPool] = None
        self._initialize_pool()
    
    def _initialize_pool(self) -> None:
        """Initialize connection pool."""
        try:
            self.connection_pool = pool.SimpleConnectionPool(
                1, 20,
                host=Config.POSTGRES_HOST,
                port=Config.POSTGRES_PORT,
                database=Config.POSTGRES_DB,
                user=Config.POSTGRES_USER,
                password=Config.POSTGRES_PASSWORD,
            )
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise
    
    def save_telemetry(self, vehicle_id: str, timestamp: str, signals: dict) -> bool:
        """Save processed telemetry to database."""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO vehicle_telemetry 
                (vehicle_id, timestamp, speed, rpm, engine_temp, fuel_level, battery_voltage)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                vehicle_id,
                timestamp,
                signals.get("speed"),
                signals.get("rpm"),
                signals.get("engine_temp"),
                signals.get("fuel_level"),
                signals.get("battery_voltage"),
            ))
            
            conn.commit()
            return True
        
        except Exception as e:
            logger.error(f"Error saving telemetry: {e}")
            if conn:
                conn.rollback()
            return False
        
        finally:
            if conn:
                self.connection_pool.putconn(conn)
    
    def save_alert(self, alert_id: str, vehicle_id: str, alert_type: str, 
                  severity: str, message: str, timestamp: str) -> bool:
        """Save alert to database."""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO alerts 
                (alert_id, vehicle_id, alert_type, severity, message, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                alert_id,
                vehicle_id,
                alert_type,
                severity,
                message,
                timestamp,
            ))
            
            conn.commit()
            return True
        
        except Exception as e:
            logger.error(f"Error saving alert: {e}")
            if conn:
                conn.rollback()
            return False
        
        finally:
            if conn:
                self.connection_pool.putconn(conn)
    
    def close(self) -> None:
        """Close all connections in pool."""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("Connection pool closed")
