"""
Overture Maps data source using AWS CLI/AzCopy for downloads and DuckDB for local processing.
"""

import os
import logging
import duckdb
import shutil
import subprocess
from typing import Dict, Any, List, Union
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class OvertureLocal:
    """Interface for accessing Overture Maps data using AWS CLI/AzCopy with local filtering."""
    
    # Latest Overture release
    OVERTURE_RELEASE = "2024-01-11-alpha.0"
    
    # Base URLs without theme= prefix
    AWS_S3_BASE = f"s3://overturemaps-us-west-2/release/{OVERTURE_RELEASE}/theme="
    AZURE_BLOB_BASE = f"https://overturemapswestus2.dfs.core.windows.net/release/{OVERTURE_RELEASE}/theme="
    
    # Available themes
    THEMES = [
        "addresses",
        "base",
        "buildings",
        "divisions",
        "places",
        "transportation"
    ]
    
    def __init__(self, data_dir: str = None, use_azure: bool = True):
        """Initialize the Overture Maps interface.
        
        Args:
            data_dir: Directory for storing downloaded data
            use_azure: Whether to use Azure (True) or AWS (False) as the data source
        """
        self.data_dir = Path(data_dir) if data_dir else Path("data/overture")
        self.use_azure = use_azure
        
        # Check for required tools
        if not use_azure:
            self._check_aws_cli()
        else:
            self._check_azcopy()
        
        # Initialize DuckDB connection for local processing
        self.con = duckdb.connect(database=":memory:")
        self.con.execute("INSTALL spatial;")
        self.con.execute("LOAD spatial;")
    
    def _check_aws_cli(self):
        """Check if AWS CLI is installed and accessible."""
        try:
            subprocess.run(['aws', '--version'], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE,
                         check=True)
        except FileNotFoundError:
            raise RuntimeError(
                "AWS CLI not found. Please install it first:\n"
                "  - macOS: brew install awscli\n"
                "  - Linux: sudo apt-get install awscli\n"
                "  - Windows: https://aws.amazon.com/cli/"
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"AWS CLI check failed: {e}")
    
    def _check_azcopy(self):
        """Check if AzCopy is installed and accessible."""
        try:
            subprocess.run(['azcopy', '--version'], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE,
                         check=True)
        except FileNotFoundError:
            raise RuntimeError(
                "AzCopy not found. Please install it first:\n"
                "  - Download from: https://aka.ms/downloadazcopy"
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"AzCopy check failed: {e}")
    
    def _download_with_aws(self, theme: str, theme_dir: Path) -> bool:
        """Download theme data using AWS CLI."""
        try:
            # Download files directly without listing first
            s3_path = f"{self.AWS_S3_BASE}{theme}"
            cmd = [
                "aws", "s3", "cp",
                "--region", "us-west-2",
                "--no-sign-request",
                "--recursive",
                s3_path,
                str(theme_dir)
            ]
            
            logger.info(f"Downloading from AWS: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Download output:\n{result.stdout}")
            
            # Verify files were downloaded
            all_files = list(theme_dir.rglob("*"))
            parquet_files = list(theme_dir.rglob("*.parquet"))
            logger.info(f"Found {len(all_files)} total files, {len(parquet_files)} parquet files in {theme_dir}")
            
            if not parquet_files:
                logger.error(f"No parquet files downloaded for theme {theme}")
                return False
                
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"AWS CLI download failed for theme='{theme}': {e}\nOutput: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Error downloading from AWS: {e}")
            return False
    
    def _download_with_azcopy(self, theme: str, theme_dir: Path) -> bool:
        """Download theme data using AzCopy."""
        try:
            # Full Azure path with theme
            azure_path = f"{self.AZURE_BLOB_BASE}{theme}"
            
            cmd = [
                "azcopy", "copy",
                azure_path,
                str(theme_dir),
                "--recursive"
            ]
            
            logger.info(f"Downloading from Azure: {' '.join(cmd)}")
            subprocess.check_call(cmd)  # Using check_call instead of run for simpler error handling
            
            # Verify files were downloaded
            all_files = list(theme_dir.rglob("*"))
            parquet_files = list(theme_dir.rglob("*.parquet"))
            logger.info(f"Found {len(all_files)} total files, {len(parquet_files)} parquet files in {theme_dir}")
            
            if not parquet_files:
                logger.error(f"No parquet files downloaded for theme {theme}")
                return False
                
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"AzCopy download failed for theme='{theme}':\n{e}")
            return False
        except Exception as e:
            logger.error(f"Error downloading from Azure: {e}")
            return False
    
    def download_theme(self, theme: str, bbox: Dict[str, float]) -> bool:
        """Download a theme using AWS CLI or AzCopy.
        
        Args:
            theme: Theme name
            bbox: Bounding box dictionary with xmin, ymin, xmax, ymax
        
        Returns:
            bool: True if download successful
        """
        if theme not in self.THEMES:
            logger.error(f"Invalid theme: {theme}")
            return False
            
        theme_dir = self.data_dir / theme
        theme_dir.mkdir(parents=True, exist_ok=True)
        
        # Remove existing files if they exist
        if theme_dir.exists():
            logger.info(f"Cleaning existing theme directory: {theme_dir}")
            shutil.rmtree(theme_dir)
            theme_dir.mkdir(parents=True)
        
        try:
            if self.use_azure:
                return self._download_with_azcopy(theme, theme_dir)
            else:
                return self._download_with_aws(theme, theme_dir)
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
            
            # Download themes
            results = {}
            for theme in self.THEMES:
                logger.info(f"\nDownloading {theme}...")
                results[theme] = self.download_theme(theme, bbox)
            
            return results
        except Exception as e:
            logger.error(f"Error during data download: {str(e)}")
            return {theme: False for theme in self.THEMES}
    
    async def search(self, bbox: Union[List[float], Dict[str, float]]) -> Dict[str, Any]:
        """
        Search Overture data within the given bounding box.
        
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
            
            # Convert bbox to WKT polygon for spatial filtering
            bbox_wkt = f"POLYGON(({bbox_dict['xmin']} {bbox_dict['ymin']}, {bbox_dict['xmin']} {bbox_dict['ymax']}, {bbox_dict['xmax']} {bbox_dict['ymax']}, {bbox_dict['xmax']} {bbox_dict['ymin']}, {bbox_dict['xmin']} {bbox_dict['ymin']}))"
            bbox_expr = f"ST_GeomFromText('{bbox_wkt}')"
            
            results = {}
            
            for theme in self.THEMES:
                theme_dir = self.data_dir / theme
                if not theme_dir.exists():
                    logger.warning(f"Theme directory not found: {theme_dir}")
                    results[theme] = []
                    continue
                
                # Look for downloaded parquet files
                parquet_files = list(theme_dir.glob("**/*.parquet"))  # Search recursively
                if not parquet_files:
                    logger.warning(f"No parquet files found in {theme_dir} or subdirectories")
                    results[theme] = []
                    continue
                
                logger.info(f"Found {len(parquet_files)} parquet files for {theme}")
                
                # Create query to filter by bbox
                parquet_paths = [str(f) for f in parquet_files]
                parquet_list = "', '".join(parquet_paths)
                query = f"""
                SELECT *
                FROM read_parquet(
                    ['{parquet_list}']
                )
                WHERE ST_Intersects(
                    ST_GeomFromGeoJSON(geometry),
                    {bbox_expr}
                )
                LIMIT 1000;
                """
                
                try:
                    # Execute query and fetch results
                    logger.info(f"Executing query for {theme}...")
                    df = self.con.execute(query).fetchdf()
                    results[theme] = df.to_dict('records')
                    logger.info(f"Found {len(results[theme])} {theme} features")
                except Exception as e:
                    logger.warning(f"Error querying {theme}: {str(e)}")
                    results[theme] = []
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching Overture data: {str(e)}")
            return {theme: [] for theme in self.THEMES}
    
    def __del__(self):
        """Clean up DuckDB connection."""
        if hasattr(self, 'con'):
            self.con.close()

#if __name__ == "__main__":
    # Run the analysis
    #error_details = index_overture_parquet()