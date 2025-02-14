"""
Landsat API data source for satellite imagery.
"""

import os
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime
import rasterio
import numpy as np
from shapely.geometry import box, Polygon, mapping
import landsatxplore.api
import landsatxplore.earthexplorer as ee
from rasterio.warp import transform_bounds

class LandsatAPI:
    """Interface for accessing data from USGS Earth Explorer."""
    
    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        Initialize Landsat API client.
        
        Args:
            username: USGS Earth Explorer username
            password: USGS Earth Explorer password
        """
        self.username = username or os.getenv("USGS_USERNAME")
        self.password = password or os.getenv("USGS_PASSWORD")
        
        if not (self.username and self.password):
            raise ValueError("USGS credentials required")
        
        self.api = landsatxplore.api.API(self.username, self.password)
        self.ee = ee.EarthExplorer(self.username, self.password)
    
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
            scenes = self.api.search(
                dataset=dataset,
                bbox=(minx, miny, maxx, maxy),
                start_date=start_date,
                end_date=end_date,
                max_cloud_cover=cloud_cover
            )
            
            if not scenes:
                return {}
            
            # Sort by cloud cover and get best scene
            scenes = sorted(scenes, key=lambda x: float(x["cloud_cover"]))
            best_scene = scenes[0]
            
            # Download scene
            scene_id = best_scene["entity_id"]
            download_path = os.path.join("temp_downloads", f"{scene_id}.tar.gz")
            os.makedirs("temp_downloads", exist_ok=True)
            
            self.ee.download(scene_id, output_dir="temp_downloads")
            
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
        
        finally:
            # Logout from Earth Explorer
            self.ee.logout()
    
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
                    "datetime": scene_info["acquisition_date"],
                    "cloud_cover": float(scene_info["cloud_cover"]),
                    "bands": bands,
                    "resolution": 30.0,
                    "crs": "EPSG:32633",  # UTM zone for the data
                    "bounds": bbox.bounds,
                    "scene_id": scene_info["entity_id"]
                }
            }
            
        finally:
            # Cleanup extracted files
            import shutil
            shutil.rmtree(extract_path)
    
    def get_datasets(self) -> List[Dict]:
        """Get list of available Landsat datasets."""
        return self.api.get_datasets()
    
    def get_scene_info(self, scene_id: str, dataset: str) -> Dict:
        """Get detailed information about a scene."""
        return self.api.get_scene_info(scene_id, dataset)
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.api.logout()
            if hasattr(self, "ee"):
                self.ee.logout()
        except:
            pass 