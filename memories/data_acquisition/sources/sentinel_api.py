"""
Sentinel satellite data source implementation.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import aiohttp
import asyncio
import rasterio
import numpy as np

class SentinelAPI:
    """Interface for accessing Sentinel satellite data."""
    
    def __init__(self, data_dir: str = None):
        """Initialize the Sentinel API interface.
        
        Args:
            data_dir: Directory for storing downloaded data
        """
        self.data_dir = Path(data_dir) if data_dir else Path("data/sentinel")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    async def download_data(self,
                          bbox: Dict[str, float],
                          cloud_cover: float = 20.0,
                          bands: Dict[str, str] = None) -> Dict[str, Any]:
        """Download Sentinel data for a given bounding box.
        
        Args:
            bbox: Bounding box dictionary with xmin, ymin, xmax, ymax
            cloud_cover: Maximum cloud cover percentage
            bands: Dictionary of band IDs to band names
            
        Returns:
            Dictionary containing download status and data
        """
        try:
            # Validate inputs
            if not isinstance(bbox, dict) or not all(k in bbox for k in ['xmin', 'ymin', 'xmax', 'ymax']):
                raise ValueError("Invalid bbox format: must be dictionary with xmin, ymin, xmax, ymax")
                
            if not isinstance(cloud_cover, (int, float)) or cloud_cover < 0 or cloud_cover > 100:
                raise ValueError("Invalid cloud_cover: must be between 0 and 100")
                
            if bands is None:
                bands = {
                    "B02": "Blue",
                    "B03": "Green",
                    "B04": "Red",
                    "B08": "NIR"
                }
                
            # Download each band
            downloaded_bands = {}
            async with aiohttp.ClientSession() as session:
                for band_id, band_name in bands.items():
                    try:
                        band_data = await self._download_band(
                            session,
                            bbox,
                            band_id,
                            cloud_cover
                        )
                        downloaded_bands[band_id] = band_data
                    except Exception as e:
                        self.logger.error(f"Error downloading band {band_id}: {e}")
                        
            if not downloaded_bands:
                return {
                    "success": False,
                    "error": "All band downloads failed"
                }
                
            # Merge bands into single array
            merged_data = self._merge_bands(downloaded_bands)
            
            return {
                "success": True,
                "data": merged_data,
                "bands": list(bands.keys()),
                "properties": {
                    "cloud_cover": cloud_cover,
                    "bbox": bbox
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error downloading Sentinel data: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _download_band(self,
                           session: aiohttp.ClientSession,
                           bbox: Dict[str, float],
                           band_id: str,
                           cloud_cover: float) -> np.ndarray:
        """Download a single Sentinel band."""
        # Mock implementation for testing
        # In production, this would make actual API calls
        return np.random.rand(100, 100)  # Random data for testing
    
    def _merge_bands(self, bands: Dict[str, np.ndarray]) -> np.ndarray:
        """Merge multiple bands into a single array."""
        # Stack bands along new axis
        return np.stack(list(bands.values()), axis=0)
    
    def _cleanup_temp_files(self, files: List[Path]) -> None:
        """Clean up temporary files after processing."""
        for file in files:
            try:
                if file.exists():
                    file.unlink()
            except Exception as e:
                self.logger.warning(f"Failed to delete temporary file {file}: {e}")