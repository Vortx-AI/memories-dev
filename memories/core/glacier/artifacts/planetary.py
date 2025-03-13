"""
Interface to Microsoft Planetary Computer.
"""

import os
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path

import planetary_computer as pc
import pystac_client
import rasterio
import numpy as np
from shapely.geometry import box, Polygon, mapping
import xarray as xr
from rasterio.warp import transform_bounds
from pystac.item import Item
from memories.core.glacier.artifacts import DataSource
from memories.core.cold import ColdMemory

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def serialize_datetime(obj):
    """Helper function to serialize datetime objects."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj

class PlanetaryConnector(DataSource):
    """Interface to Microsoft Planetary Computer."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize Planetary Computer client.
        
        Args:
            cache_dir: Optional directory for caching data
        """
        super().__init__(cache_dir)
        self.logger.info("Initializing PlanetaryConnector")
        
        try:
            self.logger.info("Connecting to Planetary Computer STAC API...")
            self.catalog = pystac_client.Client.open(
                "https://planetarycomputer.microsoft.com/api/stac/v1",
                modifier=pc.sign_inplace
            )
            self.logger.info("Successfully connected to Planetary Computer STAC API")
            
            self.cold_memory = ColdMemory()
            # Add cold attribute for backward compatibility
            self.cold = self.cold_memory
            self.logger.info(f"Initialized cold storage at: {self.cold_memory.raw_data_path}")
            
        except Exception as e:
            self.logger.error(f"Error initializing PlanetaryConnector: {e}", exc_info=True)
            raise
    
    def validate_bbox(self, bbox: List[float]) -> bool:
        """
        Validate bounding box format.
        
        Args:
            bbox: List of coordinates [west, south, east, north]
            
        Returns:
            bool: True if valid, raises ValueError if invalid
        """
        if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            raise ValueError("bbox must be a list/tuple of 4 coordinates")
        
        west, south, east, north = bbox
        if not all(isinstance(x, (int, float)) for x in [west, south, east, north]):
            raise ValueError("bbox coordinates must be numbers")
            
        if not (-180 <= west <= 180 and -180 <= east <= 180):
            raise ValueError("longitude must be between -180 and 180")
            
        if not (-90 <= south <= 90 and -90 <= north <= 90):
            raise ValueError("latitude must be between -90 and 90")
            
        return True
    
    async def search(self,
                    bbox: List[float],
                    start_date: str,
                    end_date: str,
                    collection: str = "sentinel-2-l2a",
                    cloud_cover: float = 20.0,
                    limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for satellite imagery.
        
        Args:
            bbox: Bounding box coordinates [west, south, east, north]
            start_date: Start date in ISO format
            end_date: End date in ISO format
            collection: Collection ID (e.g., "sentinel-2-l2a")
            cloud_cover: Maximum cloud cover percentage
            limit: Maximum number of results
            
        Returns:
            List of STAC items
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
                      item: Dict[str, Any],
                      output_dir: Path,
                      bands: List[str] = ["B02", "B03", "B04"]) -> Path:
        """
        Download and process satellite imagery.
        
        Args:
            item: STAC item
            output_dir: Directory to save output
            bands: List of band names to download
            
        Returns:
            Path to downloaded file
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create output filename
        item_id = item.get('id', 'unnamed')
        output_path = output_dir / f"{item_id}.tif"
        
        # Check cache
        cache_path = self.get_cache_path(f"{item_id}.tif")
        if cache_path and cache_path.exists():
            self.logger.info(f"Using cached file: {cache_path}")
            return cache_path
        
        # Download and merge bands
        band_arrays = []
        for band in bands:
            if band not in item['assets']:
                raise ValueError(f"Band {band} not found in item assets")
                
            href = item['assets'][band].href
            signed_href = pc.sign(href)
            
            with rasterio.open(signed_href) as src:
                band_arrays.append(src.read(1))
                profile = src.profile
        
        # Create multi-band image
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
    
    async def store_in_cold_memory(self, item: Dict[str, Any], data: np.ndarray, bands: List[str]) -> bool:
        """Store downloaded data in cold memory.
        
        Args:
            item: STAC item metadata
            data: Downloaded data array
            bands: List of band names
            
        Returns:
            bool: True if successful
        """
        try:
            # Create a unique identifier for this data
            item_id = item['id']
            timestamp = item.get('datetime', datetime.now().isoformat())
            
            # Create planetary directory
            planetary_dir = Path(self.cold_memory.raw_data_path) / "planetary"
            planetary_dir.mkdir(parents=True, exist_ok=True)
            
            # Create collection-specific directory
            collection_dir = planetary_dir / item.get('collection', 'unknown')
            collection_dir.mkdir(parents=True, exist_ok=True)
            
            # Prepare metadata
            metadata = {
                "id": f"planetary_{item_id}_{timestamp}",
                "type": "planetary_computer",
                "collection": item.get('collection'),
                "datetime": timestamp,
                "bbox": item.get('bbox'),
                "bands": bands,
                "cloud_cover": item.get('properties', {}).get('eo:cloud_cover'),
                "platform": item.get('properties', {}).get('platform'),
                "instrument": item.get('properties', {}).get('instruments'),
                "processing_level": item.get('properties', {}).get('processing:level'),
                "shape": data.shape
            }
            
            # Save the array to a file in the collection directory
            data_file = collection_dir / f"{item_id}_data.npy"
            np.save(data_file, data)
            
            # Save metadata to a JSON file
            metadata_file = collection_dir / f"{item_id}_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2, cls=DateTimeEncoder)
            
            # Prepare data for storage
            data_dict = {
                "data_file": str(data_file),
                "metadata_file": str(metadata_file),
                "bands": bands,
                "metadata": metadata
            }
            
            # Store in cold memory
            success = self.cold_memory.store(data_dict, metadata)
            
            if success:
                self.logger.info(f"Successfully stored {item_id} in cold memory at {data_file}")
                self.logger.info(f"Metadata stored at {metadata_file}")
            else:
                self.logger.error(f"Failed to store {item_id} in cold memory")
                if data_file.exists():
                    data_file.unlink()
                if metadata_file.exists():
                    metadata_file.unlink()
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error storing in cold memory: {e}")
            return False

    async def search_and_download(
        self,
        bbox: Dict[str, float],
        start_date: str,
        end_date: str,
        collections: List[str],
        cloud_cover: float = 20.0
    ) -> Dict[str, Any]:
        """
        Search and download data from specified collections.
        
        Args:
            bbox: Bounding box {xmin, ymin, xmax, ymax}
            start_date: Start date in ISO format
            end_date: End date in ISO format
            collections: List of collection IDs
            cloud_cover: Maximum cloud cover percentage
            
        Returns:
            Dictionary with results per collection
        """
        if not super().validate_bbox(bbox):
            return {"status": "error", "message": "Invalid bounding box"}
            
        try:
            results = {}
            for collection_id in collections:
                self.logger.info(f"Searching collection: {collection_id}")
                self.logger.info(f"Search parameters: bbox={bbox}, time={start_date}/{end_date}, cloud_cover={cloud_cover}")
                
                search = self.catalog.search(
                    collections=[collection_id],
                    bbox=[bbox["xmin"], bbox["ymin"], bbox["xmax"], bbox["ymax"]],
                    datetime=f"{start_date}/{end_date}",
                    query={"eo:cloud_cover": {"lt": cloud_cover}}
                )
                
                items = list(search.items())
                self.logger.info(f"Found {len(items)} items for collection {collection_id}")
                
                if not items:
                    self.logger.warning(f"No items found for collection {collection_id}")
                    continue
                    
                item = items[0]  # Get first item
                self.logger.info(f"Processing first item: {item.id}")
                
                # Download bands based on collection type
                bands = []
                if collection_id == "sentinel-2-l2a":
                    bands = ["B02", "B03", "B04", "B08"]  # RGB + NIR
                elif collection_id == "landsat-8-c2-l2":
                    bands = ["B2", "B3", "B4", "B5"]  # RGB + NIR
                
                if bands:
                    try:
                        self.logger.info(f"Downloading bands: {bands}")
                        # Download and process bands
                        band_arrays = []
                        for band in bands:
                            self.logger.info(f"Processing band: {band}")
                            href = item.assets[band].href
                            signed_href = pc.sign(href)
                            self.logger.info(f"Signed URL for {band}: {signed_href}")
                            
                            with rasterio.open(signed_href) as src:
                                # Get the window for our bbox
                                bounds = transform_bounds(
                                    "EPSG:4326",
                                    src.crs,
                                    bbox["xmin"],
                                    bbox["ymin"],
                                    bbox["xmax"],
                                    bbox["ymax"]
                                )
                                self.logger.info(f"Transformed bounds: {bounds}")
                                window = src.window(*bounds)
                                self.logger.info(f"Window for band {band}: {window}")
                                data = src.read(1, window=window)
                                band_arrays.append(data)
                                self.logger.info(f"Successfully read band {band}, shape: {data.shape}")
                        
                        # Stack bands into a single array
                        stacked_data = np.stack(band_arrays)
                        self.logger.info(f"Stacked data shape: {stacked_data.shape}")
                        
                        # Store in cold memory
                        self.logger.info("Storing in cold memory...")
                        await self.store_in_cold_memory(
                            item=item.to_dict(),
                            data=stacked_data,
                            bands=bands
                        )
                        
                        results[collection_id] = {
                            "data": {
                                "shape": stacked_data.shape,
                                "bands": bands
                            },
                            "metadata": {
                                "id": item.id,
                                "datetime": serialize_datetime(item.datetime),
                                "bbox": item.bbox,
                                "properties": item.properties
                            }
                        }
                        self.logger.info(f"Successfully processed collection {collection_id}")
                        
                    except Exception as e:
                        self.logger.error(f"Error downloading bands for {collection_id}: {e}", exc_info=True)
                        results[collection_id] = {
                            "status": "error",
                            "message": f"Failed to download bands: {str(e)}"
                        }
                else:
                    self.logger.warning(f"No bands defined for collection {collection_id}")
                    results[collection_id] = {
                        "metadata": {
                            "id": item.id,
                            "datetime": serialize_datetime(item.datetime),
                            "bbox": item.bbox,
                            "properties": item.properties
                        }
                    }
                
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching/downloading data: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}
    
    def get_metadata(self, collection_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a collection.
        
        Args:
            collection_id: Collection identifier
            
        Returns:
            Dictionary containing collection metadata
        """
        collection = self.catalog.get_collection(collection_id)
        metadata = {
            "id": collection.id,
            "title": collection.title,
            "description": collection.description,
            "license": collection.license,
            "providers": [p.name for p in collection.providers],
            "spatial_extent": collection.extent.spatial.bboxes,
            "temporal_extent": [
                [serialize_datetime(t[0]), serialize_datetime(t[1])]
                for t in collection.extent.temporal.intervals
            ]
        }
        return metadata
    
    def get_available_collections(self) -> List[str]:
        """Get list of available collections."""
        collections = self.catalog.get_collections()
        return [c.id for c in collections]

    def list_stored_files(self) -> Dict[str, Any]:
        """List all files stored in cold memory.
        
        Returns:
            Dictionary containing file information
        """
        try:
            storage_path = Path(self.cold_memory.raw_data_path) / "planetary"
            if not storage_path.exists():
                return {
                    "storage_path": str(storage_path),
                    "files": []
                }
            
            # Get all collections
            stored_files = {
                "storage_path": str(storage_path),
                "collections": {}
            }
            
            for collection_dir in storage_path.iterdir():
                if collection_dir.is_dir():
                    collection_files = []
                    
                    # Get all .npy and .json files
                    data_files = list(collection_dir.glob("*_data.npy"))
                    for data_file in data_files:
                        metadata_file = data_file.parent / f"{data_file.stem.replace('_data', '')}_metadata.json"
                        
                        file_info = {
                            "filename": data_file.name,
                            "path": str(data_file),
                            "size_mb": data_file.stat().st_size / (1024 * 1024),  # Convert to MB
                            "created": datetime.fromtimestamp(data_file.stat().st_ctime).isoformat()
                        }
                        
                        # Try to load metadata
                        try:
                            if metadata_file.exists():
                                with open(metadata_file) as f:
                                    metadata = json.load(f)
                                file_info["metadata"] = metadata
                            
                            data = np.load(data_file, allow_pickle=True)
                            file_info["shape"] = data.shape
                        except Exception as e:
                            file_info["load_error"] = str(e)
                        
                        collection_files.append(file_info)
                    
                    stored_files["collections"][collection_dir.name] = collection_files
            
            return stored_files
            
        except Exception as e:
            self.logger.error(f"Error listing stored files: {e}")
            return {"error": str(e)}

