"""
Memory retrieval functionality for querying cold memory storage.
"""

import logging
from typing import Dict, Any, Optional, List, Union
import pandas as pd
import os
from pathlib import Path
import duckdb

logger = logging.getLogger(__name__)

class MemoryRetrieval:
    """Memory retrieval class for querying cold memory storage."""
    
    def __init__(self):
        """Initialize memory retrieval."""
        # Get the project root (where memories-dev is located)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        
        # Connect to the metadata database in memories-dev/data
        self.db_path = os.path.join(self.project_root, 'memories-dev', 'data', 'memories.db')
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database file not found at: {self.db_path}")
            
        self.con = duckdb.connect(self.db_path)
        self.logger = logging.getLogger(__name__)

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get statistics about registered files from metadata."""
        try:
            # First check if table exists
            table_exists = self.con.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='cold_metadata'
            """).fetchone()
            
            if not table_exists:
                self.logger.warning("cold_metadata table does not exist!")
                return {
                    'total_files': 0,
                    'total_size_mb': 0,
                    'file_types': {},
                    'storage_path': os.path.join(self.project_root, 'memories-dev', 'data')
                }
            
            # Query the metadata table for registered files
            query = """
                SELECT 
                    COUNT(*) as total_files,
                    SUM(size) as total_size,
                    data_type,
                    COUNT(*) as type_count
                FROM cold_metadata
                GROUP BY data_type
            """
            
            results = self.con.execute(query).df()
            
            stats = {
                'total_files': results['total_files'].sum() if not results.empty else 0,
                'total_size_mb': round(results['total_size'].sum() / (1024 * 1024), 2) if not results.empty else 0,
                'file_types': dict(zip(results['data_type'], results['type_count'])) if not results.empty else {},
                'storage_path': os.path.join(self.project_root, 'memories-dev', 'data')
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting storage stats: {e}")
            return {
                'total_files': 0,
                'total_size_mb': 0,
                'file_types': {},
                'storage_path': os.path.join(self.project_root, 'memories-dev', 'data')
            }

    def list_registered_files(self) -> List[Dict]:
        """List all registered files and their metadata."""
        try:
            query = """
                SELECT 
                    id,
                    timestamp,
                    size,
                    data_type,
                    additional_meta
                FROM cold_metadata
                ORDER BY timestamp DESC
            """
            
            results = self.con.execute(query).fetchall()
            files = []
            for row in results:
                files.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'size': row[2],
                    'data_type': row[3],
                    'metadata': row[4]
                })
            return files
            
        except Exception as e:
            self.logger.error(f"Error listing registered files: {e}")
            return []

    def list_available_data(self) -> List[Dict[str, Any]]:
        """List all available data tables and their metadata.
        
        Returns:
            List of dictionaries containing table information:
                - table_name: Name of the table
                - file_path: Original parquet file path
                - theme: Theme tag if provided during import
                - tag: Additional tag if provided during import
                - num_rows: Number of rows
                - num_columns: Number of columns
                - schema: Column names and types
        """
        return self.cold.list_tables()

    def get_schema(self, table_name: str) -> Optional[Dict[str, str]]:
        """Get schema for a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary mapping column names to their types, or None if table not found
        """
        return self.cold.get_table_schema(table_name)

    def preview_data(self, table_name: str, limit: int = 5) -> pd.DataFrame:
        """Preview data from a specific table.
        
        Args:
            table_name: Name of the table to preview
            limit: Number of rows to preview (default: 5)
            
        Returns:
            pandas DataFrame with preview rows
        """
        return self.cold.get_table_preview(table_name, limit)

    def search(self, 
              conditions: Dict[str, Any], 
              tables: Optional[List[str]] = None,
              limit: int = 100
    ) -> pd.DataFrame:
        """Search across tables using specified conditions.
        
        Args:
            conditions: Dictionary of column-value pairs to search for
            tables: Optional list of specific table names to search in
            limit: Maximum number of results to return (default: 100)
            
        Returns:
            pandas DataFrame with matching records
        """
        return self.cold.search(conditions, tables, limit)

    def query(self, sql_query: str) -> pd.DataFrame:
        """Execute a SQL query across all imported data.
        
        Args:
            sql_query: SQL query to execute
            
        Returns:
            pandas DataFrame with query results
        """
        return self.cold.query(sql_query)

    def get_data_by_theme(self, theme: str, limit: int = 100) -> pd.DataFrame:
        """Get data from tables with a specific theme.
        
        Args:
            theme: Theme to filter by
            limit: Maximum number of results to return (default: 100)
            
        Returns:
            pandas DataFrame with matching records
        """
        try:
            # Get tables with matching theme
            tables = self.cold.list_tables()
            theme_tables = [t["table_name"] for t in tables if t["theme"] == theme]
            
            if not theme_tables:
                self.logger.warning(f"No tables found with theme: {theme}")
                return pd.DataFrame()
            
            # Build query to union all matching tables
            queries = [f"SELECT *, '{table}' as source_table FROM {table}" for table in theme_tables]
            full_query = f"""
                SELECT * FROM (
                    {" UNION ALL ".join(queries)}
                ) combined_results
                LIMIT {limit}
            """
            
            return self.cold.query(full_query)
            
        except Exception as e:
            self.logger.error(f"Error getting data for theme {theme}: {e}")
            return pd.DataFrame()

    def get_data_by_tag(self, tag: str, limit: int = 100) -> pd.DataFrame:
        """Get data from tables with a specific tag.
        
        Args:
            tag: Tag to filter by
            limit: Maximum number of results to return (default: 100)
            
        Returns:
            pandas DataFrame with matching records
        """
        try:
            # Get tables with matching tag
            tables = self.cold.list_tables()
            tag_tables = [t["table_name"] for t in tables if t["tag"] == tag]
            
            if not tag_tables:
                self.logger.warning(f"No tables found with tag: {tag}")
                return pd.DataFrame()
            
            # Build query to union all matching tables
            queries = [f"SELECT *, '{table}' as source_table FROM {table}" for table in tag_tables]
            full_query = f"""
                SELECT * FROM (
                    {" UNION ALL ".join(queries)}
                ) combined_results
                LIMIT {limit}
            """
            
            return self.cold.query(full_query)
            
        except Exception as e:
            self.logger.error(f"Error getting data for tag {tag}: {e}")
            return pd.DataFrame()

    def get_data_by_date_range(
        self,
        start_date: str,
        end_date: str,
        date_column: str = "timestamp",
        limit: int = 100
    ) -> pd.DataFrame:
        """Get data within a specific date range.
        
        Args:
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
            date_column: Name of the date column to filter on (default: "timestamp")
            limit: Maximum number of results to return (default: 100)
            
        Returns:
            pandas DataFrame with matching records
        """
        try:
            # Get all tables
            tables = self.cold.list_tables()
            if not tables:
                self.logger.warning("No tables available")
                return pd.DataFrame()
            
            # Build query to union all tables with date filter
            queries = []
            for table in tables:
                table_name = table["table_name"]
                # Check if the date column exists in this table
                schema = table["schema"]
                if date_column in schema:
                    queries.append(f"""
                        SELECT *, '{table_name}' as source_table 
                        FROM {table_name}
                        WHERE {date_column} BETWEEN '{start_date}' AND '{end_date}'
                    """)
            
            if not queries:
                self.logger.warning(f"No tables found with date column: {date_column}")
                return pd.DataFrame()
            
            full_query = f"""
                SELECT * FROM (
                    {" UNION ALL ".join(queries)}
                ) combined_results
                LIMIT {limit}
            """
            
            return self.cold.query(full_query)
            
        except Exception as e:
            self.logger.error(f"Error getting data for date range: {e}")
            return pd.DataFrame()

    def get_table_stats(self, table_name: str) -> Dict[str, Any]:
        """Get statistics for a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary containing table statistics:
                - row_count: Total number of rows
                - column_stats: Per-column statistics (min, max, avg, etc.)
        """
        try:
            # Get basic table info
            schema = self.cold.get_table_schema(table_name)
            if not schema:
                raise ValueError(f"Table not found: {table_name}")
            
            # Get row count
            count_query = f"SELECT COUNT(*) as row_count FROM {table_name}"
            row_count = self.cold.query(count_query).iloc[0]['row_count']
            
            # Get column statistics
            column_stats = {}
            for column, dtype in schema.items():
                if 'int' in dtype.lower() or 'float' in dtype.lower() or 'double' in dtype.lower():
                    stats_query = f"""
                        SELECT 
                            MIN({column}) as min_value,
                            MAX({column}) as max_value,
                            AVG({column}) as avg_value,
                            COUNT(DISTINCT {column}) as unique_count
                        FROM {table_name}
                    """
                    stats = self.cold.query(stats_query).to_dict('records')[0]
                    column_stats[column] = stats
                else:
                    # For non-numeric columns, just get unique count
                    stats_query = f"""
                        SELECT COUNT(DISTINCT {column}) as unique_count
                        FROM {table_name}
                    """
                    stats = {'unique_count': self.cold.query(stats_query).iloc[0]['unique_count']}
                    column_stats[column] = stats
            
            return {
                'row_count': row_count,
                'column_stats': column_stats
            }
            
        except Exception as e:
            self.logger.error(f"Error getting stats for table {table_name}: {e}")
            return {}

    def get_data_by_bbox(
        self,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
        lon_column: str = "longitude",
        lat_column: str = "latitude",
        geom_column: str = "geometry",
        limit: int = 1000
    ) -> pd.DataFrame:
        """Get data within a geographic bounding box.
        
        Args:
            min_lon: Minimum longitude of the bounding box
            min_lat: Minimum latitude of the bounding box
            max_lon: Maximum longitude of the bounding box
            max_lat: Maximum latitude of the bounding box
            lon_column: Name of the longitude column (default: "longitude")
            lat_column: Name of the latitude column (default: "latitude")
            geom_column: Name of the geometry column (default: "geometry")
            limit: Maximum number of results to return (default: 1000)
            
        Returns:
            pandas DataFrame with matching records
        """
        try:
            # Get all tables
            tables = self.cold.list_tables()
            if not tables:
                self.logger.warning("No tables available")
                return pd.DataFrame()
            
            # Install and load spatial extension if needed
            self.cold.con.execute("INSTALL spatial;")
            self.cold.con.execute("LOAD spatial;")
            
            # Build query to union all tables with bounding box filter
            results = pd.DataFrame()
            
            for table in tables:
                table_name = table["table_name"]
                schema = table["schema"]
                
                # Try geometry column first if it exists
                if geom_column in schema:
                    query = f"""
                        SELECT *, '{table_name}' as source_table 
                        FROM {table_name}
                        WHERE ST_Intersects(
                            ST_GeomFromWKB({geom_column}),
                            ST_MakeEnvelope({min_lon}, {min_lat}, {max_lon}, {max_lat})
                        )
                        LIMIT {limit}
                    """
                    try:
                        df = self.cold.query(query)
                        if not df.empty:
                            results = pd.concat([results, df], ignore_index=True)
                    except Exception as e:
                        self.logger.warning(f"Error querying table {table_name} with geometry: {e}")
                        
                # Fall back to lat/lon columns if they exist
                elif lon_column in schema and lat_column in schema:
                    query = f"""
                        SELECT *, '{table_name}' as source_table 
                        FROM {table_name}
                        WHERE {lon_column} BETWEEN {min_lon} AND {max_lon}
                        AND {lat_column} BETWEEN {min_lat} AND {max_lat}
                        LIMIT {limit}
                    """
                    try:
                        df = self.cold.query(query)
                        if not df.empty:
                            results = pd.concat([results, df], ignore_index=True)
                    except Exception as e:
                        self.logger.warning(f"Error querying table {table_name} with lat/lon: {e}")
            
            if results.empty:
                self.logger.warning(
                    f"No tables found with either geometry column ({geom_column}) "
                    f"or coordinate columns ({lon_column}, {lat_column})"
                )
            
            return results.head(limit) if not results.empty else results
            
        except Exception as e:
            self.logger.error(f"Error getting data for bounding box: {e}")
            return pd.DataFrame()

    def get_data_by_bbox_and_value(
        self,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
        search_value: str,
        case_sensitive: bool = False,
        lon_column: str = "longitude",
        lat_column: str = "latitude",
        geom_column: str = "geometry",
        limit: int = 1000
    ) -> pd.DataFrame:
        """Get data within a geographic bounding box that contains a specific value in any column.
        
        Args:
            min_lon: Minimum longitude of the bounding box
            min_lat: Minimum latitude of the bounding box
            max_lon: Maximum longitude of the bounding box
            max_lat: Maximum latitude of the bounding box
            search_value: Value to search for in any column
            case_sensitive: Whether to perform case-sensitive search (default: False)
            lon_column: Name of the longitude column (default: "longitude")
            lat_column: Name of the latitude column (default: "latitude")
            geom_column: Name of the geometry column (default: "geometry")
            limit: Maximum number of results to return (default: 1000)
            
        Returns:
            pandas DataFrame with matching records
        """
        try:
            # Get all tables
            tables = self.cold.list_tables()
            if not tables:
                self.logger.warning("No tables available")
                return pd.DataFrame()
            
            # Install and load spatial extension if needed
            self.cold.con.execute("INSTALL spatial;")
            self.cold.con.execute("LOAD spatial;")
            
            # Build query to union all tables with bounding box filter and value search
            queries = []
            
            for table in tables:
                table_name = table["table_name"]
                schema = table["schema"]
                
                # Get all column names for the table
                columns = list(schema.keys())
                
                # Build the LIKE conditions for each column
                # Use ILIKE for case-insensitive search if specified
                like_operator = "ILIKE" if not case_sensitive else "LIKE"
                value_conditions = []
                for col in columns:
                    # Cast column to string for searching
                    value_conditions.append(f"CAST({col} AS VARCHAR) {like_operator} '%{search_value}%'")
                
                value_query = " OR ".join(value_conditions)
                
                # Try geometry column first if it exists
                if geom_column in schema:
                    query = f"""
                        SELECT *, '{table_name}' as source_table 
                        FROM {table_name}
                        WHERE ST_Intersects(
                            ST_GeomFromWKB({geom_column}),
                            ST_MakeEnvelope({min_lon}, {min_lat}, {max_lon}, {max_lat})
                        )
                        AND ({value_query})
                    """
                    queries.append(query)
                        
                # Fall back to lat/lon columns if they exist
                elif lon_column in schema and lat_column in schema:
                    query = f"""
                        SELECT *, '{table_name}' as source_table 
                        FROM {table_name}
                        WHERE {lon_column} BETWEEN {min_lon} AND {max_lon}
                        AND {lat_column} BETWEEN {min_lat} AND {max_lat}
                        AND ({value_query})
                    """
                    queries.append(query)
            
            if not queries:
                self.logger.warning(
                    f"No tables found with either geometry column ({geom_column}) "
                    f"or coordinate columns ({lon_column}, {lat_column})"
                )
                return pd.DataFrame()
            
            # Combine all queries with UNION ALL and apply limit
            full_query = f"""
                SELECT * FROM (
                    {" UNION ALL ".join(queries)}
                ) combined_results
                LIMIT {limit}
            """
            
            # Execute the combined query
            try:
                results = self.cold.query(full_query)
            except Exception as e:
                self.logger.error(f"Error executing combined query: {e}")
                return pd.DataFrame()
            
            if results.empty:
                self.logger.warning(
                    f"No data found within bounding box containing value '{search_value}'"
                )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error getting data for bounding box and value: {e}")
            return pd.DataFrame()

    def get_data_by_fuzzy_search(
        self,
        search_term: str,
        similarity_threshold: float = 0.3,
        case_sensitive: bool = False,
        limit: int = 10
    ) -> pd.DataFrame:
        """Search for data across all columns using fuzzy string matching.
        
        Args:
            search_term: Term to search for
            similarity_threshold: Minimum similarity score (0-1) for matches (default: 0.3)
            case_sensitive: Whether to perform case-sensitive search (default: False)
            limit: Maximum number of results to return (default: 10)
            
        Returns:
            pandas DataFrame with matching records, sorted by similarity score
        """
        try:
            # Get all tables
            tables = self.cold.list_tables()
            if not tables:
                self.logger.warning("No tables available")
                return pd.DataFrame()
            
            # Build query to search across all tables with similarity scoring
            queries = []
            
            for table in tables:
                table_name = table["table_name"]
                schema = table["schema"]
                columns = list(schema.keys())
                
                # Build similarity conditions for each column
                similarity_conditions = []
                for col in columns:
                    # Handle case sensitivity
                    col_expr = col if case_sensitive else f"LOWER({col})"
                    search_expr = search_term if case_sensitive else f"LOWER('{search_term}')"
                    
                    # Calculate similarity score using Levenshtein distance
                    similarity_conditions.append(f"""
                        CASE 
                            WHEN {col_expr} IS NOT NULL THEN 
                                GREATEST(
                                    similarity(CAST({col_expr} AS VARCHAR), {search_expr}),
                                    similarity({search_expr}, CAST({col_expr} AS VARCHAR))
                                )
                        END as similarity_{col}
                    """)
                
                # Combine into a single query for this table
                query = f"""
                    SELECT 
                        *,
                        '{table_name}' as source_table,
                        {', '.join(similarity_conditions)},
                        GREATEST({
                            ', '.join([f"COALESCE(similarity_{col}, 0)" for col in columns])
                        }) as max_similarity
                    FROM {table_name}
                    WHERE GREATEST({
                        ', '.join([f"COALESCE(similarity_{col}, 0)" for col in columns])
                    }) >= {similarity_threshold}
                """
                queries.append(query)
            
            if not queries:
                self.logger.warning("No tables to search")
                return pd.DataFrame()
            
            # Combine all queries and sort by similarity
            full_query = f"""
                SELECT * FROM (
                    {" UNION ALL ".join(queries)}
                ) combined_results
                ORDER BY max_similarity DESC
                LIMIT {limit}
            """
            
            # Execute the combined query
            try:
                results = self.cold.query(full_query)
            except Exception as e:
                self.logger.error(f"Error executing fuzzy search query: {e}")
                return pd.DataFrame()
            
            if results.empty:
                self.logger.warning(
                    f"No data found matching search term '{search_term}' with "
                    f"similarity threshold {similarity_threshold}"
                )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in fuzzy search: {e}")
            return pd.DataFrame()

    def get_data_by_polygon(
        self,
        polygon_wkt: str,
        geom_column: str = "geometry",
        limit: int = 1000
    ) -> pd.DataFrame:
        """Get data that intersects with a polygon."""
        try:
            # Get all tables
            tables = self.cold.list_tables()
            if not tables:
                self.logger.warning("No tables available")
                return pd.DataFrame()
            
            # Install and load spatial extension
            self.cold.con.execute("INSTALL spatial;")
            self.cold.con.execute("LOAD spatial;")
            
            # Query each table separately and combine results
            results = pd.DataFrame()
            
            for table in tables:
                table_name = table["table_name"]
                schema = table["schema"]
                
                # Check if geometry column exists in this table
                if geom_column in schema:
                    query = f"""
                        SELECT *, '{table_name}' as source_table 
                        FROM {table_name}
                        WHERE ST_Intersects(
                            ST_GeomFromWKB({geom_column}), 
                            ST_GeomFromText('{polygon_wkt}')
                        )
                        LIMIT {limit}
                    """
                    try:
                        df = self.cold.query(query)
                        if not df.empty:
                            results = pd.concat([results, df], ignore_index=True)
                    except Exception as e:
                        self.logger.warning(f"Error querying table {table_name}: {e}")
            
            if results.empty:
                self.logger.warning(f"No tables found with geometry column: {geom_column}")
            
            return results.head(limit) if not results.empty else results
            
        except Exception as e:
            self.logger.error(f"Error getting data for polygon: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_data_by_bbox_static(
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
        lon_column: str = "longitude",
        lat_column: str = "latitude",
        geom_column: str = "geometry",
        limit: int = 1000,
        data_path: str = 'data'
    ) -> pd.DataFrame:
        """Get data within a geographic bounding box (static method).
        
        Args:
            min_lon: Minimum longitude of the bounding box
            min_lat: Minimum latitude of the bounding box
            max_lon: Maximum longitude of the bounding box
            max_lat: Maximum latitude of the bounding box
            lon_column: Name of the longitude column (default: "longitude")
            lat_column: Name of the latitude column (default: "latitude")
            geom_column: Name of the geometry column (default: "geometry")
            limit: Maximum number of results to return (default: 1000)
            data_path: Path to the data directory (default: 'data')
            
        Returns:
            pandas DataFrame with matching records
        """
        from memories.core.cold import ColdMemory
        from pathlib import Path
        
        # Create temporary retrieval instance
        cold_memory = ColdMemory(storage_path=Path(data_path))
        retrieval = MemoryRetrieval(cold_memory)
        
        # Use the instance method
        return retrieval.get_data_by_bbox(
            min_lon=min_lon,
            min_lat=min_lat,
            max_lon=max_lon,
            max_lat=max_lat,
            lon_column=lon_column,
            lat_column=lat_column,
            geom_column=geom_column,
            limit=limit
        ) 