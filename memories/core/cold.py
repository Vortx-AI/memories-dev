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
    
    def __init__(self, storage_path: Union[str, Path], max_size: int):
        self.storage_path = Path(storage_path)
        self.max_size = max_size
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Initialize DuckDB connection
        self.con = duckdb.connect()
        
        # Initialize metadata file
        self.metadata_file = self.storage_path / "metadata.json"
        self._load_metadata()

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

    def query_storage(self, query: str, theme: Optional[str] = None, tag: Optional[str] = None) -> Optional[Any]:
        """Query Parquet files in cold storage.
        
        Args:
            query: SQL query to execute
            theme: Optional theme to filter files (e.g., 'buildings')
            tag: Optional tag to filter files (e.g., 'building')
            
        Returns:
            Query results as pandas DataFrame
        """
        try:
            # Determine search directory based on theme and tag
            if theme and tag:
                search_dir = self.storage_path / "overture" / theme / tag
            elif theme:
                search_dir = self.storage_path / "overture" / theme
            else:
                search_dir = self.storage_path
            
            # Find all parquet files recursively
            parquet_files = self._find_parquet_files(search_dir)
            
            if not parquet_files:
                self.logger.warning(f"No Parquet files found in {search_dir}")
                return None
            
            # Log the files being queried
            self.logger.info("Querying the following files:")
            for f in parquet_files:
                self.logger.info(f"  - {f.relative_to(self.storage_path)}")
                
            # Create a view combining all relevant parquet files
            view_creation = f"""
            CREATE OR REPLACE VIEW cold_storage AS 
            SELECT * FROM read_parquet([{','.join(f"'{str(f)}'" for f in parquet_files)}])
            """
            
            self.con.execute(view_creation)
            
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

# Test code with more verbose output
if __name__ == "__main__":
    try:
        print("Initializing ColdMemory...")
        cold_memory = ColdMemory(Path(os.getenv('GEO_MEMORIES')), 100)
        
        # Test coordinates (Bangalore, India)
        test_lat, test_lon = 12.9095706, 77.6085865
        print(f"\nQuerying point: Latitude {test_lat}, Longitude {test_lon}")
        
        # Basic query with debug info
        print("\n1. Executing basic query...")
        results = cold_memory.retrieve({
            "latitude": test_lat,
            "longitude": test_lon,
            "limit": 5
        })
        print(f"Query returned {len(results)} results")
        
        if results:
            print("\nAll columns in results:")
            print("Available columns:", list(results.keys()))
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
            print("\nSample of available data:")
            sample_query = {
                "latitude": 12.9095706,
                "longitude": 77.6085865,
                "limit": 1
            }
            print(f"Executing sample query: {sample_query}")
            sample_data = cold_memory.retrieve(sample_query)
            if sample_data:
                print("\nAvailable columns:", list(sample_data.keys()))
                print("\nComplete sample row:")
                pd.set_option('display.max_columns', None)
                pd.set_option('display.max_rows', None)
                pd.set_option('display.width', None)
                pd.set_option('display.max_colwidth', None)
                print(sample_data)

    except Exception as e:
        print(f"An error occurred during testing: {str(e)}")
    finally:
        if 'cold_memory' in locals():
            print("\nClosed ColdMemory.")
    