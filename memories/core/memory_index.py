"""Memory index for vectorizing and indexing schema information across memory tiers."""

import logging
from typing import Dict, Any, Optional, List, Union, Tuple
import faiss
import numpy as np
from pathlib import Path
import json
from datetime import datetime
from sentence_transformers import SentenceTransformer

from memories.core.memory_catalog import memory_catalog
from memories.core.hot import HotMemory
from memories.core.warm import WarmMemory
from memories.core.cold import ColdMemory
from memories.core.red_hot import RedHotMemory
from memories.core.glacier import GlacierMemory

logger = logging.getLogger(__name__)

class MemoryIndex:
    """Memory index for vectorizing and searching schema information across memory tiers."""
    
    _instance = None
    
    def __new__(cls):
        """Create singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize memory index."""
        if not hasattr(self, 'initialized'):
            self.logger = logging.getLogger(__name__)
            self.initialized = True
            
            # Initialize memory tiers
            self._hot_memory = None
            self._warm_memory = None
            self._cold_memory = None
            self._red_hot_memory = None
            self._glacier_memory = None
            
            # Initialize FAISS indexes for each tier
            self.indexes = {}
            self.metadata = {}
            
            # Initialize sentence transformer for vectorization
            try:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                self.vector_dim = 384  # Model output dimension
                
                # Create indexes for each tier
                for tier in ["hot", "warm", "cold", "red_hot", "glacier"]:
                    self.indexes[tier] = faiss.IndexFlatL2(self.vector_dim)
                    self.metadata[tier] = {}
                    
                self.logger.info("Successfully initialized memory index")
            except Exception as e:
                self.logger.error(f"Failed to initialize memory index: {e}")
                raise

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

    def _init_glacier(self) -> None:
        """Initialize glacier memory on demand."""
        if not self._glacier_memory:
            self._glacier_memory = GlacierMemory()

    def _vectorize_schema(self, schema: Dict[str, Any]) -> np.ndarray:
        """Convert schema to vector representation.
        
        Args:
            schema: Schema dictionary
            
        Returns:
            Vector representation of schema (shape: [vector_dim])
        """
        try:
            text_parts = []
            
            # Add column names
            if 'columns' in schema:
                text_parts.extend(str(col) for col in schema['columns'])
            elif 'fields' in schema:
                text_parts.extend(str(field) for field in schema['fields'])
                
            # Add data type information
            if 'type' in schema:
                text_parts.append(f"type:{schema['type']}")
                
            # Add source information
            if 'source' in schema:
                text_parts.append(f"source:{schema['source']}")
                
            # Add geometry type for geodataframes
            if 'geometry_type' in schema:
                text_parts.append(f"geometry:{schema['geometry_type']}")
                
            # Combine all parts
            text = " ".join(text_parts) if text_parts else "empty_schema"
            
            # Convert to vector using sentence transformer and reshape to [vector_dim]
            vector = self.model.encode([text])  # Returns shape [1, 384]
            return vector.reshape(-1)  # Reshape to [vector_dim]
            
        except Exception as e:
            self.logger.error(f"Failed to vectorize schema: {e}")
            raise

    async def update_index(self, tier: str) -> None:
        """Update index for a specific memory tier.
        
        Args:
            tier: Memory tier to update ("hot", "warm", "cold", "red_hot", "glacier")
        """
        try:
            # Initialize appropriate memory tier
            if tier == "hot":
                self._init_hot()
            elif tier == "warm":
                self._init_warm()
            elif tier == "cold":
                self._init_cold()
            elif tier == "red_hot":
                self._init_red_hot()
            elif tier == "glacier":
                self._init_glacier()
            else:
                raise ValueError(f"Invalid tier: {tier}")
                
            # Get all data for the tier from catalog
            tier_data = await memory_catalog.get_tier_data(tier)
            self.logger.debug(f"Retrieved {len(tier_data)} items for {tier} tier")
            self.logger.debug(f"Tier data: {tier_data}")
            
            # Create new index and metadata
            index = faiss.IndexFlatL2(self.vector_dim)
            metadata = {}
            
            # Process each data item
            for item in tier_data:
                try:
                    # Get schema from appropriate memory tier
                    schema = None
                    if tier == "hot" and self._hot_memory:
                        self.logger.debug(f"Getting schema for hot tier item: {item['data_id']}")
                        schema = await self._hot_memory.get_schema(item['data_id'])
                    elif tier == "warm" and self._warm_memory:
                        self.logger.debug(f"Getting schema for warm tier item: {item['location']}")
                        schema = await self._warm_memory.get_schema(item['location'])
                    elif tier == "cold" and self._cold_memory:
                        self.logger.debug(f"Getting schema for cold tier item: {item['data_id']}")
                        schema = await self._cold_memory.get_schema(item['data_id'])
                    elif tier == "red_hot" and self._red_hot_memory:
                        self.logger.debug(f"Getting schema for red_hot tier item: {item['data_id']}")
                        schema = await self._red_hot_memory.get_schema(item['data_id'])
                    elif tier == "glacier" and self._glacier_memory:
                        # For glacier, we need spatial input from metadata
                        meta = json.loads(item['additional_meta'])
                        if 'spatial_input' in meta and 'source' in meta:
                            self.logger.debug(f"Getting schema for glacier tier item: {meta['source']}")
                            schema = await self._glacier_memory.get_schema(
                                meta['source'],
                                meta['spatial_input'],
                                meta.get('spatial_input_type', 'bbox')
                            )
                    
                    self.logger.debug(f"Retrieved schema for {item['data_id']}: {schema}")
                    
                    # Use empty schema if none is returned
                    if not schema:
                        schema = {'type': 'unknown', 'source': tier}
                    
                    # Vectorize schema - returns shape [vector_dim]
                    vector = self._vectorize_schema(schema)
                    self.logger.debug(f"Vectorized schema for {item['data_id']}, shape: {vector.shape}")
                    
                    # Add to FAISS index - reshape to [1, vector_dim] for faiss.add
                    index.add(vector.reshape(1, -1))
                    self.logger.debug(f"Added vector to index, total entries: {index.ntotal}")
                    
                    # Store metadata
                    idx = index.ntotal - 1
                    metadata[idx] = {
                        'data_id': item['data_id'],
                        'location': item['location'],
                        'created_at': item['created_at'],
                        'last_accessed': item['last_accessed'],
                        'access_count': item['access_count'],
                        'size': item['size'],
                        'tags': item['tags'].split(',') if item['tags'] else [],
                        'data_type': item['data_type'],
                        'schema': schema,
                        'additional_meta': json.loads(item['additional_meta'])
                    }
                    
                except Exception as e:
                    self.logger.error(f"Failed to process item {item['data_id']} in {tier} tier: {e}")
                    continue
            
            # Update index and metadata
            self.indexes[tier] = index
            self.metadata[tier] = metadata
                    
            self.logger.info(f"Updated index for {tier} tier with {self.indexes[tier].ntotal} entries")
            
        except Exception as e:
            self.logger.error(f"Failed to update index for {tier} tier: {e}")
            raise

    async def update_all_indexes(self) -> None:
        """Update indexes for all memory tiers."""
        for tier in ["hot", "warm", "cold", "red_hot", "glacier"]:
            await self.update_index(tier)

    async def search(
        self,
        query: str,
        tiers: Optional[List[str]] = None,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar schemas across memory tiers.
        
        Args:
            query: Search query (will be vectorized)
            tiers: Optional list of tiers to search (defaults to all)
            k: Number of results to return per tier
            
        Returns:
            List of dictionaries containing search results with metadata
        """
        try:
            # Vectorize query - returns shape [1, vector_dim]
            query_vector = self.model.encode([query])
            
            # Determine tiers to search
            search_tiers = tiers if tiers else ["hot", "warm", "cold", "red_hot", "glacier"]
            
            results = []
            for tier in search_tiers:
                if tier not in self.indexes:
                    continue
                    
                # Search in tier's index - query_vector is already in shape [1, vector_dim]
                D, I = self.indexes[tier].search(query_vector, k)
                
                # Add results with metadata
                for i, (dist, idx) in enumerate(zip(D[0], I[0])):
                    if idx < 0:  # Invalid index
                        continue
                        
                    if idx in self.metadata[tier]:
                        result = {
                            'tier': tier,
                            'distance': float(dist),
                            'rank': i + 1,
                            **self.metadata[tier][idx]
                        }
                        results.append(result)
            
            # Sort results by distance
            results.sort(key=lambda x: x['distance'])
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to search: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up resources."""
        try:
            # Clean up memory tiers
            if self._hot_memory:
                await self._hot_memory.cleanup()
            if self._warm_memory:
                await self._warm_memory.cleanup()
            if self._cold_memory:
                await self._cold_memory.cleanup()
            if self._red_hot_memory:
                await self._red_hot_memory.cleanup()
            if self._glacier_memory:
                await self._glacier_memory.cleanup()
                
            # Clear indexes and metadata
            self.indexes.clear()
            self.metadata.clear()
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def __del__(self):
        """Ensure cleanup is called when object is destroyed."""
        # Note: We can't await cleanup() in __del__, so we just log a warning
        self.logger.warning("Object destroyed without proper cleanup. Call cleanup() explicitly to ensure proper resource cleanup.")

# Create singleton instance
memory_index = MemoryIndex()
