"""
Warm memory implementation using DuckDB for fast in-memory operations.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import duckdb
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class WarmMemory:
    """Warm memory layer using DuckDB for fast in-memory operations."""
    
    def __init__(self, duckdb_connection):
        """Initialize warm memory.
        
        Args:
            duckdb_connection: DuckDB connection from memory manager
        """
        self.logger = logger
        self.con = duckdb_connection
        if self.con is None:
            raise ValueError("DuckDB connection is required")
            
        # Create main table for data storage
        self.con.execute("""
            CREATE TABLE IF NOT EXISTS warm_data (
                key VARCHAR PRIMARY KEY,
                data JSON,
                metadata JSON,
                created_at TIMESTAMP,
                last_accessed TIMESTAMP
            )
        """)
        
        self.logger.info("Initialized warm memory storage")

    def store(self, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> None:
        """Store data in warm memory.
        
        Args:
            data: Data to store
            metadata: Optional metadata
        """
        if not self.con:
            self.logger.error("DuckDB connection not available")
            return
            
        try:
            key = data.get('id') or str(datetime.now().timestamp())
            self.con.execute("""
                INSERT INTO warm_data (key, data, metadata, created_at, last_accessed)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (key) DO UPDATE SET
                    data = EXCLUDED.data,
                    metadata = EXCLUDED.metadata,
                    last_accessed = CURRENT_TIMESTAMP
            """, [key, json.dumps(data), json.dumps(metadata or {})])
            
        except Exception as e:
            self.logger.error(f"Failed to store data: {e}")

    def retrieve(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Retrieve data from warm memory.
        
        Args:
            query: Query parameters
            
        Returns:
            Retrieved data or None if not found
        """
        try:
            conditions = []
            params = []
            
            for key, value in query.items():
                if key == 'key':
                    conditions.append("key = ?")
                    params.append(value)
                else:
                    conditions.append(f"data->>'$.{key}' = ?")
                    params.append(str(value))
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            result = self.con.execute(f"""
                UPDATE warm_data 
                SET last_accessed = CURRENT_TIMESTAMP
                WHERE {where_clause}
                RETURNING data
            """, params).fetchone()
            
            return json.loads(result[0]) if result else None
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve data: {e}")
            return None

    def retrieve_all(self) -> List[Dict[str, Any]]:
        """Retrieve all data from warm memory.
        
        Returns:
            List of all stored data
        """
        try:
            results = self.con.execute("""
                SELECT data FROM warm_data
                ORDER BY last_accessed DESC
            """).fetchall()
            
            return [json.loads(row[0]) for row in results]
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve all data: {e}")
            return []

    def clear(self) -> None:
        """Clear all data from warm memory."""
        try:
            self.con.execute("DELETE FROM warm_data")
        except Exception as e:
            self.logger.error(f"Failed to clear data: {e}")

    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            if hasattr(self, 'con'):
                self.con.close()
        except Exception as e:
            self.logger.error(f"Failed to cleanup: {e}")

    def __del__(self):
        """Destructor to ensure cleanup is performed."""
        self.cleanup()