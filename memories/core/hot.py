"""
Hot memory implementation using Redis.
"""

import json
import logging
from typing import Dict, Any, Optional, List
import redis

logger = logging.getLogger(__name__)

class HotMemory:
    """Hot memory layer using Redis for fast access."""
    
    def __init__(self, redis_url: str, redis_db: int, max_size: int):
        """Initialize hot memory.
        
        Args:
            redis_url: Redis connection URL
            redis_db: Redis database number
            max_size: Maximum number of items to store
        """
        self.redis_url = redis_url
        self.redis_db = redis_db
        self.max_size = max_size
        self.using_redis = True
        
        # Connect to Redis
        try:
            self.redis_client = redis.from_url(redis_url, db=redis_db)
            logger.info("Successfully connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
            self.using_redis = False
    
    def store(self, data: Dict[str, Any]) -> None:
        """Store data in Redis.
        
        Args:
            data: Data to store
        """
        if not self.using_redis or not self.redis_client:
            logger.error("Redis connection not available")
            return
        
        try:
            # Use timestamp as key
            key = data.get("timestamp", "")
            if not key:
                logger.error("Data must have a timestamp")
                return
            
            # Store as JSON
            self.redis_client.set(key, json.dumps(data))
            
            # Maintain max size by removing oldest entries
            keys = self.redis_client.keys("*")
            if len(keys) > self.max_size:
                # Sort by timestamp and remove oldest
                sorted_keys = sorted(keys)
                for old_key in sorted_keys[:-self.max_size]:
                    self.redis_client.delete(old_key)
        except Exception as e:
            logger.error(f"Failed to store data in Redis: {e}")
    
    def retrieve(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Retrieve data from Redis.
        
        Args:
            query: Query to match against stored data
            
        Returns:
            Retrieved data or None if not found
        """
        if not self.using_redis or not self.redis_client:
            logger.error("Redis connection not available")
            return None
        
        try:
            # Use timestamp as key if provided
            if "timestamp" in query:
                key = query["timestamp"]
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
            
            # Otherwise, search through all keys
            for key in self.redis_client.keys("*"):
                data = json.loads(self.redis_client.get(key))
                # Check if all query items match
                if all(data.get(k) == v for k, v in query.items()):
                    return data
            
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve data from Redis: {e}")
            return None
    
    def retrieve_all(self) -> List[Dict[str, Any]]:
        """Retrieve all data from Redis.
        
        Returns:
            List of all stored data
        """
        if not self.using_redis or not self.redis_client:
            logger.error("Redis connection not available")
            return []
        
        try:
            result = []
            for key in self.redis_client.keys("*"):
                data = self.redis_client.get(key)
                if data:
                    result.append(json.loads(data))
            return result
        except Exception as e:
            logger.error(f"Failed to retrieve all data from Redis: {e}")
            return []
    
    def clear(self) -> None:
        """Clear all data from Redis."""
        if not self.using_redis or not self.redis_client:
            logger.error("Redis connection not available")
            return
        
        try:
            self.redis_client.flushdb()
        except Exception as e:
            logger.error(f"Failed to clear Redis: {e}")
    
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.using_redis and hasattr(self, 'redis_client'):
            try:
                self.redis_client.close()
            except Exception as e:
                logger.error(f"Failed to close Redis connection: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup is performed."""
        self.cleanup()
