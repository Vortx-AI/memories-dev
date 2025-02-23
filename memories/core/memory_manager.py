"""
Memory manager implementation for managing different memory tiers.
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

from .hot import HotMemory
from .warm import WarmMemory
from .cold import ColdMemory
from .glacier import GlacierMemory

logger = logging.getLogger(__name__)

class MemoryManager:
    """Memory manager that handles different memory tiers:
    - Hot Memory: GPU-accelerated memory for immediate processing
    - Warm Memory: CPU and Redis for fast in-memory access
    - Cold Memory: DuckDB for efficient on-device storage
    - Glacier Memory: Parquet files for off-device compressed storage
    """
    
    def __init__(
        self,
        storage_path: Path,
        redis_url: str = "redis://localhost:6379",
        redis_db: int = 0,
        hot_memory_size: int = 1000,
        warm_memory_size: int = 10000,
        cold_memory_size: int = 100000,
        glacier_memory_size: int = 1000000
    ):
        """Initialize memory manager.
        
        Args:
            storage_path: Base path for storing memory data
            redis_url: Redis connection URL for warm memory
            redis_db: Redis database number for warm memory
            hot_memory_size: Maximum items in GPU memory
            warm_memory_size: Maximum items in CPU/Redis memory
            cold_memory_size: Maximum items in cold memory
            glacier_memory_size: Maximum items in glacier memory
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize memory tiers
        try:
            self.hot = HotMemory(
                storage_path=self.storage_path / "hot",
                max_size=hot_memory_size
            )
            logger.info("Hot memory (GPU) initialized")
        except Exception as e:
            logger.error(f"Failed to initialize hot memory: {e}")
            self.hot = None
        
        try:
            self.warm = WarmMemory(
                redis_url=redis_url,
                redis_db=redis_db,
                max_size=warm_memory_size
            )
            logger.info("Warm memory (CPU/Redis) initialized")
        except Exception as e:
            logger.error(f"Failed to initialize warm memory: {e}")
            self.warm = None
        
        try:
            self.cold = ColdMemory(
                storage_path=self.storage_path / "cold",
                max_size=cold_memory_size
            )
            logger.info("Cold memory initialized")
        except Exception as e:
            logger.error(f"Failed to initialize cold memory: {e}")
            self.cold = None
        
        try:
            self.glacier = GlacierMemory(
                storage_path=self.storage_path / "glacier",
                max_size=glacier_memory_size
            )
            logger.info("Glacier memory initialized")
        except Exception as e:
            logger.error(f"Failed to initialize glacier memory: {e}")
            self.glacier = None
    
    def store(self, data: Dict[str, Any]) -> None:
        """Store data in all memory tiers.
        
        Args:
            data: Data to store
        """
        if not isinstance(data, dict):
            logger.error("Data must be a dictionary")
            return
        
        # Ensure timestamp exists
        if "timestamp" not in data:
            data["timestamp"] = datetime.now().isoformat()
        
        # Store in each tier
        if self.hot:
            try:
                self.hot.store(data)
            except Exception as e:
                logger.error(f"Failed to store in hot memory: {e}")
        
        if self.warm:
            try:
                self.warm.store(data)
            except Exception as e:
                logger.error(f"Failed to store in warm memory: {e}")
        
        if self.cold:
            try:
                self.cold.store(data)
            except Exception as e:
                logger.error(f"Failed to store in cold memory: {e}")
        
        if self.glacier:
            try:
                self.glacier.store(data)
            except Exception as e:
                logger.error(f"Failed to store in glacier memory: {e}")
    
    def retrieve(self, query: Dict[str, Any], tier: str = "hot") -> Optional[Dict[str, Any]]:
        """Retrieve data from specified memory tier.
        
        Args:
            query: Query to match against stored data
            tier: Memory tier to query from ('hot', 'warm', 'cold', or 'glacier')
            
        Returns:
            Retrieved data or None if not found
        """
        try:
            if tier == "hot" and self.hot:
                return self.hot.retrieve(query)
            elif tier == "warm" and self.warm:
                return self.warm.retrieve(query)
            elif tier == "cold" and self.cold:
                return self.cold.retrieve(query)
            elif tier == "glacier" and self.glacier:
                return self.glacier.retrieve(query)
            else:
                logger.error(f"Invalid memory tier: {tier}")
                return None
        except Exception as e:
            logger.error(f"Failed to retrieve from {tier} memory: {e}")
            return None
    
    def retrieve_all(self, tier: str = "hot") -> List[Dict[str, Any]]:
        """Retrieve all data from specified memory tier.
        
        Args:
            tier: Memory tier to retrieve from ('hot', 'warm', 'cold', or 'glacier')
            
        Returns:
            List of all stored data
        """
        try:
            if tier == "hot" and self.hot:
                return self.hot.retrieve_all()
            elif tier == "warm" and self.warm:
                return self.warm.retrieve_all()
            elif tier == "cold" and self.cold:
                return self.cold.retrieve_all()
            elif tier == "glacier" and self.glacier:
                return self.glacier.retrieve_all()
            else:
                logger.error(f"Invalid memory tier: {tier}")
                return []
        except Exception as e:
            logger.error(f"Failed to retrieve all from {tier} memory: {e}")
            return []
    
    def clear(self, tier: Optional[str] = None) -> None:
        """Clear data from specified memory tier or all tiers if none specified.
        
        Args:
            tier: Memory tier to clear ('hot', 'warm', 'cold', or 'glacier')
                 If None, clears all tiers
        """
        try:
            if tier is None or tier == "hot":
                if self.hot:
                    self.hot.clear()
            
            if tier is None or tier == "warm":
                if self.warm:
                    self.warm.clear()
            
            if tier is None or tier == "cold":
                if self.cold:
                    self.cold.clear()
            
            if tier is None or tier == "glacier":
                if self.glacier:
                    self.glacier.clear()
        except Exception as e:
            logger.error(f"Failed to clear memory: {e}")
    
    def cleanup(self) -> None:
        """Clean up resources for all memory tiers."""
        try:
            if self.hot:
                self.hot.cleanup()
            
            if self.warm:
                self.warm.cleanup()
            
            if self.cold:
                self.cold.cleanup()
            
            if self.glacier:
                self.glacier.cleanup()
        except Exception as e:
            logger.error(f"Failed to cleanup memory manager: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup is performed."""
        self.cleanup() 