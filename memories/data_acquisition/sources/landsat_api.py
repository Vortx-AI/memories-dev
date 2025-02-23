"""
Landsat API data source for satellite imagery using Planetary Computer.
"""

import os
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime
import planetary_computer as pc
import pystac_client
import rasterio
import numpy as np
from shapely.geometry import box, Polygon, mapping
from rasterio.warp import transform_bounds
import logging
from pathlib import Path
from .base import DataSource

class LandsatAPI(DataSource):
    """Interface for Landsat data access through Planetary Computer."""
    
    def __init__(self, token: Optional[str] = None, cache_dir: Optional[str] = None):
        """
        Initialize Landsat interface.
        
        Args:
            token: Planetary Computer API token
            cache_dir: Optional directory for caching data
        """
        super().__init__(cache_dir)
        self.token = token or os.getenv("PLANETARY_COMPUTER_API_KEY")
        if self.token:
            pc.settings.set_subscription_key(self.token)
        
        self.logger = logging.getLogger(__name__)
        self.catalog = pystac_client.Client.open(
            "https://planetarycomputer.microsoft.com/api/stac/v1",
            modifier=pc.sign_inplace
        )
    
    async def search(self,
                    bbox: List[float],
                    start_date: str,
                    end_date: str,
                    collection: str = "landsat-8-c2-l2",
                    cloud_cover: float = 20.0,
                    limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for Landsat scenes.
        
        Args:
            bbox: Bounding box coordinates [west, south, east, north]
            start_date: Start date in ISO format
            end_date: End date in ISO format
            collection: Collection ID (e.g., "landsat-8-c2-l2")
            cloud_cover: Maximum cloud cover percentage
            limit: Maximum number of results
            
        Returns:
            List of scene metadata
        """
        self.validate_bbox(bbox)
        
        search = self.catalog.search(
            collections=[collection],
            bbox=bbox,
            datetime=f"{start_date}/{end_date}",
            query={"eo:cloud_cover": {"lt": cloud_cover}},
            limit=limit
        )
        
        items = list(search.get_items())
        self.logger.info(f"Found {len(items)} items matching criteria")
        return items
    
    async def download(self,
                      item_id: str,
                      output_dir: Path,
                      bands: List[str] = ["SR_B2", "SR_B3", "SR_B4", "SR_B5"]) -> Path:
        """
        Download Landsat scene.
        
        Args:
            item_id: Item identifier or STAC item
            output_dir: Directory to save output
            bands: List of bands to download
            
        Returns:
            Path to downloaded file
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check cache
        cache_path = self.get_cache_path(f"{item_id}.tif")
        if cache_path and cache_path.exists():
            self.logger.info(f"Using cached file: {cache_path}")
            return cache_path
        
        # Get item if ID was provided
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
        
        # Download and merge bands
        band_arrays = []
        for band in bands:
            if band not in item.assets:
                raise ValueError(f"Band {band} not found in item assets")
                
            href = item.assets[band].href
            signed_href = pc.sign(href)
            
            with rasterio.open(signed_href) as src:
                band_arrays.append(src.read(1))
                profile = src.profile
        
        # Create multi-band image
        output_path = output_dir / f"{item.id}.tif"
        profile.update(count=len(bands))
        with rasterio.open(output_path, 'w', **profile) as dst:
            for i, array in enumerate(band_arrays, 1):
                dst.write(array, i)
        
        # Cache the result if caching is enabled
        if cache_path:
            output_path.rename(cache_path)
            output_path = cache_path
        
        self.logger.info(f"Saved image to {output_path}")
        return output_path
    
    def get_metadata(self, item_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a scene.
        
        Args:
            item_id: Item identifier
            
        Returns:
            Dictionary containing scene information
        """
        search = self.catalog.search(
            collections=["landsat-8-c2-l2"],
            ids=[item_id]
        )
        items = list(search.get_items())
        if not items:
            raise ValueError(f"Item {item_id} not found")
        
        item = items[0]
        return {
            "id": item.id,
            "datetime": item.datetime.strftime("%Y-%m-%d"),
            "cloud_cover": float(item.properties.get("eo:cloud_cover", 0)),
            "platform": item.properties.get("platform", ""),
            "instrument": item.properties.get("instruments", []),
            "bands": list(item.assets.keys()),
            "bbox": item.bbox,
            "collection": item.collection_id,
            "path": item.properties.get("landsat:path", ""),
            "row": item.properties.get("landsat:row", "")
        }
    
    def get_available_collections(self) -> List[str]:
        """Get list of available Landsat collections."""
        collections = self.catalog.get_collections()
        return [c.id for c in collections if c.id.startswith("landsat-")]

    def search_and_download(
        self,
        bbox: Union[Tuple[float, float, float, float], Polygon],
        start_date: str,
        end_date: str,
        cloud_cover: float = 20.0,
        dataset: str = "landsat_ot_c2_l2"  # Landsat 8-9 Collection 2 Level-2
    ) -> Dict:
        """
        Search and download Landsat imagery.
        
        Args:
            bbox: Bounding box or Polygon
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            cloud_cover: Maximum cloud cover percentage
            dataset: Landsat dataset name
            
        Returns:
            Dictionary containing downloaded data and metadata
        """
        try:
            # Convert bbox to coordinates
            if isinstance(bbox, tuple):
                minx, miny, maxx, maxy = bbox
            else:
                minx, miny, maxx, maxy = bbox.bounds
            
            # Search for scenes
            scenes = self.catalog.search(
                collections=[dataset],
                bbox=(minx, miny, maxx, maxy),
                datetime=f"{start_date}/{end_date}",
                query={"eo:cloud_cover": {"lt": cloud_cover}}
            )
            
            if not scenes:
                return {}
            
            # Sort by cloud cover and get best scene
            scenes = sorted(scenes.get_items(), key=lambda x: float(x.properties.get("eo:cloud_cover", 100)))
            best_scene = scenes[0]
            
            # Download scene
            scene_id = best_scene.id
            download_path = os.path.join("temp_downloads", f"{scene_id}.tif")
            os.makedirs("temp_downloads", exist_ok=True)
            
            self.download(scene_id, "temp_downloads")
            
            # Process downloaded data
            result = self._process_landsat(
                download_path,
                bbox if isinstance(bbox, Polygon) else box(*bbox),
                best_scene
            )
            
            # Cleanup
            os.remove(download_path)
            
            return result
            
        except Exception as e:
            print(f"Error processing Landsat data: {e}")
            if os.path.exists(download_path):
                os.remove(download_path)
            return {}
    
    def _process_landsat(
        self,
        product_path: str,
        bbox: Union[Polygon, box],
        scene_info: Dict
    ) -> Dict:
        """Process Landsat data."""
        # Extract tar.gz file
        import tarfile
        extract_path = os.path.join("temp_downloads", "extracted")
        os.makedirs(extract_path, exist_ok=True)
        
        with tarfile.open(product_path) as tar:
            tar.extractall(path=extract_path)
        
        try:
            # Get required bands (2=Blue, 3=Green, 4=Red, 5=NIR)
            bands = ["B2", "B3", "B4", "B5"]
            data_arrays = []
            
            for band in bands:
                # Find band file
                band_file = next(
                    (f for f in os.listdir(extract_path)
                     if f.endswith(f"_{band}.TIF")),
                    None
                )
                
                if not band_file:
                    raise ValueError(f"Band {band} not found")
                
                band_path = os.path.join(extract_path, band_file)
                
                with rasterio.open(band_path) as src:
                    # Reproject bbox if needed
                    bounds = transform_bounds(
                        "EPSG:4326",
                        src.crs,
                        *bbox.bounds
                    )
                    
                    # Read data
                    window = src.window(*bounds)
                    data = src.read(1, window=window)
                    data_arrays.append(data)
            
            # Stack bands
            stacked_data = np.stack(data_arrays)
            
            return {
                "data": stacked_data,
                "metadata": {
                    "datetime": scene_info.datetime.strftime("%Y-%m-%d"),
                    "cloud_cover": float(scene_info.properties.get("eo:cloud_cover", 0)),
                    "bands": bands,
                    "resolution": 30.0,
                    "crs": "EPSG:32633",  # UTM zone for the data
                    "bounds": bbox.bounds,
                    "scene_id": scene_info.id
                }
            }
            
        finally:
            # Cleanup extracted files
            import shutil
            shutil.rmtree(extract_path) 