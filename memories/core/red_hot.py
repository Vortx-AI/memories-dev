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
from io import open  # Explicitly import open from io

logger = logging.getLogger(__name__)

class RedHotMemory:
    """Red hot memory layer using FAISS for ultra-fast vector similarity search."""
    
    def __init__(self, dimension=384, max_size=10000):
        """Initialize red-hot memory with FAISS index."""
        self.dimension = dimension
        self.max_size = max_size
        self.metadata = {}
        
        # Set up storage path
        project_root = Path(__file__).parent.parent.parent
        self.storage_path = os.path.join(project_root, "data", "red_hot")
        
        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)
            
        logger.info(f"Initialized RedHotMemory with storage at: {self.storage_path}")
        
        # Try to load existing state, or initialize new if none exists
        self._load_state()

    def _init_index(self):
        """Initialize a new FAISS index."""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = {}
        logger.info("Initialized new FAISS index")

    def _save_state(self):
        """Save FAISS index and metadata to disk."""
        try:
            # Ensure storage directory exists
            os.makedirs(self.storage_path, exist_ok=True)
            
            # Save FAISS index
            index_path = os.path.join(self.storage_path, "index.faiss")
            faiss.write_index(self.index, index_path)
            
            # Save metadata
            metadata_path = os.path.join(self.storage_path, "metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(self.metadata, f)
                
            logger.debug(f"Saved FAISS index to {index_path}")
            logger.debug(f"Saved metadata to {metadata_path}")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            raise

    def _load_state(self):
        """Load FAISS index and metadata from disk."""
        index_path = os.path.join(self.storage_path, "index.faiss")
        metadata_path = os.path.join(self.storage_path, "metadata.json")
        
        if os.path.exists(index_path) and os.path.exists(metadata_path):
            # Load FAISS index
            self.index = faiss.read_index(index_path)
            
            # Load metadata
            with open(metadata_path, 'r') as f:
                self.metadata = json.load(f)
                
            logger.info(f"Loaded existing state from {self.storage_path}")
        else:
            logger.info("No existing state found, initializing new index")
            self._init_index()

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

        # Save state after each addition
        self._save_state()
        
        return self.index.ntotal - 1

    def get_metadata(self, idx: int) -> Dict[str, Any]:
        """Get metadata for a vector by index."""
        return self.metadata.get(str(idx), {})

    def __len__(self):
        """Return number of vectors in storage."""
        return self.index.ntotal if self.index is not None else 0

    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata from disk."""
        metadata_path = os.path.join(self.storage_path, "metadata.json")
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load metadata: {e}")
        return {}
    
    def _save_metadata(self):
        """Save metadata to disk."""
        try:
            metadata_path = os.path.join(self.storage_path, "metadata.json")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
            
            with open(metadata_path, 'w') as f:
                json.dump(self.metadata, f)
            logger.debug(f"Successfully saved metadata to {metadata_path}")
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
            if vector_data.shape[1] != self.dimension:
                raise ValueError(f"Vector dimension mismatch. Expected {self.dimension}, got {vector_data.shape[1]}")
            
            # Add to index
            self.index.add(vector_data)
            
            # Store metadata
            self.metadata[key] = {
                "index": len(self.metadata),  # Position in the index
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            # Save state
            self._save_state()
            
            # Check size limit
            if len(self.metadata) > self.max_size:
                self._remove_oldest()
                
            logger.info(f"Stored vector with key: {key}")
            
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
            
            # Remove oldest items until under limit
            while len(self.metadata) > self.max_size:
                key, _ = sorted_items.pop(0)
                del self.metadata[key]
                
            # Save state
            self._save_state()
            
        except Exception as e:
            logger.error(f"Failed to remove oldest vectors: {e}")

    def clear(self) -> bool:
        """Clear all data from storage."""
        try:
            # Reset index
            self._init_index()
            
            # Clear metadata
            self.metadata = {}
            
            # Save empty state
            self._save_state()
            
            return True
        except Exception as e:
            logger.error(f"Failed to clear storage: {e}")
            return False

    def reset(self) -> bool:
        """Reset storage to initial state."""
        try:
            # Clear all data
            self.clear()
            
            # Remove storage directory
            if os.path.exists(self.storage_path):
                shutil.rmtree(self.storage_path)
                os.makedirs(self.storage_path)
            
            return True
        except Exception as e:
            logger.error(f"Failed to reset storage: {e}")
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