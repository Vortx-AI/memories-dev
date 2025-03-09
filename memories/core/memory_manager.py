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

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file.

        Returns:
            Dict: Configuration dictionary
        """
        try:
            config_path = Path(__file__).parent.parent.parent / 'config' / 'db_config.yml'
            if not config_path.exists():
                raise FileNotFoundError(f"Configuration file not found at {config_path}")
                
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            # Ensure memory section exists
            if 'memory' not in config:
                config['memory'] = {}

            # Set default base path if not provided
            if 'base_path' not in config['memory']:
                config['memory']['base_path'] = './data/memory'

            # Convert base path to absolute path
            config['memory']['base_path'] = str(Path(config['memory']['base_path']).resolve())

            return config
        except Exception as e:
            raise RuntimeError(f"Error loading configuration: {e}")
            
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
        """Initialize and create necessary directory paths."""
        try:
            # Create base memory path
            base_path = Path(self.config['memory']['base_path'])
            base_path.mkdir(parents=True, exist_ok=True)
            
            # Create paths for each memory tier
            for tier in ['red_hot', 'hot', 'warm', 'cold', 'glacier']:
                if tier in self.config['memory']:
                    tier_path = base_path / self.config['memory'][tier]['path']
                    tier_path.mkdir(parents=True, exist_ok=True)
            
            # Create data paths
            for path_type in ['storage', 'models', 'cache']:
                if path_type in self.config['data']:
                    data_path = Path(self.config['data'][path_type])
                    data_path.mkdir(parents=True, exist_ok=True)
                    
        except Exception as e:
            raise RuntimeError(f"Error initializing paths: {e}")

    def _init_duckdb(self):
        """Initialize DuckDB connection."""
        try:
            if 'cold' not in self.config['memory']:
                return None

            duckdb_config = self.config['memory']['cold'].get('duckdb', {})
            memory_limit = duckdb_config.get('memory_limit', '4.0 GiB')
            
            # Normalize memory limit format to GiB
            if isinstance(memory_limit, str):
                # Extract numeric value and unit
                match = re.match(r'(\d+(?:\.\d+)?)\s*([KMGT]?B)', memory_limit.upper())
                if match:
                    value = float(match.group(1))
                    unit = match.group(2)
                    
                    # Convert to GiB
                    multipliers = {
                        'B': 1/(1024**3),
                        'KB': 1/(1024**2),
                        'MB': 1/1024,
                        'GB': 1,
                        'TB': 1024
                    }
                    value = value * multipliers.get(unit, 1)
                    memory_limit = f"{value:.1f} GiB"

            self.con = duckdb.connect(database=':memory:', config={'memory_limit': memory_limit})
            self.logger.info(f"Successfully initialized DuckDB connection with memory limit {memory_limit}")

        except Exception as e:
            self.logger.error(f"Failed to initialize DuckDB connection: {str(e)}")
            raise

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
            if 'red_hot' not in self.config['memory']:
                return None

            use_gpu = self.config['memory']['red_hot'].get('use_gpu', False)
            index_type = self.config['memory']['red_hot'].get('index_type', 'Flat')
            
            # Validate index type
            valid_index_types = ['Flat', 'IVF']
            if index_type not in valid_index_types:
                raise ValueError(f"Invalid FAISS index type: {index_type}. Must be one of {valid_index_types}")

            # Create index based on type
            if index_type == 'Flat':
                index = faiss.IndexFlatL2(384)  # 384 is default vector dimension
            elif index_type == 'IVF':
                quantizer = faiss.IndexFlatL2(384)
                index = faiss.IndexIVFFlat(quantizer, 384, 100)  # 100 is number of centroids

            # Move to GPU if requested
            if use_gpu and faiss.get_num_gpus() > 0:
                res = faiss.StandardGpuResources()
                index = faiss.index_cpu_to_gpu(res, 0, index)

            self.indexes['red_hot'] = index
            self.logger.info(f"Initialized FAISS index of type {index_type}")

        except Exception as e:
            self.logger.error(f"Failed to initialize FAISS index: {str(e)}")
            raise
            
    def _init_storage_backends(self) -> None:
        """Initialize storage backends for different memory tiers."""
        try:
            self.storage_backends = {}
            
            # Initialize Redis for hot tier if configured
            if 'hot' in self.config['memory'] and 'redis_url' in self.config['memory']['hot']:
                import redis
                hot_config = self.config['memory']['hot']
                self.storage_backends['hot'] = redis.from_url(
                    hot_config['redis_url'],
                    db=hot_config.get('redis_db', 0)
                )
                self.logger.info("Redis initialized for hot tier")
            
            # Initialize remote storage for glacier tier if configured
            if 'glacier' in self.config['memory'] and 'remote_storage' in self.config['memory']['glacier']:
                glacier_config = self.config['memory']['glacier']['remote_storage']
                storage_type = glacier_config['type']
                
                if storage_type == 's3':
                    import boto3
                    
                    # Extract AWS credentials
                    credentials = glacier_config.get('credentials', {})
                    client_kwargs = {
                        'region_name': glacier_config['region']
                    }
                    
                    # Add credentials if provided
                    if 'aws_access_key_id' in credentials:
                        client_kwargs['aws_access_key_id'] = credentials['aws_access_key_id']
                    if 'aws_secret_access_key' in credentials:
                        client_kwargs['aws_secret_access_key'] = credentials['aws_secret_access_key']
                    if 'aws_session_token' in credentials:
                        client_kwargs['aws_session_token'] = credentials['aws_session_token']
                    
                    self.storage_backends['glacier'] = boto3.client('s3', **client_kwargs)
                    
                elif storage_type == 'gcs':
                    from google.cloud import storage
                    self.storage_backends['glacier'] = storage.Client()
                elif storage_type == 'azure':
                    from azure.storage.blob import BlobServiceClient
                    self.storage_backends['glacier'] = BlobServiceClient.from_connection_string(
                        glacier_config['connection_string']
                    )
                    
                self.logger.info(f"Remote storage initialized for glacier tier: {storage_type}")
                
        except Exception as e:
            self.logger.error(f"Error initializing storage backends: {e}")
            raise

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
            base_path = Path(self.config['data']['storage'])
            source_path = base_path / source_type
            source_path.mkdir(parents=True, exist_ok=True)
            return source_path
        except Exception as e:
            self.logger.error(f"Error getting data source path for {source_type}: {e}")
            raise

    def get_cache_path(self, source_type: str) -> Path:
        """Get cache path for a specific data source.
        
        Args:
            source_type: Type of data source ('sentinel', 'landsat', 'planetary', 'osm', 'overture')
            
        Returns:
            Path: Cache path for the data source
        """
        try:
            base_path = Path(self.config['data']['cache'])
            cache_path = base_path / source_type
            cache_path.mkdir(parents=True, exist_ok=True)
            return cache_path
        except Exception as e:
            self.logger.error(f"Error getting cache path for {source_type}: {e}")
            raise

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