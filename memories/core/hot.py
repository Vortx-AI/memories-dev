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

    async def get_schema(self, key: str) -> Optional[Dict[str, Any]]:
        """Get schema information for stored data.
        
        Args:
            key: Key of the data to get schema for
            
        Returns:
            Dictionary containing schema information or None if not found
        """
        if not self.using_redis:
            logger.error("Redis not available")
            return None
            
        try:
            # Get data from Redis
            data = self.redis_client.get(key)
            if not data:
                return None
                
            # Parse stored data
            stored_data = json.loads(data)
            data_value = stored_data.get('data')
            
            if isinstance(data_value, dict):
                schema = {
                    'fields': list(data_value.keys()),
                    'types': {k: type(v).__name__ for k, v in data_value.items()},
                    'type': 'dict',
                    'source': 'redis'
                }
            elif isinstance(data_value, list):
                if data_value:
                    if all(isinstance(x, dict) for x in data_value):
                        # List of dictionaries - combine all keys
                        all_keys = set().union(*(d.keys() for d in data_value))
                        schema = {
                            'fields': list(all_keys),
                            'types': {k: type(next(d[k] for d in data_value if k in d)).__name__ 
                                    for k in all_keys},
                            'type': 'list_of_dicts',
                            'source': 'redis'
                        }
                    else:
                        schema = {
                            'type': 'list',
                            'element_type': type(data_value[0]).__name__,
                            'length': len(data_value),
                            'source': 'redis'
                        }
                else:
                    schema = {
                        'type': 'list',
                        'length': 0,
                        'source': 'redis'
                    }
            else:
                schema = {
                    'type': type(data_value).__name__,
                    'source': 'redis'
                }
                
            return schema
            
        except Exception as e:
            logger.error(f"Failed to get schema for {key}: {e}")
            return None