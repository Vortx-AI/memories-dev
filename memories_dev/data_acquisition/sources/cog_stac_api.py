"""
Cloud-Optimized GeoTIFF (COG) and STAC data source.
"""

import os
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
import logging
import json
import numpy as np
import rasterio
from rasterio.warp import transform_bounds
from shapely.geometry import box, Polygon
import pystac_client
import xarray as xr
import fsspec
import dask.array as da
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class COGSTACAPI:
    """Interface for accessing COG and STAC data."""
    
    def __init__(
        self,
        cache_dir: Optional[str] = None,
        max_workers: int = 4,
        enable_streaming: bool = True,
        chunk_size: int = 1024
    ):
        """
        Initialize COG/STAC data handler.
        
        Args:
            cache_dir: Directory for caching data
            max_workers: Maximum number of concurrent workers
            enable_streaming: Whether to enable data streaming
            chunk_size: Size of data chunks for streaming
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".cog_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_workers = max_workers
        self.enable_streaming = enable_streaming
        self.chunk_size = chunk_size
        
        # Initialize STAC catalogs
        self.catalogs = {
            "planetary_computer": {
                "url": "https://planetarycomputer.microsoft.com/api/stac/v1",
                "requires_auth": False
            },
            "earth_search": {
                "url": "https://earth-search.aws.element84.com/v0",
                "requires_auth": False
            },
            "google_earth_engine": {
                "url": "https://earthengine.googleapis.com/v1alpha/catalog",
                "requires_auth": True
            }
        }
        
        # Initialize clients
        self.clients = self._init_clients()
    
    def _init_clients(self) -> Dict:
        """Initialize STAC clients."""
        clients = {}
        for name, config in self.catalogs.items():
            try:
                if not config["requires_auth"]:
                    clients[name] = pystac_client.Client.open(config["url"])
                    logger.info(f"Successfully initialized STAC client: {name}")
            except Exception as e:
                logger.error(f"Failed to initialize STAC client {name}: {e}")
        return clients
    
    def search_collections(
        self,
        bbox: Union[Tuple[float, float, float, float], Polygon],
        start_date: str,
        end_date: str,
        query: Optional[Dict] = None,
        catalog: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for collections in STAC catalogs.
        
        Args:
            bbox: Bounding box or Polygon
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            query: Optional additional query parameters
            catalog: Optional specific catalog to search
            
        Returns:
            List of matching collections
        """
        if isinstance(bbox, Polygon):
            bbox = bbox.bounds
        
        results = []
        catalogs_to_search = (
            {catalog: self.clients[catalog]}
            if catalog and catalog in self.clients
            else self.clients
        )
        
        for name, client in catalogs_to_search.items():
            try:
                # Build search parameters
                search_params = {
                    "bbox": bbox,
                    "datetime": f"{start_date}/{end_date}"
                }
                if query:
                    search_params.update(query)
                
                # Search collections
                collections = client.get_collections()
                matching = []
                
                for collection in collections:
                    # Check temporal and spatial extent
                    if self._check_collection_extent(
                        collection,
                        bbox,
                        start_date,
                        end_date
                    ):
                        matching.append({
                            "catalog": name,
                            "id": collection.id,
                            "title": collection.title,
                            "description": collection.description,
                            "license": collection.license,
                            "extent": {
                                "spatial": collection.extent.spatial.bboxes,
                                "temporal": collection.extent.temporal.intervals
                            }
                        })
                
                results.extend(matching)
                
            except Exception as e:
                logger.error(f"Error searching {name} catalog: {e}")
        
        return results
    
    def get_cog_data(
        self,
        url: str,
        bbox: Union[Tuple[float, float, float, float], Polygon],
        bands: Optional[List[int]] = None,
        resolution: Optional[float] = None,
        masked: bool = True
    ) -> Dict:
        """
        Get data from a Cloud-Optimized GeoTIFF.
        
        Args:
            url: URL of the COG file
            bbox: Bounding box or Polygon
            bands: Optional list of band indices
            resolution: Optional target resolution
            masked: Whether to mask nodata values
            
        Returns:
            Dictionary containing data and metadata
        """
        try:
            # Open COG file
            with rasterio.open(url) as src:
                # Get transform for bbox
                if isinstance(bbox, Polygon):
                    bbox = bbox.bounds
                
                bounds = transform_bounds(
                    "EPSG:4326",
                    src.crs,
                    *bbox
                )
                
                # Calculate window
                window = src.window(*bounds)
                
                # Read data
                if bands is None:
                    bands = list(range(1, src.count + 1))
                
                if self.enable_streaming:
                    # Stream data in chunks
                    data = self._stream_cog_data(
                        src,
                        window,
                        bands,
                        resolution
                    )
                else:
                    # Read all at once
                    data = src.read(
                        bands,
                        window=window,
                        masked=masked
                    )
                
                # Get metadata
                metadata = {
                    "crs": src.crs.to_string(),
                    "transform": src.transform.to_gdal(),
                    "bounds": src.bounds,
                    "resolution": src.res,
                    "nodata": src.nodata,
                    "dtype": str(src.dtypes[0]),
                    "count": len(bands)
                }
                
                return {
                    "data": data,
                    "metadata": metadata
                }
                
        except Exception as e:
            logger.error(f"Error reading COG data: {e}")
            raise
    
    def _stream_cog_data(
        self,
        src: rasterio.DatasetReader,
        window: rasterio.windows.Window,
        bands: List[int],
        resolution: Optional[float] = None
    ) -> np.ndarray:
        """Stream COG data in chunks."""
        # Calculate chunk size in pixels
        chunk_pixels = self.chunk_size
        
        # Calculate number of chunks
        width = int(window.width)
        height = int(window.height)
        
        x_chunks = (width + chunk_pixels - 1) // chunk_pixels
        y_chunks = (height + chunk_pixels - 1) // chunk_pixels
        
        # Create dask array
        chunks = []
        for band in bands:
            band_chunks = []
            for y in range(y_chunks):
                row_chunks = []
                for x in range(x_chunks):
                    # Calculate chunk window
                    chunk_window = rasterio.windows.Window(
                        x * chunk_pixels,
                        y * chunk_pixels,
                        min(chunk_pixels, width - x * chunk_pixels),
                        min(chunk_pixels, height - y * chunk_pixels)
                    )
                    
                    # Create delayed read
                    chunk = da.from_delayed(
                        src.read(
                            band,
                            window=chunk_window,
                            masked=True
                        ),
                        shape=(chunk_window.height, chunk_window.width),
                        dtype=src.dtypes[band - 1]
                    )
                    
                    row_chunks.append(chunk)
                
                band_chunks.append(da.concatenate(row_chunks, axis=1))
            
            chunks.append(da.concatenate(band_chunks, axis=0))
        
        # Stack bands
        data = da.stack(chunks, axis=0)
        
        # Compute if resolution is specified
        if resolution is not None:
            scale_factor = src.res[0] / resolution
            if scale_factor != 1:
                data = data.map_overlap(
                    lambda x: self._resize_chunk(x, scale_factor),
                    depth=1
                )
        
        return data.compute()
    
    def _resize_chunk(
        self,
        chunk: np.ndarray,
        scale_factor: float
    ) -> np.ndarray:
        """Resize a data chunk."""
        import cv2
        
        if chunk.ndim == 2:
            return cv2.resize(
                chunk,
                None,
                fx=scale_factor,
                fy=scale_factor,
                interpolation=cv2.INTER_CUBIC
            )
        else:
            resized = np.zeros(
                (
                    chunk.shape[0],
                    int(chunk.shape[1] * scale_factor),
                    int(chunk.shape[2] * scale_factor)
                ),
                dtype=chunk.dtype
            )
            
            for i in range(chunk.shape[0]):
                resized[i] = cv2.resize(
                    chunk[i],
                    None,
                    fx=scale_factor,
                    fy=scale_factor,
                    interpolation=cv2.INTER_CUBIC
                )
            
            return resized
    
    def _check_collection_extent(
        self,
        collection: pystac_client.Collection,
        bbox: Tuple[float, float, float, float],
        start_date: str,
        end_date: str
    ) -> bool:
        """Check if collection covers requested extent."""
        # Check spatial extent
        collection_bbox = collection.extent.spatial.bboxes[0]
        if not self._bbox_intersects(bbox, collection_bbox):
            return False
        
        # Check temporal extent
        collection_interval = collection.extent.temporal.intervals[0]
        if not self._date_in_range(
            start_date,
            end_date,
            collection_interval[0],
            collection_interval[1]
        ):
            return False
        
        return True
    
    def _bbox_intersects(
        self,
        bbox1: Tuple[float, float, float, float],
        bbox2: Tuple[float, float, float, float]
    ) -> bool:
        """Check if two bounding boxes intersect."""
        return not (
            bbox1[2] < bbox2[0] or
            bbox1[0] > bbox2[2] or
            bbox1[3] < bbox2[1] or
            bbox1[1] > bbox2[3]
        )
    
    def _date_in_range(
        self,
        start_date: str,
        end_date: str,
        range_start: str,
        range_end: str
    ) -> bool:
        """Check if dates overlap with range."""
        from datetime import datetime
        
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        range_start = datetime.strptime(range_start[:10], "%Y-%m-%d")
        range_end = datetime.strptime(
            range_end[:10] if range_end else "9999-12-31",
            "%Y-%m-%d"
        )
        
        return start <= range_end and end >= range_start 