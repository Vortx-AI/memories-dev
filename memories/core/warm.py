"""
Warm memory implementation using DuckDB for intermediate data storage.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import json
from datetime import datetime
import duckdb
import uuid
import numpy as np
import os

# Remove direct import to avoid circular dependency
# from memories.core.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

class WarmMemory:
    """Warm memory layer using DuckDB for storage."""
    
    def __init__(self, storage_path: str = None):
        """Initialize warm memory.
        
        Args:
            storage_path: Optional path to store DuckDB files
        """
        self.logger = logging.getLogger(__name__)
        
        # Lazy import to avoid circular dependency
        from memories.core.memory_manager import MemoryManager
        self.memory_manager = MemoryManager()
        
        # Set up storage path
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            # Use default path from memory manager
            self.storage_path = Path(self.memory_manager.get_warm_path())
        
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Warm memory storage path: {self.storage_path}")
        
        # Initialize DuckDB connection
        self.con = self._init_duckdb()
        self._init_tables(self.con)
        self.connections = {}

    def _init_duckdb(self, db_file: Optional[str] = None) -> duckdb.DuckDBPyConnection:
        """Initialize DuckDB connection.
        
        Args:
            db_file: Optional path to a DuckDB file. If None, creates an in-memory database.
            
        Returns:
            DuckDB connection
        """
        try:
            # Get DuckDB configuration from memory manager
            warm_config = self.memory_manager.config['memory'].get('warm', {})
            duckdb_config = warm_config.get('duckdb', {})
            
            # Set memory limit and threads
            memory_limit = duckdb_config.get('memory_limit', '8GB')
            threads = duckdb_config.get('threads', 4)
            
            # Create connection
            if db_file:
                con = duckdb.connect(database=db_file, read_only=False)
            else:
                con = duckdb.connect(database=':memory:', read_only=False)
            
            # Set configuration
            con.execute(f"SET memory_limit='{memory_limit}'")
            con.execute(f"SET threads={threads}")
            
            return con
            
        except Exception as e:
            self.logger.error(f"Error initializing DuckDB for warm storage: {e}")
            raise
            
    def _init_tables(self, con: duckdb.DuckDBPyConnection) -> None:
        """Initialize database tables.
        
        Args:
            con: DuckDB connection to initialize tables in
        """
        try:
            # Create tables if they don't exist
            con.execute("""
                CREATE TABLE IF NOT EXISTS warm_data (
                    id VARCHAR PRIMARY KEY,
                    data JSON,
                    metadata JSON,
                    tags JSON,
                    stored_at TIMESTAMP
                )
            """)
            
            con.execute("""
                CREATE TABLE IF NOT EXISTS warm_tags (
                    tag VARCHAR,
                    data_id VARCHAR,
                    PRIMARY KEY (tag, data_id),
                    FOREIGN KEY (data_id) REFERENCES warm_data(id)
                )
            """)
            
            self.logger.info("Initialized warm memory tables")
            
        except Exception as e:
            self.logger.error(f"Error initializing tables for warm storage: {e}")
            raise

    async def store(
        self,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        db_name: Optional[str] = None,
        table_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Store data in warm memory with metadata and tags.
        
        Args:
            data: Data to store
            metadata: Optional metadata about the data
            tags: Optional tags for categorizing the data
            db_name: Optional name of the database file to store in (without .duckdb extension)
            table_name: Optional name for the table to create. If None, a name will be generated.
            
        Returns:
            Dict containing success status and table information:
                - success: True if storage was successful, False otherwise
                - data_id: The unique ID of the stored data
                - table_name: The name of the table where data is stored
        """
        try:
            # Get connection
            con = self.get_connection(db_name)
            
            # Generate unique ID
            data_id = str(uuid.uuid4())
            
            # Generate table name if not provided
            if not table_name:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                table_name = f"warm_data_{timestamp}_{data_id[:8]}"
            
            # Sanitize table name (remove special characters)
            table_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in table_name)
            
            # Convert data to JSON
            if isinstance(data, (np.ndarray, np.generic)):
                data_json = json.dumps(data.tolist())
            elif hasattr(data, 'to_dict'):
                # Handle pandas DataFrame or Series
                data_json = json.dumps(data.to_dict())
            else:
                data_json = json.dumps(data)
                
            # Convert metadata to JSON
            metadata_json = json.dumps(metadata or {})
            
            # Convert tags to JSON
            tags_json = json.dumps(tags or [])
            
            # Create a new table for this data entry
            con.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id VARCHAR PRIMARY KEY,
                    data JSON,
                    metadata JSON,
                    tags JSON,
                    stored_at TIMESTAMP
                )
            """)
            
            # Store data in the new table
            con.execute(f"""
                INSERT INTO {table_name} (id, data, metadata, tags, stored_at)
                VALUES (?, ?, ?, ?, ?)
            """, [data_id, data_json, metadata_json, tags_json, datetime.now()])
            
            # Also store in the main warm_data table for backward compatibility
            con.execute("""
                INSERT INTO warm_data (id, data, metadata, tags, stored_at)
                VALUES (?, ?, ?, ?, ?)
            """, [data_id, data_json, metadata_json, tags_json, datetime.now()])
            
            # Store tags for indexing
            if tags:
                for tag in tags:
                    con.execute("""
                        INSERT INTO warm_tags (tag, data_id)
                        VALUES (?, ?)
                    """, [tag, data_id])
            
            return {
                "success": True,
                "data_id": data_id,
                "table_name": table_name
            }

        except Exception as e:
            self.logger.error(f"Error storing in warm storage: {e}")
            return {
                "success": False,
                "data_id": None,
                "table_name": None
            }

    async def retrieve(
        self,
        query: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        db_name: Optional[str] = None,
        table_name: Optional[str] = None
    ) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        """Retrieve data from warm memory.
        
        Args:
            query: Optional query parameters
            tags: Optional tags to filter by
            db_name: Optional name of the database file to retrieve from (without .duckdb extension)
            table_name: Optional name of the specific table to query
            
        Returns:
            Retrieved data or None if not found
        """
        try:
            # Get connection
            con = self.get_connection(db_name)
            
            results = []
            
            # If table_name is provided, query that specific table
            if table_name:
                # Check if table exists
                table_exists = con.execute(f"""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='{table_name}'
                """).fetchone()
                
                if not table_exists:
                    self.logger.warning(f"Table {table_name} does not exist")
                    return None
                
                # Query the specific table
                query_result = con.execute(f"""
                    SELECT * FROM {table_name}
                    ORDER BY stored_at DESC
                """).fetchall()
                
            elif tags:
                # Get data by tags
                placeholders = ', '.join(['?'] * len(tags))
                query_result = con.execute(f"""
                    SELECT DISTINCT d.* 
                    FROM warm_data d
                    JOIN warm_tags t ON d.id = t.data_id
                    WHERE t.tag IN ({placeholders})
                    ORDER BY d.stored_at DESC
                """, tags).fetchall()
            elif query:
                # Build query conditions
                conditions = []
                params = []
                
                # Handle data query
                if 'data' in query:
                    for key, value in query['data'].items():
                        # Use the appropriate JSON extraction function based on value type
                        if isinstance(value, str):
                            conditions.append(f"json_extract_string(data, '$.{key}') = ?")
                        elif isinstance(value, (int, float, bool)):
                            conditions.append(f"json_extract(data, '$.{key}') = ?")
                        else:
                            # For complex types, convert to JSON and compare
                            conditions.append(f"json_extract(data, '$.{key}') = ?")
                        params.append(value)
                
                # Handle metadata query
                if 'metadata' in query:
                    for key, value in query['metadata'].items():
                        # Use the appropriate JSON extraction function based on value type
                        if isinstance(value, str):
                            conditions.append(f"json_extract_string(metadata, '$.{key}') = ?")
                        elif isinstance(value, (int, float, bool)):
                            conditions.append(f"json_extract(metadata, '$.{key}') = ?")
                        else:
                            # For complex types, convert to JSON and compare
                            conditions.append(f"json_extract(metadata, '$.{key}') = ?")
                        params.append(value)
                
                # Build WHERE clause
                where_clause = " AND ".join(conditions) if conditions else "1=1"
                
                # Execute query
                query_result = con.execute(f"""
                    SELECT * FROM warm_data
                    WHERE {where_clause}
                    ORDER BY stored_at DESC
                """, params).fetchall()
            else:
                # Get all data
                query_result = con.execute("""
                    SELECT * FROM warm_data
                    ORDER BY stored_at DESC
                """).fetchall()
            
            # Process results
            for row in query_result:
                data_json = row[1]  # data column
                metadata_json = row[2]  # metadata column
                tags_json = row[3]  # tags column
                stored_at = row[4]  # stored_at column
                
                # Parse JSON
                data = json.loads(data_json)
                metadata = json.loads(metadata_json)
                tags = json.loads(tags_json)
                
                # Add to results
                results.append({
                    "data": data,
                    "metadata": metadata,
                    "tags": tags,
                    "stored_at": stored_at.isoformat() if stored_at else None
                })
            
            return results[0] if len(results) == 1 else results if results else None

        except Exception as e:
            self.logger.error(f"Error retrieving from warm storage: {e}")
            return None

    def clear(self) -> None:
        """Clear all data from warm memory."""
        try:
            # Delete all data from tables
            self.con.execute("DELETE FROM warm_tags")
            self.con.execute("DELETE FROM warm_data")
            self.logger.info("Cleared warm memory")
        except Exception as e:
            self.logger.error(f"Failed to clear warm memory: {e}")

    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            if hasattr(self, 'con') and self.con:
                # Only close connection if it's not the one managed by memory_manager
                if not (hasattr(self.memory_manager, 'con') and self.memory_manager.con == self.con):
                    self.con.close()
                    self.con = None

            self.logger.info("Cleaned up warm memory resources")
        except Exception as e:
            self.logger.error(f"Failed to cleanup warm memory: {e}")

    def __del__(self):
        """Destructor to ensure cleanup is performed."""
        self.cleanup()

    async def get_schema(self, data_id: str) -> Optional[Dict[str, Any]]:
        """Get schema information for stored data.
        
        Args:
            data_id: ID of the data to get schema for
            
        Returns:
            Dictionary containing schema information or None if not found
        """
        try:
            # Get data by ID
            result = self.con.execute("""
                SELECT data, metadata FROM warm_data
                WHERE id = ?
            """, [data_id]).fetchone()
            
            if not result:
                return None
                
            data_json, metadata_json = result
            
            # Parse JSON
            data_value = json.loads(data_json)
            metadata = json.loads(metadata_json)
            
            # Generate schema
            if isinstance(data_value, dict):
                schema = {
                    'fields': list(data_value.keys()),
                    'types': {k: type(v).__name__ for k, v in data_value.items()},
                    'type': 'dict',
                    'source': 'duckdb'
                }
            elif isinstance(data_value, list):
                if data_value:
                    if all(isinstance(x, dict) for x in data_value):
                        # List of dictionaries - combine all keys
                        all_keys = set().union(*(d.keys() for d in data_value if isinstance(d, dict)))
                        schema = {
                            'fields': list(all_keys),
                            'types': {k: type(next(d[k] for d in data_value if k in d)).__name__ 
                                    for k in all_keys},
                            'type': 'list_of_dicts',
                            'source': 'duckdb'
                        }
                    else:
                        schema = {
                            'type': 'list',
                            'element_type': type(data_value[0]).__name__,
                            'length': len(data_value),
                            'source': 'duckdb'
                        }
                else:
                    schema = {
                        'type': 'list',
                        'length': 0,
                        'source': 'duckdb'
                    }
            else:
                schema = {
                    'type': type(data_value).__name__,
                    'source': 'duckdb'
                }
                
            # Add metadata if available
            if metadata:
                schema['metadata'] = metadata
                
            return schema
            
        except Exception as e:
            self.logger.error(f"Failed to get schema for {data_id}: {e}")
            return None

    def get_connection(self, db_name: Optional[str] = None) -> duckdb.DuckDBPyConnection:
        """Get a connection to a specific database file.
        
        Args:
            db_name: Name of the database file (without .duckdb extension).
                    If None, returns the default connection.
                    
        Returns:
            DuckDB connection
        """
        if not db_name:
            return self.con
            
        # Check if connection already exists
        if db_name in self.connections:
            return self.connections[db_name]
            
        # Create new connection
        db_file = str(self.storage_path / f"{db_name}.duckdb")
        con = self._init_duckdb(db_file)
        
        # Initialize tables
        self._init_tables(con)
        
        # Store connection
        self.connections[db_name] = con
        
        return con

    async def import_from_parquet(
        self,
        parquet_file: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        db_name: Optional[str] = None,
        table_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Import data from a parquet file into warm memory.
        
        Args:
            parquet_file: Path to the parquet file
            metadata: Optional metadata about the data
            tags: Optional tags for categorizing the data
            db_name: Optional name of the database file to store in (without .duckdb extension)
            table_name: Optional name for the table to create. If None, a name will be generated.
            
        Returns:
            Dict containing success status and table information:
                - success: True if import was successful, False otherwise
                - data_id: The unique ID of the stored data
                - table_name: The name of the table where data is stored
        """
        try:
            # Get connection
            con = self.get_connection(db_name)
            
            # Generate unique ID
            data_id = str(uuid.uuid4())
            
            # Generate table name if not provided
            if not table_name:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                file_basename = os.path.basename(parquet_file).split('.')[0]
                table_name = f"parquet_{file_basename}_{timestamp}_{data_id[:8]}"
            
            # Sanitize table name (remove special characters)
            table_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in table_name)
            
            # Create a new table from the parquet file
            con.execute(f"""
                CREATE TABLE {table_name} AS 
                SELECT * FROM read_parquet('{parquet_file}')
            """)
            
            # Get the data as JSON for storage in warm_data
            data_result = con.execute(f"SELECT * FROM {table_name}").fetchall()
            column_names = [desc[0] for desc in con.description]
            
            # Convert to list of dictionaries
            data_list = []
            for row in data_result:
                data_list.append(dict(zip(column_names, row)))
            
            # Convert to JSON
            data_json = json.dumps(data_list)
            
            # Convert metadata to JSON
            metadata_json = json.dumps(metadata or {})
            
            # Convert tags to JSON
            tags_json = json.dumps(tags or [])
            
            # Store metadata in warm_data for backward compatibility
            con.execute("""
                INSERT INTO warm_data (id, data, metadata, tags, stored_at)
                VALUES (?, ?, ?, ?, ?)
            """, [data_id, data_json, metadata_json, tags_json, datetime.now()])
            
            # Store tags for indexing
            if tags:
                for tag in tags:
                    con.execute("""
                        INSERT INTO warm_tags (tag, data_id)
                        VALUES (?, ?)
                    """, [tag, data_id])
            
            self.logger.info(f"Imported parquet file {parquet_file} to table {table_name}")
            
            return {
                "success": True,
                "data_id": data_id,
                "table_name": table_name
            }
            
        except Exception as e:
            self.logger.error(f"Error importing parquet file: {e}")
            return {
                "success": False,
                "data_id": None,
                "table_name": None
            }
    
    async def import_from_duckdb(
        self,
        source_db_file: str,
        tables: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        db_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Import tables from another DuckDB database using direct table copying.
        
        Args:
            source_db_file: Path to the source DuckDB database file
            tables: Optional list of table names to import. If None, imports all tables.
            metadata: Optional metadata about the data
            tags: Optional tags for categorizing the data
            db_name: Optional name of the database file to store in (without .duckdb extension)
            
        Returns:
            Dict containing success status and table information:
                - success: True if import was successful, False otherwise
                - imported_tables: List of imported table names
                - data_ids: Dict mapping table names to data IDs
        """
        try:
            # Get connection to target database
            target_con = self.get_connection(db_name)
            
            # Attach the source database with an alias
            target_con.execute(f"ATTACH '{source_db_file}' AS source_db")
            
            # Get list of tables in source database
            source_tables = target_con.execute("""
                SELECT name FROM source_db.sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """).fetchall()
            
            source_table_names = [table[0] for table in source_tables]
            
            # Filter tables if specified
            if tables:
                tables_to_import = [t for t in tables if t in source_table_names]
                if not tables_to_import:
                    self.logger.warning(f"None of the specified tables found in source database")
                    # Detach the source database
                    target_con.execute("DETACH source_db")
                    return {
                        "success": False,
                        "imported_tables": [],
                        "data_ids": {}
                    }
            else:
                tables_to_import = source_table_names
            
            # Import each table
            imported_tables = []
            data_ids = {}
            
            for table_name in tables_to_import:
                try:
                    # Generate unique ID
                    data_id = str(uuid.uuid4())
                    
                    # Create table in target database directly from source
                    target_con.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM source_db.{table_name}")
                    
                    # Get row count
                    row_count = target_con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                    
                    # Create minimal metadata for the warm_data table
                    meta_dict = metadata.copy() if metadata else {}
                    meta_dict["source_db"] = source_db_file
                    meta_dict["source_table"] = table_name
                    meta_dict["row_count"] = row_count
                    meta_dict["imported_at"] = datetime.now().isoformat()
                    
                    # Convert to JSON - we store empty data since the actual data is in the table
                    data_json = "[]"
                    
                    # Convert metadata to JSON
                    metadata_json = json.dumps(meta_dict)
                    
                    # Convert tags to JSON
                    tags_json = json.dumps(tags or [])
                    
                    # Store metadata in warm_data for backward compatibility
                    target_con.execute("""
                        INSERT INTO warm_data (id, data, metadata, tags, stored_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, [data_id, data_json, metadata_json, tags_json, datetime.now()])
                    
                    # Store tags for indexing
                    if tags:
                        for tag in tags:
                            target_con.execute("""
                                INSERT INTO warm_tags (tag, data_id)
                                VALUES (?, ?)
                            """, [tag, data_id])
                    
                    # Add special tags for imported tables
                    target_con.execute("""
                        INSERT INTO warm_tags (tag, data_id)
                        VALUES (?, ?)
                    """, ["duckdb_import", data_id])
                    
                    target_con.execute("""
                        INSERT INTO warm_tags (tag, data_id)
                        VALUES (?, ?)
                    """, [f"table:{table_name}", data_id])
                    
                    imported_tables.append(table_name)
                    data_ids[table_name] = data_id
                    
                except Exception as e:
                    self.logger.error(f"Error importing table {table_name}: {e}")
            
            # Detach the source database
            target_con.execute("DETACH source_db")
            
            if imported_tables:
                self.logger.info(f"Imported {len(imported_tables)} tables from {source_db_file}")
            
            return {
                "success": True,
                "imported_tables": imported_tables,
                "data_ids": data_ids
            }
            
        except Exception as e:
            self.logger.error(f"Error importing from DuckDB: {e}")
            # Make sure to detach in case of error
            try:
                target_con.execute("DETACH source_db")
            except:
                pass
            return {
                "success": False,
                "imported_tables": [],
                "data_ids": {}
            }

    async def import_from_csv(
        self,
        csv_file: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        db_name: Optional[str] = None,
        table_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Import data from a CSV file into warm memory.
        
        Args:
            csv_file: Path to the CSV file
            metadata: Optional metadata about the data
            tags: Optional tags for categorizing the data
            db_name: Optional name of the database file to store in (without .duckdb extension)
            table_name: Optional name for the table to create. If None, a name will be generated.
            
        Returns:
            Dict containing success status and table information:
                - success: True if import was successful, False otherwise
                - data_id: The unique ID of the stored data
                - table_name: The name of the table where data is stored
        """
        try:
            # Get connection
            con = self.get_connection(db_name)
            
            # Generate unique ID
            data_id = str(uuid.uuid4())
            
            # Generate table name if not provided
            if not table_name:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                file_basename = os.path.basename(csv_file).split('.')[0]
                table_name = f"csv_{file_basename}_{timestamp}_{data_id[:8]}"
            
            # Sanitize table name (remove special characters)
            table_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in table_name)
            
            # Create a new table from the CSV file
            con.execute(f"""
                CREATE TABLE {table_name} AS 
                SELECT * FROM read_csv_auto('{csv_file}')
            """)
            
            # Get the data as JSON for storage in warm_data
            data_result = con.execute(f"SELECT * FROM {table_name}").fetchall()
            column_names = [desc[0] for desc in con.description]
            
            # Convert to list of dictionaries
            data_list = []
            for row in data_result:
                data_list.append(dict(zip(column_names, row)))
            
            # Convert to JSON
            data_json = json.dumps(data_list)
            
            # Convert metadata to JSON
            metadata_json = json.dumps(metadata or {})
            
            # Convert tags to JSON
            tags_json = json.dumps(tags or [])
            
            # Store metadata in warm_data for backward compatibility
            con.execute("""
                INSERT INTO warm_data (id, data, metadata, tags, stored_at)
                VALUES (?, ?, ?, ?, ?)
            """, [data_id, data_json, metadata_json, tags_json, datetime.now()])
            
            # Store tags for indexing
            if tags:
                for tag in tags:
                    con.execute("""
                        INSERT INTO warm_tags (tag, data_id)
                        VALUES (?, ?)
                    """, [tag, data_id])
            
            self.logger.info(f"Imported CSV file {csv_file} to table {table_name}")
            
            return {
                "success": True,
                "data_id": data_id,
                "table_name": table_name
            }
            
        except Exception as e:
            self.logger.error(f"Error importing CSV file: {e}")
            return {
                "success": False,
                "data_id": None,
                "table_name": None
            }