"""
Red hot memory implementation using FAISS for vector storage.
"""

import logging
from typing import Dict, Any, Optional, List, Union
import numpy as np
import faiss
import json
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class RedHotMemory:
    """Red hot memory layer using FAISS for vector storage."""
    
    def __init__(self, dimension: int = 384, storage_path: str = "data/memory/red_hot"):
        """Initialize red hot memory.
        
        Args:
            dimension: Vector dimension (default: 384)
            storage_path: Path to store metadata
        """
        self.logger = logger
        self.dimension = dimension
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Initialize FAISS index
            self.index = faiss.IndexFlatL2(dimension)
            if faiss.get_num_gpus() > 0:
                # Use GPU if available
                res = faiss.StandardGpuResources()
                self.index = faiss.index_cpu_to_gpu(res, 0, self.index)
                logger.info("Using GPU for FAISS index")
            else:
                logger.info("Using CPU for FAISS index")
                
            # Initialize metadata storage
            self.metadata_file = self.storage_path / "metadata.json"
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
            else:
                self.metadata = {}
                
            logger.info(f"Initialized red hot memory with dimension {dimension}")
        except Exception as e:
            logger.error(f"Failed to initialize red hot memory: {e}")
            raise

    async def store(
        self,
        data: Union[np.ndarray, List[float]],
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Store vector data in red hot memory with metadata and tags.
        
        Args:
            data: Vector data (numpy array or list of floats)
            metadata: Optional metadata about the vector
            tags: Optional tags for categorizing the vector
            
        Returns:
            bool: True if storage was successful, False otherwise
        """
        try:
            # Convert data to numpy array if needed
            if isinstance(data, list):
                vector = np.array(data, dtype=np.float32).reshape(1, -1)
            elif isinstance(data, np.ndarray):
                vector = data.reshape(1, -1).astype(np.float32)
            else:
                logger.error("Data must be a vector (list or numpy array)")
                return False

            # Validate vector dimension
            if vector.shape[1] != self.dimension:
                logger.error(f"Vector dimension mismatch. Expected {self.dimension}, got {vector.shape[1]}")
                return False

            # Add vector to index
            self.index.add(vector)

            # Store metadata if provided
            if metadata or tags:
                vector_id = len(self.metadata)
                self.metadata[str(vector_id)] = {
                    "metadata": metadata or {},
                    "tags": tags or [],
                    "stored_at": datetime.now().isoformat()
                }

                # Save metadata to file
                with open(self.metadata_file, 'w') as f:
                    json.dump(self.metadata, f)

            return True

        except Exception as e:
            logger.error(f"Error storing in red hot memory: {e}")
            return False

    async def retrieve(
        self,
        query_vector: Union[np.ndarray, List[float]],
        k: int = 1,
        tags: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Retrieve nearest vectors from red hot memory.
        
        Args:
            query_vector: Query vector
            k: Number of nearest neighbors to retrieve
            tags: Optional tags to filter by
            
        Returns:
            Dictionary containing distances, indices and metadata
        """
        try:
            # Convert query vector to numpy array if needed
            if isinstance(query_vector, list):
                query = np.array(query_vector, dtype=np.float32).reshape(1, -1)
            else:
                query = query_vector.reshape(1, -1).astype(np.float32)

            # Search index
            distances, indices = self.index.search(query, k)

            # Get metadata for results
            results = []
            for i, idx in enumerate(indices[0]):
                result = {
                    "distance": float(distances[0][i]),
                    "index": int(idx)
                }
                
                # Add metadata if available
                if str(idx) in self.metadata:
                    meta = self.metadata[str(idx)]
                    if tags:
                        # Filter by tags
                        if any(tag in meta["tags"] for tag in tags):
                            result.update(meta)
                            results.append(result)
                    else:
                        result.update(meta)
                        results.append(result)

            return results if results else None

        except Exception as e:
            logger.error(f"Error retrieving from red hot memory: {e}")
            return None

    def clear(self) -> None:
        """Clear red hot memory."""
        try:
            # Reset FAISS index
            self.index = faiss.IndexFlatL2(self.dimension)
            if faiss.get_num_gpus() > 0:
                res = faiss.StandardGpuResources()
                self.index = faiss.index_cpu_to_gpu(res, 0, self.index)
            
            # Clear metadata
            self.metadata = {}
            if self.metadata_file.exists():
                self.metadata_file.unlink()
        except Exception as e:
            logger.error(f"Failed to clear red hot memory: {e}")

    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            self.clear()
            if self.storage_path.exists():
                self.storage_path.rmdir()
        except Exception as e:
            logger.error(f"Failed to cleanup red hot memory: {e}")

    def __del__(self):
        """Destructor to ensure cleanup is performed."""
        self.cleanup()

    async def get_schema(self, vector_id: Union[str, int]) -> Optional[Dict[str, Any]]:
        """Get schema information for stored vector.
        
        Args:
            vector_id: ID of the vector to get schema for
            
        Returns:
            Dictionary containing:
                - dimension: Vector dimension
                - type: Type of data ('vector')
                - source: Source of the schema ('faiss')
                - metadata: Additional metadata if available
            Returns None if vector not found
        """
        try:
            # Convert string ID to int if needed
            if isinstance(vector_id, str):
                vector_id = int(vector_id)
                
            # Check if vector exists in metadata
            if str(vector_id) not in self.metadata:
                return None
                
            schema = {
                'dimension': self.dimension,
                'type': 'vector',
                'source': 'faiss',
                'index_type': type(self.index).__name__
            }
            
            # Add metadata if available
            meta = self.metadata[str(vector_id)]
            if meta:
                schema['metadata'] = meta.get('metadata', {})
                schema['tags'] = meta.get('tags', [])
                schema['stored_at'] = meta.get('stored_at')
                
            return schema
            
        except Exception as e:
            logger.error(f"Failed to get schema for vector {vector_id}: {e}")
            return None 