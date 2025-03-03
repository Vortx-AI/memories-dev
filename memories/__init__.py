"""
Memories - A package for daily synthesis of Earth Memories
"""

import logging

from memories.core.memory_retrieval import MemoryRetrieval
from memories.core.hot import HotMemory
from memories.core.warm import WarmMemory
from memories.core.cold import ColdMemory
from memories.core.glacier import GlacierMemory
from memories.core.config import Config
from memories.models.load_model import LoadModel
from memories.utils.core.duckdb_utils import query_multiple_parquet
from memories.utils.core.system import system_check, SystemStatus


logger = logging.getLogger(__name__)

__version__ = "2.0.3"  # Match version in pyproject.toml

__all__ = [
    # Core components
    "MemoryRetrieval",
    "HotMemory",
    "WarmMemory",
    "ColdMemory",
    "GlacierMemory",
    
    # Models
    "LoadModel",
    
    # Utilities
    "query_multiple_parquet",
    
    # System check
    "system_check",
    "SystemStatus",
    
    # Version
    "__version__",
]
