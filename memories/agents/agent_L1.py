import faiss
import numpy as np
from gensim.models import KeyedVectors
import os
import pickle
from typing import Dict, List, Any, Optional

class Agent_L1:
    def __init__(self, instance_id: str, query: str):
        """
        Initialize Agent_L1 with FAISS instance ID and query.
        
        Args:
            instance_id (str): FAISS instance ID
            query (str): Query string to process
        """
        self.instance_id = instance_id
        self.query = query
        self.word_vectors = None
        self.faiss_index = None
        self.metadata = None
        
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
                    vector = self.word_vectors[w]
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
        try:
            # Load word vectors
            models_dir = os.path.join(os.getenv("PROJECT_ROOT", ""), "data", "models")
            vectors_path = os.path.join(models_dir, "glove.6B.100d.txt.word2vec")
            print(f"Loading word vectors from {vectors_path}")
            self.word_vectors = KeyedVectors.load_word2vec_format(vectors_path)
            
            # Load FAISS index and metadata
            faiss_dir = os.path.join(os.getenv("PROJECT_ROOT", ""), "data", "faiss")
            index_path = os.path.join(faiss_dir, f"index_{self.instance_id}.faiss")
            metadata_path = os.path.join(faiss_dir, f"metadata_{self.instance_id}.pkl")
            
            print(f"Loading FAISS index from {index_path}")
            self.faiss_index = faiss.read_index(index_path)
            
            print(f"Loading metadata from {metadata_path}")
            with open(metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
                
            print("Resources loaded successfully")
            
        except Exception as e:
            print(f"Error loading resources: {str(e)}")
            raise
    
    def find_similar_columns(self, k: int = 3) -> List[Dict[str, Any]]:
        """
        Find k most similar columns to the query.
        
        Args:
            k (int): Number of similar columns to retrieve
            
        Returns:
            List[Dict[str, Any]]: List of similar columns with their metadata
        """
        try:
            # Create query vector
            query_vector = self.get_word_embedding(self.query)
            query_vector = np.array([query_vector]).astype('float32')
            
            # Search for similar vectors
            D, I = self.faiss_index.search(query_vector, k)
            
            # Prepare results
            results = []
            for i, (idx, distance) in enumerate(zip(I[0], D[0])):
                if idx < len(self.metadata):
                    column_info = self.metadata[idx]
                    results.append({
                        "rank": i + 1,
                        "column_name": column_info['column_name'],
                        "file_name": column_info['file_name'],
                        "distance": float(distance)
                    })
            
            return results
            
        except Exception as e:
            print(f"Error finding similar columns: {str(e)}")
            return []
    
    def process(self) -> Dict[str, Any]:
        """
        Process the query and return similar columns.
        
        Returns:
            Dict[str, Any]: Processing results including similar columns
        """
        try:
            # Load required resources
            self.load_resources()
            
            # Find similar columns
            similar_columns = self.find_similar_columns()
            
            return {
                "query": self.query,
                "instance_id": self.instance_id,
                "similar_columns": similar_columns,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "query": self.query,
                "instance_id": self.instance_id,
                "error": str(e),
                "status": "error"
            }

def main():
    """
    Example usage of Agent_L1
    """
    # Example query and instance ID
    instance_id = "126324854065696"  # Replace with your instance ID
    query = "hospital"  # Replace with your query
    
    # Create and run agent
    agent = Agent_L1(instance_id, query)
    result = agent.process()
    
    # Print results
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
