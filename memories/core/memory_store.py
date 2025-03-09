"""Memory store functionality for storing data in different memory tiers."""

import logging
from typing import Dict, Any, Optional, List, Union
import numpy as np
import pandas as pd
from pathlib import Path
import json
import duckdb
from datetime import datetime

from memories.core.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

class MemoryStore:
    """Memory store for handling data storage across different memory tiers."""
    
    def __init__(self):
        """Initialize memory store."""
        self.memory_manager = MemoryManager()
        self.logger = logging.getLogger(__name__)

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
                return await self._store_in_glacier(data, metadata, tags)
            elif to_tier == "cold":
                return await self._store_in_cold(data, metadata, tags)
            elif to_tier == "warm":
                return await self._store_in_warm(data, metadata, tags)
            elif to_tier == "hot":
                return await self._store_in_hot(data, metadata, tags)
            elif to_tier == "red_hot":
                return await self._store_in_red_hot(data, metadata, tags)
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

    async def _store_in_cold(
        self,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Store data in cold storage using DuckDB."""
        try:
            # Get DuckDB connection
            con = self.memory_manager.get_duckdb_connection()
            if not con:
                self.logger.error("DuckDB connection not initialized")
                return False

            # Convert data to DataFrame if needed
            if isinstance(data, dict):
                df = pd.DataFrame.from_dict(data)
            elif isinstance(data, pd.DataFrame):
                df = data
            else:
                self.logger.error("Data must be a dictionary or DataFrame for cold storage")
                return False

            # Add metadata columns if provided
            if metadata:
                for key, value in metadata.items():
                    df[f"meta_{key}"] = value

            # Add tags if provided
            if tags:
                df["tags"] = ",".join(tags)

            # Add timestamp
            df["stored_at"] = datetime.now()

            # Create table name from tags or use default
            table_name = f"cold_data_{tags[0]}" if tags else "cold_data"
            table_name = table_name.replace("-", "_").lower()

            # Store in DuckDB
            con.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM df LIMIT 0")
            con.execute(f"INSERT INTO {table_name} SELECT * FROM df")

            return True

        except Exception as e:
            self.logger.error(f"Error storing in cold storage: {e}")
            return False

    async def _store_in_warm(
        self,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Store data in warm storage."""
        try:
            # Get warm storage path
            warm_path = Path(self.memory_manager.config['memory']['warm']['path'])
            warm_path.mkdir(parents=True, exist_ok=True)

            # Generate filename from tags or timestamp
            filename = f"{tags[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json" if tags else f"warm_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = warm_path / filename

            # Prepare data for storage
            storage_data = {
                "data": data,
                "metadata": metadata or {},
                "tags": tags or [],
                "stored_at": datetime.now().isoformat()
            }

            # Store as JSON
            with open(filepath, 'w') as f:
                json.dump(storage_data, f)

            return True

        except Exception as e:
            self.logger.error(f"Error storing in warm storage: {e}")
            return False

    async def _store_in_hot(
        self,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Store data in hot storage using Redis."""
        try:
            # Get Redis client
            redis_client = self.memory_manager.get_storage_backend('hot')
            if not redis_client:
                self.logger.error("Redis client not initialized")
                return False

            # Generate key from tags or timestamp
            key = f"{tags[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}" if tags else f"hot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Prepare data for storage
            storage_data = {
                "data": data,
                "metadata": metadata or {},
                "tags": tags or [],
                "stored_at": datetime.now().isoformat()
            }

            # Store in Redis
            redis_client.set(key, json.dumps(storage_data))

            # Add to tag index if tags provided
            if tags:
                for tag in tags:
                    redis_client.sadd(f"tag:{tag}", key)

            return True

        except Exception as e:
            self.logger.error(f"Error storing in hot storage: {e}")
            return False

    async def _store_in_red_hot(
        self,
        data: Union[np.ndarray, List[float]],
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Store vector data in red hot storage using FAISS."""
        try:
            # Get FAISS index
            index = self.memory_manager.get_faiss_index('red_hot')
            if not index:
                self.logger.error("FAISS index not initialized")
                return False

            # Convert data to numpy array if needed
            if isinstance(data, list):
                vector = np.array(data, dtype=np.float32).reshape(1, -1)
            elif isinstance(data, np.ndarray):
                vector = data.reshape(1, -1).astype(np.float32)
            else:
                self.logger.error("Data must be a vector (list or numpy array) for red hot storage")
                return False

            # Add vector to index
            index.add(vector)

            # Store metadata if provided
            if metadata or tags:
                # Get metadata storage path
                red_hot_path = Path(self.memory_manager.config['memory']['red_hot']['path'])
                red_hot_path.mkdir(parents=True, exist_ok=True)

                # Store metadata
                metadata_file = red_hot_path / "metadata.json"
                current_metadata = {}
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        current_metadata = json.load(f)

                # Add new metadata
                vector_id = len(current_metadata)
                current_metadata[vector_id] = {
                    "metadata": metadata or {},
                    "tags": tags or [],
                    "stored_at": datetime.now().isoformat()
                }

                with open(metadata_file, 'w') as f:
                    json.dump(current_metadata, f)

            return True

        except Exception as e:
            self.logger.error(f"Error storing in red hot storage: {e}")
            return False

# Create singleton instance
memory_store = MemoryStore()
