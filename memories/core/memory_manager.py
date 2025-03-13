from pathlib import Path
from typing import Any, Dict, Optional
import duckdb
import numpy as np
import yaml
import os
import faiss
import logging
from threading import Lock
import re

class MemoryManager:
    """Memory manager for handling different memory tiers."""

    _instance = None
    _lock = Lock()

    def __new__(cls):
        """Create singleton instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        """Initialize memory manager."""
        if not hasattr(self, 'initialized'):
            self.logger = logging.getLogger(__name__)
            self.config = self._load_config()
            self.initialized = True
            self.indexes = {}  # Store FAISS indexes
            self.con = None   # Store DuckDB connection
            self._init_paths()
            self._init_duckdb()
            self._init_cold_memory()
            self._init_faiss()
            self._init_storage_backends()

    def _load_config(self):
        """Load configuration from file.

        Returns:
            Config: Configuration object
        """
        try:
            # Import here to avoid circular imports
            from memories.core.config import Config
            
            # Try to find configuration in standard locations
            config_paths = [
                os.path.join(os.getcwd(), 'config', 'default_config.yml'),
                os.path.join(os.path.dirname(__file__), '..', 'glacier', 'default_config.yml'),
                os.path.join(os.getcwd(), 'config', 'db_config.yml')
            ]
            
            # Use the first config file found
            for config_path in config_paths:
                if os.path.exists(config_path):
                    return Config(config_path)
            
            # If no config file found, use default Config
            self.logger.info("No configuration file found, using default configuration")
            return Config()
            
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            # Import here to avoid circular imports
            from memories.core.config import Config
            # Return a default Config object
            return Config()
            
    def _update_config_recursive(self, base_config: Dict, override_config: Dict) -> None:
        """Recursively update configuration with override values.
        
        Args:
            base_config: Base configuration dictionary to update
            override_config: Override configuration dictionary
        """
        for key, value in override_config.items():
            if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
                self._update_config_recursive(base_config[key], value)
            else:
                base_config[key] = value
                
    def _init_paths(self) -> None:
        """Initialize paths for memory storage."""
        try:
            # Get base path from config
            base_path = Path(self.config.get_path('base_path', 'memory'))
            base_path.mkdir(parents=True, exist_ok=True)
            
            # Create paths for each memory tier
            for tier in ['red_hot', 'hot', 'warm', 'cold', 'glacier']:
                tier_path = base_path / tier
                tier_path.mkdir(parents=True, exist_ok=True)
            
            # Create data paths if they exist in config
            if hasattr(self.config, 'config') and 'data' in self.config.config:
                for path_type in ['storage', 'models', 'cache']:
                    if path_type in self.config.config['data']:
                        data_path = Path(self.config.config['data'][path_type])
                        data_path.mkdir(parents=True, exist_ok=True)
                    
        except Exception as e:
            self.logger.error(f"Error initializing paths: {e}")
            # Create default paths
            base_path = Path('./data/memory')
            base_path.mkdir(parents=True, exist_ok=True)
            for tier in ['red_hot', 'hot', 'warm', 'cold', 'glacier']:
                tier_path = base_path / tier
                tier_path.mkdir(parents=True, exist_ok=True)

    def _init_duckdb(self):
        """Initialize DuckDB connection."""
        try:
            # Get base path for storage
            base_path = Path(self.config.get_path('base_path', 'memory'))
            
            # Create default database path
            db_path = base_path / 'memory.duckdb'
            os.makedirs(base_path, exist_ok=True)
            
            # Get DuckDB configuration
            memory_limit = '8GB'
            threads = 4
            
            # If config has duckdb settings, use them
            if hasattr(self.config, 'hot_duckdb_config'):
                memory_limit = self.config.hot_duckdb_config.get('memory_limit', memory_limit)
                threads = self.config.hot_duckdb_config.get('threads', threads)
            
            # Create persistent connection
            self.con = duckdb.connect(database=str(db_path), read_only=False)
            
            # Set configuration
            self.con.execute(f"SET memory_limit='{memory_limit}'")
            self.con.execute(f"SET threads={threads}")
            
            self.logger.info(f"Successfully initialized DuckDB connection with memory limit {memory_limit}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize DuckDB: {e}")
            # Create in-memory connection as fallback
            self.con = duckdb.connect(database=':memory:', read_only=False)
            self.logger.info("Created in-memory DuckDB connection as fallback")

    def _init_cold_memory(self) -> None:
        """Initialize cold memory storage."""
        try:
            from memories.core.cold import ColdMemory
            
            self.cold = ColdMemory()
            self.logger.info("Cold memory initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing cold memory: {e}")
            self.cold = None
            raise

    def _init_faiss(self):
        """Initialize FAISS index for vector storage."""
        try:
            # Get vector dimension from config
            vector_dim = 384  # Default
            if hasattr(self.config, 'vector_dim'):
                vector_dim = self.config.vector_dim
                
            # Get index type from config
            index_type = 'Flat'  # Default
            if hasattr(self.config, 'faiss_index_type'):
                index_type = self.config.faiss_index_type
                
            # Get GPU settings
            use_gpu = False
            gpu_id = 0
            if hasattr(self.config, 'gpu_id'):
                gpu_id = self.config.gpu_id
                use_gpu = gpu_id >= 0
            
            # Validate index type
            valid_index_types = ['Flat', 'IVF', 'IVFFlat']
            if index_type not in valid_index_types:
                self.logger.warning(f"Invalid FAISS index type: {index_type}. Using Flat instead.")
                index_type = 'Flat'

            # Create index based on type
            if index_type == 'Flat':
                index = faiss.IndexFlatL2(vector_dim)
            elif index_type in ['IVF', 'IVFFlat']:
                quantizer = faiss.IndexFlatL2(vector_dim)
                index = faiss.IndexIVFFlat(quantizer, vector_dim, 100)  # 100 is number of centroids

            # Move to GPU if requested
            if use_gpu and faiss.get_num_gpus() > 0:
                try:
                    res = faiss.StandardGpuResources()
                    index = faiss.index_cpu_to_gpu(res, gpu_id, index)
                    self.logger.info(f"Using GPU {gpu_id} for FAISS index")
                except Exception as gpu_error:
                    self.logger.warning(f"Failed to use GPU for FAISS: {gpu_error}")

            self.indexes['red_hot'] = index
            self.logger.info(f"Initialized FAISS index of type {index_type} with dimension {vector_dim}")
            
        except Exception as e:
            self.logger.error(f"Error initializing FAISS index: {e}")
            # Create a simple fallback index
            self.indexes['red_hot'] = faiss.IndexFlatL2(384)
            self.logger.info("Created fallback FAISS index")
            
    def _init_storage_backends(self) -> None:
        """Initialize storage backends for different memory tiers."""
        self.storage_backends = {}
        
        try:
            # Check if config has glacier settings
            glacier_enabled = False
            
            # If config has the config attribute and glacier settings
            if hasattr(self.config, 'config') and 'memory' in self.config.config:
                memory_config = self.config.config['memory']
                if 'glacier' in memory_config and memory_config['glacier'].get('enabled', False):
                    glacier_enabled = True
                    
                    # Import glacier storage backend
                    from memories.storage.glacier import GlacierStorage
                    
                    # Get glacier settings
                    glacier_config = memory_config['glacier']
                    storage_type = glacier_config.get('type', 's3')
                    
                    if storage_type == 's3':
                        # Initialize S3 glacier storage
                        self.storage_backends['glacier'] = GlacierStorage(
                            bucket=glacier_config.get('bucket', 'memories-glacier'),
                            prefix=glacier_config.get('prefix', 'data/'),
                            region=glacier_config.get('region', 'us-west-2')
                        )
                        self.logger.info("Initialized S3 glacier storage backend")
            
            if not glacier_enabled:
                self.logger.info("Glacier storage not enabled in configuration")
                
        except Exception as e:
            self.logger.error(f"Error initializing storage backends: {e}")

    def cleanup_cold_memory(self, remove_storage: bool = True) -> None:
        """Clean up cold memory data and optionally remove storage directory.
        
        Args:
            remove_storage: Whether to remove the entire storage directory after cleanup
        """
        if not self.cold:
            self.logger.warning("Cold memory is not enabled")
            return
            
        try:
            # Get storage directory paths
            storage_dir = Path(self.config['memory']['base_path'])
            data_storage_dir = Path(self.config['data']['storage'])
            
            # Cleanup cold memory
            if hasattr(self.cold, 'cleanup'):
                self.cold.cleanup()
            
            # Remove storage directories if requested
            if remove_storage:
                if storage_dir.exists():
                    import shutil
                    shutil.rmtree(storage_dir)
                    self.logger.info(f"Removed storage directory {storage_dir}")
                    
                if data_storage_dir.exists():
                    import shutil
                    shutil.rmtree(data_storage_dir)
                    self.logger.info(f"Removed data storage directory {data_storage_dir}")
            
        except Exception as e:
            self.logger.error(f"Error during cold memory cleanup: {e}")
            raise 

    def get_data_source_path(self, source_type: str) -> Path:
        """Get configured path for a specific data source.
        
        Args:
            source_type: Type of data source ('sentinel', 'landsat', 'planetary', 'osm', 'overture')
            
        Returns:
            Path: Configured path for the data source
        """
        try:
            # Handle Config object correctly
            if hasattr(self.config, 'config') and isinstance(self.config.config, dict):
                # Access through the config dictionary if available
                if 'data' in self.config.config and 'storage' in self.config.config['data']:
                    base_path = Path(self.config.config['data']['storage'])
                else:
                    # Fallback to default path
                    base_path = Path(os.path.join(self.project_root, 'data', source_type))
            else:
                # Fallback to default path
                base_path = Path(os.path.join(self.project_root, 'data', source_type))
                
            source_path = base_path / source_type
            source_path.mkdir(parents=True, exist_ok=True)
            return source_path
        except Exception as e:
            self.logger.error(f"Error getting data source path for {source_type}: {e}")
            # Use a default path as fallback
            fallback_path = Path(os.path.join(self.project_root, 'data', source_type))
            fallback_path.mkdir(parents=True, exist_ok=True)
            return fallback_path

    def get_cache_path(self, source_type: str) -> Path:
        """Get cache path for a specific data source.
        
        Args:
            source_type: Type of data source ('sentinel', 'landsat', 'planetary', 'osm', 'overture')
            
        Returns:
            Path: Cache path for the data source
        """
        try:
            # Handle Config object correctly
            if hasattr(self.config, 'config') and isinstance(self.config.config, dict):
                # Access through the config dictionary if available
                if 'data' in self.config.config and 'cache' in self.config.config['data']:
                    base_path = Path(self.config.config['data']['cache'])
                else:
                    # Fallback to default path
                    base_path = Path(os.path.join(self.project_root, 'data', 'cache'))
            else:
                # Fallback to default path
                base_path = Path(os.path.join(self.project_root, 'data', 'cache'))
                
            cache_path = base_path / source_type
            cache_path.mkdir(parents=True, exist_ok=True)
            return cache_path
        except Exception as e:
            self.logger.error(f"Error getting cache path for {source_type}: {e}")
            # Use a default path as fallback
            fallback_path = Path(os.path.join(self.project_root, 'data', 'cache', source_type))
            fallback_path.mkdir(parents=True, exist_ok=True)
            return fallback_path

    def get_warm_path(self) -> str:
        """Get path for warm memory tier.
        
        Returns:
            Path to warm memory storage
        """
        try:
            # Handle Config object correctly
            if hasattr(self.config, 'config') and isinstance(self.config.config, dict):
                if 'memory' in self.config.config and 'base_path' in self.config.config['memory']:
                    base_path = Path(self.config.config['memory']['base_path'])
                    if 'warm' in self.config.config['memory'] and 'path' in self.config.config['memory']['warm']:
                        return str(base_path / self.config.config['memory']['warm']['path'])
                    return str(base_path / 'warm')
            
            # Default fallback path
            return os.path.join(self.project_root, 'data', 'memory', 'warm')
        except Exception as e:
            self.logger.error(f"Error getting warm path: {e}")
            return os.path.join(self.project_root, 'data', 'memory', 'warm')

    def get_duckdb_connection(self) -> duckdb.DuckDBPyConnection:
        """Get shared DuckDB connection.
        
        Returns:
            duckdb.DuckDBPyConnection: Shared DuckDB connection
        """
        return self.con

    def get_faiss_index(self, tier: str = 'red_hot') -> faiss.Index:
        """Get FAISS index for specified tier.
        
        Args:
            tier: Memory tier to get index for (default: 'red_hot')
            
        Returns:
            faiss.Index: FAISS index for the specified tier

        Raises:
            ValueError: If the index type is invalid
        """
        # Re-validate index type in case it was changed after initialization
        if tier == 'red_hot' and 'red_hot' in self.config['memory']:
            index_type = self.config['memory']['red_hot'].get('index_type', 'Flat')
            valid_index_types = ['Flat', 'IVF']
            if index_type not in valid_index_types:
                raise ValueError(f"Invalid FAISS index type: {index_type}. Must be one of {valid_index_types}")

        # Initialize indexes if not already done
        if not hasattr(self, 'indexes'):
            self.indexes = {}
            self._init_faiss()

        return self.indexes.get(tier)
        
    def get_storage_backend(self, tier: str) -> Any:
        """Get storage backend for specified tier.
        
        Args:
            tier: Memory tier to get storage backend for
            
        Returns:
            Any: Storage backend for the specified tier
        """
        if tier not in self.storage_backends:
            raise ValueError(f"No storage backend initialized for tier: {tier}")
        return self.storage_backends[tier]

    def get_connector(self, source_type: str, **kwargs) -> Any:
        """Get initialized connector for a data source.
        
        Args:
            source_type: Type of data source ('sentinel', 'landsat', 'planetary', 'osm', 'overture')
            **kwargs: Additional configuration options for the connector
                - keep_files (bool): Whether to keep downloaded files
                - store_in_cold (bool): Whether to use cold storage
                - data_dir (Path): Optional override for data directory
                - cache_dir (Path): Optional override for cache directory
        
        Returns:
            Initialized connector instance
        """
        try:
            # Get data and cache directories
            data_dir = kwargs.pop('data_dir', None) or self.get_data_source_path(source_type)
            cache_dir = kwargs.pop('cache_dir', None) or self.get_cache_path(source_type)
            
            # Initialize appropriate connector
            if source_type == 'sentinel':
                from memories.core.glacier.artifacts.sentinel import SentinelConnector
                return SentinelConnector(
                    data_dir=data_dir,
                    keep_files=kwargs.get('keep_files', False),
                    store_in_cold=kwargs.get('store_in_cold', True)
                )
            elif source_type == 'landsat':
                from memories.core.glacier.artifacts.landsat import LandsatConnector
                return LandsatConnector()
            elif source_type == 'planetary':
                from memories.core.glacier.artifacts.planetary import PlanetaryConnector
                return PlanetaryConnector(cache_dir=str(cache_dir))
            elif source_type == 'osm':
                from memories.core.glacier.artifacts.osm import OSMConnector
                return OSMConnector(config=kwargs.get('config', {}), cache_dir=str(cache_dir))
            elif source_type == 'overture':
                from memories.core.glacier.artifacts.overture import OvertureConnector
                return OvertureConnector(data_dir=str(data_dir))
            else:
                raise ValueError(f"Unsupported source type: {source_type}")
                
        except Exception as e:
            self.logger.error(f"Error initializing {source_type} connector: {e}")
            raise

    def add_to_hot_memory(self, vector: np.ndarray, metadata: dict):
        # Implementation of add_to_hot_memory method
        pass 

    def get_cold_memory(self):
        """Get cold memory instance.
        
        Returns:
            ColdMemory: Cold memory instance or None if not initialized
        """
        return self.cold 