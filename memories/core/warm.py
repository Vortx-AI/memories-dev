import sqlite3
from typing import Any, Optional, List, Dict, Union
import json
import logging
from datetime import datetime
import os
import uuid
import numpy as np
import pandas as pd
from pathlib import Path

class WarmMemory:
    """
    Warm memory implementation using SQLite for persistent memory operations.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize SQLite connection and create necessary tables.
        
        Args:
            db_path (Optional[str]): Path to SQLite database file. If None, uses default path.
        """
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'warm_memory.db')
            
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.instance_id = str(uuid.uuid4())
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database and create tables
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Main storage table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS warm_memory (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        expiry INTEGER,
                        created_at INTEGER NOT NULL,
                        updated_at INTEGER NOT NULL,
                        metadata TEXT
                    )
                ''')
                # Metadata table for instance tracking
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS instances (
                        instance_id TEXT PRIMARY KEY,
                        created_at INTEGER NOT NULL,
                        last_active INTEGER NOT NULL
                    )
                ''')
                # Insert instance record
                cursor.execute('''
                    INSERT INTO instances (instance_id, created_at, last_active)
                    VALUES (?, ?, ?)
                ''', (self.instance_id, int(datetime.now().timestamp()), int(datetime.now().timestamp())))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error initializing database: {str(e)}")
            raise

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with proper configuration."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create(self, key: str, value: Any, expiry: Optional[int] = None, metadata: Optional[Dict] = None) -> bool:
        """
        Create a new key-value pair in warm memory.
        
        Args:
            key (str): The key to store the value under
            value (Any): The value to store (will be JSON serialized)
            expiry (Optional[int]): Time in seconds until the key expires
            metadata (Optional[Dict]): Additional metadata to store with the value
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                now = int(datetime.now().timestamp())
                expiry_time = now + expiry if expiry else None
                cursor.execute('''
                    INSERT OR REPLACE INTO warm_memory 
                    (key, value, expiry, created_at, updated_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    key,
                    json.dumps(value),
                    expiry_time,
                    now,
                    now,
                    json.dumps(metadata) if metadata else None
                ))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Error creating key {key}: {str(e)}")
            return False

    def read(self, key: str) -> Optional[Any]:
        """
        Read a value from warm memory.
        
        Args:
            key (str): The key to read
            
        Returns:
            Optional[Any]: The deserialized value if found and not expired, None otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                now = int(datetime.now().timestamp())
                cursor.execute('''
                    SELECT value, expiry, metadata FROM warm_memory 
                    WHERE key = ? AND (expiry IS NULL OR expiry > ?)
                ''', (key, now))
                row = cursor.fetchone()
                
                if row:
                    result = {
                        'value': json.loads(row['value']),
                        'metadata': json.loads(row['metadata']) if row['metadata'] else None
                    }
                    return result
                return None
        except Exception as e:
            self.logger.error(f"Error reading key {key}: {str(e)}")
            return None

    def delete(self, key: str) -> bool:
        """
        Delete a key from warm memory.
        
        Args:
            key (str): The key to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM warm_memory WHERE key = ?', (key,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Error deleting key {key}: {str(e)}")
            return False

    def list_keys(self, pattern: str = "*") -> List[str]:
        """
        List all keys matching a pattern.
        
        Args:
            pattern (str): SQL LIKE pattern to match keys against
            
        Returns:
            List[str]: List of matching keys
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                now = int(datetime.now().timestamp())
                # Convert glob pattern to SQL LIKE pattern
                sql_pattern = pattern.replace('*', '%').replace('?', '_')
                cursor.execute('''
                    SELECT key FROM warm_memory 
                    WHERE key LIKE ? AND (expiry IS NULL OR expiry > ?)
                ''', (sql_pattern, now))
                return [row['key'] for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error listing keys with pattern {pattern}: {str(e)}")
            return []

    def cleanup_expired(self) -> int:
        """
        Remove expired entries from warm memory.
        
        Returns:
            int: Number of entries removed
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                now = int(datetime.now().timestamp())
                cursor.execute('DELETE FROM warm_memory WHERE expiry < ?', (now,))
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            self.logger.error(f"Error cleaning up expired entries: {str(e)}")
            return 0

    def cleanup(self):
        """Clean up resources."""
        try:
            # Update last active timestamp
            with self._get_connection() as conn:
                cursor = conn.cursor()
                now = int(datetime.now().timestamp())
                cursor.execute('''
                    UPDATE instances 
                    SET last_active = ? 
                    WHERE instance_id = ?
                ''', (now, self.instance_id))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error updating instance activity: {str(e)}")

    def __del__(self):
        """Destructor to ensure cleanup is performed."""
        self.cleanup()
