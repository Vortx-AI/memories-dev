"""Memory store functionality for storing data in different memory tiers."""

import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from datetime import datetime

from memories.core.memory_manager import MemoryManager
from memories.core.hot import HotMemory
from memories.core.warm import WarmMemory
from memories.core.cold import ColdMemory
from memories.core.red_hot import RedHotMemory

logger = logging.getLogger(__name__)

class MemoryStore:
    """Memory store for handling data storage across different memory tiers."""
    
    def __init__(self):
        """Initialize memory store."""
        self.memory_manager = MemoryManager()
        self.logger = logging.getLogger(__name__)
        
        # Initialize memory tiers as None - will be created on demand
        self._hot_memory = None
        self._warm_memory = None
        self._cold_memory = None
        self._red_hot_memory = None

    def _init_hot(self) -> None:
        """Initialize hot memory on demand."""
        if not self._hot_memory:
            self._hot_memory = HotMemory()

    def _init_warm(self) -> None:
        """Initialize warm memory on demand."""
        if not self._warm_memory:
            self._warm_memory = WarmMemory()

    def _init_cold(self) -> None:
        """Initialize cold memory on demand."""
        if not self._cold_memory:
            self._cold_memory = ColdMemory()

    def _init_red_hot(self) -> None:
        """Initialize red hot memory on demand."""
        if not self._red_hot_memory:
            self._red_hot_memory = RedHotMemory()

    async def store(
        self,
        to_tier: str,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        Store data in specified memory tier.
        
        Args:
            to_tier: Memory tier to store in ("glacier", "cold", "warm", "hot", "red_hot")
            data: Data to store
            metadata: Optional metadata about the data
            tags: Optional tags for categorizing the data
            
        Returns:
            bool: True if storage was successful, False otherwise
            
        Raises:
            ValueError: If the tier is invalid
        """
        valid_tiers = ["glacier", "cold", "warm", "hot", "red_hot"]
        if to_tier not in valid_tiers:
            raise ValueError(f"Invalid tier: {to_tier}. Must be one of {valid_tiers}")

        try:
            if to_tier == "glacier":
                return await self._store_in_glacier(data, metadata=metadata, tags=tags)
            elif to_tier == "cold":
                self._init_cold()
                return await self._cold_memory.store(data, metadata=metadata, tags=tags)
            elif to_tier == "warm":
                self._init_warm()
                return await self._warm_memory.store(data, metadata=metadata, tags=tags)
            elif to_tier == "hot":
                self._init_hot()
                return await self._hot_memory.store(data, metadata=metadata, tags=tags)
            elif to_tier == "red_hot":
                self._init_red_hot()
                return await self._red_hot_memory.store(data, metadata=metadata, tags=tags)
        except Exception as e:
            self.logger.error(f"Error storing in {to_tier} tier: {e}")
            return False

    async def _store_in_glacier(
        self,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Store data in glacier storage."""
        # Placeholder for glacier storage implementation
        self.logger.info("Glacier storage not implemented yet")
        return False

    def cleanup(self) -> None:
        """Clean up resources for all memory tiers."""
        try:
            if self._hot_memory:
                self._hot_memory.cleanup()
            if self._warm_memory:
                self._warm_memory.cleanup()
            if self._cold_memory:
                self._cold_memory.cleanup()
            if self._red_hot_memory:
                self._red_hot_memory.cleanup()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def __del__(self):
        """Destructor to ensure cleanup is performed."""
        self.cleanup()

# Create singleton instance
memory_store = MemoryStore()
