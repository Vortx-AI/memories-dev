"""
Base data source interface for the Memories system.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Any, Tuple
from pathlib import Path
from shapely.geometry import box, Polygon

class DataSource(ABC):
    """Abstract base class for all data sources."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize data source.
        
        Args:
            cache_dir: Optional directory for caching data
        """
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    async def search(self, *args, **kwargs) -> Union[List[Dict], Dict]:
        """
        Search for data matching specified criteria.
        
        Returns:
            List or dictionary of search results
        """
        pass
    
    @abstractmethod
    async def download(self, *args, **kwargs) -> Path:
        """
        Download data to local storage.
        
        Returns:
            Path to downloaded file
        """
        pass
    
    def validate_bbox(self, bbox: Union[List[float], Tuple[float, float, float, float]]) -> bool:
        """
        Validate bounding box format and coordinates.
        
        Args:
            bbox: List/tuple of coordinates [west, south, east, north]
            
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
    
    def bbox_to_polygon(self, bbox: Union[List[float], Tuple[float, float, float, float]]) -> Polygon:
        """
        Convert bounding box coordinates to Shapely Polygon.
        
        Args:
            bbox: List/tuple of coordinates [west, south, east, north]
            
        Returns:
            Shapely Polygon
        """
        self.validate_bbox(bbox)
        return box(*bbox)
    
    def get_cache_path(self, filename: str) -> Optional[Path]:
        """
        Get path for cached file.
        
        Args:
            filename: Name of file to cache
            
        Returns:
            Path object if cache_dir is set, None otherwise
        """
        if self.cache_dir:
            return self.cache_dir / filename
        return None
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        if self.cache_dir and self.cache_dir.exists():
            for file in self.cache_dir.glob("*"):
                if file.is_file():
                    file.unlink()
    
    @abstractmethod
    def get_metadata(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Get metadata about a data source or specific item.
        
        Returns:
            Dictionary containing metadata
        """
        pass 