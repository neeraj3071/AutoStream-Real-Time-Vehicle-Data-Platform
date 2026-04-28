"""Redis caching layer."""
import logging
import json
import redis
from typing import Optional, Dict, Any
from config import Config

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis caching manager."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5,
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis: {Config.REDIS_HOST}:{Config.REDIS_PORT}")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache."""
        if not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None
    
    def set(self, key: str, value: Dict[str, Any], ttl: int = Config.REDIS_CACHE_TTL) -> bool:
        """Set value in cache."""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.setex(
                key,
                ttl,
                json.dumps(value),
            )
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        if not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Error clearing pattern: {e}")
            return 0
    
    def close(self) -> None:
        """Close connection."""
        if self.redis_client:
            self.redis_client.close()
            logger.info("Redis connection closed")
