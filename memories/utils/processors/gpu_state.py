import torch
import gc
import logging

logger = logging.getLogger(__name__)

def cleanup_memory():
    """Clean up GPU and CPU memory after model execution."""
    try:
        # Clear PyTorch's CUDA cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        # Force garbage collection
        gc.collect()
        
        logger.debug("Memory cleanup completed")
    except Exception as e:
        logger.warning(f"Memory cleanup warning: {str(e)}")
