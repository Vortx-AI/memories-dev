import faiss
import numpy as np
from gensim.models import KeyedVectors
import os
import pickle
from typing import Dict, List, Any, Optional
import pandas as pd
import duckdb

# Module-level cache for word vectors
_WORD_VECTORS = None

class Agent_L1:
    def __init__(self, 
                 instance_id: str, 
                 query: str, 
                 file_path: Optional[str] = None, 
                 geometry_column: Optional[str] = None, 
                 geometry_type: Optional[str] = None):
        """
        Initialize Agent_L1 with FAISS instance ID, query, and options to override
        the default Parquet file path and provide geometry details.

        Args:
            instance_id (str): FAISS instance ID.
            query (str): Query string to process.
            file_path (Optional[str]): Custom path to the Parquet file. If provided,
                                       it overrides the file name from metadata.
            geometry_column (Optional[str]): Name of the geometry column.
            geometry_type (Optional[str]): Type of geometry (e.g., 'point', 'polygon').
        """
        self.instance_id = instance_id
        self.query = query
        self.file_path = file_path
        self.geometry_column = geometry_column
        self.geometry_type = geometry_type
        
        self.faiss_index = None
        self.metadata = None
        # If a file_path is provided, initialize parquet_file with it.
        self.parquet_file = self.file_path if self.file_path is not None else None

    def get_word_embedding(self, word: str, vector_size: int = 100) -> np.ndarray:
        """
        Get word embedding for a single word, handling multi-word phrases by averaging.
        """
        try:
            # Convert to lowercase and split into words
            words = word.lower().split('_')
            vectors = []
            
            for w in words:
                try:
                    vector = _WORD_VECTORS[w]
                    vectors.append(vector)
                except KeyError:
                    print(f"Warning: '{w}' not found in vocabulary")
                    continue
            
            if vectors:
                avg_vector = np.mean(vectors, axis=0)
                # Pad vector to match desired size
                if len(avg_vector) < vector_size:
                    avg_vector = np.pad(avg_vector, (0, vector_size - len(avg_vector)))
                elif len(avg_vector) > vector_size:
                    avg_vector = avg_vector[:vector_size]
                
                # Normalize
                norm = np.linalg.norm(avg_vector)
                if norm > 0:
                    avg_vector = avg_vector / norm
                return avg_vector.astype('float32')
            else:
                return np.zeros(vector_size, dtype='float32')
        except Exception as e:
            print(f"Error in get_word_embedding for word '{word}': {str(e)}")
            return np.zeros(vector_size, dtype='float32')
    
    def load_resources(self) -> None:
        """
        Load required resources: word vectors, FAISS index, and metadata.
        """
        global _WORD_VECTORS
        try:
            # Load word vectors if not already loaded.
            if _WORD_VECTORS is None:
                models_dir = os.path.join(os.getenv("PROJECT_ROOT", ""), "data", "models")
                vectors_path = os.path.join(models_dir, "glove.6B.100d.txt.word2vec")
                print(f"Loading word vectors from {vectors_path}")
                _WORD_VECTORS = KeyedVectors.load_word2vec_format(vectors_path)
                print("Word vectors loaded and cached")
            else:
                print("Using cached word vectors")
            
            # Load FAISS index and metadata.
            faiss_dir = os.path.join(os.getenv("PROJECT_ROOT", ""), "data", "faiss")
            index_path = os.path.join(faiss_dir, f"index_{self.instance_id}.faiss")
            metadata_path = os.path.join(faiss_dir, f"metadata_{self.instance_id}.pkl")
            
            print(f"Loading FAISS index from {index_path}")
            self.faiss_index = faiss.read_index(index_path)
            
            print(f"Loading metadata from {metadata_path}")
            with open(metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
            
            # Use provided file_path if available; otherwise use the file_name from metadata.
            if self.file_path:
                self.parquet_file = self.file_path
            elif self.metadata and len(self.metadata) > 0:
                self.parquet_file = self.metadata[0].get('file_name')
                
            print("Resources loaded successfully")
            
        except Exception as e:
            print(f"Error loading resources: {str(e)}")
            raise
    
    def find_similar_columns(self, k: int = 3) -> List[Dict[str, Any]]:
        """
        Find k most similar columns to the query.
        """
        try:
            # Create query vector
            query_vector = self.get_word_embedding(self.query)
            
            # Print debug information
            print(f"\nQuery vector norm: {np.linalg.norm(query_vector)}")
            print(f"FAISS index type: {type(self.faiss_index)}")
            
            query_vector = np.array([query_vector]).astype('float32')
            
            # Search for similar vectors
            D, I = self.faiss_index.search(query_vector, k)
            
            # Print raw results for debugging
            print(f"\nTop {k} columns similar to '{self.query}':")
            
            # Prepare results
            results = []
            for i, (idx, distance) in enumerate(zip(I[0], D[0])):
                if idx < len(self.metadata):
                    column_info = self.metadata[idx]
                    result = {
                        "rank": i + 1,
                        "column_name": column_info['column_name'],
                        "file_name": column_info['file_name'],
                        "file_path": column_info['file_path'],
                        "geometry": column_info['geometry_column'],
                        "geometry_type": column_info['geometry_type'],
                        "distance": float(distance)
                    }
                    results.append(result)
                    # Print results in the same format as the working example
                    print(f"\n{i+1}. Column: {column_info['column_name']}")
                    print(f"   File: {column_info['file_name']}")
                    print(f"   Distance: {distance:.4f}")
            
            return results
            
        except Exception as e:
            print(f"Error finding similar columns: {str(e)}")
            return []
    
    def process(self) -> Dict[str, Any]:
        """
        Process the query and return similar columns.
        
        Returns:
            Dict[str, Any]: Processing results including similar columns.
        """
        try:
            # Load required resources.
            self.load_resources()
            
            # Find similar columns.
            similar_columns = self.find_similar_columns()
            
            # Process search results
            similar_columns = []
            for i, (idx, distance) in enumerate(zip(I[0], D[0])):
                if idx < len(self.metadata):
                    metadata = self.metadata[idx]
                    
                    # Create result dictionary based on metadata type
                    try:
                        # Try original column metadata format
                        result = {
                            'column_name': metadata['column_name'],
                            'file_name': metadata['file_name'],
                            'file_path': metadata['file_path'],
                            'geometry': metadata['geometry'],
                            'geometry_type': metadata['geometry_type'],
                            'distance': float(distance)
                        }
                    except KeyError:
                        # Fall back to analysis terms metadata format
                        result = {
                            'column_name': metadata.get('term', 'unknown'),  # Use term as column_name
                            'file_name': metadata.get('function_name', 'unknown'),
                            'file_path': metadata.get('file_path', 'unknown'),
                            'geometry': 'POLYGON',  # Default value
                            'geometry_type': 'POLYGON',  # Default value
                            'distance': float(distance)
                        }
                    
                    similar_columns.append(result)

            return {
                "status": "success",
                "similar_columns": similar_columns
            }

        except Exception as e:
            logger.error(f"Error in L1 Agent: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

def main():
    """
    Example usage of Agent_L1 with file_path, geometry_column, and geometry_type provided.
    """
    # Example query and instance ID, with added file_path, geometry_column and geometry_type.
    instance_id = "126324854065696"  # Replace with your instance ID.
    query = "hospital"               # Replace with your query.
    file_path = os.path.join(os.getenv("PROJECT_ROOT", ""), "data", "parquet", "example.parquet")
    geometry_column = "geom"         # Replace with your geometry column name.
    geometry_type = "polygon"        # Replace with your geometry type if needed.
    
    # Create and run agent.
    agent = Agent_L1(instance_id, query, file_path, geometry_column, geometry_type)
    result = agent.process()
    
    # Print results.
    if result["status"] == "success":
        print(f"\nQuery: {result['query']}")
        print(f"Instance ID: {result['instance_id']}")
        print("\nSimilar columns:")
        for col in result["similar_columns"]:
            print(f"\n{col['rank']}. Column: {col['column_name']}")
            print(f"   File: {col['file_name']}")
            print(f"   Distance: {col['distance']:.4f}")
    else:
        print(f"Error: {result['error']}")

if __name__ == "__main__":
    main()
