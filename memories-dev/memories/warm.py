import sqlite3
from typing import Any, Optional, List, Dict
import json
import logging
from datetime import datetime
import os

class WarmStorage:
    """
    Warm storage implementation using SQLite for persistent memory operations.
    """
    
    def __init__(self, db_path: str):
        """
        Initialize SQLite connection and create necessary tables.
        
        Args:
            db_path (str): Path to SQLite database file
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database and create table
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS warm_storage (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        expiry INTEGER,
                        created_at INTEGER NOT NULL,
                        updated_at INTEGER NOT NULL
                    )
                ''')
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error initializing database: {str(e)}")
            raise

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with proper configuration."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create(self, key: str, value: Any, expiry: int) -> bool:
        """
        Create a new key-value pair in SQLite.
        
        Args:
            key (str): The key to store the value under
            value (Any): The value to store (will be JSON serialized)
            expiry (int): Time in seconds until the key expires
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            current_time = int(datetime.now().timestamp())
            expiry_time = current_time + expiry if expiry else None
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO warm_storage (key, value, expiry, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (key, json.dumps(value), expiry_time, current_time, current_time))
                conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error creating key {key}: {str(e)}")
            return False

    def read(self, key: str) -> Optional[Any]:
        """
        Read a value from SQLite.
        
        Args:
            key (str): The key to retrieve
            
        Returns:
            Optional[Any]: The deserialized value or None if not found
        """
        try:
            current_time = int(datetime.now().timestamp())
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT value FROM warm_storage 
                    WHERE key = ? 
                    AND (expiry IS NULL OR expiry > ?)
                ''', (key, current_time))
                
                row = cursor.fetchone()
                if row is None:
                    return None
                    
                return json.loads(row['value'])
        except Exception as e:
            self.logger.error(f"Error reading key {key}: {str(e)}")
            return None

    def update(self, key: str, value: Any, expiry: int) -> bool:
        """
        Update an existing key-value pair in SQLite.
        
        Args:
            key (str): The key to update
            value (Any): The new value
            expiry (int): Time in seconds until the key expires
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            current_time = int(datetime.now().timestamp())
            expiry_time = current_time + expiry if expiry else None
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE warm_storage 
                    SET value = ?, expiry = ?, updated_at = ?
                    WHERE key = ?
                ''', (json.dumps(value), expiry_time, current_time, key))
                conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Error updating key {key}: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete a key from SQLite.
        
        Args:
            key (str): The key to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM warm_storage WHERE key = ?', (key,))
                conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error deleting key {key}: {str(e)}")
            return False

    def list_keys(self, pattern: str) -> List[str]:
        """
        List all keys matching a pattern.
        
        Args:
            pattern (str): SQL LIKE pattern to match keys against
            
        Returns:
            List[str]: List of matching keys
        """
        try:
            current_time = int(datetime.now().timestamp())
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT key FROM warm_storage 
                    WHERE key LIKE ? 
                    AND (expiry IS NULL OR expiry > ?)
                ''', (pattern.replace('*', '%'), current_time))
                
                return [row['key'] for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error listing keys with pattern {pattern}: {str(e)}")
            return []

    def cleanup_expired(self) -> int:
        """
        Remove expired entries from the database.
        
        Returns:
            int: Number of entries removed
        """
        try:
            current_time = int(datetime.now().timestamp())
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM warm_storage 
                    WHERE expiry IS NOT NULL AND expiry <= ?
                ''', (current_time,))
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            self.logger.error(f"Error cleaning up expired entries: {str(e)}")
            return 0

    def flush(self) -> bool:
        """
        Clear all entries in the database.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM warm_storage')
                conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error flushing database: {str(e)}")
            return False
