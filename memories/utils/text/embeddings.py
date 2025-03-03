"""
Text embedding utilities for vector encoding.
"""

import logging
from typing import Optional, Any, Union
from pathlib import Path
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

def get_encoder(
    model_name: str = 'all-MiniLM-L6-v2',
    cache_dir: Optional[Union[str, Path]] = None
) -> Any:
    """Load a vector encoder model.
    
    Args:
        model_name: Name of the model to load (default: 'all-MiniLM-L6-v2')
        cache_dir: Optional directory to cache the model
        
    Returns:
        Loaded model's encode function
    """
    try:
        if cache_dir:
            model = SentenceTransformer(model_name, cache_folder=str(cache_dir))
        else:
            model = SentenceTransformer(model_name)
        logger.info(f"Loaded vector encoder model: {model_name}")
        return model.encode
    except Exception as e:
        logger.error(f"Failed to load vector encoder model: {e}")
        raise 