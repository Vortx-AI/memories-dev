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
import gzip
import shutil

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
    def __init__(self, config_path: str = None):
        """Initialize configuration by loading the YAML file."""
        # Try to find configuration in standard locations if not provided
        if not config_path:
            standard_paths = [
                os.path.join(os.getcwd(), 'config', 'default_config.yml'),
                os.path.join(os.path.dirname(__file__), '..', 'glacier', 'default_config.yml'),
                os.path.join(os.getcwd(), 'config', 'db_config.yml')
            ]
            
            for path in standard_paths:
                if os.path.exists(path):
                    config_path = path
                    break
        
        # Load configuration
        try:
            if config_path and os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    self.config = yaml.safe_load(f)
            else:
                # Use default configuration
                self.config = self._get_default_config()
                
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self.config = self._get_default_config()
        
        # Store project root
        self.project_root = self._get_project_root()
        print(f"[Config] Project root: {self.project_root}")

        # Set default storage path if not specified
        if 'storage' not in self.config:
            self.config['storage'] = {}
        if 'path' not in self.config['storage']:
            self.config['storage']['path'] = os.path.join(self.project_root, 'data')
            os.makedirs(self.config['storage']['path'], exist_ok=True)
            print(f"[Config] Using default storage path: {self.config['storage']['path']}")
    
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
        try:
            data_path = self.config['data']['raw_path']
        except KeyError:
            # If raw_path is not defined, use a default path
            data_path = os.path.join(self.project_root, 'data/raw')
            self.logger.warning(f"raw_path not found in configuration. Using default: {data_path}")
            
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
    """Cold memory layer using DuckDB for persistent storage."""
    
    def __init__(self, config_path: str = None):
        """Initialize cold memory storage.
        
        Args:
            config_path: Optional path to configuration file. If not provided,
                        will look for default_config.yml in standard locations.
        """
        self.logger = logging.getLogger(__name__)
        
        # Set project root
        self.project_root = os.getenv("PROJECT_ROOT") or os.path.abspath(os.getcwd())
        
        # Try to find configuration in standard locations if not provided
        if not config_path:
            standard_paths = [
                os.path.join(os.getcwd(), 'config', 'default_config.yml'),
                os.path.join(os.path.dirname(__file__), '..', 'glacier', 'default_config.yml'),
                os.path.join(os.getcwd(), 'config', 'db_config.yml')
            ]
            
            for path in standard_paths:
                if os.path.exists(path):
                    config_path = path
                    break
        
        # Load configuration
        try:
            if config_path and os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    self.config = yaml.safe_load(f)
            else:
                # Use default configuration
                self.config = self._get_default_config()
                
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            self.config = self._get_default_config()
        
        # Initialize components
        self._init_storage()
        self._initialize_schema()
        
    def _get_default_config(self) -> dict:
        """Get default configuration."""
        return {
            'storage': {
                'path': os.path.join(self.project_root, 'data', 'cold'),
                'format': 'parquet',
                'raw_data_path': os.path.join(self.project_root, 'data', 'raw')
            },
            'memory': {
                'cold_size': 1000,
                'vector_dim': 384
            }
        }

    def _init_storage(self):
        """Initialize storage components."""
        # Lazy import to avoid circular dependency
        from memories.core.memory_catalog import memory_catalog
        
        # Set up database path
        storage_config = self.config.get('storage', {})
        storage_path = storage_config.get('path', os.path.join(self.project_root, 'data', 'cold'))
        self.db_path = os.path.join(storage_path, 'cold_memory.duckdb')
        
        # Set up raw data path
        self.raw_data_path = storage_config.get('raw_data_path', os.path.join(self.project_root, 'data', 'raw'))
        
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(self.raw_data_path, exist_ok=True)
        
        # Initialize DuckDB connection
        self.conn = duckdb.connect(self.db_path)
        self.memory_catalog = memory_catalog

    def _initialize_schema(self):
        """Initialize database schema."""
        try:
            # Create data table if it doesn't exist
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS cold_data (
                    id VARCHAR PRIMARY KEY,
                    data JSON
                )
            """)
            
            self.logger.info("Initialized cold storage schema")
        except Exception as e:
            self.logger.error(f"Failed to initialize database schema: {e}")
            raise

    async def register_external_file(self, file_path: str) -> None:
        """Register an external file in the cold storage metadata."""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Get file metadata
            file_stats = file_path.stat()
            file_type = file_path.suffix.lstrip('.')

            # Register in memory catalog
            await self.memory_catalog.register_data(
                tier="cold",
                location=str(file_path),
                size=file_stats.st_size,
                data_type=file_type,
                metadata={
                    "is_external": True,
                    "file_path": str(file_path)
                }
            )

            self.logger.info(f"Registered external file: {file_path}")

        except Exception as e:
            self.logger.error(f"Error registering external file: {e}")
            raise

    async def store(
        self,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Store data in cold storage.
        
        Args:
            data: Data to store (DataFrame or dictionary)
            metadata: Optional metadata about the data
            tags: Optional tags for categorizing the data
            
        Returns:
            bool: True if storage was successful, False otherwise
        """
        try:
            # Convert data to DataFrame if needed
            if isinstance(data, dict):
                df = pd.DataFrame.from_dict(data)
            elif isinstance(data, pd.DataFrame):
                df = data
            else:
                logger.error("Data must be a dictionary or DataFrame for cold storage")
                return False

            # Generate unique ID
            data_id = await self.memory_catalog.register_data(
                tier="cold",
                location=f"cold_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                size=df.memory_usage(deep=True).sum(),
                data_type="dataframe",
                tags=tags,
                metadata=metadata
            )

            # Store data in DuckDB
            self.conn.execute(
                "INSERT INTO cold_data (id, data) VALUES (?, ?)",
                [data_id, df.to_json()]
            )

            return True

        except Exception as e:
            logger.error(f"Error storing in cold storage: {e}")
            return False

    async def retrieve(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Retrieve data from cold storage."""
        try:
            # Get data info from catalog
            data_info = await self.memory_catalog.get_data_info(query.get('data_id'))
            if not data_info:
                return None

            # Get data from cold storage
            result = self.conn.execute("""
                SELECT data FROM cold_data
                WHERE id = ?
                LIMIT 1
            """, [data_info['data_id']]).fetchone()
            
            if result:
                data = pd.read_json(result[0])
                return {
                    "data": data,
                    "metadata": json.loads(data_info['additional_meta'])
                }
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve data: {e}")
            return None

    async def clear(self) -> None:
        """Clear all data from cold storage."""
        try:
            # Get all cold tier data from catalog
            cold_data = await self.memory_catalog.get_tier_data("cold")
            
            # Clear data table
            self.conn.execute("DELETE FROM cold_data")
            
            # Remove files if they exist
            for item in cold_data:
                if json.loads(item['additional_meta']).get('is_external', False):
                    file_path = Path(item['location'])
                    if file_path.exists():
                        file_path.unlink()
                        
            logger.info("Cleared all cold storage data")
        except Exception as e:
            logger.error(f"Failed to clear cold storage: {e}")

    async def unregister_file(self, file_id: str) -> bool:
        """Unregister a specific file from cold storage.
        
        Args:
            file_id: ID of the file to unregister
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get file info from catalog
            file_info = await self.memory_catalog.get_data_info(file_id)
            if not file_info:
                return False
                
            # Remove data if exists
            self.conn.execute("DELETE FROM cold_data WHERE id = ?", [file_id])
            
            # Remove file if it's external
            if json.loads(file_info['additional_meta']).get('is_external', False):
                file_path = Path(file_info['location'])
                if file_path.exists():
                    file_path.unlink()
            
            logger.info(f"Successfully unregistered file: {file_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to unregister file {file_id}: {e}")
            return False

    async def list_registered_files(self) -> List[Dict]:
        """List all registered files and their metadata."""
        try:
            # Get all cold tier data from catalog
            cold_data = await self.memory_catalog.get_tier_data("cold")
            
            # Filter and format results
            files = []
            for item in cold_data:
                meta = json.loads(item['additional_meta'])
                if meta.get('is_external', False):
                    files.append({
                        'id': item['data_id'],
                        'timestamp': item['created_at'],
                        'size': item['size'],
                        'file_path': meta.get('file_path'),
                        'data_type': item['data_type'],
                        **meta
                    })
            
            return files
            
        except Exception as e:
            self.logger.error(f"Failed to list registered files: {e}")
            return []

    def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
                self.logger.info("Closed DuckDB connection")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def __del__(self):
        """Ensure cleanup is called when object is destroyed."""
        self.cleanup()

    async def get_all_schemas(self):
        """Get all file paths from cold storage metadata and extract their schemas."""
        try:
            # Get all cold tier data from catalog
            cold_data = await self.memory_catalog.get_tier_data("cold")
            
            # Extract schema for each file
            schemas = []
            for item in cold_data:
                meta = json.loads(item['additional_meta'])
                if meta.get('is_external', False):
                    file_path = item['location']
                    try:
                        # Use DuckDB to get schema information
                        schema_query = f"""
                        DESCRIBE SELECT * FROM parquet_scan('{file_path}')
                        """
                        schema_df = self.conn.execute(schema_query).fetchdf()
                        
                        schema = {
                            'file_path': file_path,
                            'columns': list(schema_df['column_name']),
                            'dtypes': dict(zip(schema_df['column_name'], schema_df['column_type'])),
                            'type': 'schema'
                        }
                        schemas.append(schema)
                        logger.debug(f"Extracted schema from {file_path}")
                        
                    except Exception as e:
                        logger.error(f"Error extracting schema from {file_path}: {e}")
                        continue
            
            logger.info(f"Extracted schemas from {len(schemas)} files")
            return schemas
            
        except Exception as e:
            logger.error(f"Error getting file paths from cold storage: {e}")
            return []

    async def get_schema(self, data_id: str) -> Optional[Dict[str, Any]]:
        """Get schema information for stored data.
        
        Args:
            data_id: ID of the data to get schema for
            
        Returns:
            Dictionary containing:
                - columns: List of column names
                - dtypes: Dictionary mapping column names to their data types
                - type: Type of schema (e.g., 'table', 'file', 'dataframe')
                - source: Source of the schema (e.g., 'duckdb', 'parquet', 'json')
            Returns None if data not found or schema cannot be determined
        """
        try:
            # Get data from cold storage
            result = self.conn.execute("""
                SELECT data FROM cold_data
                WHERE id = ?
                LIMIT 1
            """, [data_id]).fetchone()
            
            if not result:
                return None
                
            # Convert JSON to DataFrame
            df = pd.read_json(result[0])
            
            schema = {
                'columns': list(df.columns),
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
                'type': 'dataframe',
                'source': 'duckdb'
            }
            
            return schema
            
        except Exception as e:
            self.logger.error(f"Failed to get schema for {data_id}: {e}")
            return None



