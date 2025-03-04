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
    """Cold memory storage for infrequently accessed data using DuckDB."""
    
    def __init__(self, con):
        """Initialize cold memory storage."""
        self.config = Config()
        self.con = con  # Use the connection passed from MemoryManager
        self.logger = logging.getLogger(__name__)
        
        # Set up storage path in project root
        project_root = os.getenv("PROJECT_ROOT", os.path.expanduser("~"))
        self.storage_path = Path(project_root)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def register_external_file(self, file_path: str) -> None:
        """Register an external file in the cold storage metadata."""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Get file metadata
            file_stats = file_path.stat()
            file_type = file_path.suffix.lstrip('.')

            # Create sequence if it doesn't exist
            self.con.execute("""
                CREATE SEQUENCE IF NOT EXISTS cold_metadata_id_seq;
            """)

            # Create table if it doesn't exist
            self.con.execute("""
                CREATE TABLE IF NOT EXISTS cold_metadata (
                    id INTEGER PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    path VARCHAR,
                    size BIGINT,
                    data_type VARCHAR,
                    additional_meta JSON
                )
            """)

            # Check if file is already registered
            existing = self.con.execute(
                "SELECT id FROM cold_metadata WHERE path = ?",
                [str(file_path)]
            ).fetchone()

            if existing:
                self.logger.info(f"File already registered: {file_path}")
                return

            # Insert new file metadata using nextval from sequence
            self.con.execute("""
                INSERT INTO cold_metadata (id, path, size, data_type, additional_meta)
                VALUES (nextval('cold_metadata_id_seq'), ?, ?, ?, ?)
            """, [
                str(file_path),
                file_stats.st_size,
                file_type,
                '{}'  # Empty JSON object for additional metadata
            ])

            self.logger.info(f"Registered external file: {file_path}")

        except Exception as e:
            self.logger.error(f"Error registering external file: {e}")
            raise

    def _initialize_schema(self):
        """Initialize database schema."""
        try:
            # Create metadata table if it doesn't exist with BIGINT for size
            self.con.execute("""
                CREATE TABLE IF NOT EXISTS cold_metadata (
                    id VARCHAR PRIMARY KEY,
                    timestamp TIMESTAMP,
                    data_type VARCHAR,
                    size BIGINT,  -- Changed from INTEGER to BIGINT
                    additional_meta JSON
                )
            """)
            
            self.logger.info("Initialized cold storage schema")
        except Exception as e:
            self.logger.error(f"Failed to initialize database schema: {e}")
            raise

    def store(self, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Store data in cold storage."""
        try:
            if not isinstance(data, dict):
                raise ValueError("Data must be a dictionary")
                
            data_id = metadata.get('id') if metadata else str(uuid.uuid4())
            
            # Store metadata
            self.con.execute("""
                INSERT INTO cold_metadata (id, timestamp, data_type, size, additional_meta)
                VALUES (?, ?, ?, ?, ?)
            """, (
                data_id,
                datetime.now(),
                metadata.get('type', 'unknown'),
                len(str(data)),
                json.dumps(metadata) if metadata else None
            ))
            
            # Store data
            self.con.execute("""
                INSERT INTO cold_data (id, data)
                VALUES (?, ?)
            """, (data_id, json.dumps(data)))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store data: {e}")
            return False

    def retrieve(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Retrieve data from cold storage."""
        try:
            conditions = []
            params = []
            for key, value in query.items():
                conditions.append(f"data->>'$.{key}' = ?")
                params.append(str(value))
                
            where_clause = " AND ".join(conditions)
            
            result = self.con.execute(f"""
                SELECT d.data
                FROM cold_data d
                WHERE {where_clause}
                LIMIT 1
            """, params).fetchone()
            
            return json.loads(result[0]) if result else None
            
        except Exception as e:
            logger.error(f"Failed to retrieve data: {e}")
            return None

    def clear(self) -> None:
        """Clear all data and metadata from cold storage."""
        try:
            # Drop all registered views first
            views = self.con.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='view' AND name LIKE 'file_%'
            """).fetchall()
            
            for (view_name,) in views:
                self.con.execute(f"DROP VIEW IF EXISTS {view_name}")
            
            # Clear all metadata
            self.con.execute("DELETE FROM cold_metadata")
            self.con.execute("DELETE FROM cold_data")
            logger.info("Cleared all cold storage metadata")
        except Exception as e:
            logger.error(f"Failed to clear cold storage: {e}")

    def unregister_file(self, file_id: str) -> bool:
        """Unregister a specific file from cold storage.
        
        Args:
            file_id: ID of the file to unregister
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Drop the view if it exists
            self.con.execute(f"DROP VIEW IF EXISTS file_{file_id}")
            
            # Remove metadata
            self.con.execute("DELETE FROM cold_metadata WHERE id = ?", [file_id])
            
            logger.info(f"Successfully unregistered file: {file_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to unregister file {file_id}: {e}")
            return False

    def list_registered_files(self) -> List[Dict]:
        """List all registered files and their metadata."""
        try:
            result = self.con.execute("""
                SELECT * FROM cold_metadata 
                WHERE data_type = 'parquet'
                ORDER BY timestamp DESC
            """).fetchall()
            
            files = []
            for row in result:
                meta = json.loads(row[4])  # additional_meta column
                files.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'size': row[2],
                    'file_path': meta.get('file_path'),
                    'table_name': meta.get('table_name'),
                    **meta
                })
            
            return files
            
        except Exception as e:
            self.logger.error(f"Failed to list registered files: {e}")
            return []

    def cleanup(self) -> None:
        """Cleanup resources."""
        pass  # DuckDB connection is managed by MemoryManager

    def get_all_schemas(self):
        """Get all file paths from cold storage metadata and extract their schemas."""
        try:
            # Query cold metadata table to get both id and path
            query = """
            SELECT id, path 
            FROM cold_metadata
            """
            result = self.con.execute(query).fetchdf()
            
            logger.info(f"Found {len(result)} entries in cold metadata")
            
            # Extract schema for each file
            schemas = []
            for _, row in result.iterrows():
                file_path = row['path']
                try:
                    # Use DuckDB to get schema information
                    schema_query = f"""
                    DESCRIBE SELECT * FROM parquet_scan('{file_path}')
                    """
                    schema_df = self.con.execute(schema_query).fetchdf()
                    
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



