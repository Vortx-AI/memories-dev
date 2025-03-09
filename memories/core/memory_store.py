"""Memory store functionality for storing data in different memory tiers."""

import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from datetime import datetime
import sys
import os

from memories.core.memory_manager import MemoryManager
from memories.core.memory_catalog import memory_catalog
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

    def _get_data_size(self, data: Any) -> int:
        """Get size of data in bytes."""
        try:
            if hasattr(data, 'memory_usage'):
                # For pandas DataFrame
                return data.memory_usage(deep=True).sum()
            elif hasattr(data, 'nbytes'):
                # For numpy arrays
                return data.nbytes
            else:
                # For other objects, use sys.getsizeof
                return sys.getsizeof(data)
        except Exception as e:
            self.logger.warning(f"Could not determine data size: {e}")
            return 0

    def _get_data_type(self, data: Any) -> str:
        """Get type of data as string."""
        if hasattr(data, 'dtypes'):
            return 'dataframe'
        elif hasattr(data, 'dtype'):
            return 'array'
        else:
            return data.__class__.__name__.lower()

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
            # Get data size and type
            size = self._get_data_size(data)
            data_type = self._get_data_type(data)
            
            # Store data in the specified tier
            success = False
            location = None
            
            if to_tier == "glacier":
                success = await self._store_in_glacier(data, metadata=metadata, tags=tags)
                location = f"glacier/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            elif to_tier == "cold":
                self._init_cold()
                success = await self._cold_memory.store(data, metadata=metadata, tags=tags)
                location = f"cold/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            elif to_tier == "warm":
                self._init_warm()
                success = await self._warm_memory.store(data, metadata=metadata, tags=tags)
                location = str(self._warm_memory.storage_path / f"warm_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            elif to_tier == "hot":
                self._init_hot()
                success = await self._hot_memory.store(data, metadata=metadata, tags=tags)
                location = f"hot/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            elif to_tier == "red_hot":
                self._init_red_hot()
                success = await self._red_hot_memory.store(data, metadata=metadata, tags=tags)
                location = str(self._red_hot_memory.storage_path / f"red_hot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

            # Register in catalog if storage was successful
            if success and location:
                try:
                    await memory_catalog.register_data(
                        tier=to_tier,
                        location=location,
                        size=size,
                        data_type=data_type,
                        tags=tags,
                        metadata=metadata
                    )
                except Exception as e:
                    self.logger.error(f"Failed to register in catalog: {e}")
                    # Don't fail the operation if catalog registration fails
                    pass

            return success

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
