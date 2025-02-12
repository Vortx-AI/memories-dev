import redis
from typing import Any, Optional, List, Dict
import json
import logging

class HotStorage:
    """
    Hot storage implementation using Redis for cached memory operations.
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
            key (str): The key to retrieve
            
        Returns:
            Optional[Any]: The deserialized value or None if not found
        """
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            self.logger.error(f"Error reading key {key}: {str(e)}")
            return None

    def update(self, key: str, value: Any, expiry: Optional[int] = None) -> bool:
        """
        Update an existing key-value pair in Redis.
        
        Args:
            key (str): The key to update
            value (Any): The new value
            expiry (Optional[int]): New expiry time in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.create(key, value, expiry)  # Redis set operation handles both create and update

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
            return self.redis_client.keys(pattern)
        except Exception as e:
            self.logger.error(f"Error listing keys with pattern {pattern}: {str(e)}")
            return []

    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment a numeric value in Redis.
        
        Args:
            key (str): The key to increment
            amount (int): Amount to increment by
            
        Returns:
            Optional[int]: New value after increment or None if failed
        """
        try:
            return self.redis_client.incrby(key, amount)
        except Exception as e:
            self.logger.error(f"Error incrementing key {key}: {str(e)}")
            return None

    def flush(self) -> bool:
        """
        Clear all keys in the current database.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.redis_client.flushdb()
            return True
        except Exception as e:
            self.logger.error(f"Error flushing database: {str(e)}")
            return False

# Initialize hot storage
hot_storage = HotStorage()

# Create a key-value pair
hot_storage.create("user:1", {"name": "John", "age": 30}, expiry=3600)  # expires in 1 hour

# Read the value
user = hot_storage.read("user:1")

# Update the value
hot_storage.update("user:1", {"name": "John", "age": 31})

# Delete the key
hot_storage.delete("user:1")

# List all keys
all_keys = hot_storage.list_keys()

# Increment a counter
hot_storage.create("visits", 0)
new_count = hot_storage.increment("visits")
