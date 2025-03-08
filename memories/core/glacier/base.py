"""Base connector interface for glacier storage and data sources."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, Tuple
from pathlib import Path
import logging
import json
from datetime import datetime
from shapely.geometry import box, Polygon

class DataSource(ABC):
    """Abstract base class for all data sources."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize data source.
        
        Args:
            cache_dir: Optional directory for caching data
        """
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    async def search(self, *args, **kwargs) -> Union[List[Dict], Dict]:
        """Search for data matching specified criteria.
        
        Returns:
            List or dictionary of search results
        """
        pass
    
    @abstractmethod
    async def download(self, *args, **kwargs) -> Path:
        """Download data to local storage.
        
        Returns:
            Path to downloaded file
        """
        pass
    
    def validate_bbox(self, bbox: Union[List[float], Tuple[float, float, float, float]]) -> bool:
        """Validate bounding box format and coordinates.
        
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
        """Convert bounding box coordinates to Shapely Polygon.
        
        Args:
            bbox: List/tuple of coordinates [west, south, east, north]
            
        Returns:
            Shapely Polygon
        """
        self.validate_bbox(bbox)
        return box(*bbox)
    
    def get_cache_path(self, filename: str) -> Optional[Path]:
        """Get path for cached file.
        
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
        """Get metadata about a data source or specific item.
        
        Returns:
            Dictionary containing metadata
        """
        pass

class GlacierConnector(ABC):
    """Abstract base class for glacier storage connectors."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the connector with configuration."""
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self._connection = None
        
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the storage backend."""
        pass
    
    @abstractmethod
    def store(self, data: Any, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store data in the backend.
        
        Args:
            data: Data to store
            metadata: Optional metadata
            
        Returns:
            str: Unique identifier for stored data
        """
        pass
    
    @abstractmethod
    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve data from the backend.
        
        Args:
            key: Unique identifier for the data
            
        Returns:
            Optional[Any]: Retrieved data or None if not found
        """
        pass
    
    @abstractmethod
    def list_objects(self, prefix: str = "") -> List[Dict[str, Any]]:
        """List available objects in storage.
        
        Args:
            prefix: Optional prefix to filter objects
            
        Returns:
            List[Dict[str, Any]]: List of object metadata
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete an object from storage.
        
        Args:
            key: Unique identifier for the data
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources."""
        pass
    
    def _add_standard_metadata(self, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add standard metadata fields to user metadata."""
        standard_metadata = {
            "timestamp": datetime.now().isoformat(),
            "connector_type": self.__class__.__name__
        }
        if metadata:
            standard_metadata.update(metadata)
        return standard_metadata
    
    def _serialize_data(self, data: Any) -> bytes:
        """Serialize data to bytes."""
        try:
            if isinstance(data, bytes):
                return data
            elif isinstance(data, str):
                return data.encode('utf-8')
            else:
                return json.dumps(data).encode('utf-8')
        except Exception as e:
            self.logger.error(f"Failed to serialize data: {e}")
            raise
    
    def _deserialize_data(self, data: bytes) -> Any:
        """Deserialize data from bytes."""
        try:
            decoded = data.decode('utf-8')
            try:
                return json.loads(decoded)
            except json.JSONDecodeError:
                return decoded
        except Exception as e:
            self.logger.error(f"Failed to deserialize data: {e}")
            raise
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup() 