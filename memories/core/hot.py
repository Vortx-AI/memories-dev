"""
Hot memory implementation using Redis.
"""

import logging
from typing import Dict, Any, Optional, List, Union
import redis
import json
from datetime import datetime

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
    
    async def store(
        self,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Store data in hot memory with metadata and tags.
        
        Args:
            data: Data to store
            metadata: Optional metadata about the data
            tags: Optional tags for categorizing the data
            
        Returns:
            bool: True if storage was successful, False otherwise
        """
        if not self.using_redis or not self.redis_client:
            logger.error("Redis client not initialized")
            return False

        try:
            # Generate key from tags or timestamp
            key = f"{tags[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}" if tags else f"hot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Prepare data for storage
            storage_data = {
                "data": data,
                "metadata": metadata or {},
                "tags": tags or [],
                "stored_at": datetime.now().isoformat()
            }

            # Store in Redis
            self.redis_client.set(key, json.dumps(storage_data))

            # Add to tag index if tags provided
            if tags:
                for tag in tags:
                    self.redis_client.sadd(f"tag:{tag}", key)

            return True

        except Exception as e:
            logger.error(f"Failed to store in hot memory: {e}")
            return False
    
    async def retrieve(
        self,
        query: Dict[str, Any],
        tags: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Retrieve data from hot memory.
        
        Args:
            query: Query parameters
            tags: Optional tags to filter by
            
        Returns:
            Retrieved data or None if not found
        """
        if not self.using_redis:
            logger.error("Redis not available")
            return None
            
        try:
            if tags:
                # Get keys by tags
                keys = set()
                for tag in tags:
                    tag_keys = self.redis_client.smembers(f"tag:{tag}")
                    keys.update(tag_keys)
                
                # Get data for each key
                results = []
                for key in keys:
                    data = self.redis_client.get(key)
                    if data:
                        results.append(json.loads(data))
                return results
            else:
                # Get data by query
                data = self.redis_client.get(query.get("key", "hot_data"))
                return json.loads(data) if data else None
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