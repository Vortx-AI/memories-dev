"""
Memories - A hierarchical memory management system for AI applications.
"""

import logging

# Import only the main manager class to avoid circular imports
from memories.core import memory_manager, MemoryManager
# Lazy loading for system utilities to avoid heavy imports
def system_check(*args, **kwargs):
    from memories.utils.core.system import system_check as _system_check
    return _system_check(*args, **kwargs)

def get_system_status():
    from memories.utils.core.system import SystemStatus
    return SystemStatus

# Lazily load the duckdb utility to avoid importing heavy optional dependencies
def get_query_multiple_parquet():
    from memories.utils.core.duckdb_utils import query_multiple_parquet
    return query_multiple_parquet
from memories.core.config import Config

# Lazy loader for the model utilities to avoid heavy imports at package load
def get_load_model():
    """Lazy load and return the LoadModel class."""
    from memories.models.load_model import LoadModel
    return LoadModel

logger = logging.getLogger(__name__)

__version__ = "2.0.8"  # Match version in pyproject.toml

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
    "get_load_model",

    # Utilities
    "get_query_multiple_parquet",
    
    # System check
    "system_check",
    "get_system_status",
    
    # Version
    "__version__",
    
    # Memory manager
    "memory_manager",
    "MemoryManager",
    
    # Config
    "Config",
]
