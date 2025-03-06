"""
Memory manager implementation for managing different memory tiers.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from datetime import datetime
import yaml
import os
import duckdb
import numpy as np

from .config import Config
from .hot import HotMemory
from .red_hot import RedHotMemory
from .warm import WarmMemory
from .cold import ColdMemory
from .glacier import GlacierMemory

# Initialize logger
logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    'memory': {
        'base_path': './data/memory',
        'red_hot': {
            'path': 'red_hot',
            'max_size': 1000000,  # 1M vectors
            'vector_dim': 384,    # Default for all-MiniLM-L6-v2
            'gpu_id': 0,
            'force_cpu': True,    # Default to CPU for stability
            'index_type': 'Flat'  # Simple Flat index
        },
        'hot': {
            'path': 'hot',
            'max_size': 104857600,  # 100MB
            'redis_url': 'redis://localhost:6379',
            'redis_db': 0
        },
        'warm': {
            'path': 'warm',
            'max_size': 1073741824,  # 1GB
            'duckdb': {
                'memory_limit': '8GB',
                'threads': 4,
                'config': {
                    'enable_progress_bar': True,
                    'enable_object_cache': True
                }
            }
        },
        'cold': {
            'path': 'cold',
            'max_size': 10737418240,  # 10GB
            'duckdb': {
                'db_file': 'cold.duckdb',
                'memory_limit': '4GB',
                'threads': 4,
                'config': {
                    'enable_progress_bar': True,
                    'enable_external_access': True,
                    'enable_object_cache': True
                },
                'parquet': {
                    'compression': 'zstd',
                    'row_group_size': 100000,
                    'enable_statistics': True
                }
            }
        },
        'glacier': {
            'path': 'glacier',
            'max_size': 107374182400,  # 100GB
            'remote_storage': {
                'type': 's3',  # or 'gcs', 'azure'
                'bucket': 'my-glacier-storage',
                'prefix': 'data/',
                'region': 'us-west-2',
                'credentials': {
                    'profile': 'default'
                },
                'compression': 'zstd',
                'archive_format': 'parquet'
            }
        }
    }
}

class MemoryManager:
    """Memory manager that handles different memory tiers:
    - Red Hot Memory: GPU-accelerated FAISS for ultra-fast vector similarity search
    - Hot Memory: GPU-accelerated memory for immediate processing
    - Warm Memory: CPU and Redis for fast in-memory access
    - Cold Memory: DuckDB for efficient on-device storage
    - Glacier Memory: Parquet files for off-device compressed storage
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.config = Config()
        
        # Get project root from Config
        project_root = os.getenv("PROJECT_ROOT", os.path.expanduser("~"))
        
        # Initialize DuckDB connection in project root
        db_path = Path(project_root) / 'memories.db'
        self.con = duckdb.connect(str(db_path))
        
        # Initialize cold memory with the connection
        self.cold_memory = ColdMemory(self.con)
        
        self._initialized = True
        logger.info(f"Initialized MemoryManager with database at: {db_path}")

    def _load_and_merge_config(
        self,
        config_path: Optional[Union[str, Path]] = None,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Load and merge configuration from multiple sources."""
        # Start with default config
        config = DEFAULT_CONFIG.copy()
        
        # Try loading from file if provided
        if config_path:
            try:
                with open(config_path, 'r') as f:
                    file_config = yaml.safe_load(f)
                    if file_config:
                        self._deep_update(config, file_config)
                    self.logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                self.logger.warning(f"Failed to load config from {config_path}: {e}")
        
        # Apply custom config overrides if provided
        if custom_config:
            self._deep_update(config, custom_config)
            self.logger.info("Applied custom configuration overrides")
        
        return config

    def _deep_update(self, base_dict: Dict, update_dict: Dict) -> None:
        """Recursively update a dictionary."""
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value

    def _init_duckdb(self) -> None:
        """Initialize single DuckDB connection for warm and cold storage."""
        try:
            import duckdb
            self.db_connection = duckdb.connect(database=':memory:', read_only=False)
            self.logger.info("Initialized DuckDB connection")
        except Exception as e:
            self.logger.error(f"Failed to initialize DuckDB: {e}")
            self.db_connection = None

    def _init_red_hot_memory(self) -> None:
        """Initialize red hot memory tier."""
        try:
            red_hot_config = self.config['memory'].get('red_hot', {})
            red_hot_path = self.config['memory']['base_path'] / red_hot_config.get('path', 'red_hot')
            red_hot_path.mkdir(parents=True, exist_ok=True)
            
            self.red_hot = RedHotMemory(
                storage_path=red_hot_path,
                max_size=red_hot_config.get('max_size', 1000000),
                vector_dim=red_hot_config.get('vector_dim', 384),
                gpu_id=red_hot_config.get('gpu_id', 0),
                force_cpu=red_hot_config.get('force_cpu', True),
                index_type=red_hot_config.get('index_type', 'Flat')
            )
            self.logger.info("Initialized red hot memory")
        except Exception as e:
            self.logger.error(f"Failed to initialize red hot memory: {e}")
            self.red_hot = None

    def _init_hot_memory(self) -> None:
        """Initialize hot memory tier."""
        try:
            hot_config = self.config['memory'].get('hot', {})
            self.hot = HotMemory(
                redis_url=hot_config.get('redis_url', 'redis://localhost:6379'),
                redis_db=hot_config.get('redis_db', 0),
                max_size=hot_config.get('max_size', 100*1024*1024)
            )
            self.logger.info("Initialized hot memory")
        except Exception as e:
            self.logger.error(f"Failed to initialize hot memory: {e}")
            self.hot = None

    def _init_warm_memory(self) -> None:
        """Initialize warm memory tier."""
        try:
            self.warm = WarmMemory(
                duckdb_connection=self.db_connection
            )
            self.logger.info("Initialized warm memory")
        except Exception as e:
            self.logger.error(f"Failed to initialize warm memory: {e}")
            self.warm = None

    def _init_cold_memory(self) -> None:
        """Initialize cold memory tier."""
        try:
            self.cold = ColdMemory(
                duckdb_connection=self.db_connection
            )
            self.logger.info("Initialized cold memory")
        except Exception as e:
            self.logger.error(f"Failed to initialize cold memory: {e}")
            self.cold = None

    def _init_glacier_memory(self) -> None:
        """Initialize glacier memory tier."""
        try:
            glacier_config = self.config['memory'].get('glacier', {})
            glacier_path = self.config['memory']['base_path'] / glacier_config.get('path', 'glacier')
            glacier_path.mkdir(parents=True, exist_ok=True)
            self.glacier = GlacierMemory(
                storage_path=glacier_path,
                max_size=glacier_config.get('max_size', 100*1024*1024*1024)
            )
            self.logger.info("Initialized glacier memory")
        except Exception as e:
            self.logger.error(f"Failed to initialize glacier memory: {e}")
            self.glacier = None

    def get_memory_path(self, memory_type: str) -> Optional[Path]:
        """Get path for specific memory type"""
        try:
            if memory_type not in ['hot', 'warm', 'cold', 'glacier']:
                raise ValueError(f"Invalid memory type: {memory_type}")
                
            config = self.config['memory'][memory_type]
            return self.config['memory']['base_path'] / config['path']
            
        except Exception as e:
            self.logger.error(f"Error getting {memory_type} memory path: {e}")
            return None

    def store(
        self,
        key: str,
        data: Any,
        tier: str = "hot",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Store data in specified memory tier.
        
        Args:
            key: Unique identifier for the data
            data: Data to store (vector data for red_hot tier)
            tier: Memory tier to store in ('red_hot', 'hot', 'warm', 'cold', or 'glacier')
            metadata: Optional metadata to store with the data
        """
        if not isinstance(data, dict) and tier != "red_hot":
            logger.error("Data must be a dictionary for non-red_hot tiers")
            return
        
        # Ensure timestamp exists in metadata
        if metadata is None:
            metadata = {}
        if "timestamp" not in metadata:
            metadata["timestamp"] = datetime.now().isoformat()
        
        # Store in specified tier
        try:
            if tier == "red_hot" and self.red_hot:
                self.red_hot.store(key, data, metadata)
            elif tier == "hot" and self.hot:
                self.hot.store(data)
            elif tier == "warm" and self.warm:
                self.warm.store(data)
            elif tier == "cold" and self.cold:
                self.cold.store(data)
            elif tier == "glacier" and self.glacier:
                self.glacier.store(data)
            else:
                logger.error(f"Invalid memory tier: {tier}")
        except Exception as e:
            logger.error(f"Failed to store in {tier} memory: {e}")
    
    def search_vectors(
        self,
        query_vector: Any,
        k: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors in red hot memory.
        
        Args:
            query_vector: Query vector
            k: Number of results to return
            metadata_filter: Optional filter to apply on metadata
            
        Returns:
            List of results with distances and metadata
        """
        if not self.red_hot:
            logger.error("Red hot memory not available")
            return []
        
        try:
            return self.red_hot.search(query_vector, k, metadata_filter)
        except Exception as e:
            logger.error(f"Failed to search vectors: {e}")
            return []
    
    def retrieve(self, query: Dict[str, Any], tier: str = "hot") -> Optional[Dict[str, Any]]:
        """Retrieve data from specified memory tier.
        
        Args:
            query: Query to match against stored data
            tier: Memory tier to query from ('hot', 'warm', 'cold', or 'glacier')
            
        Returns:
            Retrieved data or None if not found
        """
        try:
            if tier == "hot" and self.hot:
                return self.hot.retrieve(query)
            elif tier == "warm" and self.warm:
                return self.warm.retrieve(query)
            elif tier == "cold" and self.cold:
                return self.cold.retrieve(query)
            elif tier == "glacier" and self.glacier:
                return self.glacier.retrieve(query)
            else:
                logger.error(f"Invalid memory tier: {tier}")
                return None
        except Exception as e:
            logger.error(f"Failed to retrieve from {tier} memory: {e}")
            return None
    
    def retrieve_all(self, tier: str = "hot") -> List[Dict[str, Any]]:
        """Retrieve all data from specified memory tier.
        
        Args:
            tier: Memory tier to retrieve from ('hot', 'warm', 'cold', or 'glacier')
            
        Returns:
            List of all stored data
        """
        try:
            if tier == "hot" and self.hot:
                return self.hot.retrieve_all()
            elif tier == "warm" and self.warm:
                return self.warm.retrieve_all()
            elif tier == "cold" and self.cold:
                return self.cold.retrieve_all()
            elif tier == "glacier" and self.glacier:
                return self.glacier.retrieve_all()
            else:
                logger.error(f"Invalid memory tier: {tier}")
                return []
        except Exception as e:
            logger.error(f"Failed to retrieve all from {tier} memory: {e}")
            return []
    
    def clear(self, tier: Optional[str] = None) -> None:
        """Clear data from specified memory tier or all tiers if none specified.
        
        Args:
            tier: Memory tier to clear ('red_hot', 'hot', 'warm', 'cold', or 'glacier')
                 If None, clears all tiers
        """
        try:
            if tier is None or tier == "red_hot":
                if self.red_hot:
                    self.red_hot.clear()
            
            if tier is None or tier == "hot":
                if self.hot:
                    self.hot.clear()
            
            if tier is None or tier == "warm":
                if self.warm:
                    self.warm.clear()
            
            if tier is None or tier == "cold":
                if self.cold:
                    self.cold.clear()
            
            if tier is None or tier == "glacier":
                if self.glacier:
                    self.glacier.clear()
        except Exception as e:
            logger.error(f"Failed to clear memory: {e}")
    
    def cleanup(self) -> None:
        """Cleanup all memory tiers and connections."""
        # Cleanup memory tiers
        if self.warm:
            self.warm.cleanup()
        if self.cold:
            self.cold.cleanup()
        
        # Close shared DuckDB connection
        if self.db_connection:
            self.db_connection.close()
            self.db_connection = None
    
    def __del__(self):
        """Destructor to ensure cleanup is performed."""
        self.cleanup()

    def configure_tiers(
        self,
        red_hot_config: Optional[Dict[str, Any]] = None,
        hot_config: Optional[Dict[str, Any]] = None,
        warm_config: Optional[Dict[str, Any]] = None,
        cold_config: Optional[Dict[str, Any]] = None,
        glacier_config: Optional[Dict[str, Any]] = None,
        reinitialize: bool = True
    ) -> None:
        """Configure memory tiers with custom values and paths.
        
        Args:
            red_hot_config: Configuration for red hot memory tier
                Example: {
                    'path': 'custom/red_hot',
                    'max_size': 2000000,
                    'vector_dim': 512,
                    'gpu_id': 1,
                    'force_cpu': True,
                    'index_type': 'Flat'
                }
            hot_config: Configuration for hot memory tier
                Example: {
                    'path': 'custom/hot',
                    'max_size': 209715200,  # 200MB
                    'redis_url': 'redis://custom:6379',
                    'redis_db': 1
                }
            warm_config: Configuration for warm memory tier
                Example: {
                    'path': 'custom/warm',
                    'max_size': 2147483648,  # 2GB
                    'duckdb': {
                        'memory_limit': '16GB',
                        'threads': 8
                    }
                }
            cold_config: Configuration for cold memory tier
                Example: {
                    'path': 'custom/cold',
                    'max_size': 21474836480,  # 20GB
                    'duckdb': {
                        'db_file': 'custom.duckdb',
                        'memory_limit': '8GB',
                        'threads': 8,
                        'parquet': {
                            'compression': 'zstd',
                            'row_group_size': 200000
                        }
                    }
                }
            glacier_config: Configuration for glacier memory tier
                Example: {
                    'path': 'custom/glacier',
                    'max_size': 214748364800,  # 200GB
                    'remote_storage': {
                        'type': 's3',
                        'bucket': 'custom-bucket',
                        'prefix': 'custom/data/',
                        'region': 'us-east-1'
                    }
                }
            reinitialize: Whether to reinitialize the memory tiers with new config
        """
        # Update configurations
        if red_hot_config:
            self._deep_update(self.config['memory']['red_hot'], red_hot_config)
            if reinitialize and self.red_hot is not None:
                self._init_red_hot_memory()
        
        if hot_config:
            self._deep_update(self.config['memory']['hot'], hot_config)
            if reinitialize and self.hot is not None:
                self._init_hot_memory()
        
        if warm_config:
            self._deep_update(self.config['memory']['warm'], warm_config)
            if reinitialize and self.warm is not None:
                self._init_warm_memory()
        
        if cold_config:
            self._deep_update(self.config['memory']['cold'], cold_config)
            if reinitialize and self.cold is not None:
                self._init_cold_memory()
        
        if glacier_config:
            self._deep_update(self.config['memory']['glacier'], glacier_config)
            if reinitialize and self.glacier is not None:
                self._init_glacier_memory()
        
        self.logger.info("Memory tiers configuration updated")

    def add_to_tier(
        self,
        tier: str,
        data: Any,
        key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> bool:
        """Add data to a specific memory tier with appropriate handling for each type.
        
        Args:
            tier: Memory tier to add data to ('red_hot', 'hot', 'warm', 'cold', or 'glacier')
            data: Data to store. Format depends on tier:
                - red_hot: vector data (numpy array or torch tensor)
                - hot: dictionary data for Redis
                - warm: dictionary data for DuckDB
                - cold: dictionary data or path to Parquet file
                - glacier: dictionary data or path to file for remote storage
            key: Optional key for the data (required for red_hot tier)
            metadata: Optional metadata to store with the data
            **kwargs: Additional arguments specific to each tier:
                red_hot:
                    - vector_dim: dimension of the vector
                hot:
                    - expiry: optional TTL in seconds
                warm:
                    - table_name: optional custom table name
                cold:
                    - parquet_path: path to Parquet file if adding external file
                    - theme: optional theme for organizing data
                    - tag: optional tag for organizing data
                glacier:
                    - bucket: optional override for S3 bucket
                    - prefix: optional override for S3 prefix
                    
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate tier
            if tier not in ['red_hot', 'hot', 'warm', 'cold', 'glacier']:
                self.logger.error(f"Invalid memory tier: {tier}")
                return False

            # Ensure metadata has timestamp
            if metadata is None:
                metadata = {}
            if 'timestamp' not in metadata:
                metadata['timestamp'] = datetime.now().isoformat()

            # Handle each tier appropriately
            if tier == 'red_hot':
                if not key:
                    self.logger.error("Key is required for red_hot tier")
                    return False
                if self.red_hot:
                    self.red_hot.store(key=key, vector_data=data, metadata=metadata)
                    return True

            elif tier == 'hot':
                if not isinstance(data, dict):
                    self.logger.error("Data must be a dictionary for hot tier")
                    return False
                if self.hot:
                    self.hot.store(data)
                    return True

            elif tier == 'warm':
                if not isinstance(data, dict):
                    self.logger.error("Data must be a dictionary for warm tier")
                    return False
                if self.warm:
                    table_name = kwargs.get('table_name', 'warm_data')
                    self.warm.store(data, metadata=metadata)
                    return True

            elif tier == 'cold':
                if self.cold:
                    if isinstance(data, (str, Path)):  # Parquet file path
                        return self.cold.query_storage(
                            query="SELECT 1",  # Validate file is readable
                            additional_files=[data]
                        ) is not None
                    elif isinstance(data, dict):
                        self.cold.store(data)
                        return True
                    else:
                        self.logger.error("Data must be a dictionary or path to Parquet file for cold tier")
                        return False

            elif tier == 'glacier':
                if self.glacier:
                    if isinstance(data, dict):
                        self.glacier.store(data, metadata=metadata)
                        return True
                    elif isinstance(data, (str, Path)):  # File path
                        path = Path(data)
                        if not path.exists():
                            self.logger.error(f"File not found: {path}")
                            return False
                        # Add file-specific metadata
                        file_metadata = {
                            'filename': path.name,
                            'size': path.stat().st_size,
                            'last_modified': datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
                            **metadata
                        }
                        self.glacier.store(
                            data={'file_path': str(path)},
                            metadata=file_metadata
                        )
                        return True
                    else:
                        self.logger.error("Data must be a dictionary or file path for glacier tier")
                        return False

            return False

        except Exception as e:
            self.logger.error(f"Failed to add data to {tier} tier: {e}")
            return False

    def batch_import_parquet(
        self,
        folder_path: Union[str, Path],
        theme: Optional[str] = None,
        tag: Optional[str] = None,
        recursive: bool = True,
        pattern: str = "*.parquet"
    ) -> Dict[str, Any]:
        """Import multiple parquet files into cold storage.
        
        Args:
            folder_path: Path to folder containing parquet files
            theme: Optional theme tag for the data
            tag: Optional additional tag for the data
            recursive: Whether to search subdirectories
            pattern: File pattern to match
            
        Returns:
            Dict containing:
                files_processed: Number of files processed
                records_imported: Total number of records imported
                total_size: Total size of imported data in bytes
                errors: List of files that had errors
        """
        if not self.cold:
            raise RuntimeError("Cold memory is not enabled. Enable it by setting enable_cold=True")

        try:
            # Delegate to cold memory's implementation
            results = self.cold.batch_import_parquet(
                folder_path=folder_path,
                theme=theme,
                tag=tag,
                recursive=recursive,
                pattern=pattern
            )
            
            # Log the results
            logger.info(
                f"Parquet import complete - "
                f"Processed: {results['files_processed']} files, "
                f"Imported: {results['records_imported']} records, "
                f"Size: {results['total_size'] / (1024*1024):.2f} MB"
            )
            
            if results['errors']:
                logger.warning(f"Errors occurred in {len(results['errors'])} files")
                
            return results
            
        except Exception as e:
            logger.error(f"Failed to import parquet files: {e}")
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
            storage_dir = self.config['memory']['base_path']
            if not storage_dir.exists():
                self.logger.info("No existing storage directory found")
                return
                
            cold_dir = storage_dir / self.config['memory']['cold']['path']
            if not cold_dir.exists():
                self.logger.info("No existing cold storage directory found")
                return
                
            # Clear all tables and their data
            self.logger.info("Clearing cold memory tables and data...")
            self.cold.clear_tables(keep_files=False)
            
            # Close DuckDB connection if it exists
            if hasattr(self, 'cold_db'):
                self.cold_db.close()
                self.logger.info("Closed cold DuckDB connection")
            
            # Optionally remove the entire storage directory
            if remove_storage and storage_dir.exists():
                self.logger.info("Removing storage directory...")
                import shutil
                shutil.rmtree(storage_dir)
                self.logger.info("Storage directory removed")
                
            self.logger.info("Cold memory cleanup completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error during cold memory cleanup: {e}")
            raise 

    def add_to_hot_memory(self, vector: np.ndarray, metadata: dict):
        """Add item to red-hot memory."""
        self.red_hot.add_item(vector, metadata)

    def search_hot_memory(self, query_vector: np.ndarray, k: int = 5):
        """Search red-hot memory."""
        return self.red_hot.search_knn(query_vector, k) 