"""
Setup script for initializing components.
"""

import os
import logging
from pathlib import Path
from typing import Optional
import yaml
from dotenv import load_dotenv
import torch
try:
    import tensorflow as tf
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
from memories.models.base_model import BaseModel
from memories.utils.processors.gpu_stat import check_gpu_memory
from memories.synthetic.generator import initialize_stable_diffusion
from memories.config import Config, set_config, set_default_device, set_backend, configure_storage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_environment(config_path: Optional[str] = None):
    """
    Set up the environment and initialize components.
    
    Args:
        config_path: Optional path to config file
    """
    try:
        # Load environment variables
        load_dotenv()
        
        # Load configuration
        config_dict = load_config(config_path)
        
        # Create and initialize config
        config = Config(
            storage_path=config_dict.get('data', {}).get('storage', './data/storage'),
            hot_memory_size=config_dict.get('memory', {}).get('hot', {}).get('max_size', 1000),
            warm_memory_size=config_dict.get('memory', {}).get('warm', {}).get('max_size', 10000),
            cold_memory_size=config_dict.get('memory', {}).get('cold', {}).get('max_size', 100000),
            redis_url=config_dict.get('redis', {}).get('url', 'redis://localhost:6379'),
            redis_db=config_dict.get('redis', {}).get('db', 0),
            backend=config_dict.get('model', {}).get('backend', 'pytorch')
        )
        set_config(config)
        
        # Configure storage
        storage_config = config_dict.get('storage', {})
        if storage_config:
            configure_storage(
                storage_type=storage_config.get('type', 'local'),
                base_path=storage_config.get('base_path', './data'),
                cache_size_gb=storage_config.get('cache_size_gb', 5),
                bucket_name=storage_config.get('bucket_name'),
                region=storage_config.get('region'),
                credentials=storage_config.get('credentials')
            )
        
        # Configure ML backend and device
        backend = config_dict.get('model', {}).get('backend', 'pytorch')
        if backend == 'pytorch':
            # Configure PyTorch
            if torch.cuda.is_available():
                logger.info("GPU available for PyTorch, checking memory...")
                check_gpu_memory()
                device = torch.device("cuda")
                logger.info(f"Using GPU: {torch.cuda.get_device_name(0)}")
            else:
                logger.warning("GPU not available for PyTorch, using CPU")
                device = torch.device("cpu")
            set_default_device(device)
            
        elif backend == 'tensorflow' and TENSORFLOW_AVAILABLE:
            # Configure TensorFlow
            logger.info("Configuring TensorFlow backend")
            gpus = tf.config.list_physical_devices('GPU')
            if gpus:
                try:
                    # Configure memory growth for all GPUs
                    for gpu in gpus:
                        tf.config.experimental.set_memory_growth(gpu, True)
                    logical_gpus = tf.config.list_logical_devices('GPU')
                    logger.info(f"Available GPUs: {len(gpus)} physical, {len(logical_gpus)} logical")
                except RuntimeError as e:
                    logger.error(f"Error configuring TensorFlow GPUs: {e}")
            else:
                logger.warning("GPU not available for TensorFlow, using CPU")
            set_backend('tensorflow')
        else:
            if backend == 'tensorflow' and not TENSORFLOW_AVAILABLE:
                logger.warning("TensorFlow not available, falling back to PyTorch")
                config.backend = 'pytorch'
                if torch.cuda.is_available():
                    device = torch.device("cuda")
                else:
                    device = torch.device("cpu")
                set_default_device(device)
            
        # Initialize models
        initialize_models(config_dict.get('models', {}))
        
        # Initialize Stable Diffusion
        if config_dict.get('use_stable_diffusion', False):
            initialize_stable_diffusion()
            
        # Set up data directories
        setup_directories(config_dict.get('directories', {}))
        
        logger.info("Setup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during setup: {str(e)}")
        raise

def load_config(config_path: Optional[str] = None) -> dict:
    """
    Load configuration from file.
    
    Args:
        config_path: Path to config file
        
    Returns:
        Configuration dictionary
    """
    if config_path is None:
        config_path = os.getenv('CONFIG_PATH', 'config/default.yaml')
        
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
        return config
        
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        return {}

def initialize_models(model_config: dict):
    """
    Initialize ML models.
    
    Args:
        model_config: Model configuration
    """
    try:
        base_model = BaseModel.get_instance()
        
        # Initialize each configured model
        for model_name, config in model_config.items():
            logger.info(f"Initializing model: {model_name}")
            success = base_model.initialize_model(
                model=config.get('name', 'default'),
                use_gpu=config.get('use_gpu', True)
            )
            if not success:
                logger.warning(f"Failed to initialize {model_name}")
                
    except Exception as e:
        logger.error(f"Error initializing models: {str(e)}")

def setup_directories(directory_config: dict):
    """
    Set up required directories.
    
    Args:
        directory_config: Directory configuration
    """
    try:
        for name, path in directory_config.items():
            # Create directory if it doesn't exist
            Path(path).mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")
            
    except Exception as e:
        logger.error(f"Error setting up directories: {str(e)}")

if __name__ == "__main__":
    setup_environment() 