"""
Red hot memory implementation using FAISS.
"""

import logging
from typing import Dict, Any, Optional, List, Union
import numpy as np
import faiss
import torch
from pathlib import Path
import json
from datetime import datetime
import os
import shutil

logger = logging.getLogger(__name__)

class RedHotMemory:
    """Red hot memory layer using FAISS for ultra-fast vector similarity search."""
    
    def __init__(self):
        """Initialize red-hot memory storage."""
        self.dimension = 384  # dimension for all-MiniLM-L6-v2
        self.max_size = 1_000_000  # default max size
        
        # Initialize FAISS index and metadata
        self.index = None
        self.metadata = {}
        
        # Initialize storage
        self._init_storage()

    def _init_storage(self):
        """Initialize storage with default FAISS index."""
        try:
            # Create new index
            self.index = faiss.IndexFlatL2(self.dimension)
            logger.info("Created new FAISS index")
            
        except Exception as e:
            logger.error(f"Error initializing storage: {e}")
            # Ensure we at least have a working index
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata = {}

    def _save_state(self):
        """Save current state to disk."""
        try:
            # Save index
            index_path = os.path.join(self.storage_path, 'faiss.index')
            faiss.write_index(self.index, index_path)
            
            # Save metadata
            metadata_path = os.path.join(self.storage_path, 'metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(self.metadata, f)
                
            logger.info(f"Saved state: {self.index.ntotal} vectors")
            
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def add_vector(self, vector: np.ndarray, metadata: Dict[str, Any] = None):
        """
        Add a vector and its metadata to storage.
        
        Args:
            vector: numpy array of shape (dimension,)
            metadata: dictionary of metadata to store with the vector
        """
        if self.index.ntotal >= self.max_size:
            raise ValueError("Storage is full")
        
        # Ensure vector is the right shape and type
        vector = np.asarray(vector).astype('float32')
        if vector.shape != (self.dimension,):
            raise ValueError(f"Vector must have shape ({self.dimension},), got {vector.shape}")
        
        # Add vector to FAISS index
        self.index.add(vector.reshape(1, -1))
        
        # Add metadata
        if metadata is not None:
            self.metadata[str(self.index.ntotal - 1)] = metadata
            logger.debug(f"Added vector {self.index.ntotal - 1} with metadata")

    def get_metadata(self, idx: int) -> Dict[str, Any]:
        """Get metadata for a vector by index."""
        return self.metadata.get(str(idx), {})

    def __len__(self):
        """Return number of vectors in storage."""
        return self.index.ntotal if self.index is not None else 0

    def _init_index(self):
        """Initialize FAISS index."""
        try:
            # For now, only support Flat index type for stability
            if self.index_type != "Flat":
                logger.warning("Only Flat index type is currently supported. Using Flat index.")
                self.index_type = "Flat"
            
            # Create CPU index
            self.index = faiss.IndexFlatL2(self.vector_dim)
            
            # Try to use GPU if not forced to use CPU
            if not self.force_cpu:
                try:
                    # Check if GPU is available
                    gpu_available = faiss.get_num_gpus() > 0
                    if gpu_available and self.gpu_id < faiss.get_num_gpus():
                        res = faiss.StandardGpuResources()
                        self.index = faiss.index_cpu_to_gpu(res, self.gpu_id, self.index)
                        self.using_gpu = True
                        logger.info(f"FAISS index initialized on GPU {self.gpu_id}")
                    else:
                        logger.warning(f"GPU {self.gpu_id} not available, using CPU")
                except Exception as e:
                    logger.warning(f"Failed to initialize on GPU, using CPU: {e}")
            
            if not self.using_gpu:
                logger.info("FAISS index initialized on CPU")
            
        except Exception as e:
            logger.error(f"Failed to initialize FAISS index: {e}")
            raise
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata from disk."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load metadata: {e}")
        return {}
    
    def _save_metadata(self):
        """Save metadata to disk."""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def store(
        self,
        key: str,
        vector_data: Union[np.ndarray, torch.Tensor],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Store vector data with metadata.
        
        Args:
            key: Unique identifier for the vector
            vector_data: Vector to store (numpy array or PyTorch tensor)
            metadata: Optional metadata to store with the vector
        """
        try:
            # Convert to numpy if needed
            if isinstance(vector_data, torch.Tensor):
                vector_data = vector_data.detach().cpu().numpy()
            
            # Ensure vector is 2D
            if vector_data.ndim == 1:
                vector_data = vector_data.reshape(1, -1)
            
            # Ensure correct data type
            vector_data = vector_data.astype('float32')
            
            # Check dimensions
            if vector_data.shape[1] != self.vector_dim:
                raise ValueError(f"Vector dimension mismatch. Expected {self.vector_dim}, got {vector_data.shape[1]}")
            
            # Add to index
            self.index.add(vector_data)
            
            # Store metadata
            self.metadata[key] = {
                "index": len(self.metadata),  # Position in the index
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            # Save metadata
            self._save_metadata()
            
            # Check size limit
            if len(self.metadata) > self.max_size:
                self._remove_oldest()
                
            device = "CPU" if not self.using_gpu else f"GPU {self.gpu_id}"
            logger.info(f"Stored vector with key: {key} on {device}")
            
        except Exception as e:
            logger.error(f"Failed to store vector data: {e}")
            raise
    
    def search(
        self,
        query_vector: Union[np.ndarray, torch.Tensor],
        k: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors.
        
        Args:
            query_vector: Query vector
            k: Number of results to return
            metadata_filter: Optional filter to apply on metadata
            
        Returns:
            List of results with distances and metadata
        """
        try:
            # Convert to numpy if needed
            if isinstance(query_vector, torch.Tensor):
                query_vector = query_vector.detach().cpu().numpy()
            
            # Ensure vector is 2D
            if query_vector.ndim == 1:
                query_vector = query_vector.reshape(1, -1)
            
            # Ensure correct data type
            query_vector = query_vector.astype('float32')
            
            # Search index
            distances, indices = self.index.search(query_vector, k)
            
            # Prepare results
            results = []
            for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
                if idx == -1:  # No more results
                    break
                
                # Find metadata for this index
                for key, data in self.metadata.items():
                    if data["index"] == idx:
                        # Apply metadata filter if provided
                        if metadata_filter:
                            matches = True
                            for filter_key, filter_value in metadata_filter.items():
                                if data["metadata"].get(filter_key) != filter_value:
                                    matches = False
                                    break
                            if not matches:
                                continue
                        
                        results.append({
                            "key": key,
                            "distance": float(dist),
                            "metadata": data["metadata"],
                            "timestamp": data["timestamp"]
                        })
                        break
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search vectors: {e}")
            raise
    
    def _remove_oldest(self):
        """Remove oldest vectors when size limit is reached."""
        try:
            # Sort by timestamp
            sorted_items = sorted(
                self.metadata.items(),
                key=lambda x: x[1]["timestamp"]
            )
            
            # Remove oldest items
            num_to_remove = len(self.metadata) - self.max_size
            for key, _ in sorted_items[:num_to_remove]:
                del self.metadata[key]
            
            # Rebuild index with remaining items
            self._rebuild_index()
            
        except Exception as e:
            logger.error(f"Failed to remove oldest vectors: {e}")
            raise
    
    def _rebuild_index(self):
        """Rebuild FAISS index after removing items."""
        try:
            # Create new index
            self._init_index()
            
            # Update indices in metadata
            for i, (key, data) in enumerate(self.metadata.items()):
                self.metadata[key]["index"] = i
            
            self._save_metadata()
            
        except Exception as e:
            logger.error(f"Failed to rebuild index: {e}")
            raise
    
    def clear(self) -> bool:
        """
        Clear all vectors and metadata from storage.
        Returns:
            bool: True if cleared successfully, False otherwise
        """
        try:
            # Reset index
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata = {}
            logger.info("Successfully cleared red-hot memory")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing storage: {e}")
            return False

    def reset(self) -> bool:
        """
        Reset the entire storage directory.
        WARNING: This will delete everything in the storage directory.
        """
        try:
            if os.path.exists(self.storage_path):
                shutil.rmtree(self.storage_path)
            os.makedirs(self.storage_path)
            
            # Reinitialize empty index
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata = {}
            
            logger.info("Successfully reset red-hot memory storage")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting red-hot memory: {e}")
            return False
    
    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            # Save metadata
            self._save_metadata()
            
            # Reset index (this will free GPU memory)
            self.index = None
            
            logger.info("Cleaned up resources")
            
        except Exception as e:
            logger.error(f"Failed to cleanup: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup is performed."""
        self.cleanup() 