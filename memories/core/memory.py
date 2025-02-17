"""Memory system for storing and retrieving processed data"""

import os
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path
import json
import uuid
from datetime import datetime
import numpy as np
import faiss
import pickle
from tqdm import tqdm
import matplotlib.pyplot as plt
import torch
import rasterio
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon, Point
import pystac
import duckdb
from dotenv import load_dotenv

from .cold import ColdMemory
from memories.models.load_model import LoadModel
from memories.models.base_model import BaseModel
from memories.core.memories_index import FAISSStorage
from memories.config import Config
from memories.core.hot import HotMemory
from memories.core.warm import WarmMemory

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

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



class MemoryEncoder:
    """
    Encoder class to convert data records into embeddings.
    Implement the encoding logic as per your requirements.
    """
    def __init__(self, embedding_dim: int = 128):
        self.embedding_dim = embedding_dim
        # Initialize your model here (e.g., a neural network)

    def encode(self, data: Dict[str, Any]) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """
        Encode the data into an embedding.
        
        Args:
            data (Dict[str, Any]): Data record to encode
        
        Returns:
            Tuple[torch.Tensor, Dict[str, torch.Tensor]]: Embedding tensor and attention maps
        """
        # Implement your encoding logic here
        # For demonstration, create a random embedding
        embedding = torch.randn(self.embedding_dim)
        attention_maps = {}  # Populate as needed
        return embedding, attention_maps

    def encode_query(self, coordinates: Tuple[float, float]) -> torch.Tensor:
        """
        Encode query coordinates into an embedding.
        Replace this with actual query encoding logic.
        
        Args:
            coordinates (Tuple[float, float]): (latitude, longitude)
        
        Returns:
            torch.Tensor: Embedding tensor
        """
        # Dummy implementation: create a random embedding based on coordinates
        np.random.seed(int(coordinates[0] * 1000 + coordinates[1]))
        embedding = torch.randn(self.embedding_dim)
        return embedding

class MemoryStore:
    """Main memory store that manages hot, warm, and cold memory layers."""
    
    def __init__(self, config: Config):
        """Initialize the memory store.
        
        Args:
            config: Configuration for the memory store
        """
        self.config = config
        
        # Initialize memory layers
        self.hot_memory = HotMemory(
            redis_url=config.redis_url,
            redis_db=config.redis_db,
            max_size=config.hot_memory_size
        )
        
        self.warm_memory = WarmMemory(
            storage_path=config.storage_path / "warm",
            max_size=config.warm_memory_size
        )
        
        self.cold_memory = ColdMemory(
            storage_path=config.storage_path / "cold",
            max_size=config.cold_memory_size
        )
        
        logger.info(f"[MemoryStore] Project root: {config.storage_path}")
    
    def store(self, data: Dict[str, Any], memory_type: str = "warm") -> None:
        """Store data in the specified memory layer.
        
        Args:
            data: Data to store
            memory_type: Type of memory to store in ("hot", "warm", or "cold")
        """
        if memory_type == "hot":
            self.hot_memory.store(data)
        elif memory_type == "warm":
            self.warm_memory.store(data)
        elif memory_type == "cold":
            self.cold_memory.store(data)
        else:
            raise ValueError(f"Invalid memory type: {memory_type}")
    
    def retrieve(self, query: Dict[str, Any], memory_type: str = "warm") -> Optional[Dict[str, Any]]:
        """Retrieve data from the specified memory layer.
        
        Args:
            query: Query to match against stored data
            memory_type: Type of memory to retrieve from ("hot", "warm", or "cold")
            
        Returns:
            Retrieved data or None if not found
        """
        if memory_type == "hot":
            return self.hot_memory.retrieve(query)
        elif memory_type == "warm":
            return self.warm_memory.retrieve(query)
        elif memory_type == "cold":
            return self.cold_memory.retrieve(query)
        else:
            raise ValueError(f"Invalid memory type: {memory_type}")
    
    def retrieve_all(self, memory_type: str = "warm") -> List[Dict[str, Any]]:
        """Retrieve all data from the specified memory layer.
        
        Args:
            memory_type: Type of memory to retrieve from ("hot", "warm", or "cold")
            
        Returns:
            List of all stored data
        """
        if memory_type == "hot":
            return self.hot_memory.retrieve_all()
        elif memory_type == "warm":
            return self.warm_memory.retrieve_all()
        elif memory_type == "cold":
            return self.cold_memory.retrieve_all()
        else:
            raise ValueError(f"Invalid memory type: {memory_type}")
    
    def clear(self, memory_type: Optional[str] = None) -> None:
        """Clear data from the specified memory layer(s).
        
        Args:
            memory_type: Type of memory to clear ("hot", "warm", "cold", or None for all)
        """
        if memory_type is None or memory_type == "hot":
            self.hot_memory.clear()
        if memory_type is None or memory_type == "warm":
            self.warm_memory.clear()
        if memory_type is None or memory_type == "cold":
            self.cold_memory.clear()

def encode_geospatial_data(data: Dict[str, Any], encoder: MemoryEncoder) -> torch.Tensor:
    """
    Example function to encode geospatial data.
    Replace with actual encoding logic.
    
    Args:
        data (Dict[str, Any]): Data record to encode
        encoder (MemoryEncoder): Encoder instance
    
    Returns:
        torch.Tensor: Embedding tensor
    """
    return encoder.encode(data)

def create_faiss_storage(artifacts_selection, instance_id):
    """
    Create FAISS storage based on selected artifacts.
    
    Args:
        artifacts_selection (dict): Dictionary of selected artifacts
        instance_id (str): Unique instance ID for this storage
    
    Returns:
        FAISSStorage: Configured FAISS storage instance
    """
    # Load artifacts configuration
    with open(os.path.join(os.path.dirname(__file__), 'artifacts.json'), 'r') as f:
        artifacts_config = json.load(f)
    
    # Collect all output fields and metadata from selected artifacts
    output_fields = []
    metadata = {
        'acquisition_files': {},
        'inputs_required': set(),
        'instance_id': instance_id  # Include instance_id in metadata
    }
    
    for category, sources in artifacts_selection.items():
        for source in sources:
            if category in artifacts_config and source in artifacts_config[category]:
                source_config = artifacts_config[category][source]
                output_fields.extend(source_config['output_fields'])
                metadata['acquisition_files'][f"{category}/{source}"] = source_config['acquisition_file']
                metadata['inputs_required'].update(source_config['inputs_required'])
    
    metadata['inputs_required'] = list(metadata['inputs_required'])
    
    # Initialize FAISS storage with instance ID
    storage = FAISSStorage(
        dimension=len(output_fields),
        field_names=output_fields,
        metadata=metadata,
        instance_id=instance_id
    )
    
    return storage

def create_memories(artifacts_selection, **kwargs):
    """Create memories from selected artifacts."""
    # Initialize FAISS storage
    storage = create_faiss_storage(artifacts_selection)
    
    # Rest of the create_memories implementation...
    return storage



