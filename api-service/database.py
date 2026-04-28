"""Database operations for API."""
import logging
import psycopg2
from psycopg2 import pool
from typing import Optional, List, Dict, Any
from config import Config

logger = logging.getLogger(__name__)


class APIDatabase:
    """Database operations for API."""
    
    def __init__(self):
        self.connection_pool: Optional[pool.SimpleConnectionPool] = None
        self._initialize_pool()
    
    def _initialize_pool(self) -> None:
        """Initialize connection pool."""
        try:
            self.connection_pool = pool.SimpleConnectionPool(
                1, 10,
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
    
    def get_latest_telemetry(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        """Get latest telemetry for a vehicle."""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            cursor = conn.cursor()
            
            query = """
                SELECT vehicle_id, timestamp, speed, rpm, engine_temp, 
                       fuel_level, battery_voltage
                FROM vehicle_telemetry
                WHERE vehicle_id = %s
                ORDER BY timestamp DESC
                LIMIT 1
            """
            
            cursor.execute(query, (vehicle_id,))
            result = cursor.fetchone()
            
            if not result:
                return None
            
            return {
                "vehicle_id": result[0],
                "timestamp": result[1].isoformat() if result[1] else None,
                "speed": result[2],
                "rpm": result[3],
                "engine_temp": result[4],
                "fuel_level": result[5],
                "battery_voltage": result[6],
            }
        
        except Exception as e:
            logger.error(f"Error getting latest telemetry: {e}")
            return None
        
        finally:
            if conn:
                self.connection_pool.putconn(conn)
    
    def get_telemetry_history(self, vehicle_id: str, limit: int = 100, 
                             offset: int = 0) -> List[Dict[str, Any]]:
        """Get telemetry history for a vehicle."""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            cursor = conn.cursor()
            
            query = """
                SELECT vehicle_id, timestamp, speed, rpm, engine_temp, 
                       fuel_level, battery_voltage
                FROM vehicle_telemetry
                WHERE vehicle_id = %s
                ORDER BY timestamp DESC
                LIMIT %s OFFSET %s
            """
            
            cursor.execute(query, (vehicle_id, limit, offset))
            results = cursor.fetchall()
            
            return [
                {
                    "vehicle_id": row[0],
                    "timestamp": row[1].isoformat() if row[1] else None,
                    "speed": row[2],
                    "rpm": row[3],
                    "engine_temp": row[4],
                    "fuel_level": row[5],
                    "battery_voltage": row[6],
                }
                for row in results
            ]
        
        except Exception as e:
            logger.error(f"Error getting telemetry history: {e}")
            return []
        
        finally:
            if conn:
                self.connection_pool.putconn(conn)
    
    def get_active_vehicles(self) -> List[str]:
        """Get list of active vehicles."""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            cursor = conn.cursor()
            
            query = """
                SELECT DISTINCT vehicle_id
                FROM vehicle_telemetry
                WHERE timestamp > NOW() - INTERVAL '5 minutes'
                ORDER BY vehicle_id
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            return [row[0] for row in results]
        
        except Exception as e:
            logger.error(f"Error getting active vehicles: {e}")
            return []
        
        finally:
            if conn:
                self.connection_pool.putconn(conn)
    
    def get_alerts(self, vehicle_id: Optional[str] = None, 
                  limit: int = 100) -> List[Dict[str, Any]]:
        """Get alerts, optionally filtered by vehicle."""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            cursor = conn.cursor()
            
            if vehicle_id:
                query = """
                    SELECT alert_id, vehicle_id, alert_type, severity, 
                           message, timestamp
                    FROM alerts
                    WHERE vehicle_id = %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                """
                cursor.execute(query, (vehicle_id, limit))
            else:
                query = """
                    SELECT alert_id, vehicle_id, alert_type, severity, 
                           message, timestamp
                    FROM alerts
                    ORDER BY timestamp DESC
                    LIMIT %s
                """
                cursor.execute(query, (limit,))
            
            results = cursor.fetchall()
            
            return [
                {
                    "alert_id": row[0],
                    "vehicle_id": row[1],
                    "alert_type": row[2],
                    "severity": row[3],
                    "message": row[4],
                    "timestamp": row[5].isoformat() if row[5] else None,
                }
                for row in results
            ]
        
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return []
        
        finally:
            if conn:
                self.connection_pool.putconn(conn)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics."""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            cursor = conn.cursor()
            
            # Total events
            cursor.execute("SELECT COUNT(*) FROM vehicle_telemetry")
            total_events = cursor.fetchone()[0] or 0
            
            # Total alerts
            cursor.execute("SELECT COUNT(*) FROM alerts")
            total_alerts = cursor.fetchone()[0] or 0
            
            # Alerts by severity
            cursor.execute("""
                SELECT severity, COUNT(*) as count
                FROM alerts
                GROUP BY severity
            """)
            alerts_by_severity = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Active vehicles
            cursor.execute("""
                SELECT COUNT(DISTINCT vehicle_id)
                FROM vehicle_telemetry
                WHERE timestamp > NOW() - INTERVAL '5 minutes'
            """)
            active_vehicles = cursor.fetchone()[0] or 0
            
            return {
                "total_events_processed": total_events,
                "total_alerts": total_alerts,
                "alerts_by_severity": alerts_by_severity,
                "active_vehicles": active_vehicles,
            }
        
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}
        
        finally:
            if conn:
                self.connection_pool.putconn(conn)
    
    def close(self) -> None:
        """Close all connections."""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("Connection pool closed")
