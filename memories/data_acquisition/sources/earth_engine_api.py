"""
Google Earth Engine data source for satellite imagery.
"""

import os
from typing import Dict, List, Optional, Tuple, Union
import ee
import numpy as np
from shapely.geometry import box, Polygon, mapping
from datetime import datetime
import rasterio
from rasterio.warp import transform_bounds
import json
import tempfile
import requests

class EarthEngineAPI:
    """Interface for accessing Google Earth Engine data."""
    
    def __init__(
        self,
        service_account: Optional[str] = None,
        key_file: Optional[str] = None,
        cache_dir: Optional[str] = None
    ):
        """
        Initialize Earth Engine API.
        
        Args:
            service_account: Service account email
            key_file: Path to service account key file
            cache_dir: Directory for caching data
        """
        self.cache_dir = cache_dir or os.path.join(os.path.expanduser("~"), ".earthengine")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialize Earth Engine
        if service_account and key_file:
            credentials = ee.ServiceAccountCredentials(service_account, key_file)
            ee.Initialize(credentials)
        else:
            ee.Initialize()
        
        # Available collections
        self.collections = {
            "sentinel-2": {
                "id": "COPERNICUS/S2_SR",
                "resolution": 10,
                "bands": ["B2", "B3", "B4", "B8"],
                "scale_factor": 0.0001
            },
            "landsat-8": {
                "id": "LANDSAT/LC08/C02/T1_L2",
                "resolution": 30,
                "bands": ["SR_B2", "SR_B3", "SR_B4", "SR_B5"],
                "scale_factor": 0.0000275
            },
            "modis": {
                "id": "MODIS/006/MOD09GA",
                "resolution": 500,
                "bands": ["sur_refl_b01", "sur_refl_b02", "sur_refl_b03", "sur_refl_b04"],
                "scale_factor": 0.0001
            }
        }
    
    def search_and_download(
        self,
        bbox: Union[Tuple[float, float, float, float], Polygon],
        start_date: str,
        end_date: str,
        collections: List[str] = ["sentinel-2"],
        cloud_cover: float = 20.0,
        max_items: int = 1
    ) -> Dict:
        """
        Search and download satellite imagery.
        
        Args:
            bbox: Bounding box or Polygon
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            collections: List of collections to search
            cloud_cover: Maximum cloud cover percentage
            max_items: Maximum number of items to return
            
        Returns:
            Dictionary containing downloaded data and metadata
        """
        results = {}
        
        # Convert bbox to ee.Geometry
        if isinstance(bbox, tuple):
            geometry = ee.Geometry.Rectangle(bbox)
        else:
            geometry = ee.Geometry.Polygon(bbox.exterior.coords)
        
        for collection_name in collections:
            if collection_name not in self.collections:
                continue
            
            collection_info = self.collections[collection_name]
            
            try:
                # Get collection
                collection = ee.ImageCollection(collection_info["id"])
                
                # Filter collection
                filtered = (collection
                    .filterBounds(geometry)
                    .filterDate(start_date, end_date)
                    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_cover))
                    .sort("CLOUDY_PIXEL_PERCENTAGE")
                    .limit(max_items))
                
                # Get images
                images = filtered.toList(max_items)
                
                collection_results = []
                for i in range(min(max_items, filtered.size().getInfo())):
                    image = ee.Image(images.get(i))
                    
                    # Get image data
                    data = self._get_image_data(
                        image,
                        geometry,
                        collection_info
                    )
                    
                    if data:
                        collection_results.append(data)
                
                if collection_results:
                    results[collection_name] = collection_results
                
            except Exception as e:
                print(f"Error processing {collection_name}: {e}")
        
        return results
    
    def _get_image_data(
        self,
        image: ee.Image,
        geometry: ee.Geometry,
        collection_info: Dict
    ) -> Optional[Dict]:
        """Get data for a single image."""
        try:
            # Select bands
            image = image.select(collection_info["bands"])
            
            # Get image properties
            properties = image.getInfo()["properties"]
            
            # Get download URL
            url = image.getDownloadURL({
                "region": geometry,
                "scale": collection_info["resolution"],
                "format": "GEO_TIFF",
                "bands": collection_info["bands"]
            })
            
            # Download data
            with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp:
                response = requests.get(url)
                tmp.write(response.content)
                tmp_path = tmp.name
            
            try:
                # Read data
                with rasterio.open(tmp_path) as src:
                    data = src.read()
                    
                    # Apply scale factor
                    data = data * collection_info["scale_factor"]
                    
                    return {
                        "data": data,
                        "metadata": {
                            "datetime": properties.get("system:time_start"),
                            "cloud_cover": properties.get("CLOUDY_PIXEL_PERCENTAGE"),
                            "bands": collection_info["bands"],
                            "resolution": collection_info["resolution"],
                            "crs": src.crs.to_string(),
                            "transform": src.transform.to_gdal(),
                            "bounds": src.bounds
                        }
                    }
            
            finally:
                # Cleanup
                os.unlink(tmp_path)
            
        except Exception as e:
            print(f"Error downloading image: {e}")
            return None
    
    def get_time_series(
        self,
        bbox: Union[Tuple[float, float, float, float], Polygon],
        start_date: str,
        end_date: str,
        collection: str,
        band: str,
        temporal_resolution: str = "month"
    ) -> Dict:
        """
        Get time series data.
        
        Args:
            bbox: Bounding box or Polygon
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            collection: Collection name
            band: Band name
            temporal_resolution: Temporal resolution ("day", "week", "month")
            
        Returns:
            Dictionary containing time series data
        """
        if collection not in self.collections:
            raise ValueError(f"Unknown collection: {collection}")
            
        collection_info = self.collections[collection]
        
        # Convert bbox to ee.Geometry
        if isinstance(bbox, tuple):
            geometry = ee.Geometry.Rectangle(bbox)
        else:
            geometry = ee.Geometry.Polygon(bbox.exterior.coords)
        
        # Get collection
        ee_collection = ee.ImageCollection(collection_info["id"])
        
        # Filter collection
        filtered = (ee_collection
            .filterBounds(geometry)
            .filterDate(start_date, end_date)
            .select([band]))
        
        # Aggregate by temporal resolution
        if temporal_resolution == "month":
            reducer = ee.Reducer.mean()
            temporal = filtered.map(
                lambda img: img.set("month", ee.Date(img.get("system:time_start")).format("YYYY-MM"))
            )
            aggregated = ee.ImageCollection(
                temporal.reduceColumns(
                    reducer=reducer,
                    selectors=["month"]
                )
            )
        else:
            aggregated = filtered
        
        # Get time series
        values = aggregated.getRegion(
            geometry=geometry,
            scale=collection_info["resolution"]
        ).getInfo()
        
        # Convert to dictionary
        headers = values[0]
        data = values[1:]
        
        time_series = {
            "timestamps": [row[0] for row in data],
            "values": [row[4] * collection_info["scale_factor"] for row in data],
            "metadata": {
                "band": band,
                "resolution": collection_info["resolution"],
                "temporal_resolution": temporal_resolution
            }
        }
        
        return time_series
    
    def get_available_collections(self) -> List[Dict]:
        """Get list of available collections."""
        return [
            {
                "name": name,
                "id": info["id"],
                "resolution": info["resolution"],
                "bands": info["bands"]
            }
            for name, info in self.collections.items()
        ]
    
    def add_collection(
        self,
        name: str,
        collection_id: str,
        resolution: float,
        bands: List[str],
        scale_factor: float = 1.0
    ):
        """
        Add a new collection.
        
        Args:
            name: Collection name
            collection_id: Earth Engine collection ID
            resolution: Spatial resolution in meters
            bands: List of band names
            scale_factor: Scale factor for data values
        """
        self.collections[name] = {
            "id": collection_id,
            "resolution": resolution,
            "bands": bands,
            "scale_factor": scale_factor
        } 