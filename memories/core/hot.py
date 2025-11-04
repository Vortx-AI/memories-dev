"""
Hot memory implementation using DuckDB for in-memory storage.
"""

import logging
from typing import Dict, Any, Optional, List, Union
import duckdb
import json
from datetime import datetime
import uuid
import numpy as np
import os
from memories.core.db_connection_pool import get_connection_pool

logger = logging.getLogger(__name__)

class HotMemory:
    """Hot memory layer using DuckDB for fast in-memory storage."""
    
    def __init__(self, config_path: str = None):
        """Initialize hot memory with in-memory DuckDB.

        Args:
            config_path: Optional path to configuration file (not used but kept for API compatibility)
        """
        self.logger = logging.getLogger(__name__)

        # Lazy import to avoid circular dependency
        from memories.core.memory_manager import MemoryManager
        self.memory_manager = MemoryManager()

        # Get connection pool
        self.connection_pool = get_connection_pool()
        self.db_name = ":memory:_hot"

        # Initialize tables
        self._init_duckdb()
        self._init_tables()

        self.logger.info("Initialized hot memory with in-memory DuckDB")

    @property
    def con(self):
        """Get a connection from the pool for backward compatibility.

        Returns:
            A connection context manager
        """
        return self._get_connection().__enter__()
    
    def _init_duckdb(self) -> None:
        """Initialize in-memory DuckDB connection in the pool."""
        try:
            # Set default values
            memory_limit = '2GB'
            threads = 2
            
            # Try to get config values safely
            if hasattr(self.memory_manager, 'config'):
                config = self.memory_manager.config
                # Check if config has memory and hot attributes
                if hasattr(config, 'config') and isinstance(config.config, dict):
                    if 'memory' in config.config and 'hot' in config.config['memory']:
                        hot_config = config.config['memory']['hot']
                        if 'duckdb' in hot_config:
                            duckdb_config = hot_config['duckdb']
                            memory_limit = duckdb_config.get('memory_limit', memory_limit)
                            threads = duckdb_config.get('threads', threads)
            
            # Configuration for the connection
            config = {
                'memory_limit': memory_limit,
                'threads': threads
            }
            
            # Initialize connection in pool
            with self.connection_pool.get_connection(self.db_name, config) as con:
                # Connection is configured, just verify it works
                con.execute("SELECT 1").fetchone()
            
        except Exception as e:
            self.logger.error(f"Error initializing DuckDB for hot storage: {e}")
            # Use default configuration
            with self.connection_pool.get_connection(self.db_name) as con:
                con.execute("SELECT 1").fetchone()
    
    def _init_tables(self) -> None:
        """Initialize database tables."""
        try:
            # Create tables if they don't exist
            with self.connection_pool.get_connection(self.db_name) as con:
                con.execute("""
                    CREATE TABLE IF NOT EXISTS hot_data (
                        id VARCHAR PRIMARY KEY,
                        data JSON,
                        metadata JSON,
                        tags JSON,
                        stored_at TIMESTAMP
                    )
                """)
                
                con.execute("""
                    CREATE TABLE IF NOT EXISTS hot_tags (
                        tag VARCHAR,
                        data_id VARCHAR,
                        PRIMARY KEY (tag, data_id),
                        FOREIGN KEY (data_id) REFERENCES hot_data(id)
                    )
                """)
            
                self.logger.info("Initialized hot memory tables")
            
        except Exception as e:
            self.logger.error(f"Error initializing tables for hot storage: {e}")
            raise
    
    def _get_connection(self):
        """Get a connection from the pool."""
        return self.connection_pool.get_connection(self.db_name)
    
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
        try:
            # Generate unique ID
            data_id = str(uuid.uuid4())
            
            # Prepare data for storage
            metadata = metadata or {}
            tags_list = tags or []
            
            # Convert data to JSON if needed
            if isinstance(data, (dict, list)):
                data_json = json.dumps(data)
            elif isinstance(data, np.ndarray):
                data_json = json.dumps(data.tolist())
            else:
                data_json = json.dumps(str(data))
            
            # Store in hot_data table
            with self._get_connection() as con:
                con.execute(
                    """
                    INSERT INTO hot_data (id, data, metadata, tags, stored_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    [
                        data_id,
                        data_json,
                        json.dumps(metadata),
                        json.dumps(tags_list),
                        datetime.now()
                    ]
                )
                
                # Store tags in hot_tags table
                if tags_list:
                    for tag in tags_list:
                        con.execute(
                            """
                            INSERT INTO hot_tags (tag, data_id)
                            VALUES (?, ?)
                            """,
                            [tag, data_id]
                        )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store in hot memory: {e}")
            return False
    
    async def retrieve(
        self,
        query: Dict[str, Any] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[Union[List[Dict[str, Any]], Dict[str, Any]]]:
        """Retrieve data from hot memory.

        Args:
            query: Query parameters (can contain 'id' to retrieve specific data)
            tags: Optional tags to filter by

        Returns:
            Retrieved data as a list of dicts, a single dict (for ID queries), or None if not found
        """
        try:
            query = query or {}  # Default to empty dict if None

            if tags:
                # Get data by tags
                tag_placeholders = ', '.join(['?'] * len(tags))
                with self._get_connection() as con:
                    result = con.execute(
                        f"""
                        SELECT hd.id, hd.data, hd.metadata, hd.tags, hd.stored_at
                        FROM hot_data hd
                        JOIN hot_tags ht ON hd.id = ht.data_id
                        WHERE ht.tag IN ({tag_placeholders})
                        GROUP BY hd.id, hd.data, hd.metadata, hd.tags, hd.stored_at
                        """,
                        tags
                    ).fetchall()

                if not result:
                    return None

                # Convert to list of dictionaries
                results = []
                for row in result:
                    results.append({
                        'id': row[0],
                        'data': json.loads(row[1]),
                        'metadata': json.loads(row[2]),
                        'tags': json.loads(row[3]),
                        'stored_at': row[4]
                    })

                return results

            elif 'id' in query:
                # Get specific data by ID
                with self._get_connection() as con:
                    result = con.execute(
                        """
                        SELECT id, data, metadata, tags, stored_at
                        FROM hot_data
                        WHERE id = ?
                        """,
                        [query['id']]
                    ).fetchone()

                if result:
                    return [{
                        'id': result[0],
                        'data': json.loads(result[1]),
                        'metadata': json.loads(result[2]),
                        'tags': json.loads(result[3]),
                        'stored_at': result[4]
                    }]

            else:
                # Get all data
                with self._get_connection() as con:
                    result = con.execute(
                        """
                        SELECT id, data, metadata, tags, stored_at
                        FROM hot_data
                        ORDER BY stored_at DESC
                        LIMIT 100
                        """
                    ).fetchall()

                if result:
                    results = []
                    for row in result:
                        results.append({
                            'id': row[0],
                            'data': json.loads(row[1]),
                            'metadata': json.loads(row[2]),
                            'tags': json.loads(row[3]),
                            'stored_at': row[4]
                        })
                    return results

            return None

        except Exception as e:
            self.logger.error(f"Failed to retrieve from hot memory: {e}")
            return None
    
    async def clear(self) -> bool:
        """Clear all data from hot memory.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self._get_connection() as con:
                con.execute("DELETE FROM hot_tags")
                con.execute("DELETE FROM hot_data")
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear hot memory: {e}")
            return False
    
    def get_table_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the tables in hot memory.
        
        Returns:
            Dictionary with table information or None if error
        """
        try:
            info = {}
            with self._get_connection() as con:
                # Get row counts
                hot_data_count = con.execute(
                    "SELECT COUNT(*) FROM hot_data"
                ).fetchone()[0]
                
                hot_tags_count = con.execute(
                    "SELECT COUNT(*) FROM hot_tags"
                ).fetchone()[0]
                
                info['hot_data_count'] = hot_data_count
                info['hot_tags_count'] = hot_tags_count
                
                # Get table sizes (approximate)
                table_info = con.execute(
                    "SHOW TABLES"
                ).fetchall()
                
                info['tables'] = [row[0] for row in table_info]
                
            return info
        except Exception as e:
            self.logger.error(f"Failed to get table info: {e}")
            return None
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in hot memory.
        
        Args:
            key: The key to check
            
        Returns:
            bool: True if key exists, False otherwise
        """
        try:
            # Check if the table exists
            try:
                with self._get_connection() as con:
                    con.execute("SELECT * FROM hot_data LIMIT 1")
            except duckdb.CatalogException:
                self.logger.warning("Hot data table does not exist")
                return False
                
            # Check if key exists
            with self._get_connection() as con:
                result = con.execute(f"""
                    SELECT COUNT(*) FROM hot_data WHERE id = ?
                """, [key]).fetchone()
                
                return result[0] > 0
                
        except Exception as e:
            self.logger.error(f"Error checking key existence: {e}")
            return False
    
    async def get_schema(self, data_id: str) -> Optional[Dict[str, Any]]:
        """Get schema information for stored data.

        Args:
            data_id: The ID of the data to get schema for

        Returns:
            Dictionary with schema information or None if not found
        """
        try:
            with self._get_connection() as con:
                result = con.execute(
                    """
                    SELECT data, metadata, tags
                    FROM hot_data
                    WHERE id = ?
                    """,
                    [data_id]
                ).fetchone()

            if not result:
                return None

            data = json.loads(result[0])
            metadata = json.loads(result[1])
            tags = json.loads(result[2])

            # Determine data type and schema
            if isinstance(data, dict):
                return {
                    'columns': list(data.keys()),
                    'dtypes': {k: type(v).__name__ for k, v in data.items()},
                    'type': 'json',
                    'source': 'hot',
                    'metadata': metadata,
                    'tags': tags
                }
            elif isinstance(data, list):
                return {
                    'type': 'list',
                    'length': len(data),
                    'source': 'hot',
                    'metadata': metadata,
                    'tags': tags
                }
            else:
                return {
                    'type': type(data).__name__,
                    'source': 'hot',
                    'metadata': metadata,
                    'tags': tags
                }

        except Exception as e:
            self.logger.error(f"Failed to get schema for {data_id}: {e}")
            return None

    async def delete(self, key: str) -> bool:
        """Delete a specific key from hot memory.

        Args:
            key: The key to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            with self._get_connection() as con:
                con.execute(f"""
                    DELETE FROM hot_tags WHERE data_id = ?
                """, [key])

                con.execute(f"""
                    DELETE FROM hot_data WHERE id = ?
                """, [key])

            return True

        except Exception as e:
            self.logger.error(f"Failed to delete key {key}: {e}")
            return False
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        try:
            # Connection pool will handle cleanup
            pass
        except Exception:
            pass