"""Glacier Memory implementation."""

from typing import Dict, Any, Optional, List
import logging
from .base import DataSource

class GlacierMemory:
    """Base class for Glacier Memory."""
    
    def __init__(self):
        """Initialize Glacier Memory."""
        self.connectors = {}
        self.logger = logging.getLogger(__name__)
    
    async def retrieve(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Retrieve data from a glacier source.
        
        Args:
            query: Query dictionary containing:
                - source: Name of the source ('osm', 'overture', etc.)
                - Other source-specific parameters
                
        Returns:
            Optional[Dict[str, Any]]: Retrieved data or None if not found
            
        Raises:
            ValueError: If source is not supported or query is invalid
        """
        source = query.get('source')
        if not source:
            raise ValueError("Query must specify a source")
        
        try:
            # Create connector for the source
            connector = self.connectors.get(source)
            if not connector:
                raise ValueError(f"Source {source} not registered")
            
            # Validate query
            if not connector.validate_query(query):
                raise ValueError(f"Invalid query for source: {source}")
            
            # Retrieve data
            return await connector.retrieve(query)
            
        except Exception as e:
            self.logger.error(f"Error retrieving from {source}: {str(e)}")
            raise
    
    def get_available_sources(self) -> List[str]:
        """Get list of available data sources.
        
        Returns:
            List[str]: List of supported source names
        """
        return list(self.connectors.keys())

    def register_connector(self, name: str, connector: Any) -> None:
        """Register a connector."""
        self.connectors[name] = connector 