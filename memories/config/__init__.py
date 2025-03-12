"""
Configuration for the memories system.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, Literal
import torch
import logging
import os

logger = logging.getLogger(__name__)

@dataclass
class StorageConfig:
    """Configuration for storage system."""
    storage_type: Literal["local"]
    base_path: str
    cache_size_gb: float
    
    def __post_init__(self):
        """Validate storage configuration."""
        if self.storage_type != "local":
            raise ValueError("storage_type must be 'local'")
            
        # Convert and create base path
        self.base_path = Path(self.base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

@dataclass
class Config:
    """Configuration for the memories system."""
    
    storage_path: str
    hot_memory_size: int
    warm_memory_size: int
    cold_memory_size: int
    redis_url: Optional[str] = "redis://localhost:6379"
    redis_db: Optional[int] = 0
    device: Optional[str] = None
    backend: Literal["pytorch", "tensorflow"] = "pytorch"
    backend_config: Dict[str, Any] = None
    storage_config: Optional[StorageConfig] = None
    
    def __post_init__(self):
        """Validate and process configuration after initialization."""
        # Convert storage path to Path object
        self.storage_path = Path(self.storage_path)
        
        # Create storage directory if it doesn't exist
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize backend config if None
        if self.backend_config is None:
            self.backend_config = {}
        
        # Validate memory sizes
        if self.hot_memory_size <= 0:
            raise ValueError("hot_memory_size must be positive")
        if self.warm_memory_size <= 0:
            raise ValueError("warm_memory_size must be positive")
        if self.cold_memory_size <= 0:
            raise ValueError("cold_memory_size must be positive")
        
        # Validate memory size relationships
        if self.hot_memory_size > self.warm_memory_size:
            raise ValueError("hot_memory_size must be less than or equal to warm_memory_size")
        if self.warm_memory_size > self.cold_memory_size:
            raise ValueError("warm_memory_size must be less than or equal to cold_memory_size")
        
        # Validate backend
        if self.backend not in ["pytorch", "tensorflow"]:
            raise ValueError("backend must be either 'pytorch' or 'tensorflow'")

# Global config instance
_config = None

def get_config() -> Config:
    """Get the global config instance."""
    global _config
    if _config is None:
        # Create default config
        _config = Config(
            storage_path=os.getenv('MEMORIES_STORAGE_PATH', './data/storage'),
            hot_memory_size=int(os.getenv('MEMORIES_HOT_MEMORY_SIZE', '1000')),
            warm_memory_size=int(os.getenv('MEMORIES_WARM_MEMORY_SIZE', '10000')),
            cold_memory_size=int(os.getenv('MEMORIES_COLD_MEMORY_SIZE', '100000')),
            redis_url=os.getenv('MEMORIES_REDIS_URL', 'redis://localhost:6379'),
            redis_db=int(os.getenv('MEMORIES_REDIS_DB', '0')),
            backend=os.getenv('MEMORIES_BACKEND', 'pytorch')
        )
    return _config

def set_config(config: Config):
    """Set the global config instance."""
    global _config
    _config = config

def set_default_device(device: torch.device):
    """Set the default device for PyTorch.
    
    Args:
        device: The torch device to use (e.g., torch.device("cuda") or torch.device("cpu"))
    """
    config = get_config()
    config.device = str(device)
    config.backend = "pytorch"
    config.backend_config["device"] = str(device)

def set_backend(backend: str, **kwargs):
    """Set the ML backend and its configuration.
    
    Args:
        backend: The ML backend to use ('pytorch' or 'tensorflow')
        **kwargs: Additional backend-specific configuration
    """
    config = get_config()
    
    if backend not in ["pytorch", "tensorflow"]:
        raise ValueError("backend must be either 'pytorch' or 'tensorflow'")
    
    config.backend = backend
    config.backend_config.update(kwargs)
    
    if backend == "tensorflow":
        import tensorflow as tf
        gpus = tf.config.list_physical_devices('GPU')
        config.backend_config["gpus"] = gpus
        if gpus:
            config.device = "GPU"
            # Configure memory growth for all GPUs
            for gpu in gpus:
                try:
                    tf.config.experimental.set_memory_growth(gpu, True)
                except RuntimeError as e:
                    print(f"Error configuring GPU {gpu}: {e}")
        else:
            config.device = "CPU"

def configure_storage(
    storage_type: str,
    base_path: str,
    cache_size_gb: float
) -> None:
    """Configure the storage system.
    
    Args:
        storage_type: Type of storage (only "local" is supported)
        base_path: Base path for storage
        cache_size_gb: Size of cache in GB
    """
    config = get_config()  # This will create a default config if none exists
    
    try:
        storage_config = StorageConfig(
            storage_type=storage_type,
            base_path=base_path,
            cache_size_gb=cache_size_gb
        )
        
        # Initialize storage system
        logger.info(f"Configuring local storage at {base_path}")
        # Local storage initialization is handled in StorageConfig.__post_init__
        
        config.storage_config = storage_config
        logger.info("Storage configuration completed successfully")
        
    except Exception as e:
        logger.error(f"Error configuring storage: {str(e)}")
