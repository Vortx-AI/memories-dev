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
            try:
                self.storage_path = Path(self.memory_manager.get_warm_path())
            except Exception as e:
                self.logger.warning(f"Error getting warm path from memory manager: {e}")
                # Fallback to default path
                self.storage_path = Path(os.path.join(os.getcwd(), 'data', 'memory', 'warm'))
                
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
            # Set default values
            memory_limit = '8GB'
            threads = 4
            
            # Try to get config values safely
            if hasattr(self.memory_manager, 'config'):
                config = self.memory_manager.config
                # Check if config has memory and warm attributes
                if hasattr(config, 'config') and isinstance(config.config, dict):
                    if 'memory' in config.config and 'warm' in config.config['memory']:
                        warm_config = config.config['memory']['warm']
                        if 'duckdb' in warm_config:
                            duckdb_config = warm_config['duckdb']
                            memory_limit = duckdb_config.get('memory_limit', memory_limit)
                            threads = duckdb_config.get('threads', threads)
            
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
            # Create a basic connection as fallback
            try:
                if db_file:
                    return duckdb.connect(database=db_file, read_only=False)
                else:
                    return duckdb.connect(database=':memory:', read_only=False)
            except:
                raise
            
    def _init_tables(self, con: duckdb.DuckDBPyConnection) -> None:
        """Initialize database tables.
        
        Args:
            con: DuckDB connection to initialize tables in
        """
        try:
            # Create warm_data table first
            con.execute("""
                CREATE TABLE IF NOT EXISTS warm_data (
                    id VARCHAR PRIMARY KEY,
                    data JSON,
                    metadata JSON,
                    tags JSON,
                    stored_at TIMESTAMP
                )
            """)
            
            # Then create warm_tags table with foreign key reference
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
        
        # Initialize tables for the new connection
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
    
    def import_from_duckdb(
        self, 
        source_path: Union[str, Path], 
        db_name: Optional[str] = None,
        tables: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Import tables from another DuckDB database.
        
        Args:
            source_path: Path to source DuckDB database file
            db_name: Optional name for target database. If None, uses default connection.
            tables: Optional list of table names to import. If None, imports all tables.
            metadata: Optional metadata about the data
            tags: Optional tags for categorizing the data
            
        Returns:
            Dict containing success status and table information:
                - success: True if import was successful, False otherwise
                - data_ids: Dictionary mapping table names to their data IDs
                - imported_tables: List of imported table names
        """
        con = self.get_connection(db_name)
        source_path = str(source_path)
        
        try:
            # Attach source database
            con.execute(f"ATTACH '{source_path}' as source")
            
            # Get list of tables excluding system tables
            if tables:
                # Filter to only the specified tables
                tables_query = f"""
                    SELECT name as table_name
                    FROM source.sqlite_master 
                    WHERE type='table' 
                    AND name IN ({','.join(['?' for _ in tables])})
                """
                tables_result = con.execute(tables_query, tables).fetchall()
            else:
                # Get all non-system tables
                tables_result = con.execute("""
                    SELECT name as table_name
                    FROM source.sqlite_master 
                    WHERE type='table' 
                    AND name NOT IN ('warm_data', 'warm_tags')
                    AND name NOT LIKE 'sqlite_%'
                    AND name NOT LIKE 'pg_%'
                """).fetchall()
            
            # Track imported tables and their IDs
            imported_tables = []
            data_ids = {}
            
            for (table,) in tables_result:
                # Handle prefixed table names (e.g. dubai_memories.warm_data)
                target_table = table.split('.')[-1] if '.' in table else table
                source_table = f"source.{table}"
                
                # Create target table and copy data
                con.execute(f"""
                    CREATE TABLE IF NOT EXISTS "{target_table}" AS 
                    SELECT * FROM {source_table}
                """)
                
                # Store metadata about imported table
                table_metadata = {
                    'source_path': source_path,
                    'source_table': table,
                    'imported_at': datetime.now().isoformat(),
                    'row_count': con.execute(f'SELECT COUNT(*) FROM "{target_table}"').fetchone()[0]
                }
                
                # Add user-provided metadata if available
                if metadata:
                    table_metadata.update(metadata)
                
                # Generate unique ID for the table
                table_id = str(uuid.uuid4())
                
                # Insert metadata into warm_data
                con.execute("""
                    INSERT INTO warm_data (id, data, metadata, tags, stored_at)
                    VALUES (?, ?, ?, ?, ?)
                """, [
                    table_id,
                    None,  # No data payload for imported tables
                    json.dumps(table_metadata),
                    json.dumps(tags or []),  # Use provided tags or empty list
                    datetime.now()
                ])
                
                # Store tags for indexing
                if tags:
                    for tag in tags:
                        con.execute("""
                            INSERT INTO warm_tags (tag, data_id)
                            VALUES (?, ?)
                        """, [tag, table_id])
                
                # Track imported table
                imported_tables.append(target_table)
                data_ids[target_table] = table_id
                
                self.logger.info(f"Imported table {table} as {target_table}")
                
            con.execute("DETACH source")
            
            # Return success with table information
            return {
                "success": True,
                "data_ids": data_ids,
                "imported_tables": imported_tables
            }
            
        except Exception as e:
            self.logger.error(f"Error importing from DuckDB {source_path}: {e}")
            return {
                "success": False,
                "data_ids": {},
                "imported_tables": []
            }
            
        finally:
            # Always try to detach source database
            try:
                con.execute("DETACH source")
            except:
                pass

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