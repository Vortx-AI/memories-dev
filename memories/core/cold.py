import duckdb
import geopandas as gpd
from pathlib import Path
import logging
from typing import Optional, List, Dict, Any, Tuple, Union
import pyarrow as pa
import pyarrow.parquet as pq
from shapely.geometry import shape
import json
import uuid
import yaml
import os
import sys
from dotenv import load_dotenv
import logging
import pkg_resources
import numpy as np
import pandas as pd
from datetime import datetime
import subprocess

# Initialize GPU support flags
HAS_GPU_SUPPORT = False
HAS_CUDF = False
HAS_CUSPATIAL = False

try:
    import cudf
    HAS_CUDF = True
except ImportError:
    logging.warning("cudf not available. GPU acceleration for dataframes will be disabled.")

try:
    import cuspatial
    HAS_CUSPATIAL = True
except ImportError:
    logging.warning("cuspatial not available. GPU acceleration for spatial operations will be disabled.")

if HAS_CUDF and HAS_CUSPATIAL:
    HAS_GPU_SUPPORT = True
    logging.info("GPU support enabled with cudf and cuspatial.")

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

logger = logging.getLogger(__name__)

class ColdMemory:
    """Cold memory implementation using DuckDB and optional GPU acceleration."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize cold memory with configuration."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.instance_id = str(uuid.uuid4())
        
        # Initialize storage
        self.db = self._init_database()
        
    def _init_database(self) -> duckdb.DuckDBPyConnection:
        """Initialize DuckDB database."""
        db_path = self.config.get('db_path', ':memory:')
        return duckdb.connect(db_path)
    
    def store(self, data: Union[pd.DataFrame, 'cudf.DataFrame'], table_name: str) -> None:
        """Store data in cold memory."""
        if HAS_CUDF and isinstance(data, cudf.DataFrame):
            # Convert cudf DataFrame to pandas for storage
            self.logger.debug("Converting cudf DataFrame to pandas for storage")
            data = data.to_pandas()
        elif not isinstance(data, pd.DataFrame):
            raise TypeError("Data must be a pandas DataFrame or cudf DataFrame")

        # Store the data using DuckDB
        self.db.register("temp_data", data)
        self.db.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM temp_data")
        self.db.unregister("temp_data")
        self.logger.debug(f"Successfully stored data in table {table_name}")
    
    def retrieve(self, table_name: str, use_gpu: bool = False) -> Union[pd.DataFrame, 'cudf.DataFrame']:
        """Retrieve data from cold memory.
        
        Args:
            table_name: Name of the table to retrieve data from
            use_gpu: Whether to return data as a GPU DataFrame (if GPU support is available)
            
        Returns:
            DataFrame either as pandas DataFrame or cudf DataFrame based on use_gpu flag
        """
        query = f"SELECT * FROM {table_name}"
        result = self.db.execute(query).fetchdf()
        
        if use_gpu:
            if not HAS_CUDF:
                self.logger.warning("GPU acceleration requested but cudf is not available")
                return result
            try:
                self.logger.debug("Converting pandas DataFrame to cudf")
                return cudf.from_pandas(result)
            except Exception as e:
                self.logger.warning(f"Failed to convert to GPU DataFrame: {e}")
                return result
        return result
    
    def _store_metadata(self, storage_id: str, metadata: Dict[str, Any]):
        """Store metadata for the given storage ID."""
        try:
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    storage_id VARCHAR PRIMARY KEY,
                    metadata JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.db.execute("""
                INSERT INTO metadata (storage_id, metadata)
                VALUES (?, ?)
                ON CONFLICT (storage_id) DO UPDATE SET
                    metadata = excluded.metadata
            """, (storage_id, json.dumps(metadata)))
            
        except Exception as e:
            self.logger.error(f"Error storing metadata: {str(e)}")
            raise
    
    def _retrieve_metadata(self, storage_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve metadata for the given storage ID."""
        try:
            result = self.db.execute("""
                SELECT metadata FROM metadata WHERE storage_id = ?
            """, (storage_id,)).fetchone()
            
            if result:
                return json.loads(result[0])
            return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving metadata: {str(e)}")
            return None
    
    def delete(self, storage_id: str) -> bool:
        """Delete data from cold memory."""
        try:
            # Drop table if exists
            self.db.execute(f"DROP TABLE IF EXISTS {storage_id}")
            
            # Delete metadata
            self.db.execute("""
                DELETE FROM metadata WHERE storage_id = ?
            """, (storage_id,))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting data: {str(e)}")
            return False
    
    def cleanup(self):
        """Clean up resources."""
        if hasattr(self, 'db'):
            self.db.close()

    def __del__(self):
        """Destructor to ensure cleanup is performed."""
        self.cleanup()

# Test code with more verbose output
if __name__ == "__main__":
    try:
        print("Initializing ColdMemory...")
        cold_memory = ColdMemory()
        
        # Test coordinates (Bangalore, India)
        test_lat, test_lon = 12.9095706, 77.6085865
        print(f"\nQuerying point: Latitude {test_lat}, Longitude {test_lon}")
        
        # Basic query with debug info
        print("\n1. Executing basic query...")
        results = cold_memory.query_by_point(
            lat=test_lat,
            lon=test_lon,
            limit=5
        )
        print(f"Query returned {len(results)} results")
        
        if not results.empty:
            print("\nAll columns in results:")
            print("Available columns:", list(results.columns))
            print("\nComplete results:")
            # Set pandas to show all columns and rows without truncation
            pd.set_option('display.max_columns', None)  # Show all columns
            pd.set_option('display.max_rows', None)     # Show all rows
            pd.set_option('display.width', None)        # Don't wrap
            pd.set_option('display.max_colwidth', None) # Don't truncate column content
            print(results)
        else:
            print("\nNo results found. Checking data in the Parquet files...")
            
            # Show sample of available data with all columns
            geo_memories_path = os.getenv('GEO_MEMORIES')
            print("\nSample of available data:")
            sample_query = f"""
                SELECT *
                FROM read_parquet('{geo_memories_path}/*.parquet', union_by_name=True)
                LIMIT 1;
            """
            print(f"Executing sample query: {sample_query}")
            sample_df = cold_memory.conn.execute(sample_query).df()
            print("\nAvailable columns:", list(sample_df.columns))
            print("\nComplete sample row:")
            pd.set_option('display.max_columns', None)
            pd.set_option('display.max_rows', None)
            pd.set_option('display.width', None)
            pd.set_option('display.max_colwidth', None)
            print(sample_df)

    except Exception as e:
        print(f"An error occurred during testing: {str(e)}")
    finally:
        if 'cold_memory' in locals():
            cold_memory.conn.close()
            print("\nClosed DuckDB connection.")
    