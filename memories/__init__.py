"""
Memories - A hierarchical memory management system for AI applications.
"""

import logging

# Safe imports with fallbacks
logger = logging.getLogger(__name__)

try:
    from memories.core import memory_manager, MemoryManager
except ImportError as e:
    logger.warning(f"Core memory manager not available: {e}")
    memory_manager = None
    MemoryManager = None

try:
    from memories.models.load_model import LoadModel
except ImportError as e:
    logger.warning(f"Model loader not available: {e}")
    LoadModel = None

try:
    from memories.utils.core.duckdb_utils import query_multiple_parquet
except ImportError as e:
    logger.warning(f"DuckDB utilities not available: {e}")
    query_multiple_parquet = None

try:
    from memories.utils.core.system import system_check, SystemStatus
except ImportError as e:
    logger.warning(f"System utilities not available: {e}")
    system_check = None
    SystemStatus = None

try:
    from memories.core.config import Config
except ImportError as e:
    logger.warning(f"Config module not available: {e}")
    Config = None

# Always available - simple memory store without dependencies
from memories.simple_memory import SimpleMemoryStore, SimpleConfig, create_memory_store, verify_ai_response

logger = logging.getLogger(__name__)

__version__ = "2.0.9"  # Match version in pyproject.toml

# Define lazy loading functions to avoid circular imports
def get_memory_retrieval():
    """Lazy load MemoryRetrieval to avoid circular imports."""
    try:
        from memories.core.memory_retrieval import MemoryRetrieval
        return MemoryRetrieval()
    except ImportError as e:
        logger.warning(f"MemoryRetrieval not available: {e}")
        return None

def get_hot_memory():
    """Lazy load HotMemory to avoid circular imports."""
    try:
        from memories.core.hot import HotMemory
        return HotMemory()
    except ImportError as e:
        logger.warning(f"HotMemory not available: {e}")
        return None

def get_warm_memory():
    """Lazy load WarmMemory to avoid circular imports."""
    try:
        from memories.core.warm import WarmMemory
        return WarmMemory()
    except ImportError as e:
        logger.warning(f"WarmMemory not available: {e}")
        return None

def get_cold_memory():
    """Lazy load ColdMemory to avoid circular imports."""
    try:
        from memories.core.cold import ColdMemory
        return ColdMemory()
    except ImportError as e:
        logger.warning(f"ColdMemory not available: {e}")
        return None

def get_glacier_memory():
    """Lazy load GlacierMemory to avoid circular imports."""
    try:
        from memories.core.glacier import GlacierMemory
        return GlacierMemory()
    except ImportError as e:
        logger.warning(f"GlacierMemory not available: {e}")
        return None

__all__ = [
    # Core components
    "get_memory_retrieval",
    "get_hot_memory",
    "get_warm_memory",
    "get_cold_memory",
    "get_glacier_memory",
    
    # Simple memory (always available)
    "SimpleMemoryStore",
    "SimpleConfig", 
    "create_memory_store",
    "verify_ai_response",
    
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
