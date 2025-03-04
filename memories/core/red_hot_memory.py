import faiss
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import time
import yaml
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class RedHotMemory:
    def __init__(self, config_path: str = None):
        """Initialize FAISS-based red-hot memory.
        
        Args:
            config_path: Path to db_config.yml
        """
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize FAISS parameters from config
        self.vector_dim = self.config.get('red_hot', {}).get('vector_dim', 128)
        self.max_size = self.config.get('red_hot', {}).get('max_size', 10000)
        self.index_type = self.config.get('red_hot', {}).get('index_type', 'L2')
        
        # Initialize FAISS index based on config
        self.index = self._create_index()
        
        # Storage for metadata and vectors
        self.metadata: Dict[int, Dict] = {}
        self.vectors: Dict[int, np.ndarray] = {}
        self.last_access: Dict[int, float] = {}
        self.current_id = 0
        
        logger.info(f"Initialized RedHotMemory with dim={self.vector_dim}, max_size={self.max_size}")

    def _load_config(self, config_path: Optional[str] = None) -> dict:
        """Load configuration from db_config.yml."""
        if not config_path:
            config_path = os.path.join(
                Path(__file__).parent.parent.parent,
                'config',
                'db_config.yml'
            )
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {e}")
            return {}

    def _create_index(self) -> faiss.Index:
        """Create FAISS index based on configuration."""
        if self.index_type == 'L2':
            return faiss.IndexFlatL2(self.vector_dim)
        elif self.index_type == 'IVF':
            # IVF index for faster search with approximate results
            quantizer = faiss.IndexFlatL2(self.vector_dim)
            nlist = self.config.get('red_hot', {}).get('nlist', 100)
            return faiss.IndexIVFFlat(quantizer, self.vector_dim, nlist)
        else:
            logger.warning(f"Unknown index type {self.index_type}, falling back to L2")
            return faiss.IndexFlatL2(self.vector_dim)

    def add_item(self, vector: np.ndarray, metadata: Dict[str, Any] = None):
        """Add an item to red-hot memory.
        
        Args:
            vector: Feature vector
            metadata: Associated metadata (e.g., geometry, properties)
        """
        try:
            if len(self.metadata) >= self.max_size:
                self._evict()
                
            # Ensure vector is the right shape and type
            vector = np.asarray(vector, dtype=np.float32).reshape(1, self.vector_dim)
            
            # Add to FAISS index
            self.index.add(vector)
            
            # Store metadata and vector
            self.metadata[self.current_id] = metadata or {}
            self.vectors[self.current_id] = vector
            self.last_access[self.current_id] = time.time()
            
            self.current_id += 1
            
        except Exception as e:
            logger.error(f"Error adding item to red-hot memory: {e}")

    def search_knn(self, query_vector: np.ndarray, k: int = 5) -> List[Dict]:
        """Search for k nearest neighbors.
        
        Args:
            query_vector: Query vector
            k: Number of nearest neighbors to return
            
        Returns:
            List of metadata for nearest neighbors
        """
        try:
            # Ensure query vector is the right shape
            query_vector = np.asarray(query_vector, dtype=np.float32).reshape(1, self.vector_dim)
            
            # Search FAISS index
            distances, indices = self.index.search(query_vector, k)
            
            # Update access times and prepare results
            results = []
            for idx in indices[0]:  # indices is a 2D array
                if idx != -1 and idx in self.metadata:
                    self.last_access[idx] = time.time()
                    results.append({
                        'metadata': self.metadata[idx],
                        'distance': float(distances[0][list(indices[0]).index(idx)])
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching red-hot memory: {e}")
            return []

    def _evict(self):
        """Evict least recently used items when memory is full."""
        if not self.metadata:
            return
            
        # Find oldest accessed item
        oldest_id = min(self.last_access.items(), key=lambda x: x[1])[0]
        
        # Remove from all storage
        del self.metadata[oldest_id]
        del self.vectors[oldest_id]
        del self.last_access[oldest_id]
        
        # Rebuild FAISS index (since FAISS doesn't support removal)
        self.index = self._create_index()
        vectors = np.vstack([v for v in self.vectors.values()])
        if len(vectors) > 0:
            self.index.add(vectors)

    def clear(self):
        """Clear all data from red-hot memory."""
        self.metadata.clear()
        self.vectors.clear()
        self.last_access.clear()
        self.index = self._create_index()
        self.current_id = 0 