"""
Memories - A package for daily synthesis of Earth Memories
"""

import logging

from memories.core.memory import MemoryStore
from memories.core.hot import HotMemory
from memories.core.warm import WarmMemory
from memories.core.cold import ColdMemory
from memories.core.glacier import GlacierMemory
from memories.core.config import Config
from memories.models.load_model import LoadModel
from memories.utils.processors import gpu_stat
from memories.utils.duckdb_utils import query_multiple_parquet
from memories.utils.system import system_check, SystemStatus
from .config import get_config, configure_storage

logger = logging.getLogger(__name__)

__version__ = "2.0.3"  # Match version in pyproject.toml

__all__ = [
    # Core components
    "MemoryStore",
    "HotMemory",
    "WarmMemory",
    "ColdMemory",
    "GlacierMemory",
    "Config",
    
    # Models
    "LoadModel",
    
    # Utilities
    "gpu_stat",
    "query_multiple_parquet",
    
    # System check
    "system_check",
    "SystemStatus",
    
    # Version
    "__version__",
]
