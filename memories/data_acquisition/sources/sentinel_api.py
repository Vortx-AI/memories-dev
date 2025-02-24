"""Sentinel satellite imagery data acquisition module."""

import os
import logging
from pathlib import Path
import numpy as np
import rasterio
from pystac_client import Client
import planetary_computer
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)

class SentinelAPI:
    """Interface for downloading Sentinel satellite imagery."""
    
    def __init__(self, data_dir: str):
        """Initialize SentinelAPI.
        
        Args:
            data_dir: Directory to store downloaded data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    async def download_data(
        self,
        bbox: Dict[str, float],
        cloud_cover: float = 10.0,
        bands: Optional[Dict[str, str]] = None
    ) -> Dict:
        """Download Sentinel data for the given parameters.
        
        Args:
            bbox: Bounding box {xmin, ymin, xmax, ymax}
            cloud_cover: Maximum cloud cover percentage
            bands: Dictionary of band IDs to names to download
            
        Returns:
            Dictionary containing:
                success: bool indicating success
                data: numpy array of imagery data if successful
                bands: list of downloaded bands
                properties: dict of scene properties
                error: error message if unsuccessful
        """
        try:
            # Validate bbox
            required_keys = ['xmin', 'ymin', 'xmax', 'ymax']
            if not all(key in bbox for key in required_keys):
                raise ValueError("Invalid bbox format")
                
            # Set default bands if none provided
            if bands is None:
                bands = {
                    'B04': 'Red',
                    'B08': 'NIR',
                    'B11': 'SWIR'
                }
                
            # Initialize STAC client
            catalog = Client.open(
                "https://planetarycomputer.microsoft.com/api/stac/v1",
                modifier=planetary_computer.sign_inplace,
            )
            
            # Search for scenes
            search = catalog.search(
                collections=["sentinel-2-l2a"],
                bbox=[bbox['xmin'], bbox['ymin'], bbox['xmax'], bbox['ymax']],
                query={"eo:cloud_cover": {"lt": cloud_cover}}
            )
            
            items = list(search.get_items())
            if not items:
                return {
                    'success': False,
                    'error': f'No scenes found with cloud cover < {cloud_cover}%'
                }
                
            # Get most recent scene
            scene = items[0]
            
            # Download requested bands
            data_arrays = []
            downloaded_bands = []
            
            for band_id in bands:
                if band_id not in scene.assets:
                    logger.warning(f"Band {band_id} not found in scene")
                    continue
                    
                href = scene.assets[band_id].href
                output_path = self.data_dir / f"{scene.id}_{band_id}.tif"
                
                # Download and read band data
                with rasterio.open(href) as src:
                    data = src.read(1)
                    data_arrays.append(data)
                    downloaded_bands.append(band_id)
                    
            if not downloaded_bands:
                return {
                    'success': False,
                    'error': 'No valid bands could be downloaded'
                }
                
            # Stack bands into single array
            data = np.stack(data_arrays)
            
            return {
                'success': True,
                'data': data,
                'bands': downloaded_bands,
                'properties': {
                    'scene_id': scene.id,
                    'cloud_cover': scene.properties['eo:cloud_cover'],
                    'bbox': bbox,
                    'datetime': scene.properties['datetime']
                }
            }
            
        except Exception as e:
            logger.error(f"Error downloading Sentinel data: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
            
    def _cleanup_temp_files(self, files: List[Union[str, Path]]) -> None:
        """Clean up temporary downloaded files.
        
        Args:
            files: List of file paths to remove
        """
        for file in files:
            try:
                Path(file).unlink()
            except Exception as e:
                logger.warning(f"Failed to remove file {file}: {str(e)}")