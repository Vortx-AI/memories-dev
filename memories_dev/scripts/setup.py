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
from ..models.base_model import BaseModel
from ..utils.processors.gpu_stat import check_gpu_memory
from ..synthetic.generator import initialize_stable_diffusion

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
        config = load_config(config_path)
        
        # Check GPU availability
        if torch.cuda.is_available():
            logger.info("GPU available, checking memory...")
            check_gpu_memory()
        else:
            logger.warning("No GPU available, using CPU")
            
        # Initialize models
        initialize_models(config.get('models', {}))
        
        # Initialize Stable Diffusion
        if config.get('use_stable_diffusion', False):
            initialize_stable_diffusion()
            
        # Set up data directories
        setup_directories(config.get('directories', {}))
        
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