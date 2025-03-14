"""Glacier Memory implementation."""

from typing import Dict, Any, Optional, List
import logging
from .base import DataSource, GlacierConnector
from .factory import create_connector, create_storage_connector

class GlacierMemory:
    """Base class for Glacier Memory."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Glacier Memory.
        
        Args:
            config (Optional[Dict[str, Any]]): Configuration dictionary containing:
                - storage: Storage configuration with:
                    - type: Storage connector type (e.g., 'gcs')
                    - config: Connector-specific configuration
        """
        self.data_connectors = {}
        self.storage_connector = None
        self.logger = logging.getLogger(__name__)
        
        if config and 'storage' in config:
            storage_config = config['storage']
            storage_type = storage_config.get('type')
            if storage_type:
                try:
                    connector_config = storage_config.get('config', {})
                    self.storage_connector = create_storage_connector(
                        storage_type,
                        connector_config
                    )
                except Exception as e:
                    self.logger.error(f"Failed to initialize storage connector: {str(e)}")
                    raise
    
    async def store(self, data: Any, key: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Store data in glacier storage.
        
        Args:
            data: Data to store
            key: Key to store the data under
            metadata: Optional metadata to store with the object
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            RuntimeError: If no storage connector is configured
        """
        if not self.storage_connector:
            raise RuntimeError("No storage connector configured")
        
        try:    
            # Use the async version if available, otherwise call the sync version
            if hasattr(self.storage_connector, 'store_async'):
                return await self.storage_connector.store_async(data, key, metadata)
            else:
                if metadata is None:
                    metadata = {}
                metadata["key"] = key
                stored_key = self.storage_connector.store(data, metadata)
                return stored_key == key
        except Exception as e:
            self.logger.error(f"Error storing data: {str(e)}")
            return False
    
    async def retrieve_stored(self, key: str) -> Optional[Any]:
        """Retrieve data from glacier storage.
        
        Args:
            key: Key of the data to retrieve
            
        Returns:
            Optional[Any]: Retrieved data or None if not found
            
        Raises:
            RuntimeError: If no storage connector is configured
        """
        if not self.storage_connector:
            raise RuntimeError("No storage connector configured")
        
        try:
            # Use the async version if available, otherwise call the sync version
            if hasattr(self.storage_connector, 'retrieve_async'):
                return await self.storage_connector.retrieve_async(key)
            else:
                return self.storage_connector.retrieve(key)
        except Exception as e:
            self.logger.error(f"Error retrieving data: {str(e)}")
            return None
    
    async def delete_stored(self, key: str) -> bool:
        """Delete data from glacier storage.
        
        Args:
            key: Key of the data to delete
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            RuntimeError: If no storage connector is configured
        """
        if not self.storage_connector:
            raise RuntimeError("No storage connector configured")
            
        return await self.storage_connector.delete(key)
    
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
            connector = self.data_connectors.get(source)
            if not connector:
                connector = create_connector(source, query.get('config'))
                self.data_connectors[source] = connector
            
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
        return list(self.data_connectors.keys())

    def register_connector(self, name: str, connector: DataSource) -> None:
        """Register a data source connector.
        
        Args:
            name: Name of the connector
            connector: Connector instance
        """
        self.data_connectors[name] = connector
        
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.storage_connector:
            self.storage_connector.cleanup()
            
        for connector in self.data_connectors.values():
            connector.cleanup() 