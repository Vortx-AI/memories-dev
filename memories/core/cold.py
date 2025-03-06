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
    def __init__(self, config_path: str = 'config/db_config.yml'):
        """Initialize configuration by loading the YAML file."""
        # Store project root
        self.project_root = self._get_project_root()
        print(f"[Config] Project root: {self.project_root}")

        # Make config_path absolute if it's not already
        if not os.path.isabs(config_path):
            config_path = os.path.join(self.project_root, config_path)
        
        # Load the configuration
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found at: {config_path}")
            
        self.config = self._load_config(config_path)
        
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
    """Cold memory storage using DuckDB for efficient querying of parquet files."""
    
    def __init__(self, connection: duckdb.DuckDBPyConnection, config: Optional[Dict[str, Any]] = None):
        """Initialize cold memory storage.
        
        Args:
            connection: DuckDB connection to use
            config: Optional configuration dictionary
        """
        self.con = connection
        self.config = config or {}
        
        # Create metadata table if it doesn't exist
        self.con.execute("""
            CREATE TABLE IF NOT EXISTS cold_metadata (
                file_path VARCHAR,
                theme VARCHAR,
                tag VARCHAR,
                num_rows INTEGER,
                num_columns INTEGER,
                schema JSON,
                imported_at TIMESTAMP,
                table_name VARCHAR
            )
        """)
        
        logger.info("Initialized cold memory storage")
        
    def batch_import_parquet(
        self,
        folder_path: Union[str, Path],
        theme: Optional[str] = None,
        tag: Optional[str] = None,
        recursive: bool = True,
        pattern: str = "*.parquet"
    ) -> Dict[str, Any]:
        """Import multiple parquet files into cold storage.
        
        Args:
            folder_path: Path to folder containing parquet files
            theme: Optional theme tag for the data
            tag: Optional additional tag for the data
            recursive: Whether to search subdirectories
            pattern: File pattern to match
            
        Returns:
            Dict containing:
                files_processed: Number of files processed
                records_imported: Total number of records imported
                total_size: Total size of imported data in bytes
                errors: List of files that had errors
        """
        folder_path = Path(folder_path)
        if not folder_path.exists():
            raise FileNotFoundError(f"Directory not found: {folder_path}")

        files_processed = 0
        records_imported = 0
        total_size = 0
        errors = []

        # Find all parquet files
        if recursive:
            parquet_files = list(folder_path.rglob(pattern))
        else:
            parquet_files = list(folder_path.glob(pattern))

        for file_path in parquet_files:
            try:
                # Import the parquet file
                table_name = f"parquet_{files_processed}"
                self.con.execute(f"CREATE VIEW {table_name} AS SELECT * FROM parquet_scan('{file_path}')")
                
                # Get file stats
                file_stats = file_path.stat()
                num_rows = self.con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                num_cols = len(self.con.execute(f"SELECT * FROM {table_name} LIMIT 0").description)
                
                # Store metadata
                self.con.execute("""
                    INSERT INTO cold_metadata 
                    (file_path, theme, tag, num_rows, num_columns, imported_at, table_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(file_path),
                    theme,
                    tag,
                    num_rows,
                    num_cols,
                    datetime.now(),
                    table_name
                ))
                
                files_processed += 1
                records_imported += num_rows
                total_size += file_stats.st_size
                
            except Exception as e:
                errors.append({"file": str(file_path), "error": str(e)})
                logger.error(f"Error importing {file_path}: {e}")

        return {
            "files_processed": files_processed,
            "records_imported": records_imported,
            "total_size": total_size,
            "errors": errors
        }

    def cleanup(self) -> None:
        """Clean up resources and close connections."""
        try:
            # Drop all views
            views = self.con.execute("SELECT table_name FROM cold_metadata").fetchall()
            for view in views:
                try:
                    self.con.execute(f"DROP VIEW IF EXISTS {view[0]}")
                except Exception as e:
                    logger.warning(f"Error dropping view {view[0]}: {e}")

            # Drop metadata table
            self.con.execute("DROP TABLE IF EXISTS cold_metadata")
            
            logger.info("Cleaned up cold memory storage")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")



