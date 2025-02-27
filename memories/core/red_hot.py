"""
Red hot memory implementation using FAISS on GPU.
"""

import logging
from typing import Dict, Any, Optional, List, Union
import numpy as np
import faiss
import torch
from pathlib import Path
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class RedHotMemory:
    """Red hot memory layer using FAISS on GPU for ultra-fast vector similarity search."""
    
    def __init__(
        self,
        storage_path: Path,
        max_size: int,
        vector_dim: int = 384,
        gpu_id: int = 0,
        index_type: str = "IVFFlat",
        force_cpu: bool = False
    ):
        """Initialize red hot memory.
        
        Args:
            storage_path: Path to store index and metadata
            max_size: Maximum number of vectors to store
            vector_dim: Dimension of vectors to store (default: 384 for BERT-like models)
            gpu_id: GPU device ID to use (default: 0)
            index_type: FAISS index type ("Flat", "IVFFlat", "IVFPQ")
            force_cpu: Force CPU usage even if GPU is available
        """
        self.storage_path = Path(storage_path)
        self.max_size = max_size
        self.vector_dim = vector_dim
        self.gpu_id = gpu_id
        self.index_type = index_type
        self.force_cpu = force_cpu
        self.using_gpu = False
        
        # Create storage directory
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize metadata storage
        self.metadata_file = self.storage_path / "metadata.json"
        self.metadata = self._load_metadata()
        
        # Initialize FAISS index
        self._init_index()
        device = "CPU" if not self.using_gpu else f"GPU {gpu_id}"
        logger.info(f"Initialized red hot memory at {storage_path} using {device}")
    
    def _init_index(self):
        """Initialize FAISS index on GPU with fallback to CPU."""
        try:
            # Create CPU index first
            if self.index_type == "Flat":
                self.index = faiss.IndexFlatL2(self.vector_dim)
            elif self.index_type == "IVFFlat":
                quantizer = faiss.IndexFlatL2(self.vector_dim)
                nlist = min(4096, max(self.max_size // 30, 1))  # Number of clusters
                self.index = faiss.IndexIVFFlat(quantizer, self.vector_dim, nlist)
            elif self.index_type == "IVFPQ":
                quantizer = faiss.IndexFlatL2(self.vector_dim)
                nlist = min(4096, max(self.max_size // 30, 1))  # Number of clusters
                m = 8  # Number of subquantizers
                bits = 8  # Bits per subquantizer
                self.index = faiss.IndexIVFPQ(quantizer, self.vector_dim, nlist, m, bits)
            else:
                raise ValueError(f"Unsupported index type: {self.index_type}")
            
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
                        logger.warning(f"GPU {self.gpu_id} not available, falling back to CPU")
                except Exception as e:
                    logger.warning(f"Failed to initialize on GPU, falling back to CPU: {e}")
            
            # Train index if needed (for IVF indices)
            if isinstance(self.index, (faiss.IndexIVFFlat, faiss.IndexIVFPQ, 
                                    faiss.GpuIndexIVFFlat, faiss.GpuIndexIVFPQ)):
                if not self.index.is_trained:
                    # Generate random training data if no data available
                    train_size = min(100000, max(self.max_size, 256))
                    train_data = np.random.normal(size=(train_size, self.vector_dim)).astype('float32')
                    self.index.train(train_data)
            
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
    
    def clear(self) -> None:
        """Clear all data."""
        try:
            # Reset index
            self._init_index()
            
            # Clear metadata
            self.metadata = {}
            self._save_metadata()
            
            logger.info("Cleared all data")
            
        except Exception as e:
            logger.error(f"Failed to clear data: {e}")
            raise
    
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