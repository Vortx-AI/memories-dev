"""
Overture Maps data source using DuckDB to read from local GeoJSONSeq files.
"""

import os
import logging
import duckdb
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class OvertureAPI:
    """Interface for accessing Overture Maps data using DuckDB."""
    
    # Latest Overture release
    OVERTURE_RELEASE = "2025-01-22.0"
    
    # Themes to download with their specific columns
    THEMES = {
        'buildings': """
            id,
            type as building_type,
            height,
            bbox.xmin,
            bbox.ymin,
            bbox.xmax,
            bbox.ymax,
            geometry
        """,
        'places': """
            id,
            type as place_type,
            confidence,
            bbox.xmin,
            bbox.ymin,
            bbox.xmax,
            bbox.ymax,
            geometry
        """,
        'transportation': """
            id,
            type as road_type,
            bbox.xmin,
            bbox.ymin,
            bbox.xmax,
            bbox.ymax,
            geometry
        """
    }
    
    def __init__(self, data_dir: str = None):
        """Initialize the Overture Maps interface."""
        self.con = duckdb.connect(database=":memory:")
        self.con.execute("INSTALL spatial;")
        self.con.execute("LOAD spatial;")
        
        # Set data directory
        self.data_dir = Path(data_dir) if data_dir else Path("examples/data/overture")
        
    def download_theme(self, theme: str, bbox: Dict[str, float], columns: str = None) -> bool:
        """Download a theme from Azure using DuckDB.
        
        Args:
            theme: Theme name
            bbox: Bounding box dictionary with xmin, ymin, xmax, ymax
            columns: Optional columns to select (uses default if None)
        
        Returns:
            bool: True if download successful
        """
        theme_dir = self.data_dir / theme
        theme_dir.mkdir(parents=True, exist_ok=True)
        output_file = theme_dir / f"{theme}.geojsonseq"
        
        # Remove existing file if it exists
        if output_file.exists():
            logger.info(f"Removing existing file: {output_file}")
            output_file.unlink()
        
        logger.info(f"Downloading {theme} data...")
        
        try:
            # Use provided columns or default
            columns_to_select = columns or self.THEMES.get(theme)
            if not columns_to_select:
                raise ValueError(f"No column definition found for theme: {theme}")
            
            # Create optimized query with index hint and feature limit
            query = f"""
            COPY (
                SELECT
                    {columns_to_select}
                FROM read_parquet(
                    'azure://release/{self.OVERTURE_RELEASE}/theme={theme}/type=*/*',
                    filename=true,
                    hive_partitioning=1
                )
                WHERE bbox.xmin >= {bbox['xmin']}
                AND bbox.xmin <= {bbox['xmax']}
                AND bbox.ymin >= {bbox['ymin']}
                AND bbox.ymin <= {bbox['ymax']}
                LIMIT 100  -- Limit to 100 features per category
            ) TO '{output_file}' WITH (FORMAT GDAL, DRIVER 'GeoJSONSeq');
            """
            
            # Execute query with optimized memory settings
            self.con.execute("SET memory_limit='1GB';")  # Reduced memory limit
            self.con.execute("SET threads=4;")  # Limit thread usage
            self.con.execute(query)
            logger.info(f"Successfully downloaded {theme} data to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading {theme} data: {e}")
            return False
            
    def download_data(self, bbox: Dict[str, float]) -> Dict[str, bool]:
        """Download all themes for a given bounding box.
        
        Args:
            bbox: Bounding box dictionary with xmin, ymin, xmax, ymax
            
        Returns:
            Dictionary of theme names and their download status
        """
        try:
            # Create data directory
            self.data_dir.mkdir(parents=True, exist_ok=True)
            
            # Install and load extensions
            self.con.execute("INSTALL azure;")
            self.con.execute("LOAD azure;")
            self.con.execute("INSTALL spatial;")
            self.con.execute("LOAD spatial;")
            
            # Set up Azure connection
            self.con.execute("""
                SET azure_storage_connection_string = 'DefaultEndpointsProtocol=https;AccountName=overturemapswestus2;EndpointSuffix=core.windows.net';
            """)
            
            # Download themes
            results = {}
            for theme in self.THEMES.keys():
                logger.info(f"\nDownloading {theme}...")
                results[theme] = self.download_theme(theme, bbox)
            
            return results
        except Exception as e:
            logger.error(f"Error during data download: {str(e)}")
            return {theme: False for theme in self.THEMES.keys()}

    async def search(self, bbox: List[float]) -> Dict[str, Any]:
        """
        Search Overture data within the given bounding box.
        
        Args:
            bbox: Bounding box [min_lon, min_lat, max_lon, max_lat]
            
        Returns:
            Dictionary containing buildings, places, and transportation features
        """
        try:
            # First, download the data if it doesn't exist
            bbox_dict = {
                "xmin": bbox[0],
                "ymin": bbox[1],
                "xmax": bbox[2],
                "ymax": bbox[3]
            }
            download_results = self.download_data(bbox_dict)
            
            if not any(download_results.values()):
                logger.warning("Failed to download any Overture data")
                return {theme: [] for theme in self.THEMES.keys()}
            
            # Convert bbox to WKT polygon
            bbox_wkt = f"POLYGON(({bbox[0]} {bbox[1]}, {bbox[0]} {bbox[3]}, {bbox[2]} {bbox[3]}, {bbox[2]} {bbox[1]}, {bbox[0]} {bbox[1]}))"
            bbox_expr = f"ST_GeomFromText('{bbox_wkt}')"
            
            results = {}
            
            for theme in self.THEMES.keys():
                # Local path for theme
                theme_file = self.data_dir / theme / f"{theme}.geojsonseq"
                if not theme_file.exists():
                    logger.warning(f"Theme file not found: {theme_file}")
                    results[theme] = []
                    continue
                
                # Create query to filter by bbox
                query = f"""
                SELECT *
                FROM read_json_auto('{theme_file}', format='newline_delimited')
                WHERE ST_Intersects(ST_GeomFromGeoJSON(geometry), {bbox_expr})
                LIMIT 1000;
                """
                
                try:
                    # Execute query and fetch results
                    df = self.con.execute(query).fetchdf()
                    results[theme] = df.to_dict('records')
                    logger.info(f"Found {len(results[theme])} {theme} features")
                except Exception as e:
                    logger.warning(f"Error querying {theme}: {str(e)}")
                    results[theme] = []
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching Overture data: {str(e)}")
            return {theme: [] for theme in self.THEMES.keys()}
            
    def __del__(self):
        """Clean up DuckDB connection."""
        if hasattr(self, 'con'):
            self.con.close()
