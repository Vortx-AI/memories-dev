import subprocess
import torch

import logging
from typing import Dict, Optional

# Initialize GPU support flags
HAS_CUDF = False
cudf = None

try:
    import cudf
    HAS_CUDF = True
except ImportError:
    pass

logger = logging.getLogger(__name__)

def check_gpu_memory() -> Optional[Dict[str, int]]:
    """
    Check the total and available GPU memory and current utilization.
    Uses `nvidia-smi` for detailed monitoring if available, 
    otherwise falls back to PyTorch's `torch.cuda` API.
    """
    if not (HAS_CUDF and cudf):
        logger.warning("GPU support not available")
        return None
    
    try:
        # Use `torch.cuda` API for memory stats
        total_memory = torch.cuda.get_device_properties(0).total_memory / 1e9  # Convert to GB
        reserved_memory = torch.cuda.memory_reserved(0) / 1e9  # Reserved by PyTorch
        allocated_memory = torch.cuda.memory_allocated(0) / 1e9  # Allocated by PyTorch
        free_memory = reserved_memory - allocated_memory

        print(f"Using PyTorch GPU Stats:")
        print(f"Total GPU Memory: {total_memory:.2f} GB")
        print(f"Allocated GPU Memory: {allocated_memory:.2f} GB")
        print(f"Reserved GPU Memory: {reserved_memory:.2f} GB")
        print(f"Free GPU Memory: {free_memory:.2f} GB\n")

        # Use `nvidia-smi` for detailed stats if available
        try:
            nvidia_smi_output = subprocess.check_output(["nvidia-smi"], text=True)
            print(f"nvidia-smi output:\n{nvidia_smi_output}")
        except FileNotFoundError:
            print("nvidia-smi not available. Install NVIDIA tools for detailed stats.")

        # Get GPU memory stats
        memory_info = cudf.cuda.current_context().memory_info()
        return {
            'total': memory_info.total,
            'free': memory_info.free,
            'used': memory_info.used
        }
    except Exception as e:
        logger.error(f"Error checking GPU memory: {e}")
        return None

def get_gpu_utilization() -> Optional[float]:
    """Get GPU utilization percentage."""
    if not (HAS_CUDF and cudf):
        logger.warning("GPU support not available")
        return None
    
    try:
        # Get GPU utilization
        return cudf.cuda.current_context().gpu_busy_time()
    except Exception as e:
        logger.error(f"Error checking GPU utilization: {e}")
        return None


