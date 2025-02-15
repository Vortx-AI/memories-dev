import redis
from typing import Any, Optional, List, Dict, Union
import json
import logging
import os
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime
import uuid

class HotMemory:
    """
    Hot memory implementation using Redis for cached memory operations.
    Gracefully falls back to in-memory storage if Redis is not available.
    """
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        """
        Initialize Redis connection with fallback to in-memory storage.
        
        Args:
            host (str): Redis host address
            port (int): Redis port number
            db (int): Redis database number
        """
        self.logger = logging.getLogger(__name__)
        self.instance_id = str(uuid.uuid4())
        self.in_memory_storage = {}
        self.using_redis = False
        
        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True,  # Automatically decode responses to strings
                socket_connect_timeout=1  # Short timeout for quick failure
            )
            # Test connection
            self.redis_client.ping()
            self.using_redis = True
            self.logger.info("Successfully connected to Redis")
        except (redis.ConnectionError, redis.TimeoutError) as e:
            self.logger.warning(f"Redis connection failed: {str(e)}. Falling back to in-memory storage.")
            self.redis_client = None
        except Exception as e:
            self.logger.warning(f"Unexpected error connecting to Redis: {str(e)}. Falling back to in-memory storage.")
            self.redis_client = None

    def create(self, key: str, value: Any, expiry: Optional[int] = None) -> bool:
        """
        Create a new key-value pair in storage.
        
        Args:
            key (str): The key to store the value under
            value (Any): The value to store (will be JSON serialized)
            expiry (Optional[int]): Time in seconds until the key expires
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            serialized_value = json.dumps(value)
            if self.using_redis:
                if expiry:
                    return self.redis_client.setex(key, expiry, serialized_value)
                return self.redis_client.set(key, serialized_value)
            else:
                self.in_memory_storage[key] = {
                    'value': serialized_value,
                    'expiry': datetime.now().timestamp() + expiry if expiry else None
                }
                return True
        except Exception as e:
            self.logger.error(f"Error creating key {key}: {str(e)}")
            return False

    def read(self, key: str) -> Optional[Any]:
        """
        Read a value from storage.
        
        Args:
            key (str): The key to read
            
        Returns:
            Optional[Any]: The deserialized value if found, None otherwise
        """
        try:
            if self.using_redis:
                value = self.redis_client.get(key)
            else:
                if key not in self.in_memory_storage:
                    return None
                stored = self.in_memory_storage[key]
                if stored['expiry'] and stored['expiry'] < datetime.now().timestamp():
                    del self.in_memory_storage[key]
                    return None
                value = stored['value']
            
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            self.logger.error(f"Error reading key {key}: {str(e)}")
            return None

    def delete(self, key: str) -> bool:
        """
        Delete a key from storage.
        
        Args:
            key (str): The key to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.using_redis:
                return bool(self.redis_client.delete(key))
            else:
                if key in self.in_memory_storage:
                    del self.in_memory_storage[key]
                    return True
                return False
        except Exception as e:
            self.logger.error(f"Error deleting key {key}: {str(e)}")
            return False

    def list_keys(self, pattern: str = "*") -> List[str]:
        """
        List all keys matching a pattern.
        
        Args:
            pattern (str): Pattern to match keys against
            
        Returns:
            List[str]: List of matching keys
        """
        try:
            if self.using_redis:
                return [key.decode() if isinstance(key, bytes) else key 
                       for key in self.redis_client.keys(pattern)]
            else:
                import fnmatch
                return [key for key in self.in_memory_storage.keys() 
                       if fnmatch.fnmatch(key, pattern)]
        except Exception as e:
            self.logger.error(f"Error listing keys with pattern {pattern}: {str(e)}")
            return []

    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment a key's value.
        
        Args:
            key (str): The key to increment
            amount (int): Amount to increment by
            
        Returns:
            Optional[int]: New value after increment, None if error
        """
        try:
            if self.using_redis:
                return self.redis_client.incrby(key, amount)
            else:
                if key not in self.in_memory_storage:
                    self.in_memory_storage[key] = {'value': '0', 'expiry': None}
                current = int(json.loads(self.in_memory_storage[key]['value']))
                new_value = current + amount
                self.in_memory_storage[key]['value'] = json.dumps(new_value)
                return new_value
        except Exception as e:
            self.logger.error(f"Error incrementing key {key}: {str(e)}")
            return None

    def cleanup(self):
        """Clean up resources."""
        if self.using_redis and hasattr(self, 'redis_client'):
            try:
                self.redis_client.close()
            except Exception as e:
                self.logger.error(f"Error closing Redis connection: {str(e)}")
        
        # Clear in-memory storage
        self.in_memory_storage.clear()

    def __del__(self):
        """Destructor to ensure connection is closed."""
        self.cleanup()

# Initialize hot storage
hot_storage = HotMemory()

# Create a key-value pair
hot_storage.create("user:1", {"name": "John", "age": 30}, expiry=3600)  # expires in 1 hour

# Read the value
user = hot_storage.read("user:1")

# Update the value
hot_storage.create("user:1", {"name": "John", "age": 31})

# Delete the key
hot_storage.delete("user:1")

# List all keys
all_keys = hot_storage.list_keys()

# Increment a counter
hot_storage.create("visits", 0)
new_count = hot_storage.increment("visits")
