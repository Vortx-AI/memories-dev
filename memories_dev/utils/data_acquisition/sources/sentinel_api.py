"""
Sentinel API data source for satellite imagery.
"""

import os
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime
import rasterio
import numpy as np
from shapely.geometry import box, Polygon, mapping
from sentinelsat.sentinel import SentinelAPI  # Direct import from sentinel module
from rasterio.warp import transform_bounds
import json

class CustomSentinelAPI:
    """Interface for accessing data from Copernicus Open Access Hub."""
    
    def __init__(
        self,
        user: Optional[str] = None,
        password: Optional[str] = None,
        api_url: str = "https://scihub.copernicus.eu/dhus"
    ):
        """
        Initialize Sentinel API client.
        
        Args:
            user: Copernicus Hub username
            password: Copernicus Hub password
            api_url: API endpoint URL
        """
        self.user = user or os.getenv("COPERNICUS_USER")
        self.password = password or os.getenv("COPERNICUS_PASSWORD")
        
        if not (self.user and self.password):
            raise ValueError("Copernicus credentials required")
        
        # Create API instance using direct import
        self._api = SentinelAPI(
            self.user,
            self.password,
            api_url
        )
        
    @property
    def api(self):
        """Access the underlying API instance"""
        return self._api
    
    def search_and_download(
        self,
        bbox: Union[Tuple[float, float, float, float], Polygon],
        start_date: str,
        end_date: str,
        cloud_cover: float = 20.0,
        product_type: str = "S2MSI2A"  # Sentinel-2 L2A
    ) -> Dict:
        """
        Search and download Sentinel imagery.
        
        Args:
            bbox: Bounding box or Polygon
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            cloud_cover: Maximum cloud cover percentage
            product_type: Sentinel product type
            
        Returns:
            Dictionary containing downloaded data and metadata
        """
        # Convert bbox to WKT
        if isinstance(bbox, tuple):
            footprint = box(*bbox)
        else:
            footprint = bbox
        area_wkt = footprint.wkt
        
        # Search for products
        products = self.api.query(
            area=area_wkt,
            date=(start_date, end_date),
            platformname="Sentinel-2",
            producttype=product_type,
            cloudcoverpercentage=(0, cloud_cover)
        )
        
        if not products:
            return {}
        
        # Sort by cloud cover and get best scene
        products_df = self.api.to_dataframe(products)
        products_df = products_df.sort_values("cloudcoverpercentage")
        best_product = products_df.iloc[0]
        
        # Download product
        product_info = self.api.download(
            best_product.uuid,
            directory_path="temp_downloads"
        )
        
        try:
            # Process downloaded data
            result = self._process_sentinel2(
                product_info["path"],
                bbox,
                best_product
            )
            
            # Cleanup
            os.remove(product_info["path"])
            
            return result
            
        except Exception as e:
            print(f"Error processing Sentinel data: {e}")
            if os.path.exists(product_info["path"]):
                os.remove(product_info["path"])
            return {}
    
    def _process_sentinel2(
        self,
        product_path: str,
        bbox: Union[Polygon, box],
        product_info: Dict
    ) -> Dict:
        """Process Sentinel-2 data."""
        # Get required bands (B2, B3, B4, B8)
        bands = ["B02", "B03", "B04", "B08"]
        data_arrays = []
        
        with rasterio.open(product_path) as src:
            # Reproject bbox if needed
            bounds = transform_bounds(
                "EPSG:4326",
                src.crs,
                *bbox.bounds
            )
            
            for band in bands:
                # Find band index
                band_idx = [i for i, desc in enumerate(src.descriptions)
                          if band in desc][0] + 1
                
                # Read data
                window = src.window(*bounds)
                data = src.read(band_idx, window=window)
                data_arrays.append(data)
        
        # Stack bands
        stacked_data = np.stack(data_arrays)
        
        return {
            "data": stacked_data,
            "metadata": {
                "datetime": product_info.beginposition.strftime("%Y-%m-%d"),
                "cloud_cover": float(product_info.cloudcoverpercentage),
                "bands": bands,
                "resolution": 10.0,
                "crs": "EPSG:32632",  # UTM zone for the data
                "bounds": bbox.bounds,
                "product_id": product_info.uuid
            }
        }
    
    def get_product_info(self, product_id: str) -> Dict:
        """Get detailed information about a product."""
        product = self.api.get_product_odata(product_id)
        return {
            "id": product["id"],
            "title": product["title"],
            "size": product["size"],
            "footprint": product["footprint"],
            "date": product["beginposition"],
            "cloud_cover": product["cloudcoverpercentage"],
            "product_type": product["producttype"]
        }
    
    def get_download_progress(self, product_id: str) -> Dict:
        """Get download progress for a product."""
        return self.api.get_download_progress(product_id) 
