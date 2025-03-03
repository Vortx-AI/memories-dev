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
    """Cold memory storage for infrequently accessed data"""
    
    def __init__(self, storage_path: Union[str, Path], max_size: int, duckdb_connection: Optional[Any] = None):
        """Initialize cold storage.
        
        Args:
            storage_path: Path to cold storage directory
            max_size: Maximum size in bytes
            duckdb_connection: Pre-configured DuckDB connection
        """
        self.storage_path = Path(storage_path)
        self.max_size = max_size
        
        # Create storage directory
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Use provided DuckDB connection
        self.con = duckdb_connection
        if self.con is None:
            self.logger.warning("No DuckDB connection provided, cold memory will be disabled")
            return
        
        # Initialize schema
        self._initialize_db()
        
        logger.info(f"Initialized cold storage at {self.storage_path}")

    def _initialize_db(self) -> None:
        """Initialize the database schema."""
        try:
            # Create file_metadata table if it doesn't exist
            self.con.execute("""
                CREATE TABLE IF NOT EXISTS file_metadata (
                    file_path VARCHAR PRIMARY KEY,
                    metadata JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.con.commit()
            logger.info("Database schema initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise

    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata from disk."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file) as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load metadata: {e}")
        return {}

    def _find_parquet_files(self, directory: Path) -> List[Path]:
        """Recursively find all parquet files in directory and its subdirectories.
        
        Args:
            directory: Directory to search in
            
        Returns:
            List of paths to parquet files
        """
        parquet_files = []
        try:
            # Recursively search for all .parquet files
            for path in directory.rglob("*.parquet"):
                parquet_files.append(path)
            
            if parquet_files:
                self.logger.info(f"Found {len(parquet_files)} parquet files in {directory}")
            else:
                self.logger.warning(f"No parquet files found in {directory}")
                
        except Exception as e:
            self.logger.error(f"Error searching for parquet files: {e}")
            
        return parquet_files

    def query_storage(
        self, 
        query: str, 
        theme: Optional[str] = None, 
        tag: Optional[str] = None,
        additional_files: Optional[List[Union[str, Path]]] = None
    ) -> Optional[Any]:
        """Query Parquet files in cold storage and additional locations.
        
        Args:
            query: SQL query to execute. Use 'cold_storage' as the table name to query all parquet files
                  Example: "SELECT * FROM cold_storage WHERE column > 0"
            theme: Optional theme to filter files (e.g., 'buildings')
            tag: Optional tag to filter files (e.g., 'building')
            additional_files: Optional list of additional Parquet file paths to include in the query
            
        Returns:
            Query results as pandas DataFrame
        """
        try:
            # Determine search directory based on theme and tag
            if theme and tag:
                search_dir = self.storage_path / theme / tag
            elif theme:
                search_dir = self.storage_path / theme
            else:
                search_dir = self.storage_path
            
            # Find all parquet files recursively
            parquet_files = self._find_parquet_files(search_dir)
            
            # Add additional files if provided
            if additional_files:
                for file_path in additional_files:
                    file_path = Path(file_path)
                    if file_path.exists() and file_path.suffix == '.parquet':
                        parquet_files.append(file_path)
                    else:
                        self.logger.warning(f"Skipping invalid file: {file_path}")
            
            if not parquet_files:
                self.logger.warning(f"No Parquet files found to query")
                return None
            
            # Log the files being queried
            self.logger.info("Querying the following files:")
            for f in parquet_files:
                self.logger.info(f"  - {f}")
            
            # Create a view combining all relevant parquet files
            view_creation = f"""
            CREATE OR REPLACE VIEW cold_storage AS 
            SELECT * FROM read_parquet([{','.join(f"'{str(f.absolute())}'" for f in parquet_files)}])
            """
            
            self.con.execute(view_creation)
            
            # If the query doesn't specify a FROM clause, add it
            if 'from' not in query.lower():
                query = f"{query} FROM cold_storage"
            
            # Execute the actual query
            self.logger.info(f"Executing query: {query}")
            result = self.con.execute(query).fetchdf()
            self.logger.info(f"Query returned {len(result)} rows")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error querying cold storage: {e}")
            return None

    def list_available_data(self) -> Dict[str, Dict[str, List[str]]]:
        """List all available data in storage with file counts"""
        try:
            data_structure = {}
            
            # Recursively find all parquet files
            all_files = list(self.storage_path.rglob("*.parquet"))
            
            for file_path in all_files:
                # Get relative path components
                rel_path = file_path.relative_to(self.storage_path)
                parts = rel_path.parts
                
                # Skip if not enough path components
                if len(parts) < 3:  # expecting at least: overture/theme/tag/file.parquet
                    continue
                
                theme = parts[1]  # overture/theme/...
                tag = parts[2]    # overture/theme/tag/...
                
                # Initialize nested structure
                if theme not in data_structure:
                    data_structure[theme] = {"tags": {}}
                
                if tag not in data_structure[theme]["tags"]:
                    data_structure[theme]["tags"][tag] = []
                
                # Add file info
                data_structure[theme]["tags"][tag].append(str(rel_path))
            
            # Add file counts
            for theme in data_structure:
                total_theme_files = sum(len(files) for files in data_structure[theme]["tags"].values())
                data_structure[theme]["file_count"] = total_theme_files
                
                for tag in data_structure[theme]["tags"]:
                    files = data_structure[theme]["tags"][tag]
                    data_structure[theme]["tags"][tag] = {
                        "file_count": len(files),
                        "files": files
                    }
            
            return data_structure
            
        except Exception as e:
            self.logger.error(f"Error listing available data: {e}")
            return {}

    def store(self, data: Dict[str, Any]) -> None:
        """Store data in a compressed file.
        
        Args:
            data: Data to store
        """
        try:
            # Use timestamp as filename
            timestamp = data.get("timestamp", "")
            if not timestamp:
                logger.error("Data must have a timestamp")
                return
            
            filename = self.storage_path / f"{timestamp}.json.gz"
            
            # Store as compressed JSON
            with gzip.open(filename, "wt") as f:
                json.dump(data, f, indent=2)
            
            # Maintain max size by removing oldest files
            files = list(self.storage_path.glob("*.json.gz"))
            if len(files) > self.max_size:
                # Sort by modification time and remove oldest
                files.sort(key=lambda x: x.stat().st_mtime)
                for old_file in files[:-self.max_size]:
                    old_file.unlink()
        except Exception as e:
            logger.error(f"Failed to store data in file: {e}")
    
    def retrieve(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Retrieve data from compressed files.
        
        Args:
            query: Query to match against stored data
            
        Returns:
            Retrieved data or None if not found
        """
        try:
            # Use timestamp as filename if provided
            if "timestamp" in query:
                filename = self.storage_path / f"{query['timestamp']}.json.gz"
                if filename.exists():
                    with gzip.open(filename, "rt") as f:
                        return json.load(f)
            
            # Otherwise, search through all files
            for file in self.storage_path.glob("*.json.gz"):
                with gzip.open(file, "rt") as f:
                    data = json.load(f)
                    # Check if all query items match
                    if all(data.get(k) == v for k, v in query.items()):
                        return data
            
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve data from file: {e}")
            return None
    
    def retrieve_all(self) -> List[Dict[str, Any]]:
        """Retrieve all data from compressed files.
        
        Returns:
            List of all stored data
        """
        try:
            result = []
            for file in self.storage_path.glob("*.json.gz"):
                with gzip.open(file, "rt") as f:
                    result.append(json.load(f))
            return result
        except Exception as e:
            logger.error(f"Failed to retrieve all data from files: {e}")
            return []
    
    def clear(self) -> None:
        """Clear all data files."""
        try:
            shutil.rmtree(self.storage_path)
            self.storage_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to clear files: {e}")

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
        try:
            folder_path = Path(folder_path)
            if not folder_path.exists():
                raise ValueError(f"Folder not found: {folder_path}")

            results = {
                "files_processed": 0,
                "records_imported": 0,
                "total_size": 0,
                "errors": []
            }

            # Find all matching parquet files
            if recursive:
                parquet_files = list(folder_path.rglob(pattern))
            else:
                parquet_files = list(folder_path.glob(pattern))

            if not parquet_files:
                logger.warning(f"No parquet files found in {folder_path}")
                return results

            logger.info(f"Found {len(parquet_files)} parquet files to process")
            
            # Process each file
            for file_path in parquet_files:
                try:
                    logger.info(f"Processing file: {file_path}")
                    
                    # Read parquet file metadata
                    table = pq.read_table(file_path)
                    file_size = file_path.stat().st_size
                    
                    # Create destination path preserving directory structure
                    rel_path = file_path.relative_to(folder_path)
                    dest_path = self.storage_path / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file to cold storage
                    import shutil
                    shutil.copy2(file_path, dest_path)
                    
                    # Update database metadata
                    metadata = {
                        "file_path": str(rel_path),
                        "theme": theme,
                        "tag": tag,
                        "num_rows": table.num_rows,
                        "num_columns": len(table.schema),
                        "file_size": file_size,
                        "import_time": datetime.now().isoformat(),
                        "schema": {
                            field.name: str(field.type) 
                            for field in table.schema
                        }
                    }
                    
                    # Create a table for this specific file
                    table_name = f"parquet_data_{results['files_processed']}"
                    
                    try:
                        # Drop table if it exists
                        self.con.execute(f"DROP TABLE IF EXISTS {table_name}")
                        
                        # Create table directly from parquet file
                        self.con.execute(f"""
                            CREATE TABLE {table_name} AS 
                            SELECT * FROM read_parquet('{dest_path}')
                        """)
                        
                        # Store table name in metadata
                        metadata["table_name"] = table_name
                        
                    except Exception as e:
                        logger.error(f"Error creating table for {file_path}: {e}")
                        results["errors"].append(f"{file_path}: {str(e)}")
                        continue
                    
                    # Store metadata in database
                    self._store_metadata(str(rel_path), metadata)
                    
                    # Update results
                    results["files_processed"] += 1
                    results["records_imported"] += table.num_rows
                    results["total_size"] += file_size
                    
                    logger.info(f"Successfully processed file {results['files_processed']}/{len(parquet_files)}")
                    
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    results["errors"].append(str(file_path))
                    continue

            logger.info(f"Import complete: {results}")
            return results

        except Exception as e:
            logger.error(f"Failed to import parquet files: {e}")
            raise

    def _store_metadata(self, file_path: str, metadata: Dict[str, Any]) -> None:
        """Store file metadata in the database."""
        query = """
        INSERT INTO file_metadata (file_path, metadata)
        VALUES (?, ?)
        """
        self.con.execute(query, (file_path, json.dumps(metadata)))
        self.con.commit()

