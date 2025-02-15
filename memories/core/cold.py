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
    def __init__(self):
        """Initialize Cold Storage with DuckDB and GeoParquet support."""
        load_dotenv()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize DuckDB connection with spatial extension
        self.conn = duckdb.connect()
        self.conn.execute("INSTALL spatial;")
        self.conn.execute("LOAD spatial;")

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
                ST_Contains(geom, (SELECT point FROM point_geom))
                OR
                ST_Equals(geom, (SELECT point FROM point_geom))
            )
            """
            
            if geometry_types:
                geometry_types_str = "', '".join(geometry_types)
                point_query += f"""
                AND ST_GeometryType(geom) IN ('ST_{geometry_types_str}')
                """
                
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

# Test code with more verbose output
if __name__ == "__main__":
    try:
        print("Initializing ColdStorage...")
        cold_storage = ColdStorage()
        
        # Test coordinates (Bangalore, India)
        test_lat, test_lon = 12.9095706, 77.6085865
        print(f"\nQuerying point: Latitude {test_lat}, Longitude {test_lon}")
        
        # Basic query with debug info
        print("\n1. Executing basic query...")
        results = cold_storage.query_by_point(
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
            sample_df = cold_storage.conn.execute(sample_query).df()
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
        if 'cold_storage' in locals():
            cold_storage.conn.close()
            print("\nClosed DuckDB connection.")
    