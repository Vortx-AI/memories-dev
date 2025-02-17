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
    """Cold memory layer using compressed file-based storage."""
    
    def __init__(self, storage_path: Path, max_size: int):
        """Initialize cold memory.
        
        Args:
            storage_path: Path to store data files
            max_size: Maximum number of items to store
        """
        self.storage_path = storage_path
        self.max_size = max_size
        
        # Create storage directory
        self.storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized cold memory at {storage_path}")
    
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
    