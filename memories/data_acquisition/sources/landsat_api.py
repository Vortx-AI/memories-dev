"""
Landsat data source implementation.
"""

import os
from typing import Dict, List, Optional, Union, Any, Tuple
from pathlib import Path
import logging
from datetime import datetime
import numpy as np
import rasterio
from shapely.geometry import box, Polygon
import planetary_computer as pc
import pystac_client
import json
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LandsatAPI:
    """Interface for accessing Landsat data through Planetary Computer."""
    
    def __init__(
        self,
        cache_dir: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize Landsat client.
        
        Args:
            cache_dir: Directory for caching data
            timeout: Timeout for requests in seconds
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".landsat_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        
        # Initialize STAC catalog
        self.catalog = pystac_client.Client.open(
            "https://planetarycomputer.microsoft.com/api/stac/v1",
            modifier=pc.sign_inplace
        )
    
    def validate_bbox(self, bbox: Union[List[float], Tuple[float, float, float, float]]) -> None:
        """Validate bounding box format."""
        if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            raise ValueError("Bounding box must be a list/tuple of 4 coordinates [minx, miny, maxx, maxy]")
        try:
            minx, miny, maxx, maxy = map(float, bbox)
            if minx >= maxx or miny >= maxy:
                raise ValueError("Invalid bounding box coordinates")
        except (ValueError, TypeError):
            raise ValueError("Bounding box coordinates must be numeric")
    
    async def search(
        self,
        bbox: Union[List[float], Tuple[float, float, float, float], Polygon],
        start_date: str,
        end_date: str,
        cloud_cover: float = 20.0,
        limit: int = 10
    ) -> List[Dict]:
        """
        Search for Landsat scenes.
        
        Args:
            bbox: Bounding box [minx, miny, maxx, maxy] or Polygon
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            cloud_cover: Maximum cloud cover percentage
            limit: Maximum number of results
            
        Returns:
            List of matching scenes
        """
        try:
            # Convert bbox to list if it's a Polygon
            if isinstance(bbox, Polygon):
                bbox = list(bbox.bounds)
            else:
                self.validate_bbox(bbox)
            
            # Search for items
            search = self.catalog.search(
                collections=["landsat-8-c2-l2"],
                bbox=bbox,
                datetime=f"{start_date}/{end_date}",
                query={"eo:cloud_cover": {"lt": cloud_cover}},
                limit=limit
            )
            
            items = list(search.get_items())
            logger.info(f"Found {len(items)} items matching criteria")
            
            return items
            
        except Exception as e:
            logger.error(f"Error searching Landsat data: {e}")
            return []
    
    def get_cache_path(self, filename: str) -> Path:
        """Get path for cached file."""
        return self.cache_dir / filename
    
    async def download(
        self,
        item_id: str,
        output_dir: Union[str, Path],
        bands: Optional[List[str]] = None
    ) -> Optional[Path]:
        """
        Download Landsat data.
        
        Args:
            item_id: Scene ID or item dictionary
            output_dir: Directory to save downloaded data
            bands: List of bands to download (default: visible bands)
            
        Returns:
            Path to downloaded file
        """
        try:
            # Get cache path
            cache_path = self.get_cache_path(f"{item_id}.tif")
            if cache_path and cache_path.exists():
                logger.info(f"Using cached file: {cache_path}")
                return cache_path
            
            # Get item if ID provided
            if isinstance(item_id, str):
                search = self.catalog.search(
                    collections=["landsat-8-c2-l2"],
                    ids=[item_id]
                )
                items = list(search.get_items())
                if not items:
                    raise ValueError(f"Item {item_id} not found")
                item = items[0]
            else:
                item = item_id
            
            # Default bands if not specified
            if bands is None:
                bands = ["SR_B2", "SR_B3", "SR_B4"]  # RGB
            
            # Validate bands
            for band in bands:
                if band not in item['assets']:
                    raise ValueError(f"Band {band} not found in item assets")
            
            # Create output directory
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Download and merge bands
            band_data = []
            profile = None
            
            try:
                for band in bands:
                    href = item['assets'][band]['href']
                    signed_href = pc.sign(href)
                    
                    with rasterio.open(signed_href) as src:
                        band_data.append(src.read(1))
                        if profile is None:
                            profile = src.profile.copy()
                
                if not band_data:
                    raise ValueError("No band data downloaded")
                
                # Update profile for multi-band output
                profile.update(count=len(bands))
                
                # Save merged bands
                output_path = output_dir / f"{item['id']}.tif"
                with rasterio.open(output_path, 'w', **profile) as dst:
                    for i, data in enumerate(band_data, 1):
                        dst.write(data, i)
                
                return output_path
                
            except Exception as e:
                # Re-raise any rasterio or other errors
                raise Exception(f"Error processing band data: {str(e)}")
                
        except ValueError as e:
            logger.error(f"Error downloading Landsat data: {e}")
            raise
        except Exception as e:
            logger.error(f"Error downloading Landsat data: {e}")
            raise  # Re-raise the exception instead of returning None
    
    def get_metadata(self, item_id: str) -> Dict[str, Any]:
        """
        Get metadata for a Landsat scene.
        
        Args:
            item_id: Scene ID
            
        Returns:
            Dictionary containing metadata
        """
        try:
            # Search for item
            search = self.catalog.search(
                collections=["landsat-8-c2-l2"],
                ids=[item_id]
            )
            items = list(search.get_items())
            if not items:
                raise ValueError(f"Item {item_id} not found")
            
            item = items[0]
            
            # Extract metadata
            return {
                "id": item['id'],
                "datetime": item['properties']['datetime'].split('T')[0],
                "cloud_cover": item['properties']['eo:cloud_cover'],
                "platform": item['properties']['platform'],
                "instruments": item['properties']['instruments'],
                "path": item['properties']['landsat:path'],
                "row": item['properties']['landsat:row'],
                "bands": list(item['assets'].keys())
            }
            
        except Exception as e:
            logger.error(f"Error getting metadata: {e}")
            raise
    
    def get_available_collections(self) -> List[str]:
        """Get available Landsat collections."""
        try:
            collections = self.catalog.get_collections()
            return [
                collection.id for collection in collections
                if collection.id.startswith('landsat-')
            ]
        except Exception as e:
            logger.error(f"Error getting collections: {e}")
            return []
    
    async def search_and_download(
        self,
        bbox: Union[List[float], Tuple[float, float, float, float], Polygon],
        start_date: str,
        end_date: str,
        cloud_cover: float = 20.0,
        bands: Optional[List[str]] = None,
        output_dir: Optional[Union[str, Path]] = None
    ) -> Dict[str, Any]:
        """
        Search for and download Landsat data.
        
        Args:
            bbox: Bounding box [minx, miny, maxx, maxy] or Polygon
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            cloud_cover: Maximum cloud cover percentage
            bands: List of bands to download
            output_dir: Directory to save downloaded data
            
        Returns:
            Dictionary containing downloaded data and metadata
        """
        try:
            # Search for scenes
            items = await self.search(
                bbox=bbox,
                start_date=start_date,
                end_date=end_date,
                cloud_cover=cloud_cover
            )
            
            if not items:
                logger.warning("No items found matching criteria")
                return {}
            
            # Use first item (best match)
            item = items[0]
            
            # Set output directory
            if output_dir is None:
                output_dir = self.cache_dir
            
            # Download data
            output_path = await self.download(
                item_id=item['id'],
                output_dir=output_dir,
                bands=bands
            )
            
            if output_path and output_path.exists():
                # Read downloaded data
                with rasterio.open(output_path) as src:
                    data = src.read()
                
                return {
                    'data': data,
                    'metadata': {
                        'scene_id': item['id'],
                        'datetime': item['properties']['datetime'].split('T')[0],
                        'cloud_cover': item['properties']['eo:cloud_cover'],
                        'bands': bands or ["SR_B2", "SR_B3", "SR_B4"],
                        'crs': 'EPSG:32610',  # UTM zone 10N (San Francisco)
                        'transform': [30.0, 0.0, 0.0, 0.0, -30.0, 0.0]  # 30m resolution
                    }
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error processing Landsat data: {e}")
            return {}
    
    def cleanup_temp_files(self, path: Union[str, Path]):
        """Clean up temporary files."""
        try:
            path = Path(path)
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
        except Exception as e:
            logger.error(f"Error cleaning up temporary files: {e}") 