import duckdb
import geopandas as gpd
from pathlib import Path
import logging
from typing import Optional, List, Dict, Any, Tuple
import pyarrow as pa
import pyarrow.parquet as pq
from shapely.geometry import shape
import json
import uuid
import yaml
import os
import os
import sys
from dotenv import load_dotenv
import logging
import pkg_resources
import cudf
import cuspatial
import numpy as np
import pandas as pd
from datetime import datetime
import subprocess

# Load environment variables
load_dotenv()

import os
import sys
from dotenv import load_dotenv
import logging


#print(f"Using project root: {project_root}")




class Config:
    def __init__(self, config_path: str = 'config/db_config.yml'):
        """Initialize configuration by loading the YAML file."""
        # Store project root
        self.project_root = self._get_project_root()
        print(f"[Config] Project root: {self.project_root}")

        # Make config_path absolute if it's not already
        if not os.path.isabs(config_path):
            config_path = os.path.join(self.project_root, config_path)
            print(f"[Config] Converted to absolute path: {config_path}")
        else:
            print(f"[Config] Using absolute config path: {config_path}")

        # Load the configuration
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found at: {config_path}")
            
        self.config = self._load_config(config_path)
        print(f"[Config] Loaded configuration successfully")
        #self._discover_modalities()
    
    def _get_project_root(self) -> str:
        """Get the project root directory."""
        # Get the project root from environment variable or compute it
        project_root = os.getenv("PROJECT_ROOT")
        if not project_root:
            # If PROJECT_ROOT is not set, try to find it relative to the current file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        print(f"[Config] Determined project root: {project_root}")
        return project_root
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        print(f"[Config] Loading config from: {config_path}")
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    @property
    def database_path(self) -> str:
        """Get full database path"""
        db_path = os.path.join(
            self.config['database']['path'],
            self.config['database']['name']
        )
        if not os.path.isabs(db_path):
            db_path = os.path.join(self.project_root, db_path)
        return db_path
    
    @property
    def raw_data_path(self) -> Path:
        """Get raw data directory path"""
        data_path = self.config['data']['raw_path']
        if not os.path.isabs(data_path):
            data_path = os.path.join(self.project_root, data_path)
        return Path(data_path)
    
    @property
    def log_path(self) -> str:
        """Get log file path"""
        log_path = 'logs/database.log'
        if not os.path.isabs(log_path):
            log_path = os.path.join(self.project_root, log_path)
        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        return log_path

    def _discover_modalities(self):
        """Discover modalities and their tables from folder structure"""
        self.modality_tables = {}
        raw_path = self.raw_data_path
        
        # Scan through modality folders
        for modality_path in raw_path.iterdir():
            if modality_path.is_dir():
                modality = modality_path.name
                # Get all parquet files in this modality folder
                parquet_files = [
                    f.stem for f in modality_path.glob('*.parquet')
                ]
                if parquet_files:
                    self.modality_tables[modality] = parquet_files
                    
        self.config['modalities'] = self.modality_tables

    def get_modality_path(self, modality: str) -> Path:
        """Get path for a specific modality"""
        return self.raw_data_path / modality

class ColdStorage:
    def __init__(self, config_path: str = None):
        """
        Initialize Cold Storage with DuckDB and GeoParquet support.
        
        Args:
            config_path (str): Path to configuration file
        """
        print(f"ColdStorage init with config_path: {config_path}")  # Debug print
        
        # Get the project root directory
        #project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        load_dotenv()

        # Add the project root to Python path if needed
        project_root = os.getenv("PROJECT_ROOT")
        if not project_root:
            # If PROJECT_ROOT is not set, try to find it relative to the notebook
            project_root = os.path.abspath(os.path.join(os.getcwd(), '..', '..'))

        # If config_path is not provided, use default path relative to project root
        #if config_path is None:
        config_path = os.path.join(project_root, 'config', 'db_config.yml')
            
        print(f"Using config path: {config_path}")  # Debug print
        
        self.config = Config(config_path)
        self._setup_logging()
        self.conn = self._initialize_db()
        self._init_gpu_connection()  # Enable GPU acceleration on startup
        #self.modality_tables = self._discover_modalities()

    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            filename=self.config.log_path,
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _initialize_db(self) -> duckdb.DuckDBPyConnection:
        """Initialize DuckDB connection and required extensions."""
        conn = duckdb.connect(self.config.database_path)
        conn.execute("INSTALL spatial;")
        conn.execute("LOAD spatial;")
        return conn

    def _init_gpu_connection(self):
        """Initialize GPU-enabled DuckDB connection"""
        try:
            # Enable GPU acceleration
            self.conn.execute("INSTALL 'spatial'")
            self.conn.execute("LOAD 'spatial'")
            self.conn.execute("SET enable_gpu=true")
            self.conn.execute("SET gpu_device_id=0")  # Use first available GPU
        except Exception as e:
            self.logger.warning(f"Could not enable GPU acceleration: {e}")

    def _initialize_tables(self):
        """Create tables for each modality if they do not exist."""
        for modality, tables in self.modality_tables.items():
            for table in tables:
                self.conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table} (
                        id VARCHAR PRIMARY KEY,
                        data BLOB,
                        metadata JSON,
                        geometry JSON,
                        timestamp TIMESTAMP,
                        tags VARCHAR[]
                    )
                """)
                self.logger.info(f"Ensured table '{table}' exists for modality '{modality}'.")

    def get_tables_by_modality(self, modality: str) -> List[str]:
        """
        Get list of tables associated with a modality.
        
        Args:
            modality (str): The modality name
            
        Returns:
            List[str]: List of table names
        """
        return self.modality_tables.get(modality, [])

    def get_columns(self, modality: str, table: str) -> List[str]:
        """
        Retrieve column names for a specific table under a modality.
        
        Args:
            modality (str): The modality name
            table (str): The table name
            
        Returns:
            List[str]: List of column names
        """
        if table not in self.modality_tables.get(modality, []):
            self.logger.error(f"Table '{table}' does not exist under modality '{modality}'.")
            return []
        
        try:
            # Ensure connection is open
            if not self.conn:
                self.conn = self._initialize_db()
                
            result = self.conn.execute(f"PRAGMA table_info({table});").fetchall()
            columns = [row[1] for row in result]  # row[1] is the column name
            self.logger.info(f"Columns for table '{table}' under modality '{modality}': {columns}")
            return columns
        except Exception as e:
            self.logger.error(f"Error getting columns for table '{table}': {str(e)}")
            return []

    def create(
        self, 
        modality: str,
        table: str,
        gdf: gpd.GeoDataFrame, 
        metadata: Dict[str, Any] = None, 
        tags: List[str] = None
    ) -> Optional[str]:
        """
        Create a new entry in cold storage.
        
        Args:
            modality (str): The modality name
            table (str): The table name under the modality
            gdf (gpd.GeoDataFrame): GeoDataFrame to store
            metadata (Dict[str, Any], optional): Metadata dictionary
            tags (List[str], optional): List of tags
        
        Returns:
            Optional[str]: ID of the created entry
        """
        if table not in self.modality_tables.get(modality, []):
            self.logger.error(f"Table '{table}' does not exist under modality '{modality}'.")
            return None
        
        try:
            entry_id = str(uuid.uuid4())
            parquet_bytes = self._gdf_to_parquet_bytes(gdf)
            geometry_json = gdf.geometry.to_json()
            
            # Insert into DuckDB
            self.conn.execute(f"""
                INSERT INTO {table} (id, data, metadata, geometry, timestamp, tags) 
                VALUES (?, ?, ?, ?, now(), ?)
            """, (entry_id, parquet_bytes, json.dumps(metadata) if metadata else json.dumps({}), geometry_json, tags))
            
            self.logger.info(f"Inserted entry with ID '{entry_id}' into table '{table}' under modality '{modality}'.")
            return entry_id
        except Exception as e:
            self.logger.error(f"Error inserting entry into table '{table}': {str(e)}")
            return None

    def read(self, modality: str, table: str, entry_id: str) -> Optional[gpd.GeoDataFrame]:
        """
        Read an entry from cold storage.
        
        Args:
            modality (str): The modality name
            table (str): The table name under the modality
            entry_id (str): The ID of the entry
        
        Returns:
            Optional[gpd.GeoDataFrame]: Retrieved GeoDataFrame or None
        """
        if table not in self.modality_tables.get(modality, []):
            self.logger.error(f"Table '{table}' does not exist under modality '{modality}'.")
            return None
        
        try:
            result = self.conn.execute(f"""
                SELECT data FROM {table} WHERE id = ?
            """, (entry_id,)).fetchone()
            
            if result:
                parquet_bytes = result[0]
                gdf = self._parquet_bytes_to_gdf(parquet_bytes)
                self.logger.info(f"Retrieved entry with ID '{entry_id}' from table '{table}' under modality '{modality}'.")
                return gdf
            else:
                self.logger.warning(f"No entry found with ID '{entry_id}' in table '{table}' under modality '{modality}'.")
                return None
        except Exception as e:
            self.logger.error(f"Error reading entry from table '{table}': {str(e)}")
            return None

    def update(
        self, 
        modality: str,
        table: str,
        entry_id: str,
        gdf: Optional[gpd.GeoDataFrame] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        Update an existing entry in cold storage.
        
        Args:
            modality (str): The modality name
            table (str): The table name under the modality
            entry_id (str): The ID of the entry
            gdf (Optional[gpd.GeoDataFrame], optional): Updated GeoDataFrame
            metadata (Optional[Dict[str, Any]], optional): Updated metadata
            tags (Optional[List[str]], optional): Updated tags
        
        Returns:
            bool: True if update succeeded, False otherwise
        """
        if table not in self.modality_tables.get(modality, []):
            self.logger.error(f"Table '{table}' does not exist under modality '{modality}'.")
            return False
        
        try:
            updates = []
            params = []
            
            if gdf is not None:
                parquet_bytes = self._gdf_to_parquet_bytes(gdf)
                geometry_json = gdf.geometry.to_json()
                updates.append("data = ?")
                updates.append("geometry = ?")
                params.extend([parquet_bytes, geometry_json])
            
            if metadata is not None:
                updates.append("metadata = ?")
                params.append(json.dumps(metadata))
            
            if tags is not None:
                updates.append("tags = ?")
                params.append(tags)
            
            if not updates:
                self.logger.warning("No updates provided.")
                return False
            
            update_query = f"UPDATE {table} SET {', '.join(updates)} WHERE id = ?"
            params.append(entry_id)
            
            self.conn.execute(update_query, params)
            self.logger.info(f"Updated entry with ID '{entry_id}' in table '{table}' under modality '{modality}'.")
            return True
        except Exception as e:
            self.logger.error(f"Error updating entry in table '{table}': {str(e)}")
            return False

    def delete(self, modality: str, table: str, entry_id: str) -> bool:
        """
        Delete an entry from cold storage.
        
        Args:
            modality (str): The modality name
            table (str): The table name under the modality
            entry_id (str): The ID of the entry
        
        Returns:
            bool: True if deletion succeeded, False otherwise
        """
        if table not in self.modality_tables.get(modality, []):
            self.logger.error(f"Table '{table}' does not exist under modality '{modality}'.")
            return False
        
        try:
            self.conn.execute(f"""
                DELETE FROM {table} WHERE id = ?
            """, (entry_id,))
            self.logger.info(f"Deleted entry with ID '{entry_id}' from table '{table}' under modality '{modality}'.")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting entry from table '{table}': {str(e)}")
            return False

    def search(
        self,
        modality: str,
        table: str,
        tags: Optional[List[str]] = None,
        bbox: Optional[List[float]] = None,
        columns: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[gpd.GeoDataFrame]:
        """
        Search entries by tags, bounding box, and specific columns.
        
        Args:
            modality (str): The modality name
            table (str): The table name under the modality
            tags (list, optional): Tags to search for
            bbox (list, optional): Bounding box [minx, miny, maxx, maxy]
            columns (list, optional): Specific columns to retrieve
            limit (int): Maximum number of results
            
        Returns:
            list: List of matching GeoDataFrames
        """
        if table not in self.modality_tables.get(modality, []):
            self.logger.error(f"Table '{table}' does not exist under modality '{modality}'.")
            return []
        
        try:
            select_columns = ", ".join(columns) if columns else "id, data, geometry, timestamp, metadata, tags"
            query = f"SELECT {select_columns} FROM {table} WHERE 1=1"
            params = []
            
            if tags:
                query += " AND tags && ?"
                params.append(tags)
                
            if bbox:
                query += """ 
                    AND ST_Intersects(
                        ST_GeomFromGeoJSON(geometry),
                        ST_MakeEnvelope(?, ?, ?, ?)
                    )
                """
                params.extend(bbox)
                
            if limit:
                query += f" LIMIT {limit}"
            
            results = self.conn.execute(query, params).fetchall()
            
            geo_dfs = []
            for row in results:
                if isinstance(row, tuple):
                    data = row[1] if len(row) > 1 else None
                else:
                    data = row
                if data:
                    gdf = self._parquet_bytes_to_gdf(data)
                    geo_dfs.append(gdf)
            
            self.logger.info(f"Found {len(geo_dfs)} entries in table '{table}' under modality '{modality}'.")
            return geo_dfs
                
        except Exception as e:
            self.logger.error(f"Error searching entries in table '{table}': {str(e)}")
            return []

    def list_modality_tables(self, modality: str) -> List[str]:
        """
        List all tables under a specific modality.
        
        Args:
            modality (str): The modality name
        
        Returns:
            List[str]: List of table names
        """
        tables = self.modality_tables.get(modality, [])
        self.logger.info(f"Tables under modality '{modality}': {tables}")
        return tables

    def list_columns(self, modality: str, table: str) -> List[str]:
        """
        List all columns in a specific table under a modality.
        
        Args:
            modality (str): The modality name
            table (str): The table name
            
        Returns:
            List[str]: List of column names
        """
        return self.get_columns(modality, table)

    def _gdf_to_parquet_bytes(self, gdf: gpd.GeoDataFrame) -> bytes:
        """Convert GeoDataFrame to Parquet bytes."""
        buffer = pa.BufferOutputStream()
        gdf.to_parquet(buffer)
        return buffer.getvalue().to_pybytes()

    def _parquet_bytes_to_gdf(self, parquet_bytes: bytes) -> gpd.GeoDataFrame:
        """Convert Parquet bytes back to GeoDataFrame."""
        table = pq.read_table(pa.BufferReader(parquet_bytes))
        return gpd.GeoDataFrame.from_arrow(table)
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.logger.info("Closed DuckDB connection.")

    def __enter__(self):
        if not self.conn:
            self.conn = self._initialize_db()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def load_parquet_file(self, modality: str, table: str) -> bool:
        """
        Load a parquet file into its corresponding table.
        
        Args:
            modality (str): The modality name
            table (str): The table name (without .parquet extension)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            file_path = self.config.get_modality_path(modality) / f"{table}.parquet"
            if not file_path.exists():
                self.logger.error(f"Parquet file not found: {file_path}")
                return False
                
            # Read and store the parquet file
            gdf = gpd.read_parquet(file_path)
            entry_id = self.create(modality, table, gdf)
            
            self.logger.info(f"Loaded parquet file {file_path} into {modality}/{table}")
            return entry_id is not None
            
        except Exception as e:
            self.logger.error(f"Error loading parquet file: {str(e)}")
            return False
            
    def load_all_parquet_files(self):
        """Load all parquet files from all modality folders"""
        for modality, tables in self.modality_tables.items():
            for table in tables:
                self.load_parquet_file(modality, table)

    def _discover_modalities(self) -> Dict[str, List[str]]:
        """Discover modalities and their tables from folder structure in data/raw."""
        modalities = {}
        raw_path = os.path.join(self.config.project_root, 'data', 'raw')
        print(f"[ColdStorage] Discovering modalities in: {raw_path}")

        try:
            # Iterate through directories in data/raw
            for modality in os.listdir(raw_path):
                modality_path = os.path.join(raw_path, modality)
                if os.path.isdir(modality_path):
                    print(f"[ColdStorage] Found modality directory: {modality}")
                    # Get all parquet files in this modality folder
                    parquet_files = [
                        f.replace('.parquet', '') for f in os.listdir(modality_path)
                        if f.endswith('.parquet')
                    ]
                    if parquet_files:
                        modalities[modality] = parquet_files
                        print(f"[ColdStorage] Found tables for {modality}: {parquet_files}")

            print(f"[ColdStorage] Discovered modalities: {modalities}")
            return modalities
        except Exception as e:
            print(f"[ColdStorage] Error discovering modalities: {str(e)}")
            return {}

    def get_schema_for_modalities(self, modalities: List[str]) -> Dict[str, Dict[str, List[str]]]:
        """Get schema information for specified modalities."""
        schemas = {}
        print(f"[ColdStorage] Getting schemas for modalities: {modalities}")

        # Discover available modalities if not already done
        if not hasattr(self, 'modality_tables'):
            self.modality_tables = self._discover_modalities()

        for modality in modalities:
            if modality in self.modality_tables:
                schemas[modality] = {}
                print(f"[ColdStorage] Processing modality: {modality}")
                
                for table in self.modality_tables[modality]:
                    try:
                        # Read parquet file to get schema
                        parquet_path = os.path.join(
                            self.config.project_root, 
                            'data', 'raw', 
                            modality, 
                            f"{table}.geoparquet"
                        )
                        print(f"[ColdStorage] Reading schema from: {parquet_path}")
                        
                        import pyarrow.parquet as pq
                        parquet_schema = pq.read_schema(parquet_path)
                        columns = [field.name for field in parquet_schema]
                        
                        schemas[modality][table] = columns
                        print(f"[ColdStorage] Found columns for {modality}.{table}: {columns}")
                    except Exception as e:
                        print(f"[ColdStorage] Error reading schema for {modality}.{table}: {str(e)}")
                        schemas[modality][table] = []

        return schemas

    def query_landuse_at_point(self, lat: float, lon: float, landuse_types: List[str] = None) -> gpd.GeoDataFrame:
        """
        Query landuse exactly at a specific point.
        
        Args:
            lat (float): Latitude of the point.
            lon (float): Longitude of the point.
            landuse_types (List[str], optional): List of landuse types to filter by.
            
        Returns:
            gpd.GeoDataFrame: GeoDataFrame containing matching landuse features.
        """
        try:
            file_path = os.path.join(self.config.raw_data_path, 'landuse', 'india_landuse.geoparquet')
            # Load the GeoParquet data
            self.conn.sql(f"CREATE OR REPLACE TABLE india_landuse AS SELECT * FROM read_parquet('{file_path}');")
            
            query = f"""
                SELECT *
                FROM india_landuse
                WHERE ST_Contains(
                    geometry,
                    ST_Point({lon}, {lat})
                )
            """
            if landuse_types:
                landuse_list = "', '".join(landuse_types)
                query += f" AND landuse IN ('{landuse_list}')"
            query += ";"
    
            result = self.conn.sql(query).df()
            return gpd.GeoDataFrame(result, geometry='geometry')
            
        except Exception as e:
            self.logger.error(f"Error querying landuse at point: {str(e)}")
            return gpd.GeoDataFrame()

    def add_columns_to_faiss(self, new_columns: List[Dict], update_existing: bool = False):
        """
        Add new columns to FAISS index
        
        Args:
            new_columns (List[Dict]): List of column dictionaries with format:
                {
                    'source': str,
                    'table': str,
                    'file_path': str,
                    'column_name': str,
                    'column_type': str,
                    'samples': List[str],
                    'unique_values': int (optional),
                    'null_count': int (optional),
                    'record_count': int
                }
            update_existing (bool): If True, update existing columns if found
            
        Returns:
            bool: Success status
        """
        try:
            # Load existing index and metadata
            index = faiss.read_index('schema_index.faiss')
            with open('schema_metadata.json', 'r') as f:
                metadata = json.load(f)
            
            # Track new entries
            new_texts = []
            new_metadata = []
            
            for col in new_columns:
                # Create description text
                description = f"Column '{col['column_name']}' of type {col['column_type']}"
                if 'samples' in col:
                    sample_str = ', '.join(str(s) for s in col['samples'][:3])
                    description += f" with sample values: {sample_str}"
                
                # Check if column already exists
                exists = False
                if update_existing:
                    for idx, meta in enumerate(metadata):
                        if (meta['source'] == col['source'] and 
                            meta['table'] == col['table'] and 
                            meta['column_name'] == col['column_name']):
                            metadata[idx] = col
                            exists = True
                            self.logger.info(f"Updated existing column: {col['source']}/{col['table']}/{col['column_name']}")
                            break
                
                if not exists:
                    new_texts.append(description)
                    new_metadata.append(col)
            
            if new_texts:
                # Create embeddings for new texts
                embeddings = self.model.encode(new_texts)
                
                # Normalize embeddings
                faiss.normalize_L2(embeddings)
                
                # Add to index
                index.add(embeddings.astype('float32'))
                
                # Update metadata
                metadata.extend(new_metadata)
                
                # Save updated index and metadata
                faiss.write_index(index, 'schema_index.faiss')
                with open('schema_metadata.json', 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                self.logger.info(f"Added {len(new_texts)} new columns to index")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding columns to FAISS: {str(e)}")
            return False

    def add_table_to_faiss(self, source: str, table: str, file_path: str, columns: List[Dict]):
        """
        Add a complete table's columns to FAISS
        
        Args:
            source (str): Data source name
            table (str): Table name
            file_path (str): Path to the table file
            columns (List[Dict]): List of column information dictionaries with format:
                {
                    'name': str,
                    'type': str,
                    'samples': List[str],
                    'unique_values': int (optional),
                    'null_count': int (optional)
                }
        
        Returns:
            bool: Success status
        """
        try:
            # Format columns for FAISS
            faiss_columns = []
            for col in columns:
                faiss_col = {
                    'source': source,
                    'table': table,
                    'file_path': file_path,
                    'column_name': col['name'],
                    'column_type': col['type'],
                    'record_count': col.get('record_count', 0)
                }
                
                if 'samples' in col:
                    faiss_col['samples'] = col['samples']
                if 'unique_values' in col:
                    faiss_col['unique_values'] = col['unique_values']
                if 'null_count' in col:
                    faiss_col['null_count'] = col['null_count']
                
                faiss_columns.append(faiss_col)
            
            # Add to FAISS
            return self.add_columns_to_faiss(faiss_columns)
            
        except Exception as e:
            self.logger.error(f"Error adding table to FAISS: {str(e)}")
            return False

    def update_columns_in_faiss(self, updated_columns: List[Dict]):
        """
        Update existing columns in FAISS
        
        Args:
            updated_columns (List[Dict]): List of column dictionaries with format:
                {
                    'source': str,
                    'table': str,
                    'file_path': str,
                    'column_name': str,
                    'column_type': str,
                    'samples': List[str],
                    'record_count': int
                }
        
        Returns:
            bool: Success status
        """
        try:
            # Load existing index and metadata
            index = faiss.read_index('schema_index.faiss')
            with open('schema_metadata.json', 'r') as f:
                metadata = json.load(f)
            
            # Track updated entries
            updated_texts = []
            updated_metadata = []
            
            for col in updated_columns:
                # Check if column already exists
                exists = False
                for idx, meta in enumerate(metadata):
                    if (meta['source'] == col['source'] and 
                        meta['table'] == col['table'] and 
                        meta['column_name'] == col['column_name']):
                        metadata[idx] = col
                        exists = True
                        self.logger.info(f"Updated existing column: {col['source']}/{col['table']}/{col['column_name']}")
                        break
                
                if not exists:
                    updated_texts.append(f"Column '{col['column_name']}' of type {col['column_type']}")
                    updated_metadata.append(col)
            
            if updated_texts:
                # Create embeddings for updated texts
                embeddings = self.model.encode(updated_texts)
                
                # Normalize embeddings
                faiss.normalize_L2(embeddings)
                
                # Update index
                index.update(embeddings.astype('float32'))
                
                # Update metadata
                metadata.extend(updated_metadata)
                
                # Save updated index and metadata
                faiss.write_index(index, 'schema_index.faiss')
                with open('schema_metadata.json', 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                self.logger.info(f"Updated {len(updated_texts)} columns in index")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating columns in FAISS: {str(e)}")
            return False

    def query_by_point(
        self, 
        lat: float, 
        lon: float,
        geometry_types: List[str] = None,
        columns: List[str] = None,
        limit: int = None
    ) -> pd.DataFrame:
        """
        Query all geometries that either match or contain the given point.
        
        Args:
            lat (float): Latitude of the point
            lon (float): Longitude of the point
            geometry_types (List[str], optional): List of geometry types to filter by (e.g., ['Point', 'Polygon'])
            columns (List[str], optional): List of columns to return. If None, returns all columns.
            limit (int, optional): Maximum number of results to return
            
        Returns:
            pd.DataFrame: DataFrame containing all matching geometries
        """
        try:
            # Get the GEO_MEMORIES path from environment variables
            geo_memories_path = os.getenv('GEO_MEMORIES')
            if not geo_memories_path:
                raise ValueError("GEO_MEMORIES path is not set in the .env file.")

            # Prepare column selection
            select_cols = '*' if not columns else ', '.join(columns)
            
            # Create or replace the view combining all Parquet files
            self.conn.execute(f"""
                CREATE OR REPLACE VIEW combined_data AS
                SELECT *
                FROM read_parquet('{geo_memories_path}/*.parquet', union_by_name=True)
            """)
            
            # Build the spatial query
            point_query = f"""
            WITH point_geom AS (
                SELECT ST_Point({lon}, {lat}) as point
            )
            SELECT {select_cols}
            FROM combined_data
            WHERE (
                -- Check if the geometry contains the point
                ST_Contains(ST_GeomFromWKB(geom), (SELECT point FROM point_geom))
                OR
                -- Check if the geometry is the point itself
                ST_Equals(ST_GeomFromWKB(geom), (SELECT point FROM point_geom))
            )
            """
            
            # Add geometry type filter if specified
            if geometry_types:
                geometry_types_str = "', '".join(geometry_types)
                point_query += f"""
                AND ST_GeometryType(ST_GeomFromWKB(geom)) IN ('ST_{geometry_types_str}')
                """
                
            # Add limit if specified
            if limit:
                point_query += f"\nLIMIT {limit}"
                
            point_query += ";"
            
            result = self.conn.execute(point_query).df()
            
            if len(result) > 0:
                self.logger.info(f"Found {len(result)} geometries at/containing point ({lat}, {lon})")
            else:
                self.logger.info(f"No geometries found at/containing point ({lat}, {lon})")
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error querying geometries by point: {str(e)}")
            return pd.DataFrame()

# Add this at the bottom of the file
if __name__ == "__main__":
    try:
        # Initialize ColdStorage
        print("Initializing ColdStorage...")
        cold_storage = ColdStorage()

        # Test coordinates (Bangalore, India)
        test_lat, test_lon = 12.9716, 77.5946
        print(f"\nQuerying point: Latitude {test_lat}, Longitude {test_lon}")

        # Test different query scenarios
        print("\n1. Basic query (first 5 results):")
        results = cold_storage.query_by_point(
            lat=test_lat,
            lon=test_lon,
            limit=5
        )
        print(f"Found {len(results)} results")
        if not results.empty:
            print("\nSample results:")
            print(results[['osm_id', 'name', 'type']].head() if 'name' in results.columns else results.head())

        print("\n2. Query only Polygons (first 3 results):")
        polygon_results = cold_storage.query_by_point(
            lat=test_lat,
            lon=test_lon,
            geometry_types=['Polygon'],
            limit=3
        )
        print(f"Found {len(polygon_results)} polygon results")
        if not polygon_results.empty:
            print("\nSample polygon results:")
            print(polygon_results[['osm_id', 'name', 'type']].head() if 'name' in polygon_results.columns else polygon_results.head())

        print("\n3. Query with specific columns:")
        column_results = cold_storage.query_by_point(
            lat=test_lat,
            lon=test_lon,
            columns=['osm_id', 'name', 'type', 'geom'],
            limit=2
        )
        print(f"Found {len(column_results)} results with specific columns")
        if not column_results.empty:
            print("\nSample results with specific columns:")
            print(column_results[['osm_id', 'name', 'type']].head() if 'name' in column_results.columns else column_results.head())

    except Exception as e:
        print(f"An error occurred during testing: {str(e)}")
    finally:
        # Close the connection
        if 'cold_storage' in locals():
            cold_storage.conn.close()
            print("\nClosed DuckDB connection.")
    