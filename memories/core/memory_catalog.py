"""Memory catalog for tracking data across all memory tiers."""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import duckdb
import json
import uuid
import numpy as np
# Remove direct import to avoid circular dependency
# from memories.core.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

class MemoryCatalog:
    """Central registry for tracking data across all memory tiers."""
    
    _instance = None
    
    def __new__(cls):
        """Create singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize memory catalog."""
        if not hasattr(self, 'initialized'):
            self.logger = logging.getLogger(__name__)
            
            # Lazy import to avoid circular dependency
            from memories.core.memory_manager import MemoryManager
            self.memory_manager = MemoryManager()
            
            # Get database path from memory manager
            db_path = self.memory_manager.config.get_path('catalog_db_path', 'memory_catalog.duckdb')
            
            # Initialize database with persistent storage
            self.logger.info(f"Connecting to memory catalog database at: {db_path}")
            self.con = duckdb.connect(str(db_path))
            self._initialize_schema()
            self.initialized = True

    def _initialize_schema(self):
        """Initialize database schema."""
        try:
            # Create catalog table if it doesn't exist
            self.con.execute("""
                CREATE TABLE IF NOT EXISTS memory_catalog (
                    data_id VARCHAR PRIMARY KEY,
                    primary_tier VARCHAR,
                    location VARCHAR,
                    created_at TIMESTAMP,
                    last_accessed TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    size BIGINT,
                    tags VARCHAR,
                    data_type VARCHAR,
                    table_name VARCHAR,
                    additional_meta JSON
                )
            """)
            self.logger.info("Initialized memory catalog schema")
        except Exception as e:
            self.logger.error(f"Failed to initialize catalog schema: {e}")
            raise

    def _validate_inputs(
        self,
        tier: str,
        location: str,
        size: int,
        data_type: str
    ) -> None:
        """Validate input parameters.
        
        Args:
            tier: Memory tier where data is stored
            location: Location of the data
            size: Size of the data in bytes
            data_type: Type of the data
            
        Raises:
            ValueError: If any of the inputs are invalid
        """
        valid_tiers = ["glacier", "cold", "warm", "hot", "red_hot"]
        if not tier or tier not in valid_tiers:
            raise ValueError(f"Invalid tier: {tier}. Must be one of {valid_tiers}")
        
        if not location:
            raise ValueError("Location cannot be None or empty")
            
        if not isinstance(size, (int, np.integer)) or size < 0:
            raise ValueError(f"Invalid size: {size}. Must be a non-negative integer")
            
        if not data_type:
            raise ValueError("Data type cannot be None or empty")

    async def register_data(
        self,
        tier: str,
        location: str,
        size: int,
        data_type: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        table_name: Optional[str] = None
    ) -> str:
        """Register data in the catalog.
        
        Args:
            tier: Memory tier where data is stored
            location: Location of the data (e.g., file path, table name)
            size: Size of the data in bytes
            data_type: Type of the data
            tags: Optional tags for categorizing the data
            metadata: Optional additional metadata
            table_name: Optional name of the table where data is stored
            
        Returns:
            str: Generated data ID
            
        Raises:
            ValueError: If any of the inputs are invalid
        """
        try:
            # Validate inputs
            self._validate_inputs(tier, location, size, data_type)
            
            data_id = str(uuid.uuid4())
            now = datetime.now()
            
            # Convert numpy.int64 to regular Python int
            if isinstance(size, np.integer):
                size = int(size)
            
            # Convert tags list to comma-separated string
            tags_str = ','.join(tags) if tags else None
            
            # Convert metadata to JSON string
            meta_json = json.dumps(metadata) if metadata else '{}'
            
            # Use table_name if provided, otherwise use location
            actual_table_name = table_name if table_name else location
            
            # Insert into catalog
            self.con.execute("""
                INSERT INTO memory_catalog (
                    data_id, primary_tier, location, created_at, last_accessed,
                    access_count, size, tags, data_type, table_name, additional_meta
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                data_id, tier, location, now, now,
                0, size, tags_str, data_type, actual_table_name, meta_json
            ])
            
            self.logger.info(f"Registered data {data_id} in {tier} tier")
            return data_id
            
        except Exception as e:
            self.logger.error(f"Failed to register data: {e}")
            raise

    async def update_access(self, data_id: str) -> None:
        """Update last access time and count for data.
        
        Args:
            data_id: ID of the data to update
        """
        try:
            self.con.execute("""
                UPDATE memory_catalog
                SET last_accessed = ?,
                    access_count = access_count + 1
                WHERE data_id = ?
            """, [datetime.now(), data_id])
        except Exception as e:
            self.logger.error(f"Failed to update access for {data_id}: {e}")

    async def get_data_info(self, data_id: str) -> Optional[Dict[str, Any]]:
        """Get information about data item.
        
        Args:
            data_id: ID of the data to retrieve
            
        Returns:
            Dict containing data information or None if not found
        """
        try:
            result = self.con.execute("""
                SELECT * FROM memory_catalog
                WHERE data_id = ?
            """, [data_id]).fetchone()
            
            if result:
                # Convert row to dictionary
                columns = ['data_id', 'primary_tier', 'location', 'created_at',
                          'last_accessed', 'access_count', 'size', 'tags',
                          'data_type', 'table_name', 'additional_meta']
                return dict(zip(columns, result))
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get data info for {data_id}: {e}")
            return None

    async def search_by_tags(self, tags: List[str]) -> List[Dict[str, Any]]:
        """Search for data items by tags.
        
        Args:
            tags: List of tags to search for
            
        Returns:
            List of matching data items
        """
        try:
            # Create conditions for each tag
            conditions = []
            for tag in tags:
                conditions.append(f"tags LIKE '%{tag}%'")
            
            query = f"""
                SELECT * FROM memory_catalog
                WHERE {' OR '.join(conditions)}
            """
            
            results = self.con.execute(query).fetchall()
            
            # Convert rows to dictionaries
            columns = ['data_id', 'primary_tier', 'location', 'created_at',
                      'last_accessed', 'access_count', 'size', 'tags',
                      'data_type', 'table_name', 'additional_meta']
            return [dict(zip(columns, row)) for row in results]
            
        except Exception as e:
            self.logger.error(f"Failed to search by tags: {e}")
            return []

    async def get_tier_data(self, tier: str) -> List[Dict[str, Any]]:
        """Get all data items stored in a specific memory tier.
        
        Args:
            tier: Memory tier to get data from ("glacier", "cold", "warm", "hot", "red_hot")
            
        Returns:
            List of dictionaries containing data information
            
        Raises:
            ValueError: If the tier is invalid
        """
        try:
            # Validate tier
            valid_tiers = ["glacier", "cold", "warm", "hot", "red_hot"]
            if tier not in valid_tiers:
                raise ValueError(f"Invalid tier: {tier}. Must be one of {valid_tiers}")
            
            # Query catalog for all data in the tier
            results = self.con.execute("""
                SELECT * FROM memory_catalog
                WHERE primary_tier = ?
                ORDER BY created_at DESC
            """, [tier]).fetchall()
            
            # Convert rows to dictionaries
            columns = ['data_id', 'primary_tier', 'location', 'created_at',
                      'last_accessed', 'access_count', 'size', 'tags',
                      'data_type', 'table_name', 'additional_meta']
            return [dict(zip(columns, row)) for row in results]
            
        except Exception as e:
            self.logger.error(f"Failed to get data for tier {tier}: {e}")
            raise

    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            if hasattr(self, 'con') and self.con:
                self.con.close()
                self.logger.info("Closed DuckDB connection")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def __del__(self):
        """Ensure cleanup is called when object is destroyed."""
        self.cleanup()

# Create singleton instance
memory_catalog = MemoryCatalog()
