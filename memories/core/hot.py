"""
Hot memory implementation using GPU acceleration (Metal for Mac, CUDA for others).
If no GPU is available, this memory tier is disabled.
"""

import json
import logging
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
from pathlib import Path
from datetime import datetime
import platform

logger = logging.getLogger(__name__)

# Check if running on Mac
IS_MAC = platform.system() == "Darwin"

# Check for GPU availability
HAS_GPU = False
GPU_TYPE = None

if IS_MAC:
    try:
        import tensorflow as tf
        physical_devices = tf.config.list_physical_devices('GPU')
        if physical_devices:
            HAS_GPU = True
            GPU_TYPE = "metal"
            logger.info("Metal GPU detected")
    except Exception as e:
        logger.warning(f"Metal GPU not available: {e}")
else:
    try:
        import torch
        if torch.cuda.is_available():
            HAS_GPU = True
            GPU_TYPE = "cuda"
            logger.info("CUDA GPU detected")
    except Exception as e:
        logger.warning(f"CUDA GPU not available: {e}")

class HotMemory:
    """Hot memory layer using GPU acceleration for fastest possible access.
    This tier is disabled if no GPU is available."""
    
    def __init__(self, storage_path: Path, max_size: int):
        """Initialize hot memory if GPU is available.
        
        Args:
            storage_path: Path to store GPU state (not used directly, kept for interface consistency)
            max_size: Maximum number of items to store in GPU memory
        """
        if not HAS_GPU:
            logger.warning("No GPU available - Hot memory tier is disabled")
            self.enabled = False
            return
            
        self.enabled = True
        self.max_size = max_size
        self.current_size = 0
        
        try:
            from sentence_transformers import SentenceTransformer
            
            if GPU_TYPE == "metal":
                with tf.device('/GPU:0'):
                    self.model = SentenceTransformer('all-MiniLM-L6-v2')
                    self.vector_dim = self.model.get_sentence_embedding_dimension()
                    self.vectors = tf.zeros((max_size, self.vector_dim), dtype=tf.float32)
            else:  # CUDA
                self.model = SentenceTransformer('all-MiniLM-L6-v2', device='cuda')
                self.vector_dim = self.model.get_sentence_embedding_dimension()
                self.vectors = torch.zeros((max_size, self.vector_dim), device='cuda')
            
            self.metadata = []
            logger.info(f"Successfully initialized GPU memory using {GPU_TYPE}")
        except Exception as e:
            logger.error(f"Failed to initialize GPU memory: {e}")
            self.enabled = False
            raise
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text using GPU-accelerated sentence transformer."""
        if not self.enabled:
            return np.zeros(0)
            
        try:
            if GPU_TYPE == "metal":
                with tf.device('/GPU:0'):
                    embedding = self.model.encode(text, convert_to_tensor=True)
                    return embedding.numpy()
            else:  # CUDA
                embedding = self.model.encode(text, convert_to_tensor=True)
                return embedding.cpu().numpy()
        except Exception as e:
            logger.error(f"Failed to get embedding: {e}")
            return np.zeros(self.vector_dim)
    
    def _similarity_search(self, query_vector: np.ndarray, k: int = 5) -> List[Tuple[int, float]]:
        """Perform GPU-accelerated similarity search."""
        if not self.enabled:
            return []
            
        try:
            if GPU_TYPE == "metal":
                with tf.device('/GPU:0'):
                    distances = tf.reduce_sum(
                        tf.square(self.vectors[:self.current_size] - query_vector),
                        axis=1
                    )
                    if k > self.current_size:
                        k = self.current_size
                    _, indices = tf.nn.top_k(-distances, k=k)
                    distances = distances.numpy()
                    indices = indices.numpy()
            else:  # CUDA
                distances = torch.sum((self.vectors[:self.current_size] - torch.tensor(query_vector, device='cuda')) ** 2, dim=1)
                if k > self.current_size:
                    k = self.current_size
                values, indices = torch.topk(-distances, k=k)
                distances = -values.cpu().numpy()
                indices = indices.cpu().numpy()
            
            return list(zip(indices.tolist(), distances.tolist()))
        except Exception as e:
            logger.error(f"Failed to perform similarity search: {e}")
            return []
    
    def store(self, data: Dict[str, Any]) -> None:
        """Store data in GPU memory if available."""
        if not self.enabled:
            return
            
        try:
            timestamp = data.get("timestamp", "")
            if not timestamp:
                logger.error("Data must have a timestamp")
                return
            
            text_fields = []
            for k, v in data.items():
                if isinstance(v, str) and len(v.strip()) > 0:
                    text_fields.append((k, v))
            
            for field_name, text in text_fields:
                if self.current_size >= self.max_size:
                    if GPU_TYPE == "metal":
                        with tf.device('/GPU:0'):
                            self.vectors = tf.roll(self.vectors, shift=-1, axis=0)
                    else:  # CUDA
                        self.vectors = torch.roll(self.vectors, -1, dim=0)
                    self.metadata.pop(0)
                    self.current_size -= 1
                
                vector = self._get_embedding(text)
                if GPU_TYPE == "metal":
                    with tf.device('/GPU:0'):
                        self.vectors = tf.tensor_scatter_nd_update(
                            self.vectors,
                            [[self.current_size]],
                            [vector]
                        )
                else:  # CUDA
                    self.vectors[self.current_size] = torch.tensor(vector, device='cuda')
                
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
        """Retrieve data from GPU memory if available."""
        if not self.enabled:
            return None
            
        try:
            if 'text_search' in query:
                text = query['text_search']
                vector = self._get_embedding(text)
                
                results = self._similarity_search(vector, k=5)
                
                if results:
                    idx, distance = results[0]
                    if idx < len(self.metadata):
                        data = self.metadata[idx]['data'].copy()
                        data['similarity_score'] = float(1 / (1 + distance))
                        return data
            
            if "timestamp" in query:
                timestamp = query["timestamp"]
                for meta in self.metadata:
                    if meta['timestamp'] == timestamp:
                        return meta['data']
            
            for meta in self.metadata:
                if all(meta['data'].get(k) == v for k, v in query.items()):
                    return meta['data']
            
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve data from GPU memory: {e}")
            return None
    
    def retrieve_all(self) -> List[Dict[str, Any]]:
        """Retrieve all data from GPU memory if available."""
        if not self.enabled:
            return []
            
        try:
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
        """Clear all data from GPU memory if available."""
        if not self.enabled:
            return
            
        try:
            if GPU_TYPE == "metal":
                with tf.device('/GPU:0'):
                    self.vectors = tf.zeros((self.max_size, self.vector_dim), dtype=tf.float32)
            else:  # CUDA
                self.vectors.zero_()
            self.metadata = []
            self.current_size = 0
        except Exception as e:
            logger.error(f"Failed to clear GPU memory: {e}")
    
    def cleanup(self) -> None:
        """Clean up GPU resources if available."""
        if not self.enabled:
            return
            
        try:
            if GPU_TYPE == "metal":
                self.vectors = None
            else:  # CUDA
                if hasattr(self, 'vectors'):
                    del self.vectors
                torch.cuda.empty_cache()
        except Exception as e:
            logger.error(f"Failed to cleanup GPU resources: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup is performed."""
        self.cleanup()
