# Import required libraries
import faiss
import numpy as np
from gensim.models import KeyedVectors
import os
import pickle
from typing import Dict, Any
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def normalize_vector(vector: np.ndarray) -> np.ndarray:
    """Normalize vector to unit length."""
    norm = np.linalg.norm(vector)
    if norm > 0:
        return vector / norm
    return vector

def get_word_embedding(word: str, word_vectors: KeyedVectors, vector_size: int = 100) -> np.ndarray:
    """Get word embedding and normalize it."""
    try:
        # Convert to lowercase and split into words
        words = word.lower().split('_')
        vectors = []
        
        for w in words:
            try:
                vector = word_vectors[w]
                vectors.append(vector)
            except KeyError:
                logger.warning(f"Warning: '{w}' not found in vocabulary")
                continue
        
        if vectors:
            avg_vector = np.mean(vectors, axis=0)
            return normalize_vector(avg_vector.astype('float32'))
        else:
            return np.zeros(vector_size, dtype='float32')
    except Exception as e:
        logger.error(f"Error in get_word_embedding for word '{word}': {str(e)}")
        return np.zeros(vector_size, dtype='float32')

def search_faiss(query_word: str, instance_id: int = 1739846342, top_k: int = 3) -> None:
    """Search FAISS index and print complete metadata for results."""
    try:
        # Load word vectors
        load_dotenv()
        project_root = os.getenv("PROJECT_ROOT")
        models_dir = os.path.join(project_root, "data", "models")
        word_vectors = KeyedVectors.load_word2vec_format(
            os.path.join(models_dir, "glove.6B.100d.txt.word2vec")
        )

        # Load FAISS index
        faiss_dir = os.path.join(project_root, "data", "faiss")
        index_path = os.path.join(faiss_dir, f"index_{instance_id}.faiss")
        metadata_path = os.path.join(faiss_dir, f"metadata_{instance_id}.pkl")

        index = faiss.read_index(index_path)
        
        with open(metadata_path, 'rb') as f:
            metadata = pickle.load(f)

        # Create query vector
        query_vector = get_word_embedding(query_word, word_vectors)
        query_vector = np.array([query_vector]).astype('float32')

        # Search for similar vectors
        D, I = index.search(query_vector, top_k)

        # Print results
        print(f"\nTop {top_k} matches for '{query_word}':")
        for i, (idx, distance) in enumerate(zip(I[0], D[0])):
            if idx < len(metadata):
                print(f"\n{i+1}. Distance: {distance:.4f}")
                print("Metadata:")
                for key, value in metadata[idx].items():
                    print(f"   {key}: {value}")
            else:
                print(f"\n{i+1}. Index {idx} out of range for metadata")

    except Exception as e:
        logger.error(f"Error during search: {str(e)}", exc_info=True)

if __name__ == "__main__":
    search_faiss("ambiance") 