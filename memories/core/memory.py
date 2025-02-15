"""Memory system for storing and retrieving processed data"""

import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path
import json
import uuid
from datetime import datetime, timedelta
import numpy as np
import faiss
import pickle
from tqdm import tqdm
import matplotlib.pyplot as plt
import os
import torch
import rasterio
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon, Point
import pystac
import duckdb
from dotenv import load_dotenv

# Import required classes
from memories.models.load_model import LoadModel

# Set up logging
logging.basicConfig(level=logging.INFO)

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
    """Storage and retrieval system for earth observation memories with DuckDB."""
    
    def __init__(self):
        """Initialize the MemoryStore with database connection and FAISS index."""
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Get project root
        self.project_root = os.getenv("PROJECT_ROOT")
        if not self.project_root:
            raise ValueError("PROJECT_ROOT environment variable not set")
        print(f"[MemoryStore] Project root: {self.project_root}")
        
        # Initialize database
        db_path = os.path.join(self.project_root, "data", "memory.db")
        self.conn = duckdb.connect(db_path)
        print(f"[MemoryStore] Connected to DuckDB at {db_path}")
        
        # Initialize FAISS index
        self.index = None  # Will be created when first embeddings are added
        self.data = []    # Store data corresponding to vectors
        
        # Initialize memories table
        self._initialize_table()
        print("[MemoryStore] Memories table initialized")
        
    def _initialize_table(self):
        """Initialize the memories table if it doesn't exist."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                instance_id VARCHAR PRIMARY KEY,
                data_connectors JSON,
                artifacts JSON,
                geometry JSON,
                input_location JSON,
                start_date VARCHAR,
                end_date VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def create_memories(
        self,
        model: 'LoadModel',
        location: Union[Tuple[float, float], List[Tuple[float, float]], 
                       str, gpd.GeoDataFrame, Polygon, MultiPolygon, 
                       pystac.Item, Dict[str, Any]],
        time_range: Tuple[str, str],
        artifacts: Dict[str, List[str]],
        data_connectors: Optional[List[Dict[str, str]]] = None,
        batch_size: int = 10000  # Added batch size parameter
    ) -> Dict[str, Dict[str, List[str]]]:
        """
        Create memories by inserting into the existing table and FAISS storage.
        Process data in batches to manage memory usage.
        """
        try:
            instance_id = str(id(model))
            
            # Convert location to JSON-serializable format
            if isinstance(location, (Polygon, MultiPolygon)):
                geometry = json.loads(gpd.GeoSeries([location]).__geo_interface__)
            elif isinstance(location, gpd.GeoDataFrame):
                geometry = json.loads(location.geometry.__geo_interface__)
            else:
                geometry = {"type": "Point", "coordinates": location} if isinstance(location, tuple) else location

            # Process data connectors and add to FAISS storage
            connector_metadata = {}
            if data_connectors:
                from memories.data_acquisition.data_connectors import parquet_connector
                
                for connector in data_connectors:
                    if connector["type"] == "parquet":
                        total_vectors = 0
                        
                        # Process the parquet file in batches
                        for batch_data in parquet_connector(
                            file_path=connector["file_path"],
                            batch_size=batch_size
                        ):
                            if batch_data and len(batch_data) > 0:
                                # Create embeddings for the batch
                                embeddings = self._create_embeddings(batch_data, model)
                                
                                # Add batch to FAISS index
                                if embeddings is not None and len(embeddings) > 0:
                                    if self.index is None:
                                        # Initialize FAISS index with first batch
                                        dimension = embeddings.shape[1]
                                        self.index = faiss.IndexFlatL2(dimension)
                                    
                                    self.index.add(embeddings)
                                    total_vectors += len(embeddings)
                                    print(f"[MemoryStore] Added batch of {len(embeddings)} vectors to FAISS index from {connector['name']}")
                        
                        if total_vectors > 0:
                            print(f"[MemoryStore] Total vectors added from {connector['name']}: {total_vectors}")
                            connector_metadata[connector["name"]] = {
                                "vector_count": total_vectors,
                                "file_path": connector["file_path"]
                            }
                        else:
                            print(f"[MemoryStore] No data found in {connector['name']}")
                    else:
                        print(f"[MemoryStore] Unsupported connector type: {connector['type']}")

            # Insert into the memories table
            self.conn.execute("""
                INSERT INTO memories (
                    instance_id,
                    data_connectors,
                    artifacts,
                    geometry,
                    input_location,
                    start_date,
                    end_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                instance_id,
                json.dumps(connector_metadata if connector_metadata else {}),
                json.dumps(artifacts),
                json.dumps(geometry),
                json.dumps(location if isinstance(location, dict) else str(location)),
                time_range[0],
                time_range[1]
            ))
            
            print(f"[MemoryStore] Created memory with ID: {instance_id}")
            return {
                "instance_id": instance_id,
                "data_connectors": connector_metadata
            }

        except Exception as e:
            print(f"[MemoryStore] Error creating memory: {str(e)}")
            raise

    def _create_embeddings(self, data: List[Dict[str, Any]], model: 'LoadModel') -> Optional[np.ndarray]:
        """
        Create embeddings for the data using the provided model.
        
        Args:
            data: List of data items to create embeddings for
            model: The model instance for generating embeddings
            
        Returns:
            np.ndarray: Array of embeddings or None if creation fails
        """
        try:
            # This is a placeholder - implement actual embedding creation
            # based on your model's capabilities
            num_items = len(data)
            embedding_dim = 128  # Adjust based on your needs
            return np.random.rand(num_items, embedding_dim).astype('float32')
            
        except Exception as e:
            print(f"[MemoryStore] Error creating embeddings: {str(e)}")
            return None

    def close(self):
        """Close DuckDB connection."""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            print("[MemoryStore] DuckDB connection closed")

    def _process_connector(self, 
                         config: Dict[str, Any],
                         location: Union[Tuple[float, float], Dict[str, Any]],
                         time_range: Tuple[str, str]) -> Optional[Dict[str, Any]]:
        """Process data from a connector"""
        try:
            connector_type = config.get("type")
            if connector_type == "stac":
                return self._process_stac_data(config, location, time_range)
            elif connector_type == "file":
                return self._process_file_data(config, location, time_range)
            else:
                print(f"[MemoryStore] Unknown connector type: {connector_type}")
                return None
        except Exception as e:
            print(f"[MemoryStore] Error processing connector: {str(e)}")
            return None

    def _process_stac_data(self, 
                          config: Dict[str, Any],
                          location: Union[Tuple[float, float], Dict[str, Any]],
                          time_range: Tuple[str, str]) -> Dict[str, Any]:
        """Process STAC data"""
        # Implementation depends on your STAC processing needs
        pass

    def _process_file_data(self,
                          config: Dict[str, Any],
                          location: Union[Tuple[float, float], Dict[str, Any]],
                          time_range: Tuple[str, str]) -> Dict[str, Any]:
        """Process local file data"""
        # Implementation depends on your file processing needs
        pass

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

    def search_memories(self, query: str, coordinates: Optional[Dict[str, float]] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar memories using FAISS index.
        
        Args:
            query (str): The search query
            coordinates (Dict[str, float], optional): Location coordinates {lat, lon}
            top_k (int): Number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of similar items with scores
        """
        try:
            if self.index is None:
                print("[MemoryStore] No index available for search")
                return []
            
            # Create query embedding (placeholder - implement based on your model)
            query_embedding = np.random.rand(1, 128).astype('float32')  # Using same dim as in _create_embeddings
            
            # Perform similarity search
            distances, indices = self.index.search(query_embedding, top_k)
            
            # Format results
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx < len(self.data):
                    item = self.data[idx].copy()
                    item['score'] = float(1.0 / (1.0 + distance))  # Convert distance to score
                    
                    # Add coordinates if available
                    if coordinates and 'geometry' in item:
                        item['distance'] = self._calculate_distance(
                            coordinates,
                            item.get('geometry', {}).get('coordinates', [])
                        )
                    
                    results.append(item)
            
            # Sort by score and distance if available
            results.sort(key=lambda x: (-x['score'], x.get('distance', float('inf'))))
            
            return results
            
        except Exception as e:
            print(f"[MemoryStore] Error in similarity search: {str(e)}")
            return []

    def _calculate_distance(self, point1: Dict[str, float], point2: List[float]) -> float:
        """
        Calculate the distance between two points using Haversine formula.
        
        Args:
            point1 (Dict[str, float]): First point with lat/lon
            point2 (List[float]): Second point as [lon, lat]
            
        Returns:
            float: Distance in kilometers
        """
        try:
            from math import radians, sin, cos, sqrt, atan2
            
            # Extract coordinates
            lat1, lon1 = radians(point1['lat']), radians(point1['lon'])
            lat2, lon2 = radians(point2[1]), radians(point2[0])  # Note the order swap for GeoJSON format
            
            # Haversine formula
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            r = 6371  # Earth's radius in kilometers
            
            return r * c
            
        except Exception as e:
            print(f"[MemoryStore] Error calculating distance: {str(e)}")
            return float('inf')

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

class FAISSStorage:
    def __init__(self, dimension, field_names, metadata, instance_id):
        """
        Initialize FAISS storage.
        
        Args:
            dimension (int): Vector dimension based on total number of output fields
            field_names (list): Names of the fields being stored
            metadata (dict): Storage metadata including acquisition files and required inputs
            instance_id (str): Unique instance ID to identify this storage
        """
        self.instance_id = instance_id
        self.storage_path = Path(f"data/faiss_storage/{instance_id}")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.index = faiss.IndexFlatL2(dimension)
        self.field_names = field_names
        self.metadata = metadata
        self.vectors = []
        
        # Save index configuration
        self.index_path = self.storage_path / "index.faiss"
        self.metadata_path = self.storage_path / "metadata.json"
        
        # Save metadata
        with open(self.metadata_path, 'w') as f:
            json.dump({
                'dimension': dimension,
                'field_names': field_names,
                'metadata': metadata,
                'instance_id': instance_id
            }, f)
        
    def add(self, vector_data):
        """Add vector data to storage."""
        vector = [vector_data[field] for field in self.field_names]
        self.vectors.append(vector)
        if len(self.vectors) % 1000 == 0:  # Batch processing
            vectors_array = np.array(self.vectors, dtype=np.float32)
            self.index.add(vectors_array)
            faiss.write_index(self.index, str(self.index_path))
            self.vectors = []

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



