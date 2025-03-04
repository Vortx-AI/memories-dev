"""
Hot memory implementation using Redis.
"""

import logging
from typing import Dict, Any, Optional
import redis

logger = logging.getLogger(__name__)

class HotMemory:
    """Hot memory layer using Redis for fast in-memory storage."""
    
    def __init__(self, redis_url: str = 'redis://localhost:6379', redis_db: int = 0):
        """Initialize hot memory.
        
        Args:
            redis_url: Redis connection URL (optional, default: redis://localhost:6379)
            redis_db: Redis database number (optional, default: 0)
        """
        self.redis_url = redis_url
        self.redis_db = redis_db
        self.max_size = 100 * 1024 * 1024  # 100MB default
        self.using_redis = True
        
        try:
            self.redis_client = redis.from_url(
                url=redis_url,
                db=redis_db,
                decode_responses=True
            )
            logger.info(f"Connected to Redis at {redis_url}, db={redis_db}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.using_redis = False
            self.redis_client = None
    
    def store(self, data: Dict[str, Any]) -> None:
        """Store data in hot memory."""
        if not self.using_redis:
            logger.error("Redis not available")
            return
            
        try:
            self.redis_client.set("hot_data", str(data))
        except Exception as e:
            logger.error(f"Failed to store in hot memory: {e}")
    
    def retrieve(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Retrieve data from hot memory."""
        if not self.using_redis:
            logger.error("Redis not available")
            return None
            
        try:
            data = self.redis_client.get("hot_data")
            return eval(data) if data else None
        except Exception as e:
            logger.error(f"Failed to retrieve from hot memory: {e}")
            return None
    
    def clear(self) -> None:
        """Clear hot memory."""
        if not self.using_redis:
            return
            
        try:
            self.redis_client.flushdb()
        except Exception as e:
            logger.error(f"Failed to clear hot memory: {e}")
    
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.using_redis and hasattr(self, 'redis_client') and self.redis_client:
            try:
                self.redis_client.close()
            except Exception as e:
                logger.error(f"Failed to cleanup hot memory: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup is performed."""
        self.cleanup()