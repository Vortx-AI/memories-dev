"""Memory system for storing and retrieving processed data"""

import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import json
import uuid
from datetime import datetime
import numpy as np
import faiss
import pickle
from tqdm import tqdm
import matplotlib.pyplot as plt
import sys

class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for NumPy types"""
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        return super().default(obj)

class MemorySystem:
    """Memory system for storing and retrieving processed data"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize storage paths
        self.storage_path = Path(self.config.get("storage_path", "data/memory"))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Get JSON encoder
        self.json_encoder = self.config.get("json_encoder", None)
        
        # Initialize index
        self.index_path = self.storage_path / "index"
        self.index_path.mkdir(exist_ok=True)
        self._init_index()
    
    def _init_index(self):
        """Initialize FAISS index"""
        index_file = self.index_path / "memory.index"
        if index_file.exists():
            self.index = faiss.read_index(str(index_file))
            with open(self.index_path / "metadata.pkl", "rb") as f:
                self.metadata = pickle.load(f)
        else:
            # Create new index
            self.index = faiss.IndexFlatL2(512)  # 512-dimensional embeddings
            self.metadata = {}
    
    def store(self,
             data: Dict[str, Any],
             metadata: Dict[str, Any],
             tags: List[str] = None) -> str:
        """Store data in memory"""
        try:
            # Generate unique ID
            memory_id = str(uuid.uuid4())
            
            # Add timestamp
            metadata["timestamp"] = datetime.now().isoformat()
            metadata["tags"] = tags or []
            
            # Store data
            data_path = self.storage_path / f"{memory_id}.json"
            with open(data_path, "w", cls=self.json_encoder) as f:
                json.dump({
                    "data": data,
                    "metadata": metadata
                }, f)
            
            # Update index
            if "embedding" in data:
                embedding = np.array(data["embedding"]).reshape(1, -1)
                self.index.add(embedding)
                self.metadata[memory_id] = metadata
                
                # Save index
                faiss.write_index(self.index, str(self.index_path / "memory.index"))
                with open(self.index_path / "metadata.pkl", "wb") as f:
                    pickle.dump(self.metadata, f)
            
            self.logger.info(f"Stored memory with ID: {memory_id}")
            return memory_id
            
        except Exception as e:
            self.logger.error(f"Error storing memory: {e}")
            raise
    
    def retrieve(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve data from memory"""
        try:
            data_path = self.storage_path / f"{memory_id}.json"
            if not data_path.exists():
                return None
            
            with open(data_path) as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(f"Error retrieving memory: {e}")
            raise
    
    def search(self,
              query: Union[str, np.ndarray],
              tags: List[str] = None,
              limit: int = 10) -> List[Dict[str, Any]]:
        """Search memory system"""
        try:
            if isinstance(query, str):
                # Convert text query to embedding
                embedding = self._text_to_embedding(query)
            else:
                embedding = query
            
            # Search index
            distances, indices = self.index.search(
                embedding.reshape(1, -1),
                limit
            )
            
            # Get results
            results = []
            for i, idx in enumerate(indices[0]):
                if idx == -1:  # No more results
                    break
                    
                memory_id = list(self.metadata.keys())[idx]
                metadata = self.metadata[memory_id]
                
                # Filter by tags if specified
                if tags and not all(tag in metadata["tags"] for tag in tags):
                    continue
                
                result = self.retrieve(memory_id)
                if result:
                    result["score"] = float(distances[0][i])
                    results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching memory: {e}")
            raise
    
    def delete(self, memory_id: str) -> bool:
        """Delete memory entry"""
        try:
            data_path = self.storage_path / f"{memory_id}.json"
            if not data_path.exists():
                return False
            
            # Remove from storage
            data_path.unlink()
            
            # Remove from index if exists
            if memory_id in self.metadata:
                # Note: FAISS doesn't support deletion, so we need to rebuild index
                del self.metadata[memory_id]
                self._rebuild_index()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting memory: {e}")
            raise
    
    def _rebuild_index(self):
        """Rebuild FAISS index"""
        new_index = faiss.IndexFlatL2(512)
        new_metadata = {}
        
        for memory_id, metadata in tqdm(self.metadata.items(),
                                      desc="Rebuilding index"):
            data = self.retrieve(memory_id)
            if data and "embedding" in data["data"]:
                embedding = np.array(data["data"]["embedding"]).reshape(1, -1)
                new_index.add(embedding)
                new_metadata[memory_id] = metadata
        
        self.index = new_index
        self.metadata = new_metadata
        
        # Save new index
        faiss.write_index(self.index, str(self.index_path / "memory.index"))
        with open(self.index_path / "metadata.pkl", "wb") as f:
            pickle.dump(self.metadata, f)
    
    def _text_to_embedding(self, text: str) -> np.ndarray:
        """Convert text to embedding"""
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            return model.encode(text)
        except ImportError:
            self.logger.warning("sentence-transformers not installed")
            return np.random.randn(512)  # Fallback to random embedding
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        try:
            total_memories = len(list(self.storage_path.glob("*.json")))
            indexed_memories = len(self.metadata)
            
            # Calculate storage size
            storage_size = sum(f.stat().st_size for f in self.storage_path.rglob("*"))
            
            return {
                "total_memories": total_memories,
                "indexed_memories": indexed_memories,
                "storage_size_bytes": storage_size,
                "index_dimension": self.index.d,
                "index_size": self.index.ntotal
            }
            
        except Exception as e:
            self.logger.error(f"Error getting memory stats: {e}")
            raise 