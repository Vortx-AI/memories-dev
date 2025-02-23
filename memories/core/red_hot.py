"""
Red Hot memory implementation using GPU acceleration.
"""

import json
import logging
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
from pathlib import Path
from datetime import datetime
import cupy as cp
import cudf
import cuspatial
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class RedHotMemory:
    """Red Hot memory layer using GPU acceleration for fastest possible access."""
    
    def __init__(self, max_size: int):
        """Initialize red hot memory.
        
        Args:
            max_size: Maximum number of items to store in GPU memory
        """
        self.max_size = max_size
        
        # Initialize GPU components
        try:
            # Check CUDA availability
            if not cp.cuda.is_available():
                raise RuntimeError("CUDA is not available")
            
            # Initialize GPU memory
            self.device = cp.cuda.Device(0)  # Use first GPU
            self.device.use()
            
            # Initialize sentence transformer on GPU
            self.model = SentenceTransformer('all-MiniLM-L6-v2', device=f'cuda:{self.device.id}')
            self.vector_dim = self.model.get_sentence_embedding_dimension()
            
            # Initialize storage
            self.vectors = cp.zeros((max_size, self.vector_dim), dtype=cp.float32)
            self.metadata = []
            self.current_size = 0
            
            logger.info("Successfully initialized GPU memory")
        except Exception as e:
            logger.error(f"Failed to initialize GPU memory: {e}")
            raise
    
    def _get_embedding(self, text: str) -> cp.ndarray:
        """Get embedding for text using GPU-accelerated sentence transformer."""
        try:
            # Get embedding on GPU
            with cp.cuda.Device(self.device.id):
                embedding = self.model.encode(text, convert_to_tensor=True)
                return cp.asarray(embedding.cpu().numpy())
        except Exception as e:
            logger.error(f"Failed to get embedding: {e}")
            return cp.zeros(self.vector_dim, dtype=cp.float32)
    
    def _similarity_search(self, query_vector: cp.ndarray, k: int = 5) -> List[Tuple[int, float]]:
        """Perform GPU-accelerated similarity search."""
        try:
            with cp.cuda.Device(self.device.id):
                # Compute distances using GPU
                distances = cp.sum((self.vectors[:self.current_size] - query_vector) ** 2, axis=1)
                
                # Get top k indices
                if k > self.current_size:
                    k = self.current_size
                indices = cp.argsort(distances)[:k]
                
                # Convert to CPU and return with distances
                return list(zip(
                    indices.get().tolist(),
                    distances[indices].get().tolist()
                ))
        except Exception as e:
            logger.error(f"Failed to perform similarity search: {e}")
            return []
    
    def store(self, data: Dict[str, Any]) -> None:
        """Store data in GPU memory.
        
        Args:
            data: Data to store
        """
        try:
            # Use timestamp as key
            timestamp = data.get("timestamp", "")
            if not timestamp:
                logger.error("Data must have a timestamp")
                return
            
            # Store text fields in GPU memory
            text_fields = []
            for k, v in data.items():
                if isinstance(v, str) and len(v.strip()) > 0:
                    text_fields.append((k, v))
            
            for field_name, text in text_fields:
                if self.current_size >= self.max_size:
                    # Remove oldest entry
                    self.vectors = cp.roll(self.vectors, -1, axis=0)
                    self.metadata.pop(0)
                    self.current_size -= 1
                
                # Get embedding and store in GPU memory
                vector = self._get_embedding(text)
                self.vectors[self.current_size] = vector
                
                # Store metadata
                self.metadata.append({
                    'timestamp': timestamp,
                    'field': field_name,
                    'text': text,
                    'data': data,
                    'index': self.current_size,
                    'created_at': datetime.now().isoformat()
                })
                
                self.current_size += 1
                
        except Exception as e:
            logger.error(f"Failed to store data in GPU memory: {e}")
    
    def retrieve(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Retrieve data from GPU memory.
        
        Args:
            query: Query to match against stored data. If contains 'text_search',
                  performs similarity search using GPU acceleration.
            
        Returns:
            Retrieved data or None if not found
        """
        try:
            # Check for text similarity search
            if 'text_search' in query:
                text = query['text_search']
                vector = self._get_embedding(text)
                
                # Perform GPU-accelerated similarity search
                results = self._similarity_search(vector, k=5)
                
                if results:
                    # Get most similar result
                    idx, distance = results[0]
                    if idx < len(self.metadata):
                        data = self.metadata[idx]['data'].copy()
                        data['similarity_score'] = float(1 / (1 + distance))
                        return data
            
            # Use timestamp for direct lookup
            if "timestamp" in query:
                timestamp = query["timestamp"]
                for meta in self.metadata:
                    if meta['timestamp'] == timestamp:
                        return meta['data']
            
            # Otherwise, search through metadata
            for meta in self.metadata:
                if all(meta['data'].get(k) == v for k, v in query.items()):
                    return meta['data']
            
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve data from GPU memory: {e}")
            return None
    
    def retrieve_all(self) -> List[Dict[str, Any]]:
        """Retrieve all data from GPU memory.
        
        Returns:
            List of all stored data
        """
        try:
            # Get unique data entries by timestamp
            seen = set()
            result = []
            for meta in self.metadata:
                timestamp = meta['timestamp']
                if timestamp not in seen:
                    seen.add(timestamp)
                    result.append(meta['data'])
            return result
        except Exception as e:
            logger.error(f"Failed to retrieve all data from GPU memory: {e}")
            return []
    
    def clear(self) -> None:
        """Clear all data from GPU memory."""
        try:
            with cp.cuda.Device(self.device.id):
                self.vectors.fill(0)
                self.metadata = []
                self.current_size = 0
        except Exception as e:
            logger.error(f"Failed to clear GPU memory: {e}")
    
    def cleanup(self) -> None:
        """Clean up GPU resources."""
        try:
            with cp.cuda.Device(self.device.id):
                # Clear GPU memory
                self.vectors = None
                cp.get_default_memory_pool().free_all_blocks()
                cp.get_default_pinned_memory_pool().free_all_blocks()
        except Exception as e:
            logger.error(f"Failed to cleanup GPU resources: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup is performed."""
        self.cleanup() 