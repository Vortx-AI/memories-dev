"""Factory for creating data source connectors."""

from typing import Dict, Any, Optional
from .base import DataSource

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
    # Add other connectors here
    
    raise ValueError(f"Unsupported source type: {source_type}") 