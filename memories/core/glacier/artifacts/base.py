"""
Base class for data source connectors.
"""

from typing import Optional, Dict, Any, Union, Tuple, List
from pathlib import Path
import os
import logging

class DataSource:
    """Base class for data source connectors."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize data source.
        
        Args:
            cache_dir: Optional directory for caching data
        """
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing DataSource base class")
        if self.cache_dir:
            self.logger.info(f"Cache directory set to: {self.cache_dir}")
        else:
            self.logger.info("No cache directory specified")
    
    def get_cache_path(self, filename: str) -> Optional[Path]:
        """Get cache path for a file.
        
        Args:
            filename: Name of file to cache
            
        Returns:
            Path to cached file or None if caching disabled
        """
        if not self.cache_dir:
            return None
            
        return self.cache_dir / filename
    
    def clear_cache(self):
        """Clear the cache directory."""
        if self.cache_dir and self.cache_dir.exists():
            for file in self.cache_dir.glob("*"):
                try:
                    if file.is_file():
                        file.unlink()
                    elif file.is_dir():
                        file.rmdir()
                except Exception as e:
                    self.logger.error(f"Error removing {file}: {e}")
    
    def validate_bbox(self, bbox: Union[Dict[str, float], List[float], Tuple[float, ...]]) -> bool:
        """Validate bounding box coordinates.
        
        Args:
            bbox: Dictionary with xmin, ymin, xmax, ymax or list/tuple of [west, south, east, north]
            
        Returns:
            bool: True if valid
        """
        try:
            # Convert list/tuple to dict format
            if isinstance(bbox, (list, tuple)):
                if len(bbox) != 4:
                    self.logger.error("bbox must contain exactly 4 coordinates")
                    return False
                bbox = {
                    "xmin": bbox[0],
                    "ymin": bbox[1],
                    "xmax": bbox[2],
                    "ymax": bbox[3]
                }
            
            # Check required keys for dict format
            required_keys = ['xmin', 'ymin', 'xmax', 'ymax']
            if not all(k in bbox for k in required_keys):
                self.logger.error("Missing required bbox coordinates")
                return False
            
            # Check coordinate ranges
            if not (-180 <= bbox['xmin'] <= 180 and -180 <= bbox['xmax'] <= 180):
                self.logger.error("Invalid longitude values. Must be between -180 and 180.")
                return False
                
            if not (-90 <= bbox['ymin'] <= 90 and -90 <= bbox['ymax'] <= 90):
                self.logger.error("Invalid latitude values. Must be between -90 and 90.")
                return False
                
            # Check that min is less than max
            if bbox['xmin'] >= bbox['xmax']:
                self.logger.error("xmin must be less than xmax")
                return False
                
            if bbox['ymin'] >= bbox['ymax']:
                self.logger.error("ymin must be less than ymax")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating bbox: {e}")
            return False 