import json
import os
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import torch
from tqdm import tqdm
import rasterio
import numpy as np
import faiss
import uuid
import sys
from dotenv import load_dotenv
import logging


from .cold import ColdStorage  # Ensure correct import path
#from .earth_memory_encoder import EarthMemoryEncoder  # Ensure you have this module


class EarthMemoryEncoder:
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

class EarthMemoryStore:
    """Enhanced storage and retrieval system for earth observation memories with dynamic field handling."""
    
    # Load environment variables
    load_dotenv()

    # Add the project root to Python path if needed
    project_root = os.getenv("PROJECT_ROOT")
    if not project_root:
        # If PROJECT_ROOT is not set, try to find it relative to the notebook
        project_root = os.path.abspath(os.path.join(os.getcwd(), '..', '..'))

    #print(f"Using project root: {project_root}")

    if project_root not in sys.path:
        sys.path.append(project_root)
        print(f"Added {project_root} to Python path")

    def __init__(
        self,
        config_path: str = None
    ):
        """Initialize EarthMemoryStore."""
        # Get the project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        print(f"[EarthMemoryStore] Project root: {project_root}")

        # If config_path is not provided, use default path relative to project root
        if config_path is None:
            config_path = os.path.join(project_root, 'config', 'db_config.yml')
            print(f"[EarthMemoryStore] Using default config path: {config_path}")

        # Initialize ColdStorage with the config path
        print(f"[EarthMemoryStore] Initializing ColdStorage with config path: {config_path}")
        self.cold_storage = ColdStorage(config_path)
        print("[EarthMemoryStore] ColdStorage initialized successfully")

        # Initialize FAISS index
        self.index = faiss.IndexFlatL2(512)  # or whatever dimension you're using
        print("[EarthMemoryStore] FAISS index initialized")

    def create_memories(
        self,
        location: Tuple[float, float],
        time_range: Tuple[str, str],
        modalities: List[str],
    ) -> Dict[str, Dict[str, List[str]]]:
        """
        Create memories by fetching data for specified modalities.
        
        Args:
            location (Tuple[float, float]): (latitude, longitude)
            time_range (Tuple[str, str]): (start_date, end_date)
            modalities (List[str]): List of modalities to fetch data from
            
        Returns:
            Dict[str, Dict[str, List[str]]]: Schema information for each modality and table
        """
        print(f"[EarthMemoryStore] Creating memories for location: {location}, time range: {time_range}")
        print(f"[EarthMemoryStore] Requested modalities: {modalities}")

        # Get schema information for all specified modalities
        schemas = self.cold_storage.get_schema_for_modalities(modalities)
        
        #print(f"[EarthMemoryStore] Retrieved schemas: {schemas}")
        return schemas

    def _create_bbox(self, location: Tuple[float, float], buffer: float = 0.1) -> Optional[List[float]]:
        """
        Create a bounding box around the location with the given buffer.
        
        Args:
            location (Tuple[float, float]): (latitude, longitude)
            buffer (float): Buffer in degrees
        
        Returns:
            Optional[List[float]]: Bounding box [minx, miny, maxx, maxy] or None
        """
        if not location:
            return None
        lat, lon = location
        minx = lon - buffer
        miny = lat - buffer
        maxx = lon + buffer
        maxy = lat + buffer
        return [minx, miny, maxx, maxy]

    def _persist_memories(self, memory: Dict[str, Any]):
        """
        Persist a single memory embedding to the FAISS index.
        
        Args:
            memory (Dict[str, Any]): Memory record with embedding
        """
        if self.index_type == "faiss" and self.faiss_index is not None:
            embedding = memory["embedding"].reshape(1, -1).astype('float32')
            self.faiss_index.add(embedding)
            self.id_to_key.append(str(uuid.uuid4()))  # Assign a unique ID
            self.memory_index[self.id_to_key[-1]] = memory
            print(f"Persisted memory with ID: {self.id_to_key[-1]} to FAISS index.")
        else:
            # Implement other indexing methods if necessary
            pass

    def query_memories(
        self,
        coordinates: Tuple[float, float],
        k: int = 10,
        time_range: Optional[Tuple[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query memories based on coordinates and optional time range.
        
        Args:
            coordinates (Tuple[float, float]): (latitude, longitude)
            k (int): Number of nearest memories to retrieve
            time_range (Optional[Tuple[str, str]]): (start_date, end_date) in 'YYYY-MM-DD' format
        
        Returns:
            List[Dict[str, Any]]: List of matching memory records
        """
        if self.index_type == "faiss" and self.faiss_index is not None:
            # Encode query point
            query_embedding = self.encoder.encode_query(coordinates).reshape(1, -1).detach().numpy().astype('float32')
            
            # Search in FAISS index
            distances, indices = self.faiss_index.search(query_embedding, k)
            
            # Retrieve memories based on indices
            retrieved_memories = []
            for idx in indices[0]:
                if idx < len(self.id_to_key):
                    memory_id = self.id_to_key[idx]
                    memory = self.memory_index.get(memory_id)
                    if memory:
                        # Apply time range filter if specified
                        if time_range:
                            start_time, end_time = time_range
                            if not (start_time <= memory["timestamp"].strftime('%Y-%m-%d') <= end_time):
                                continue
                        retrieved_memories.append(memory)
            print(f"Retrieved {len(retrieved_memories)} memories using FAISS.")
            return retrieved_memories
        else:
            # Implement alternative querying methods if FAISS not used
            print("FAISS index not initialized. Cannot perform query.")
            return []
        
    def close(self):
        """Close resources."""
        self.cold_storage.close()

def encode_geospatial_data(data: Dict[str, Any], encoder: EarthMemoryEncoder) -> torch.Tensor:
    """
    Example function to encode geospatial data.
    Replace with actual encoding logic.
    
    Args:
        data (Dict[str, Any]): Data record to encode
        encoder (EarthMemoryEncoder): Encoder instance
    
    Returns:
        torch.Tensor: Embedding tensor
    """
    return encoder.encode(data)



