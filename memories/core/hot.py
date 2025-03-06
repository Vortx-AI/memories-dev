"""
Hot memory implementation using Redis for fast in-memory operations.
"""

import logging
from typing import Dict, Any, Optional, List
import redis
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class HotMemory:
    """Hot memory layer using Redis for fast in-memory operations."""
    
    def __init__(self, redis_url: str = 'redis://localhost:6379', redis_db: int = 0):
        """Initialize hot memory.
        
        Args:
            redis_url: Redis connection URL
            redis_db: Redis database number
        """
        self.redis_url = redis_url
        self.redis_db = redis_db
        self.client = redis.from_url(redis_url, db=redis_db)
        logger.info("Initialized hot memory storage")

    def store(self, data: Dict[str, Any]) -> None:
        """Store data in hot memory.
        
        Args:
            data: Data to store
        """
        try:
            # Generate key if not provided
            key = str(data.get('id', datetime.now().timestamp()))
            
            # Store data with timestamp
            data_with_timestamp = {
                **data,
                'stored_at': datetime.now().isoformat()
            }
            
            self.client.set(key, json.dumps(data_with_timestamp))
            logger.debug(f"Stored data with key: {key}")
            
        except Exception as e:
            logger.error(f"Failed to store data: {e}")
            raise

    def retrieve(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Retrieve data from hot memory.
        
        Args:
            query: Query parameters
            
        Returns:
            Retrieved data or None if not found
        """
        try:
            # Try direct key lookup first
            if 'id' in query:
                key = str(query['id'])
                data = self.client.get(key)
                if data:
                    return json.loads(data)
            
            # Search through all keys
            for key in self.client.scan_iter():
                try:
                    data = self.client.get(key)
                    if data:
                        data_dict = json.loads(data)
                        # Check if all query parameters match
                        if all(data_dict.get(k) == v for k, v in query.items()):
                            return data_dict
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON data for key: {key}")
                    continue
                    
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve data: {e}")
            return None

    def retrieve_all(self) -> List[Dict[str, Any]]:
        """Retrieve all data from hot memory.
        
        Returns:
            List of all stored data
        """
        try:
            result = []
            for key in self.client.scan_iter():
                data = self.client.get(key)
                if data:
                    result.append(json.loads(data))
            return result
        except Exception as e:
            logger.error(f"Failed to retrieve all data: {e}")
            return []

    def clear(self) -> None:
        """Clear all data from hot memory."""
        try:
            if self.client:
                self.client.flushdb()
                self.client.save()  # Force save to disk
                logger.info("Hot memory cleared successfully")
        except Exception as e:
            logger.error(f"Failed to clear hot memory: {e}")
            # Don't raise the exception, just log it
            
    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            self.clear()
            if self.client:
                self.client.save()  # Force save before closing
                self.client.close()
                self.client = None
                logger.info("Hot memory cleaned up successfully")
        except Exception as e:
            logger.error(f"Failed to cleanup hot memory: {e}")
            # Don't raise the exception, just log it

    def __del__(self):
        """Destructor to ensure cleanup is performed."""
        self.cleanup()