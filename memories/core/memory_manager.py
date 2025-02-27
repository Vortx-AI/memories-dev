"""
Memory manager implementation for managing different memory tiers.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from datetime import datetime
import yaml
import os

from .hot import HotMemory
from .red_hot import RedHotMemory
from .warm import WarmMemory
from .cold import ColdMemory
from .glacier import GlacierMemory

logger = logging.getLogger(__name__)

class MemoryManager:
    """Memory manager that handles different memory tiers:
    - Red Hot Memory: GPU-accelerated FAISS for ultra-fast vector similarity search
    - Hot Memory: GPU-accelerated memory for immediate processing
    - Warm Memory: CPU and Redis for fast in-memory access
    - Cold Memory: DuckDB for efficient on-device storage
    - Glacier Memory: Parquet files for off-device compressed storage
    """
    
    def __init__(self, storage_path: Optional[Union[str, Path]] = None, config_path: Optional[Union[str, Path]] = None):
        """Initialize MemoryManager.
        
        Args:
            storage_path: Optional explicit storage path. If provided, overrides config.
            config_path: Optional path to config file. If None, uses default db_config.yml.
        """
        self.logger = logging.getLogger(__name__)
        
        # Load config
        self.config = self._load_config(config_path)
        if not self.config:
            raise ValueError("Failed to load memory configuration")
            
        # Get base storage path (prefer explicit path over config)
        if storage_path:
            self.storage_path = Path(storage_path)
            self.logger.info(f"Using explicit storage path: {self.storage_path}")
        else:
            self.storage_path = Path(self.config['memory']['base_path'])
            self.logger.info(f"Using config storage path: {self.storage_path}")
            
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Initialize hot memory
            hot_config = self.config['memory']['hot']
            self.hot = HotMemory(
                redis_url=hot_config.get('redis_url', "redis://localhost:6379"),
                max_size=hot_config.get('max_size', 100*1024*1024)
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize hot memory: {e}")
            self.hot = None

        try:
            # Initialize warm memory
            warm_config = self.config['memory']['warm']
            self.warm = WarmMemory(
                storage_path=self.storage_path / warm_config['path'],
                max_size=warm_config.get('max_size', 1024*1024*1024)
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize warm memory: {e}")
            self.warm = None

        try:
            # Initialize cold memory
            cold_config = self.config['memory']['cold']
            self.cold = ColdMemory(
                storage_path=self.storage_path / cold_config['path'],
                max_size=cold_config.get('max_size', 10*1024*1024*1024)
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize cold memory: {e}")
            self.cold = None

        try:
            # Initialize glacier memory
            glacier_config = self.config['memory']['glacier']
            self.glacier = GlacierMemory(
                storage_path=self.storage_path / glacier_config['path'],
                max_size=glacier_config.get('max_size', 100*1024*1024*1024)
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize glacier memory: {e}")
            self.glacier = None

    def _load_config(self, config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            # Default config paths to check
            default_paths = [
                Path("config/db_config.yml"),
                Path("../config/db_config.yml"),
                Path(__file__).parent.parent.parent / "config" / "db_config.yml"
            ]
            
            # Add provided config path if specified
            if config_path:
                paths_to_check = [Path(config_path)] + default_paths
            else:
                paths_to_check = default_paths
            
            # Try each path
            for path in paths_to_check:
                if path.exists():
                    self.logger.info(f"Loading memory config from {path}")
                    with open(path, 'r') as f:
                        return yaml.safe_load(f)
            
            self.logger.error("No valid config file found")
            return {}
            
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return {}

    def get_memory_path(self, memory_type: str) -> Optional[Path]:
        """Get path for specific memory type"""
        try:
            if memory_type not in ['hot', 'warm', 'cold', 'glacier']:
                raise ValueError(f"Invalid memory type: {memory_type}")
                
            config = self.config['memory'][memory_type]
            return self.storage_path / config['path']
            
        except Exception as e:
            self.logger.error(f"Error getting {memory_type} memory path: {e}")
            return None

    def store(
        self,
        key: str,
        data: Any,
        tier: str = "hot",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Store data in specified memory tier.
        
        Args:
            key: Unique identifier for the data
            data: Data to store (vector data for red_hot tier)
            tier: Memory tier to store in ('red_hot', 'hot', 'warm', 'cold', or 'glacier')
            metadata: Optional metadata to store with the data
        """
        if not isinstance(data, dict) and tier != "red_hot":
            logger.error("Data must be a dictionary for non-red_hot tiers")
            return
        
        # Ensure timestamp exists in metadata
        if metadata is None:
            metadata = {}
        if "timestamp" not in metadata:
            metadata["timestamp"] = datetime.now().isoformat()
        
        # Store in specified tier
        try:
            if tier == "red_hot" and self.red_hot:
                self.red_hot.store(key, data, metadata)
            elif tier == "hot" and self.hot:
                self.hot.store(data)
            elif tier == "warm" and self.warm:
                self.warm.store(data)
            elif tier == "cold" and self.cold:
                self.cold.store(data)
            elif tier == "glacier" and self.glacier:
                self.glacier.store(data)
            else:
                logger.error(f"Invalid memory tier: {tier}")
        except Exception as e:
            logger.error(f"Failed to store in {tier} memory: {e}")
    
    def search_vectors(
        self,
        query_vector: Any,
        k: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors in red hot memory.
        
        Args:
            query_vector: Query vector
            k: Number of results to return
            metadata_filter: Optional filter to apply on metadata
            
        Returns:
            List of results with distances and metadata
        """
        if not self.red_hot:
            logger.error("Red hot memory not available")
            return []
        
        try:
            return self.red_hot.search(query_vector, k, metadata_filter)
        except Exception as e:
            logger.error(f"Failed to search vectors: {e}")
            return []
    
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
            tier: Memory tier to clear ('red_hot', 'hot', 'warm', 'cold', or 'glacier')
                 If None, clears all tiers
        """
        try:
            if tier is None or tier == "red_hot":
                if self.red_hot:
                    self.red_hot.clear()
            
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
            if self.red_hot:
                self.red_hot.cleanup()
            
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