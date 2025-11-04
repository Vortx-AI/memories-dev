"""
Core components of the memories system.
"""

# Import only the main manager class to avoid circular imports
from memories.core.memory_manager import MemoryManager

# Other imports should be done directly by the modules that need them
# to avoid circular dependencies
# from memories.core.hot import HotMemory
# from memories.core.warm import WarmMemory
# from memories.core.cold import ColdMemory
# from memories.core.glacier import GlacierMemory

# Create a singleton instance of the memory manager
memory_manager = MemoryManager()

from .analyzers import (
    TerrainAnalyzer,
    ClimateAnalyzer,
    WaterResourceAnalyzer,
    EnvironmentalAnalyzer
)
from .analyzers.change_detector import ChangeDetector

__all__ = [
    "MemoryManager",
    "memory_manager",
    "TerrainAnalyzer",
    "ClimateAnalyzer",
    "WaterResourceAnalyzer",
    "EnvironmentalAnalyzer",
    "ChangeDetector"
]
