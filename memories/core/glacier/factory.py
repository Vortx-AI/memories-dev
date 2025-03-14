"""Factory for creating data source connectors."""

from typing import Dict, Any, Optional
from .base import DataSource, GlacierConnector

def create_connector(source_type: str, config: Optional[Dict[str, Any]] = None) -> DataSource:
    """Create a connector instance based on source type."""
    if config is None:
        config = {}
        
    if source_type == "osm":
        from .artifacts.osm import OSMConnector
        return OSMConnector(config)
    elif source_type == "overture":
        from .artifacts.overture import OvertureConnector
        return OvertureConnector()
    elif source_type == "sentinel":
        from .artifacts.sentinel import SentinelConnector
        return SentinelConnector(keep_files=False, store_in_cold=True)
    elif source_type == "planetary":
        from .artifacts.planetary import PlanetaryConnector
        return PlanetaryConnector()
    elif source_type == "landsat":
        from .artifacts.landsat import LandsatConnector
        return LandsatConnector()
    elif source_type == "gcs":
        from .connectors import GCSConnector
        return GCSConnector(config)
    # Add other connectors here
    
    raise ValueError(f"Unsupported source type: {source_type}")

def create_storage_connector(connector_type: str, config: Optional[Dict[str, Any]] = None) -> GlacierConnector:
    """Create a storage connector instance based on connector type."""
    if config is None:
        config = {}
        
    if connector_type == "gcs":
        from .connectors import GCSConnector
        return GCSConnector(config)
        
    raise ValueError(f"Unsupported storage connector type: {connector_type}") 