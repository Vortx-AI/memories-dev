"""Glacier memory implementation for long-term storage."""

import os
import logging
from typing import Dict, Any, Optional, List, Union
import json
import pandas as pd
import geopandas as gpd

from .glacier.factory import GlacierConnectorFactory
from .glacier.base import GlacierConnector

class GlacierMemory:
    """Glacier memory for long-term storage of rarely accessed data.
    
    This class provides a unified interface for storing and retrieving data
    from various cold storage backends (S3, databases, APIs) using a connector-based
    architecture.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, config_path: Optional[str] = None):
        """Initialize glacier memory.
        
        Args:
            config: Optional configuration dictionary containing:
                - storage_path: Local path for temporary storage
                - max_size: Maximum size in bytes (0 for unlimited)
                - connectors: Dictionary mapping connector names to their configurations
                - default_connector: Name of the default connector to use
            config_path: Optional path to a configuration file
        """
        # Load configuration from file if provided
        if config_path:
            try:
                import yaml
                from pathlib import Path
                
                config_file = Path(config_path)
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        file_config = yaml.safe_load(f)
                    
                    # Extract glacier-specific configuration
                    if 'memory' in file_config and 'glacier' in file_config['memory']:
                        glacier_config = file_config['memory']['glacier']
                        
                        # Merge with provided config
                        if config:
                            for key, value in glacier_config.items():
                                if key not in config:
                                    config[key] = value
                        else:
                            config = glacier_config
                else:
                    self.logger = logging.getLogger(__name__)
                    self.logger.warning(f"Config file not found at: {config_path}, using default configuration")
                    
                    # Try to load default configuration
                    default_config_path = Path(__file__).parent / 'glacier' / 'default_config.yml'
                    if default_config_path.exists():
                        with open(default_config_path, 'r') as f:
                            config = yaml.safe_load(f)
                        self.logger.info(f"Loaded default configuration from {default_config_path}")
            except Exception as e:
                self.logger = logging.getLogger(__name__)
                self.logger.error(f"Error loading config from {config_path}: {e}")
                self.logger.info("Using default configuration")
                
                # Try to load default configuration
                try:
                    import yaml
                    from pathlib import Path
                    
                    default_config_path = Path(__file__).parent / 'glacier' / 'default_config.yml'
                    if default_config_path.exists():
                        with open(default_config_path, 'r') as f:
                            config = yaml.safe_load(f)
                        self.logger.info(f"Loaded default configuration from {default_config_path}")
                except Exception as e2:
                    self.logger.error(f"Error loading default configuration: {e2}")
        
        # Use provided or default configuration
        config = config or {}
        
        # Set up logging if not already done
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger(__name__)
        
        # Get storage path from config or use default
        self.storage_path = config.get('storage_path', os.path.join(os.getcwd(), 'data', 'glacier'))
        self.max_size = config.get('max_size', 0)  # 0 means unlimited
        
        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Initialize connectors
        self.connectors: Dict[str, GlacierConnector] = {}
        self.default_connector: Optional[str] = config.get('default_connector')
        
        connector_configs = config.get('connectors', {})
            
        try:
            if connector_configs:
                self.connectors = GlacierConnectorFactory.create_multi_connector(connector_configs)
                # If default_connector not specified and we have connectors, use the first one
                if not self.default_connector and self.connectors:
                    self.default_connector = next(iter(self.connectors))
        except Exception as e:
            self.logger.error(f"Failed to initialize connectors: {e}")
            raise
            
    def store(self, data: Any, metadata: Optional[Dict[str, Any]] = None, connector: Optional[str] = None) -> str:
        """Store data in glacier storage.
        
        Args:
            data: Data to store
            metadata: Optional metadata
            connector: Optional connector name to use (defaults to default_connector)
            
        Returns:
            str: Unique key for stored data
            
        Raises:
            ValueError: If no connectors are configured or specified connector is not found
            RuntimeError: If storage operation fails
        """
        if not self.connectors:
            raise ValueError("No connectors configured")
            
        connector_name = connector or self.default_connector
        if connector_name not in self.connectors:
            raise ValueError(f"Connector not found: {connector_name}")
            
        try:
            return self.connectors[connector_name].store(data, metadata)
        except Exception as e:
            self.logger.error(f"Failed to store data using connector '{connector_name}': {e}")
            raise RuntimeError(f"Storage operation failed: {str(e)}")
    
    def retrieve(self, key: str, connector: Optional[str] = None) -> Optional[Any]:
        """Retrieve data from glacier storage.
        
        Args:
            key: Unique key for the data
            connector: Optional connector name to use (defaults to default_connector)
            
        Returns:
            Optional[Any]: Retrieved data or None if not found
            
        Raises:
            ValueError: If no connectors are configured or specified connector is not found
            RuntimeError: If retrieval operation fails
        """
        if not self.connectors:
            raise ValueError("No connectors configured")
            
        connector_name = connector or self.default_connector
        if connector_name not in self.connectors:
            raise ValueError(f"Connector not found: {connector_name}")
            
        try:
            return self.connectors[connector_name].retrieve(key)
        except Exception as e:
            self.logger.error(f"Failed to retrieve data using connector '{connector_name}': {e}")
            raise RuntimeError(f"Retrieval operation failed: {str(e)}")
    
    def retrieve_all(self, prefix: str = "", connector: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all objects in glacier storage.
        
        Args:
            prefix: Optional prefix to filter object keys
            connector: Optional connector name to use (defaults to default_connector)
            
        Returns:
            List[Dict[str, Any]]: List of object metadata
            
        Raises:
            ValueError: If no connectors are configured or specified connector is not found
            RuntimeError: If list operation fails
        """
        if not self.connectors:
            return []
            
        connector_name = connector or self.default_connector
        if connector_name not in self.connectors:
            raise ValueError(f"Connector not found: {connector_name}")
            
        try:
            return self.connectors[connector_name].list_objects(prefix)
        except Exception as e:
            self.logger.error(f"Failed to list objects using connector '{connector_name}': {e}")
            raise RuntimeError(f"List operation failed: {str(e)}")
    
    def delete(self, key: str, connector: Optional[str] = None) -> bool:
        """Delete object from glacier storage.
        
        Args:
            key: Unique key for the data
            connector: Optional connector name to use (defaults to default_connector)
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            ValueError: If no connectors are configured or specified connector is not found
            RuntimeError: If delete operation fails
        """
        if not self.connectors:
            return False
            
        connector_name = connector or self.default_connector
        if connector_name not in self.connectors:
            raise ValueError(f"Connector not found: {connector_name}")
            
        try:
            return self.connectors[connector_name].delete(key)
        except Exception as e:
            self.logger.error(f"Failed to delete object using connector '{connector_name}': {e}")
            raise RuntimeError(f"Delete operation failed: {str(e)}")
    
    def clear(self, connector: Optional[str] = None) -> None:
        """Clear all objects from glacier storage.
        
        Args:
            connector: Optional connector name to use (defaults to all connectors)
            
        Raises:
            ValueError: If specified connector is not found
            RuntimeError: If clear operation fails
        """
        if not self.connectors:
            return
            
        if connector:
            if connector not in self.connectors:
                raise ValueError(f"Connector not found: {connector}")
            connectors_to_clear = {connector: self.connectors[connector]}
        else:
            connectors_to_clear = self.connectors
            
        errors = []
        for name, conn in connectors_to_clear.items():
            try:
                objects = conn.list_objects()
                for obj in objects:
                    conn.delete(obj['key'])
            except Exception as e:
                errors.append(f"Failed to clear objects using connector '{name}': {str(e)}")
                
        if errors:
            raise RuntimeError("\n".join(errors))
    
    def cleanup(self) -> None:
        """Clean up resources and temporary files."""
        # Clean up connectors
        for name, connector in self.connectors.items():
            try:
                connector.cleanup()
            except Exception as e:
                self.logger.error(f"Failed to clean up connector '{name}': {e}")
        
        # Clean up local storage
        try:
            if os.path.exists(self.storage_path):
                for filename in os.listdir(self.storage_path):
                    filepath = os.path.join(self.storage_path, filename)
                    try:
                        if os.path.isfile(filepath):
                            os.unlink(filepath)
                    except Exception as e:
                        self.logger.error(f"Failed to delete file {filepath}: {e}")
                os.rmdir(self.storage_path)
        except Exception as e:
            self.logger.error(f"Failed to clean up storage path: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup is called."""
        self.cleanup()

    async def get_schema(self, source: str, spatial_input: Union[List[float], str], spatial_input_type: str = "bbox") -> Optional[Dict[str, Any]]:
        """Get schema information for data from a specific source.
        
        Args:
            source: Source type ('sentinel', 'landsat', 'osm', 'overture', etc.)
            spatial_input: Spatial input (bounding box coordinates or address)
            spatial_input_type: Type of spatial input ('bbox' or 'address')
            
        Returns:
            Dictionary containing schema information or None if not found
        """
        try:
            if not self.connectors:
                raise ValueError("No connectors configured")
                
            # Get appropriate connector
            connector = None
            if source == "sentinel":
                from .glacier.artifacts.sentinel import SentinelConnector
                connector = SentinelConnector(data_dir=self.storage_path)
            elif source == "landsat":
                from .glacier.artifacts.landsat import LandsatConnector
                connector = LandsatConnector()
            elif source == "osm":
                from .glacier.artifacts.osm import OSMConnector
                connector = OSMConnector(config={}, cache_dir=self.storage_path)
            elif source == "overture":
                from .glacier.artifacts.overture import OvertureConnector
                connector = OvertureConnector(data_dir=self.storage_path)
            else:
                raise ValueError(f"Unsupported source: {source}")
                
            # Get a small sample of data to determine schema
            if spatial_input_type == "bbox":
                if isinstance(spatial_input, list):
                    # Use a very small bounding box for quick schema retrieval
                    bbox = [
                        spatial_input[0],  # south
                        spatial_input[1],  # west
                        spatial_input[0] + 0.001,  # north (tiny area)
                        spatial_input[1] + 0.001   # east (tiny area)
                    ]
                else:
                    raise ValueError("Invalid bbox format")
            else:
                bbox = spatial_input  # For address-based queries
                
            # Get sample data
            data = await connector.get_data(bbox, spatial_input_type)
            if not data:
                return None
                
            # Determine schema based on data type
            if isinstance(data, pd.DataFrame):
                schema = {
                    'columns': list(data.columns),
                    'dtypes': {col: str(dtype) for col, dtype in data.dtypes.items()},
                    'type': 'dataframe',
                    'source': source
                }
            elif isinstance(data, dict):
                schema = {
                    'fields': list(data.keys()),
                    'types': {k: type(v).__name__ for k, v in data.items()},
                    'type': 'dict',
                    'source': source
                }
            elif isinstance(data, gpd.GeoDataFrame):
                schema = {
                    'columns': list(data.columns),
                    'dtypes': {col: str(dtype) for col, dtype in data.dtypes.items()},
                    'geometry_type': str(data.geometry.geom_type.iloc[0]),
                    'crs': str(data.crs),
                    'type': 'geodataframe',
                    'source': source
                }
            else:
                schema = {
                    'type': type(data).__name__,
                    'source': source
                }
                
            # Add metadata from connector if available
            if hasattr(connector, 'get_metadata'):
                schema['metadata'] = connector.get_metadata()
                
            return schema
            
        except Exception as e:
            self.logger.error(f"Failed to get schema for {source}: {e}")
            return None