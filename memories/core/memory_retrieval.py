"""
Memory retrieval functionality for querying cold memory storage.
"""

import logging
from typing import Dict, Any, Optional, List, Union, Tuple
import pandas as pd
import os
from pathlib import Path
import duckdb
from memories.core.cold import Config
import json
import glob
import time
from memories.core.red_hot import RedHotMemory
from sentence_transformers import SentenceTransformer
import numpy as np
from memories.core.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

class MemoryRetrieval:
    """Memory retrieval class for querying cold memory storage."""
    
    def __init__(self):
        """Initialize memory retrieval with DuckDB connection."""
        # Get project root directory
        project_root = Path(__file__).parent.parent.parent
        
        # Set up data directories
        self.data_dir = os.path.join(project_root, "data")
        
        # Get memory manager instance and its connection
        self.memory_manager = MemoryManager()
        self.con = self.memory_manager.con
        
        # Install and load spatial extension
        try:
            self.con.execute("INSTALL spatial;")
            self.con.execute("LOAD spatial;")
            logger.info("Spatial extension installed and loaded successfully")
        except Exception as e:
            logger.error(f"Error setting up spatial extension: {e}")
        
        # Initialize red-hot memory
        self.red_hot = RedHotMemory()
        
        # Initialize sentence transformer model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        logger.info(f"Initialized MemoryRetrieval")
        logger.info(f"Data directory: {self.data_dir}")

    def get_table_schema(self) -> List[str]:
        """Get the schema of the parquet files."""
        try:
            # Get first parquet file
            file_query = """
                SELECT path 
                FROM cold_metadata 
                WHERE data_type = 'parquet' 
                LIMIT 1
            """
            first_file = self.con.execute(file_query).fetchone()
            
            if not first_file:
                return []
                
            # Create temporary view to inspect schema
            self.con.execute(f"""
                CREATE OR REPLACE VIEW temp_view AS 
                SELECT * FROM read_parquet('{first_file[0]}')
            """)
            
            # Get column names
            schema = self.con.execute("DESCRIBE temp_view").fetchall()
            
            return [col[0] for col in schema]
            
        except Exception as e:
            logger.error(f"Error getting schema: {e}")
            return []

    def find_geometry_column(self, schema: List[Tuple]) -> Tuple[Optional[str], Optional[str]]:
        """
        Find the geometry column and its type in the schema.
        
        Returns:
            Tuple of (column_name, column_type) or (None, None) if not found
        """
        geometry_names = ['geom', 'geometry', 'the_geom', 'wkb_geometry']
        for col in schema:
            col_name = col[0].lower()
            if col_name in geometry_names:
                return col[0], col[1]
        return None, None

    def get_geometry_expression(self, column: str, col_type: str) -> str:
        """
        Get the appropriate geometry expression based on column type.
        """
        if 'BLOB' in col_type.upper():
            return f"ST_GeomFromWKB(CAST({column} AS BLOB))"
        elif 'GEOMETRY' in col_type.upper():
            return column
        else:
            raise ValueError(f"Unsupported geometry type: {col_type}")

    def get_parquet_schema(self, file_path: str) -> List[Tuple]:
        """Get schema for a specific parquet file."""
        try:
            self.con.execute(f"""
                CREATE OR REPLACE VIEW temp_view AS 
                SELECT * FROM read_parquet('{file_path}')
            """)
            schema = self.con.execute("DESCRIBE temp_view").fetchall()
            
            # Print schema details for debugging
            logger.debug(f"Schema for {file_path}:")
            for col in schema:
                logger.debug(f"Column: {col[0]}, Type: {col[1]}")
                
            return schema
        except Exception as e:
            logger.error(f"Error getting schema for {file_path}: {e}")
            return []

    def get_geometry_bounds(self, geom_expr: str) -> str:
        """Get the bounds of a geometry using ST_Envelope."""
        return f"""
            SELECT 
                MIN(ST_XMin(ST_Envelope({geom_expr}))) as min_lon,
                MIN(ST_YMin(ST_Envelope({geom_expr}))) as min_lat,
                MAX(ST_XMax(ST_Envelope({geom_expr}))) as max_lon,
                MAX(ST_YMax(ST_Envelope({geom_expr}))) as max_lat
        """

    def build_select_clause(self, schema: List[Tuple], geom_column: str, geom_type: str) -> str:
        """Build SELECT clause based on available columns."""
        available_columns = [col[0] for col in schema]
        select_parts = []

        # Map of possible column names to standardized names
        column_mappings = {
            'names': 'name',
            'name': 'name',
            'osm_id': 'id',
            'id': 'id',
            'highway': 'type',
            'waterway': 'type',
            'place': 'type',
            'building': 'type'
        }

        # Add mapped columns that exist
        for source, target in column_mappings.items():
            if source in available_columns:
                select_parts.append(f"{source} as {target}")

        # Add other interesting columns that exist
        extra_columns = ['min_height', 'num_floors', 'addresses', 'categories', 'confidence']
        for col in extra_columns:
            if col in available_columns:
                select_parts.append(col)

        # Get geometry expression
        geom_expr = self.get_geometry_expression(geom_column, geom_type)

        # Add geometry-derived columns
        select_parts.extend([
            f"ST_X(ST_Centroid({geom_expr})) as lon",
            f"ST_Y(ST_Centroid({geom_expr})) as lat"
        ])

        return ", ".join(select_parts)

    def get_parquet_files(self) -> List[str]:
        """Get all parquet files in the data directory."""
        parquet_files = []
        for pattern in ["**/*.parquet", "**/*.zstd.parquet"]:
            parquet_files.extend(
                glob.glob(os.path.join(self.data_dir, pattern), recursive=True)
            )
        return parquet_files

    def build_spatial_index(self):
        """Build spatial index for all parquet files."""
        try:
            # Get all parquet files
            files = self.get_parquet_files()
            
            if not files:
                logger.warning(f"No parquet files found in {self.data_dir}")
                return
                
            logger.info(f"Found {len(files)} parquet files")
            
            # Clear existing index
            self.con.execute("DELETE FROM spatial_index")
            
            for file_path in files:
                try:
                    # Get schema and geometry column
                    schema = self.get_parquet_schema(file_path)
                    geom_column, geom_type = self.find_geometry_column(schema)
                    
                    if not geom_column:
                        continue
                        
                    logger.info(f"Indexing {file_path}")
                    
                    # Get geometry expression
                    geom_expr = self.get_geometry_expression(geom_column, geom_type)
                    
                    # Calculate bounds for this file
                    bounds_query = f"""
                        {self.get_geometry_bounds(geom_expr)}
                        FROM read_parquet('{file_path}')
                    """
                    bounds = self.con.execute(bounds_query).fetchone()
                    
                    # Insert into spatial index
                    if bounds and None not in bounds:
                        self.con.execute("""
                            INSERT INTO spatial_index 
                            VALUES (?, ?, ?, ?, ?)
                        """, (file_path, *bounds))
                        logger.info(f"Indexed {file_path} with bounds: {bounds}")
                        
                except Exception as e:
                    logger.error(f"Error indexing {file_path}: {e}")
                    continue
                    
            # Create index on bounds
            self.con.execute("CREATE INDEX IF NOT EXISTS idx_spatial ON spatial_index(min_lon, min_lat, max_lon, max_lat)")
            
            # Log index statistics
            count = self.con.execute("SELECT COUNT(*) FROM spatial_index").fetchone()[0]
            logger.info(f"Built spatial index with {count} entries")
            
        except Exception as e:
            logger.error(f"Error building spatial index: {e}")
            raise

    def query_by_bbox(self, min_lon: float, min_lat: float, max_lon: float, max_lat: float) -> pd.DataFrame:
        """Query places within a bounding box using spatial index."""
        try:
            # Find potentially intersecting files using spatial index
            files_query = """
                SELECT path 
                FROM spatial_index 
                WHERE max_lon >= ? AND min_lon <= ? 
                  AND max_lat >= ? AND min_lat <= ?
            """
            files = self.con.execute(files_query, 
                                   (min_lon, max_lon, min_lat, max_lat)).fetchall()
            
            if not files:
                logger.warning("No files intersect the query bbox")
                return pd.DataFrame()

            logger.info(f"Found {len(files)} potentially matching files")

            # Process matching files
            results = []
            for file_path in [f[0] for f in files]:
                try:
                    schema = self.get_parquet_schema(file_path)
                    geom_column, geom_type = self.find_geometry_column(schema)
                    
                    if not geom_column:
                        continue
                        
                    geom_expr = self.get_geometry_expression(geom_column, geom_type)
                    select_clause = self.build_select_clause(schema, geom_column, geom_type)
                    
                    query = f"""
                        SELECT {select_clause}
                        FROM read_parquet('{file_path}')
                        WHERE ST_Intersects(
                            {geom_expr},
                            ST_MakeEnvelope(CAST({min_lon} AS DOUBLE), 
                                          CAST({min_lat} AS DOUBLE), 
                                          CAST({max_lon} AS DOUBLE), 
                                          CAST({max_lat} AS DOUBLE))
                        )
                    """
                    
                    result = self.con.execute(query).df()
                    
                    if not result.empty:
                        result['source_file'] = os.path.basename(file_path)
                        result['source_type'] = os.path.basename(os.path.dirname(os.path.dirname(file_path)))
                        results.append(result)
                        logger.info(f"Found {len(result)} results in {file_path}")
                        
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    continue
            
            if not results:
                return pd.DataFrame()
                
            combined = pd.concat(results, ignore_index=True, sort=False)
            return combined.sort_values('name') if 'name' in combined.columns else combined
            
        except Exception as e:
            logger.error(f"Error executing spatial query: {e}")
            raise

    def query_files(self, sql_query: str) -> pd.DataFrame:
        """
        Query across all registered parquet files.
        
        Args:
            sql_query: SQL query string. Use 'files.*' to query all columns.
        
        Returns:
            pandas.DataFrame with query results
        """
        try:
            # Get all registered parquet files
            files_query = """
                SELECT path 
                FROM cold_metadata 
                WHERE data_type = 'parquet'
            """
            files = self.con.execute(files_query).fetchall()
            
            if not files:
                logger.warning("No parquet files registered in the database")
                return pd.DataFrame()

            # Create a view combining all parquet files
            file_paths = [f[0] for f in files]
            files_list = ", ".join(f"'{path}'" for path in file_paths)
            
            create_view = f"""
                CREATE OR REPLACE VIEW files AS 
                SELECT * FROM read_parquet([{files_list}])
            """
            self.con.execute(create_view)
            
            # Execute the actual query
            result = self.con.execute(sql_query).df()
            return result
            
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise

    def get_similar_vectors(self, query_vector: np.ndarray, k: int = 5) -> List[Tuple[int, float]]:
        """
        Find most similar vectors in FAISS index.
        
        Args:
            query_vector: The vector to search for (must match index dimension)
            k: Number of similar results to return (default: 5)
            
        Returns:
            List of tuples containing (vector_id, similarity_score)
        """
        try:
            # Check if index exists and has vectors
            if not self.red_hot.index or self.red_hot.index.ntotal == 0:
                logger.warning("No vectors found in FAISS index")
                return []
            
            # Ensure vector has correct shape
            query_vector = query_vector.reshape(1, -1).astype('float32')
            
            # Search in FAISS index
            distances, indices = self.red_hot.index.search(query_vector, k)
            
            # Convert distances to similarities and pair with indices
            results = []
            for idx, (distance, vector_idx) in enumerate(zip(distances[0], indices[0])):
                if vector_idx != -1:  # Valid index
                    similarity = 1 - (distance / 2)  # Convert L2 distance to similarity score
                    results.append((int(vector_idx), float(similarity)))
            
            logger.info(f"Found {len(results)} similar vectors")
            return results

        except Exception as e:
            logger.error(f"Error finding similar vectors: {e}")
            return []

    def get_similar_words(self, query_word: str, k: int = 5) -> List[Tuple[str, float]]:
        """
        Find most similar words in FAISS index.
        
        Args:
            query_word: The word to search for
            k: Number of similar results to return (default: 5)
            
        Returns:
            List of tuples containing (word, similarity_score)
        """
        try:
            # Check if index exists and has vectors
            if not self.red_hot.index or self.red_hot.index.ntotal == 0:
                logger.warning("No vectors found in FAISS index")
                return []
            
            # Convert word to vector using sentence transformer
            query_vector = self.model.encode([query_word])[0]
            query_vector = query_vector.reshape(1, -1).astype('float32')
            
            # Search in FAISS index
            distances, indices = self.red_hot.index.search(query_vector, k)
            
            # Get words from metadata and pair with similarities
            results = []
            for idx, (distance, vector_idx) in enumerate(zip(distances[0], indices[0])):
                if vector_idx != -1:  # Valid index
                    metadata = self.red_hot.get_metadata(int(vector_idx))
                    word = metadata.get('word', f'Unknown_{vector_idx}')
                    similarity = 1 - (distance / 2)  # Convert L2 distance to similarity score
                    results.append((word, float(similarity)))
            
            logger.info(f"Found {len(results)} similar words for '{query_word}'")
            return results

        except Exception as e:
            logger.error(f"Error finding similar words: {e}")
            return []

    def get_storage_stats(self) -> Dict:
        """Get statistics about the FAISS index."""
        try:
            # Get index statistics if available
            index_stats = {}
            if self.red_hot.index:
                index = self.red_hot.index
                index_stats = {
                    'type': type(index).__name__,
                    'dimension': index.d,
                    'total_vectors': index.ntotal,
                    'is_trained': getattr(index, 'is_trained', True)
                }
            
            stats = {
                'faiss_index': {
                    'max_size': self.red_hot.max_size,
                    'storage_path': self.red_hot.storage_path,
                    'index_stats': index_stats,
                    'is_initialized': self.red_hot.index is not None
                }
            }

            logger.info(f"FAISS index statistics: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error getting FAISS stats: {e}")
            return {
                'faiss_index': {
                    'max_size': 0,
                    'storage_path': self.red_hot.storage_path,
                    'index_stats': {},
                    'is_initialized': False
                }
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
            logger.error(f"Error listing registered files: {e}")
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
                logger.warning(f"No tables found with theme: {theme}")
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
            logger.error(f"Error getting data for theme {theme}: {e}")
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
                logger.warning(f"No tables found with tag: {tag}")
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
            logger.error(f"Error getting data for tag {tag}: {e}")
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
                logger.warning("No tables available")
                return pd.DataFrame()
            
            # Build query to union all tables with date filter
            queries = []
            for table in tables:
                table_name = table["table_name"]
                schema = table["schema"]
                if date_column in schema:
                    queries.append(f"""
                        SELECT *, '{table_name}' as source_table 
                        FROM {table_name}
                        WHERE {date_column} BETWEEN '{start_date}' AND '{end_date}'
                    """)
            
            if not queries:
                logger.warning(f"No tables found with date column: {date_column}")
                return pd.DataFrame()
            
            full_query = f"""
                SELECT * FROM (
                    {" UNION ALL ".join(queries)}
                ) combined_results
                LIMIT {limit}
            """
            
            return self.cold.query(full_query)
            
        except Exception as e:
            logger.error(f"Error getting data for date range: {e}")
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
            logger.error(f"Error getting stats for table {table_name}: {e}")
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
                logger.warning("No tables available")
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
                        logger.warning(f"Error querying table {table_name} with geometry: {e}")
                        
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
                        logger.warning(f"Error querying table {table_name} with lat/lon: {e}")
            
            if results.empty:
                logger.warning(
                    f"No tables found with either geometry column ({geom_column}) "
                    f"or coordinate columns ({lon_column}, {lat_column})"
                )
            
            return results.head(limit) if not results.empty else results
            
        except Exception as e:
            logger.error(f"Error getting data for bounding box: {e}")
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
                logger.warning("No tables available")
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
                logger.warning(
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
                logger.error(f"Error executing combined query: {e}")
                return pd.DataFrame()
            
            if results.empty:
                logger.warning(
                    f"No data found within bounding box containing value '{search_value}'"
                )
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting data for bounding box and value: {e}")
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
                logger.warning("No tables available")
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
                logger.warning("No tables to search")
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
                logger.error(f"Error executing fuzzy search query: {e}")
                return pd.DataFrame()
            
            if results.empty:
                logger.warning(
                    f"No data found matching search term '{search_term}' with "
                    f"similarity threshold {similarity_threshold}"
                )
            
            return results
            
        except Exception as e:
            logger.error(f"Error in fuzzy search: {e}")
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
                logger.warning("No tables available")
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
                        logger.warning(f"Error querying table {table_name}: {e}")
            
            if results.empty:
                logger.warning(f"No tables found with geometry column: {geom_column}")
            
            return results.head(limit) if not results.empty else results
            
        except Exception as e:
            logger.error(f"Error getting data for polygon: {e}")
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

    def get_red_hot_stats(self) -> dict:
        """Get statistics about the data in red-hot storage."""
        try:
            red_hot = RedHotMemory()
            stats = red_hot.get_storage_stats()
            
            logger.info(f"Red-hot storage stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting red-hot stats: {e}")
            return {}

    def get_similar_columns(self, query_word, similarity_threshold=0.5):
        """Find semantically similar columns above the similarity threshold."""
        logger.info(f"\n{'='*80}")
        logger.info("SEMANTIC SEARCH")
        logger.info(f"{'='*80}")
        logger.info(f"Query word: '{query_word}'")
        logger.info(f"Similarity threshold: {similarity_threshold}")
        
        # Initialize components
        red_hot = RedHotMemory()
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create embedding for query
        logger.info("\nCreating query embedding...")
        query_embedding = model.encode([query_word])[0]
        logger.info(f"Embedding shape: {query_embedding.shape}")
        
        # Search in FAISS index - use a larger k initially to filter by threshold
        logger.info("\nSearching FAISS index...")
        k = min(100, red_hot.index.ntotal)  # Search more to filter by threshold
        D, I = red_hot.index.search(query_embedding.reshape(1, -1), k)
        
        # Display similarity results
        logger.info("\nSimilarity Results:")
        logger.info("-" * 40)
        similar_columns = []
        
        for i, (distance, idx) in enumerate(zip(D[0], I[0])):
            similarity = 1 / (1 + float(distance))
            
            # Only process if above threshold
            if similarity >= similarity_threshold:
                metadata = red_hot.get_metadata(str(int(idx)))
                file_name = os.path.basename(metadata.get('file_path', ''))
                column = metadata.get('column_name', '')
                dtype = metadata.get('dtype', 'unknown')
                
                result = {
                    'column': column,
                    'file': file_name,
                    'full_path': metadata.get('file_path', ''),
                    'similarity': similarity,
                    'dtype': dtype
                }
                similar_columns.append(result)
                
                logger.info(f"Match #{len(similar_columns)}:")
                logger.info(f"  Column: {column}")
                logger.info(f"  File: {file_name}")
                logger.info(f"  Type: {dtype}")
                logger.info(f"  Similarity Score: {similarity:.4f}")
                logger.info("-" * 40)
        
        logger.info(f"\nFound {len(similar_columns)} matches above threshold {similarity_threshold}")
        return similar_columns

    def format_spatial_results(self, results):
        """Format spatial query results for display."""
        output = []
        output.append("\nSpatial Query Results:")
        output.append("=" * 100)
        
        # High similarity matches (complete rows)
        if results['high_similarity']:
            output.append("\nHigh Similarity Matches (Complete Rows):")
            output.append("-" * 80)
            for match in results['high_similarity']:
                output.append(f"\nSource: {match['file_path']}")
                output.append(f"Column: {match['column_name']}")
                output.append(f"Similarity Score: {match['similarity']:.4f}")
                output.append("\nSample Rows:")
                for row in match['data'][:5]:  # Show first 5 rows
                    output.append(f"  {row}")
                if len(match['data']) > 5:
                    output.append(f"  ... and {len(match['data'])-5} more rows")
                output.append("-" * 80)
        
        # Partial matches (column values only)
        if results['partial_matches']:
            output.append("\nPartial Matches (Column Values Only):")
            output.append("-" * 80)
            for key, data in results['partial_matches'].items():
                output.append(f"\nSource: {data['file_path']}")
                output.append(f"Column: {data['column_name']}")
                output.append(f"Similarity Score: {data['similarity']:.4f}")
                output.append("\nValues:")
                output.append(", ".join(map(str, data['values'][:10])))
                if len(data['values']) > 10:
                    output.append(f"... and {len(data['values'])-10} more values")
                output.append("-" * 80)
        
        return "\n".join(output)

    def get_spatial_semantic_data(
        self,
        query_word: str,
        bbox: tuple,
        similarity_threshold: float = 0.5
    ) -> pd.DataFrame:
        """
        Search for data that matches semantically and falls within a bounding box.
        """
        logger.info(f"\n{'='*80}")
        logger.info("SPATIAL SEMANTIC SEARCH")
        logger.info(f"{'='*80}")
        logger.info(f"Query word: '{query_word}'")
        logger.info(f"Bounding box: {bbox}")
        
        # First get semantically similar columns
        similar_columns = self.get_similar_columns(query_word, similarity_threshold)
        
        if not similar_columns:
            logger.warning("No similar columns found")
            return pd.DataFrame()
        
        # Deduplicate file paths and group columns
        unique_files = {}
        for match in similar_columns:
            file_path = match['full_path']
            if file_path not in unique_files:
                unique_files[file_path] = {
                    'columns': set(),
                    'geometry_column': None
                }
            unique_files[file_path]['columns'].add(match['column'])
        
        logger.info(f"\nFound {len(unique_files)} unique files to process")
        
        # Process each unique file
        min_lon, min_lat, max_lon, max_lat = bbox
        results = pd.DataFrame()
        
        for file_path, info in unique_files.items():
            try:
                # Get schema info directly from parquet file
                schema_query = f"DESCRIBE SELECT * FROM parquet_scan('{file_path}')"
                schema_df = self.con.execute(schema_query).fetchdf()
                
                # Look for geometry column
                for _, row in schema_df.iterrows():
                    col_name = row['column_name']
                    col_type = str(row['column_type']).lower()
                    if ('geometry' in col_type or 
                        'binary' in col_type or 
                        col_name.lower() in ['geom', 'geometry', 'the_geom']):
                        info['geometry_column'] = col_name
                        info['geometry_type'] = col_type
                        logger.info(f"Found geometry column: {col_name} ({col_type})")
                        break
                
                # Skip if no geometry column found
                if not info['geometry_column']:
                    logger.warning(f"No geometry column found in {file_path}, skipping")
                    continue
                
                # Build and execute spatial query
                columns = list(info['columns'])
                columns.append(info['geometry_column'])
                cols_str = ', '.join(f'"{col}"' for col in columns)
                
                # Adjust query based on geometry type
                geom_expr = f'"{info["geometry_column"]}"'
                if 'binary' in info['geometry_type'].lower():
                    geom_expr = f'ST_GeomFromWKB("{info["geometry_column"]}")'
                
                query = f"""
                SELECT 
                    {cols_str},
                    '{os.path.basename(file_path)}' as source_file
                FROM parquet_scan('{file_path}')
                WHERE ST_Intersects(
                    {geom_expr},
                    ST_GeomFromText('POLYGON(({min_lon} {min_lat}, {min_lon} {max_lat}, 
                    {max_lon} {max_lat}, {max_lon} {min_lat}, {min_lon} {min_lat}))')
                )
                """
                
                logger.info(f"Executing query...")
                logger.debug(f"Query: {query}")
                df = self.con.execute(query).fetchdf()
                logger.info(f"Found {len(df)} results")
                
                if not df.empty:
                    results = pd.concat([results, df], ignore_index=True)
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                continue
        
        logger.info(f"\nTotal results found: {len(results)}")
        return results 