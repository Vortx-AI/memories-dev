"""
Memories - A hierarchical memory management system for AI applications.
"""

import logging

# Import only the main manager class to avoid circular imports
from memories.core import memory_manager, MemoryManager
from memories.models.load_model import LoadModel
from memories.utils.core.duckdb_utils import query_multiple_parquet
from memories.utils.core.system import system_check, SystemStatus
from memories.core.config import Config

logger = logging.getLogger(__name__)

__version__ = "2.0.6"  # Match version in pyproject.toml

# Define lazy loading functions to avoid circular imports
def get_memory_retrieval():
    """Lazy load MemoryRetrieval to avoid circular imports."""
    from memories.core.memory_retrieval import MemoryRetrieval
    return MemoryRetrieval()

def get_hot_memory():
    """Lazy load HotMemory to avoid circular imports."""
    from memories.core.hot import HotMemory
    return HotMemory()  # No longer needs Redis URL and DB parameters

def get_warm_memory():
    """Lazy load WarmMemory to avoid circular imports."""
    from memories.core.warm import WarmMemory
    return WarmMemory()

def get_cold_memory():
    """Lazy load ColdMemory to avoid circular imports."""
    from memories.core.cold import ColdMemory
    return ColdMemory()

def get_glacier_memory():
    """Lazy load GlacierMemory to avoid circular imports."""
    from memories.core.glacier import GlacierMemory
    return GlacierMemory()

__all__ = [
    # Core components
    "get_memory_retrieval",
    "get_hot_memory",
    "get_warm_memory",
    "get_cold_memory",
    "get_glacier_memory",
    
    # Models
    "LoadModel",
    
    # Utilities
    "query_multiple_parquet",
    
    # System check
    "system_check",
    "SystemStatus",
    
    # Version
    "__version__",
    
    # Memory manager
    "memory_manager",
    "MemoryManager",
    
    # Config
    "Config",
]
