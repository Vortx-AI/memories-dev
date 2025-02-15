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
    """
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        """
        Initialize Redis connection.
        
        Args:
            host (str): Redis host address
            port (int): Redis port number
            db (int): Redis database number
        """
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True  # Automatically decode responses to strings
        )
        self.logger = logging.getLogger(__name__)
        self.instance_id = str(uuid.uuid4())

    def create(self, key: str, value: Any, expiry: Optional[int] = None) -> bool:
        """
        Create a new key-value pair in Redis.
        
        Args:
            key (str): The key to store the value under
            value (Any): The value to store (will be JSON serialized)
            expiry (Optional[int]): Time in seconds until the key expires
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            serialized_value = json.dumps(value)
            if expiry:
                return self.redis_client.setex(key, expiry, serialized_value)
            return self.redis_client.set(key, serialized_value)
        except Exception as e:
            self.logger.error(f"Error creating key {key}: {str(e)}")
            return False

    def read(self, key: str) -> Optional[Any]:
        """
        Read a value from Redis.
        
        Args:
            key (str): The key to read
            
        Returns:
            Optional[Any]: The deserialized value if found, None otherwise
        """
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            self.logger.error(f"Error reading key {key}: {str(e)}")
            return None

    def delete(self, key: str) -> bool:
        """
        Delete a key from Redis.
        
        Args:
            key (str): The key to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            return bool(self.redis_client.delete(key))
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
            return [key.decode() for key in self.redis_client.keys(pattern)]
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
            return self.redis_client.incrby(key, amount)
        except Exception as e:
            self.logger.error(f"Error incrementing key {key}: {str(e)}")
            return None

    def cleanup(self):
        """Clean up resources."""
        if hasattr(self, 'redis_client'):
            self.redis_client.close()

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
