from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Union, Tuple, Set
import json
import pickle
import hashlib
from datetime import datetime
import re
from shapely.geometry import Point, Polygon
from geopy.geocoders import Nominatim
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import os
from pathlib import Path
import base64
from langchain_community.embeddings import HuggingFaceEmbeddings
import logging

@dataclass
class NodeData:
    """Structured and unstructured data for a node"""
    # Structured data
    id: str
    table_name: str
    column_name: str
    data_type: str
    created_at: str
    updated_at: str
    
    # Unstructured data containers
    metadata: Dict[str, Any] = None          # For JSON-serializable metadata
    raw_values: List[Any] = None             # For sample/raw values
    vector_data: Optional[np.ndarray] = None # For embedding vector
    binary_data: Optional[bytes] = None      # For any binary data
    
    def to_json(self) -> Dict[str, Any]:
        """Convert node data to JSON-serializable format"""
        data = asdict(self)
        # Convert numpy array to list
        if self.vector_data is not None:
            data['vector_data'] = self.vector_data.tolist()
        # Convert binary data to base64
        if self.binary_data is not None:
            data['binary_data'] = base64.b64encode(self.binary_data).decode('utf-8')
        return data

class NodeStorage:
    """Storage manager for node data"""
    
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)  # Ensure it's a Path object
        self.json_path = self.base_path / "json"
        self.pickle_path = self.base_path / "pickle"
        self.vector_path = self.base_path / "vectors"
        
        # Create directories
        for path in [self.json_path, self.pickle_path, self.vector_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    def _generate_node_id(self, table_name: str, column_name: str) -> str:
        """Generate unique node ID"""
        unique_string = f"{table_name}_{column_name}_{datetime.now().isoformat()}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:16]
    
    def store_node(self, node_data: NodeData):
        """Store node data in multiple formats"""
        # Store JSON-serializable data
        json_data = {
            'id': node_data.id,
            'table_name': node_data.table_name,
            'column_name': node_data.column_name,
            'data_type': node_data.data_type,
            'created_at': node_data.created_at,
            'updated_at': node_data.updated_at,
            'metadata': node_data.metadata
        }
        with open(self.json_path / f"{node_data.id}.json", 'w') as f:
            json.dump(json_data, f, indent=2)
        
        # Store raw values and binary data using pickle
        pickle_data = {
            'id': node_data.id,
            'raw_values': node_data.raw_values,
            'binary_data': node_data.binary_data
        }
        with open(self.pickle_path / f"{node_data.id}.pkl", 'wb') as f:
            pickle.dump(pickle_data, f)
        
        # Store vector data in numpy format
        if node_data.vector_data is not None:
            np.save(
                self.vector_path / f"{node_data.id}.npy",
                node_data.vector_data
            )

class ColumnTypes:
    """Enumeration of specialized column types"""
    ADDRESS = "address"
    COORDINATES = "coordinates"
    POLYGON = "polygon"
    GENERAL = "general"

class ColumnFilter:
    """Filter patterns and validators for different column types"""
    
    def __init__(self):
        self.geolocator = Nominatim(user_agent="column_search_agent")
        
        # Regex patterns
        self.coord_patterns = [
            r'^[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?),\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)$',  # lat,long
            r'POINT\s*\(\s*[-+]?\d*\.?\d+\s+[-+]?\d*\.?\d+\s*\)'  # WKT POINT format
        ]
        
        self.polygon_patterns = [
            r'POLYGON\s*\(\s*\(\s*([-+]?\d*\.?\d+\s+[-+]?\d*\.?\d+\s*,\s*)*[-+]?\d*\.?\d+\s+[-+]?\d*\.?\d+\s*\)\s*\)',  # WKT POLYGON
            r'\{\s*"type"\s*:\s*"Polygon"\s*,\s*"coordinates"\s*:\s*\[\s*\[\s*\[.*\]\s*\]\s*\]\s*\}'  # GeoJSON
        ]
    
    def detect_column_type(self, sample_values: List[str]) -> str:
        """Detect the type of data in the column"""
        if not sample_values:
            return ColumnTypes.GENERAL
            
        # Check a subset of values for performance
        check_values = sample_values[:10]
        
        # Check coordinates first (most strict pattern)
        if all(any(re.match(pattern, str(val)) for pattern in self.coord_patterns) 
               for val in check_values):
            return ColumnTypes.COORDINATES
            
        # Check polygons
        if all(any(re.match(pattern, str(val)) for pattern in self.polygon_patterns) 
               for val in check_values):
            return ColumnTypes.POLYGON
            
        # Check addresses (try to geocode a sample)
        address_count = 0
        for val in check_values[:3]:  # Check only first 3 for performance
            try:
                if self.geolocator.geocode(str(val)):
                    address_count += 1
            except:
                continue
        
        if address_count >= 2:  # If majority are valid addresses
            return ColumnTypes.ADDRESS
            
        return ColumnTypes.GENERAL

class ColumnSearchAgent:
    """Agent for intelligent database column search with geographic filters"""
    
    def __init__(self, storage_path: str = "data/column_memory"):
        self.storage_path = Path(storage_path)
        self.node_storage = NodeStorage(self.storage_path)
        self.column_filter = ColumnFilter()
        self.column_types: Dict[str, Set[str]] = {
            ColumnTypes.ADDRESS: set(),
            ColumnTypes.COORDINATES: set(),
            ColumnTypes.POLYGON: set(),
            ColumnTypes.GENERAL: set()
        }
        self._load_column_types()
    
    def _load_column_types(self):
        """Load column type classifications"""
        type_file = self.storage_path / "column_types.json"
        if type_file.exists():
            with open(type_file) as f:
                types_data = json.load(f)
                for col_type, columns in types_data.items():
                    self.column_types[col_type] = set(columns)
    
    def _save_column_types(self):
        """Save column type classifications"""
        type_file = self.storage_path / "column_types.json"
        with open(type_file, 'w') as f:
            json.dump({
                k: list(v) for k, v in self.column_types.items()
            }, f, indent=2)
    
    def add_column_node(self, 
                       table_name: str,
                       column_name: str,
                       data_type: str,
                       unstructured_data: Dict[str, Any] = None):
        """Add a new column node with type detection"""
        try:
            # Detect column type from sample values
            sample_values = unstructured_data.get('sample_values', [])
            column_type = self.column_filter.detect_column_type(sample_values)
            
            # Add to type classification
            column_key = f"{table_name}.{column_name}"
            self.column_types[column_type].add(column_key)
            
            # Add type information to metadata
            if not unstructured_data:
                unstructured_data = {}
            if not unstructured_data.get('metadata'):
                unstructured_data['metadata'] = {}
            unstructured_data['metadata']['column_type'] = column_type
            
            # Create node as before
            node_id = super().add_column_node(
                table_name=table_name,
                column_name=column_name,
                data_type=data_type,
                unstructured_data=unstructured_data
            )
            
            # Save updated type classifications
            self._save_column_types()
            
            return node_id
            
        except Exception as e:
            print(f"❌ Error adding node with type detection: {str(e)}")
            raise
    
    def search_columns(self, 
                      query: str, 
                      limit: int = 5,
                      threshold: float = 0.7,
                      column_type: Optional[str] = None) -> List[Tuple[NodeData, float]]:
        """Search columns with optional type filter"""
        try:
            # Get base results
            results = super().search_columns(query, limit=limit * 2, threshold=threshold)
            
            # Apply type filter if specified
            if column_type:
                filtered_results = []
                for node, score in results:
                    column_key = f"{node.table_name}.{node.column_name}"
                    if column_key in self.column_types[column_type]:
                        filtered_results.append((node, score))
                results = filtered_results[:limit]
            else:
                results = results[:limit]
            
            return results
            
        except Exception as e:
            print(f"❌ Error searching with filter: {str(e)}")
            raise

@dataclass
class FAISSNode:
    """Single node in FAISS index"""
    embedding: np.ndarray        # The vector stored in FAISS
    field_name: str             # The value being embedded
    metadata: Dict[str, Any]    # Flexible metadata structure

class FAISSStorage:
    def __init__(self, directory="faiss_data"):
        self.vector_dim = 384
        self.index = faiss.IndexFlatL2(self.vector_dim)
        self.nodes: List[FAISSNode] = []
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.directory = directory
        os.makedirs(directory, exist_ok=True)
        self.load()  # Try to load existing data on initialization
    
    def store_value(self, field_name: str, metadata: Dict[str, Any]):
        """Store a field name with its metadata, handling duplicates"""
        try:
            # Check if field already exists
            existing_node = None
            for node in self.nodes:
                if node.field_name == field_name:
                    existing_node = node
                    break
            
            if existing_node:
                # Handle duplicate - merge api_ids
                if 'api_id' in existing_node.metadata and 'api_id' in metadata:
                    existing_api_ids = str(existing_node.metadata['api_id']).split(',')
                    new_api_id = str(metadata['api_id'])
                    if new_api_id not in existing_api_ids:
                        existing_api_ids.append(new_api_id)
                        existing_node.metadata['api_id'] = ','.join(existing_api_ids)
                print(f"Updated existing field: {field_name}")
                self.save()  # Save after update
                return
            
            # Store new field
            embedding = self.model.encode(field_name)
            self.index.add(embedding.reshape(1, -1))
            
            node = FAISSNode(
                embedding=embedding,
                field_name=field_name,
                metadata=metadata
            )
            self.nodes.append(node)
            print(f"Stored new field: {field_name}")
            self.save()  # Save after adding new field
            return len(self.nodes) - 1
            
        except Exception as e:
            print(f"Error storing in FAISS: {e}")
            raise

    def query_by_metadata(self, metadata_filter: Dict[str, Any]) -> List[FAISSNode]:
        """Query nodes by metadata values"""
        try:
            results = []
            for node in self.nodes:
                matches = True
                for key, value in metadata_filter.items():
                    if key not in node.metadata or node.metadata[key] != value:
                        matches = False
                        break
                if matches:
                    results.append(node)
            return results
            
        except Exception as e:
            print(f"Error querying metadata: {e}")
            raise

    def save(self):
        """Save FAISS index and nodes"""
        try:
            # Save FAISS index
            faiss.write_index(self.index, f"{self.directory}/index.faiss")
            
            # Save nodes
            with open(f"{self.directory}/nodes.pkl", "wb") as f:
                pickle.dump(self.nodes, f)
            
            print("✅ Data saved successfully")
            
        except Exception as e:
            print(f"Error saving data: {e}")
            raise
    
    def load(self):
        """Load FAISS index and nodes if they exist"""
        try:
            if os.path.exists(f"{self.directory}/index.faiss") and \
               os.path.exists(f"{self.directory}/nodes.pkl"):
                # Load FAISS index
                self.index = faiss.read_index(f"{self.directory}/index.faiss")
                
                # Load nodes
                with open(f"{self.directory}/nodes.pkl", "rb") as f:
                    self.nodes = pickle.load(f)
                
                print("✅ Loaded existing data")
                return True
            return False
            
        except Exception as e:
            print(f"Error loading data: {e}")
            return False

    def get_all_fields(self) -> List[Dict[str, Any]]:
        """Get all stored fields with their metadata"""
        return [{
            'field_name': node.field_name,
            **node.metadata
        } for node in self.nodes]

    def query_similar_with_metadata(self, 
                                  query: str, 
                                  metadata_filter: Optional[Dict[str, Any]] = None,
                                  limit: int = 5) -> List[tuple[FAISSNode, float]]:
        """Query similar vectors with optional metadata filtering"""
        try:
            # Get similar vectors from FAISS
            query_embedding = self.model.encode(query)
            distances, indices = self.index.search(
                query_embedding.reshape(1, -1),
                self.index.ntotal  # Get all results for filtering
            )
            
            # Combine with metadata filtering
            results = []
            for i, idx in enumerate(indices[0]):
                if idx == -1:
                    continue
                    
                node = self.nodes[idx]
                
                # Apply metadata filter if provided
                if metadata_filter:
                    matches = True
                    for key, value in metadata_filter.items():
                        if key not in node.metadata or node.metadata[key] != value:
                            matches = False
                            break
                    if not matches:
                        continue
                
                similarity = 1 / (1 + distances[0][i])
                results.append((node, similarity))
            
            return results[:limit]
            
        except Exception as e:
            print(f"Error querying FAISS with metadata: {e}")
            raise

    def delete_by_metadata(self, metadata_filter: Dict[str, Any]) -> int:
        """
        Delete nodes that match the given metadata filter.
        Returns number of nodes deleted.
        """
        try:
            # Find nodes to delete
            nodes_to_delete = []
            indices_to_delete = []
            
            for idx, node in enumerate(self.nodes):
                matches = True
                for key, value in metadata_filter.items():
                    if key not in node.metadata or node.metadata[key] != value:
                        matches = False
                        break
                if matches:
                    nodes_to_delete.append(node)
                    indices_to_delete.append(idx)
            
            if not nodes_to_delete:
                print("No matching nodes found to delete")
                return 0
            
            # Create new index without deleted vectors
            new_index = faiss.IndexFlatL2(self.vector_dim)
            new_nodes = []
            
            # Add only non-deleted vectors to new index
            for idx, node in enumerate(self.nodes):
                if idx not in indices_to_delete:
                    new_index.add(node.embedding.reshape(1, -1))
                    new_nodes.append(node)
            
            # Replace old index and nodes
            self.index = new_index
            self.nodes = new_nodes
            
            # Save changes
            self.save()
            
            deleted_count = len(nodes_to_delete)
            print(f"Successfully deleted {deleted_count} nodes")
            return deleted_count
            
        except Exception as e:
            print(f"Error deleting nodes: {e}")
            raise

class HeaderMemory:
    def __init__(self):
        """Initialize the HeaderMemory system with FAISS index."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        try:
            # Determine embedding dimension
            sample_embedding = self.embeddings.embed_query("Sample query")
            self.embedding_dim = len(sample_embedding)
            self.logger.info(f"HeaderMemory: Determined embedding dimension: {self.embedding_dim}")
            
            # Initialize FAISS index
            self.faiss_index = faiss.IndexFlatL2(self.embedding_dim)
            self.logger.info("HeaderMemory: FAISS index initialized.")
            
            # Fetch and populate data columns
            self.data_columns = self.fetch_all_values()
            self.populate_faiss()
            
        except Exception as e:
            self.logger.error(f"HeaderMemory initialization failed: {e}")
            raise ValueError(f"HeaderMemory initialization error: {e}")
    
    def fetch_all_values(self) -> List[str]:
        """Fetch all column names."""
        # Implement the logic to fetch column names from your data source
        # For demonstration, returning a static list
        return [
            "city_name",
            "population",
            "average_temperature",
            "humidity",
            "latitude",
            "longitude",
            # Add more column names as needed
        ]
    
    def populate_faiss(self):
        """Populate the FAISS index with embedded column names."""
        self.logger.info("HeaderMemory: Populating FAISS index with column names.")
        try:
            embeddings = self.embeddings.embed_documents(self.data_columns)
            embeddings_array = np.array(embeddings).astype('float32')
            if embeddings_array.shape[1] != self.embedding_dim:
                self.logger.error(f"HeaderMemory: Embedding dimension mismatch. Expected {self.embedding_dim}, got {embeddings_array.shape[1]}")
                raise ValueError("Embedding dimensions do not match FAISS index dimensions.")
            self.faiss_index.add(embeddings_array)
            self.logger.info(f"HeaderMemory: FAISS index populated with {len(self.data_columns)} data columns.")
        except Exception as e:
            self.logger.error(f"HeaderMemory: Failed to populate FAISS index: {e}")
            raise ValueError(f"HeaderMemory population error: {e}")
    
    def search_relevant_columns(self, query: str, top_k: int = 5) -> List[str]:
        """Retrieve the top_k most relevant data columns based on the query."""
        self.logger.info(f"HeaderMemory: Embedding the query for retrieval: {query}")
        try:
            query_vector = self.embeddings.embed_query(query)
            distances, indices = self.faiss_index.search(np.array([query_vector]).astype('float32'), top_k)
            
            retrieved_columns = []
            for idx in indices[0]:
                column = self.get_data_column_by_index(idx)
                if column:
                    retrieved_columns.append(column)
            
            self.logger.info(f"HeaderMemory: Retrieved columns for the query: {retrieved_columns}")
            return retrieved_columns
        except Exception as e:
            self.logger.error(f"HeaderMemory: Error during FAISS search: {e}")
            raise ValueError(f"HeaderMemory FAISS search error: {e}")
    
    def get_data_column_by_index(self, index: int) -> str:
        """Retrieve the data column name by its FAISS index."""
        try:
            return self.data_columns[index]
        except IndexError:
            self.logger.error(f"HeaderMemory: Invalid index {index} retrieved from FAISS.")
            return ""


