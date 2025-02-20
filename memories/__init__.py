"""
Memories - A package for daily synthesis of Earth Memories
"""

__version__ = "2.0.1"  # Match version in pyproject.toml

# Import core functionality
from memories.core.memory import MemoryStore
from memories.core.hot import HotMemory
from memories.core.warm import WarmMemory
from memories.core.cold import ColdMemory
from memories.core.glacier import GlacierMemory
from memories.core.config import Config
from memories.models.load_model import LoadModel
from memories.utils.processors import gpu_stat
from memories.utils.duckdb_utils import query_multiple_parquet

__all__ = [
    "MemoryStore",
    "HotMemory",
    "WarmMemory",
    "ColdMemory",
    "GlacierMemory",
    "Config",
    "LoadModel",
    "gpu_stat",
    "query_multiple_parquet",
]
