"""
Landsat data source using Planetary Computer.
"""

import os
import logging
import asyncio
import planetary_computer
import pystac_client
import rasterio
import numpy as np
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import json
from memories.core.cold import ColdMemory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LandsatConnector:
    """Interface for accessing Landsat data using Planetary Computer."""
    
    def __init__(self, data_dir: Union[str, Path] = None, keep_files: bool = False, store_in_cold: bool = True):
        """Initialize the Landsat interface.
        
        Args:
            data_dir: Directory to store downloaded data. If None, uses cold storage
            keep_files: Whether to keep downloaded files (default: False)
            store_in_cold: Whether to store files in cold memory (default: True)
        """
        self.keep_files = keep_files
        self.store_in_cold = store_in_cold
        self.client = None
        self._downloaded_files = []
        
        # Initialize cold memory if enabled
        self.cold_memory = ColdMemory() if store_in_cold else None
        self.cold = self.cold_memory  # For backward compatibility
        
        if self.cold_memory:
            logger.info(f"Cold storage location: {self.cold_memory.raw_data_path}")
        
        # Set up data directory
        if data_dir is None and self.cold_memory:
            data_dir = self.cold_memory.raw_data_path / "landsat"
            logger.info(f"Using cold storage path for data: {data_dir}")
        else:
            data_dir = Path(data_dir) if data_dir else Path("data/landsat")
            logger.info(f"Using custom data directory: {data_dir}")
            
        self.data_dir = Path(data_dir)
        os.makedirs(self.data_dir, exist_ok=True)

    async def initialize(self) -> bool:
        """Initialize the Landsat API.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Initialize the STAC client
            self.client = pystac_client.Client.open(
                "https://planetarycomputer.microsoft.com/api/stac/v1",
                modifier=planetary_computer.sign_inplace
            )
            return True
        except Exception as e:
            logger.error(f"Error initializing Landsat API: {str(e)}")
            return False

    async def download_data(
        self,
        bbox: Dict[str, float],
        start_date: datetime,
        end_date: datetime,
        collection: str = "LANDSAT_8_C2_L2",
        bands: Optional[List[str]] = None,
        cloud_cover: float = 30.0
    ) -> Dict[str, Any]:
        """
        Download Landsat data for a specified area and time range.
        
        Args:
            bbox: Dictionary with bounding box coordinates (xmin, ymin, xmax, ymax)
            start_date: Start date for data retrieval
            end_date: End date for data retrieval
            collection: Landsat collection ID (default: LANDSAT_8_C2_L2)
            bands: List of band names to download
            cloud_cover: Maximum cloud cover percentage (default: 30.0)
            
        Returns:
            Dictionary containing download results and metadata
        """
        try:
            # Convert collection name to STAC format
            collection_id = collection.lower().replace("_", "-")
            
            # Set default bands if none provided
            if bands is None:
                bands = ["SR_B4", "SR_B5"]  # Default to Red and NIR bands
            
            # Search for scenes
            search = self.client.search(
                collections=[collection_id],
                bbox=[bbox["xmin"], bbox["ymin"], bbox["xmax"], bbox["ymax"]],
                datetime=f"{start_date.isoformat()}/{end_date.isoformat()}",
                query={"eo:cloud_cover": {"lt": cloud_cover}}
            )
            
            # Get the first matching scene
            items = list(search.items())
            if not items:
                return {
                    "status": "error",
                    "message": "No scenes found matching criteria"
                }
            
            scene = items[0]
            logger.info(f"Selected scene: {scene.id}")
            
            # Download requested bands
            downloaded_bands = []
            for band in bands:
                try:
                    # Get band asset
                    asset = scene.assets.get(band)
                    if not asset:
                        logger.warning(f"Band {band} not found in scene {scene.id}")
                        continue
                        
                    # Download the band
                    output_file = self.data_dir / f"{scene.id}_{band}.tif"
                    
                    # Use rasterio to download and save the band
                    with rasterio.open(asset.href) as src:
                        profile = src.profile.copy()
                        with rasterio.open(output_file, 'w', **profile) as dst:
                            dst.write(src.read())
                    
                    downloaded_bands.append(band)
                    logger.info(f"Successfully downloaded band {band}")
                    
                except Exception as e:
                    logger.error(f"Error downloading band {band}: {str(e)}")
                    continue
            
            if not downloaded_bands:
                return {
                    "status": "error",
                    "message": "Failed to download any bands"
                }
            
            # Prepare result
            result = {
                "status": "success",
                "scene_id": scene.id,
                "product_id": scene.properties.get("landsat:product_id"),
                "cloud_cover": scene.properties.get("eo:cloud_cover"),
                "bands": downloaded_bands,
                "metadata": {
                    "DATE_ACQUIRED": scene.properties.get("datetime"),
                    "SPACECRAFT_ID": scene.properties.get("platform"),
                    "COLLECTION_NUMBER": scene.properties.get("landsat:collection_number"),
                    "COLLECTION_CATEGORY": scene.properties.get("landsat:collection_category"),
                    "PROCESSING_LEVEL": scene.properties.get("processing:level")
                }
            }
            
            # Store in cold memory if enabled
            if self.store_in_cold:
                try:
                    cold_data = {
                        "scene_id": scene.id,
                        "bands": downloaded_bands,
                        "metadata": result["metadata"]
                    }
                    self.cold_memory.store(cold_data, result["metadata"])
                except Exception as e:
                    logger.warning(f"Failed to store in cold memory: {str(e)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error downloading Landsat data: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

    def cleanup(self):
        """Clean up downloaded files if keep_files is False."""
        if not self.keep_files and not self.store_in_cold:
            try:
                if self.data_dir.exists():
                    logger.info(f"Cleaning up directory: {self.data_dir}")
                    shutil.rmtree(self.data_dir)
                    logger.info("Cleanup completed")
            except Exception as e:
                logger.error(f"Error during cleanup: {str(e)}")

    def __del__(self):
        """Cleanup on object destruction."""
        self.cleanup() 