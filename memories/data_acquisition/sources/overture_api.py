"""
Overture Maps data source using DuckDB for direct S3 access and filtering.
"""

import os
import logging
import duckdb
from pathlib import Path
from typing import Dict, List, Union, Any

logger = logging.getLogger(__name__)

class OvertureAPI:
    """Interface for accessing Overture Maps data using DuckDB's S3 integration."""
    
    # Latest Overture release
    OVERTURE_RELEASE = "2024-09-18.0"
    
    # Theme configurations with exact type paths
    THEMES = {
        "buildings": ["building"],      # theme=buildings/type=building/*
        "places": ["place"],           # theme=places/type=place/*
        "transportation": ["segment"],  # theme=transportation/type=segment/*
        "base": ["water", "land"],     # theme=base/type=water/*, theme=base/type=land/*
        "divisions": ["division_area"]  # theme=divisions/type=division_area/*
    }
    
    def __init__(self, data_dir: str = None):
        """Initialize the Overture Maps interface.
        
        Args:
            data_dir: Directory for storing downloaded data
        """
        self.data_dir = Path(data_dir) if data_dir else Path("data/overture")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Initialize DuckDB connection
            self.con = duckdb.connect(database=":memory:")
            
            # Try to load extensions if already installed
            try:
                self.con.execute("LOAD spatial;")
                self.con.execute("LOAD httpfs;")
            except duckdb.Error:
                # If loading fails, install and then load
                logger.info("Installing required DuckDB extensions...")
                self.con.execute("INSTALL spatial;")
                self.con.execute("INSTALL httpfs;")
                self.con.execute("LOAD spatial;")
                self.con.execute("LOAD httpfs;")
            
            # Configure S3 access
            self.con.execute("SET s3_region='us-west-2';")
            self.con.execute("SET enable_http_metadata_cache=true;")
            self.con.execute("SET enable_object_cache=true;")
            
            # Test the connection by running a simple query
            test_query = "SELECT 1;"
            self.con.execute(test_query)
            logger.info("DuckDB connection and extensions initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing DuckDB: {e}")
            raise RuntimeError(f"Failed to initialize DuckDB: {e}")
    
    def get_s3_path(self, theme: str, type_name: str) -> str:
        """Get the S3 path for a theme and type.
        
        Args:
            theme: Theme name
            type_name: Type name within theme
            
        Returns:
            S3 path string
        """
        return f"s3://overturemaps-us-west-2/release/{self.OVERTURE_RELEASE}/theme={theme}/type={type_name}/*"
    
    def download_theme(self, theme: str, bbox: Dict[str, float]) -> bool:
        """Download theme data directly from S3 with bbox filtering.
        
        Args:
            theme: Theme name
            bbox: Bounding box dictionary with xmin, ymin, xmax, ymax
        
        Returns:
            bool: True if download successful
        """
        if theme not in self.THEMES:
            logger.error(f"Invalid theme: {theme}")
            return False
            
        try:
            # Create output directory
            theme_dir = self.data_dir / theme
            theme_dir.mkdir(parents=True, exist_ok=True)
            
            results = []
            for type_name in self.THEMES[theme]:
                s3_path = self.get_s3_path(theme, type_name)
                output_file = theme_dir / f"{type_name}_filtered.parquet"
                
                # Test S3 access
                test_query = f"""
                SELECT COUNT(*) 
                FROM read_parquet('{s3_path}', filename=true, hive_partitioning=1)
                LIMIT 1
                """
                
                try:
                    logger.info(f"Testing S3 access for {theme}/{type_name}...")
                    self.con.execute(test_query)
                except Exception as e:
                    logger.error(f"Failed to access S3 path for {theme}/{type_name}: {e}")
                    continue
                
                # Query to filter and download data
                query = f"""
                COPY (
                    SELECT 
                        id, 
                        names.primary AS primary_name,
                        ST_AsText(geometry) as geometry,
                        *
                    FROM 
                        read_parquet('{s3_path}', filename=true, hive_partitioning=1)
                    WHERE 
                        bbox.xmin >= {bbox['xmin']}
                        AND bbox.xmax <= {bbox['xmax']}
                        AND bbox.ymin >= {bbox['ymin']}
                        AND bbox.ymax <= {bbox['ymax']}
                ) TO '{output_file}' (FORMAT 'parquet');
                """
                
                logger.info(f"Downloading filtered data for {theme}/{type_name}...")
                try:
                    self.con.execute(query)
                    
                    # Verify the file was created and has content
                    if output_file.exists() and output_file.stat().st_size > 0:
                        count_query = f"SELECT COUNT(*) as count FROM read_parquet('{output_file}')"
                        count = self.con.execute(count_query).fetchone()[0]
                        logger.info(f"Saved {count} features for {theme}/{type_name}")
                        results.append(True)
                    else:
                        logger.warning(f"No features found for {theme}/{type_name}")
                        results.append(False)
                except Exception as e:
                    logger.error(f"Error downloading {theme}/{type_name}: {e}")
                    results.append(False)
            
            return any(results)  # Return True if any type was downloaded successfully
                
        except Exception as e:
            logger.error(f"Error downloading {theme} data: {e}")
            return False
    
    def download_data(self, bbox: Dict[str, float]) -> Dict[str, bool]:
        """Download all theme data for a given bounding box.
        
        Args:
            bbox: Bounding box dictionary with xmin, ymin, xmax, ymax
            
        Returns:
            Dictionary with download status for each theme
        """
        try:
            results = {}
            for theme in self.THEMES:
                logger.info(f"\nDownloading {theme} data...")
                results[theme] = self.download_theme(theme, bbox)
            return results
            
        except Exception as e:
            logger.error(f"Error during data download: {str(e)}")
            return {theme: False for theme in self.THEMES}
    
    async def search(self, bbox: Union[List[float], Dict[str, float]]) -> Dict[str, Any]:
        """
        Search downloaded data within the given bounding box.
        
        Args:
            bbox: Bounding box as either:
                 - List [min_lon, min_lat, max_lon, max_lat]
                 - Dict with keys 'xmin', 'ymin', 'xmax', 'ymax'
            
        Returns:
            Dictionary containing features by theme
        """
        try:
            # Convert bbox to dictionary format if it's a list
            if isinstance(bbox, (list, tuple)):
                bbox_dict = {
                    "xmin": bbox[0],
                    "ymin": bbox[1],
                    "xmax": bbox[2],
                    "ymax": bbox[3]
                }
            else:
                bbox_dict = bbox
            
            results = {}
            
            for theme in self.THEMES:
                theme_dir = self.data_dir / theme
                if not theme_dir.exists():
                    logger.warning(f"No data directory found for theme {theme}")
                    results[theme] = []
                    continue
                
                theme_results = []
                for type_name in self.THEMES[theme]:
                    parquet_file = theme_dir / f"{type_name}_filtered.parquet"
                    if not parquet_file.exists():
                        logger.warning(f"No data file found for {theme}/{type_name}")
                        continue
                        
                    try:
                        query = f"""
                        SELECT 
                            id,
                            names.primary AS primary_name,
                            geometry,
                            *
                        FROM read_parquet('{parquet_file}')
                        """
                        
                        df = self.con.execute(query).fetchdf()
                        if not df.empty:
                            theme_results.extend(df.to_dict('records'))
                            logger.info(f"Found {len(df)} features in {parquet_file.name}")
                    except Exception as e:
                        logger.warning(f"Error reading {parquet_file}: {str(e)}")
                
                results[theme] = theme_results
                if theme_results:
                    logger.info(f"Found total {len(theme_results)} features for theme {theme}")
                else:
                    logger.warning(f"No features found for theme {theme}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching data: {str(e)}")
            return {theme: [] for theme in self.THEMES}
    
    def __del__(self):
        """Clean up DuckDB connection."""
        if hasattr(self, 'con'):
            try:
                self.con.close()
            except:
                pass