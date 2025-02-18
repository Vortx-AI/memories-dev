import os
import numpy as np
import logging
import faiss
import pickle
from typing import Dict, List
from pathlib import Path
from dotenv import load_dotenv
from gensim.models import KeyedVectors

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_faiss_index(instance_id: int) -> faiss.Index:
    """Get FAISS index for the specified instance."""
    load_dotenv()
    project_root = os.getenv("PROJECT_ROOT")
    if not project_root:
        raise ValueError("PROJECT_ROOT not found in environment variables")
    
    faiss_dir = os.path.join(project_root, "data", "faiss")
    index_path = os.path.join(faiss_dir, f"index_{instance_id}.faiss")
    metadata_path = os.path.join(faiss_dir, f"metadata_{instance_id}.pkl")
    
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"FAISS index not found at {index_path}")
    
    return faiss.read_index(index_path), metadata_path

def normalize_vector(vector: np.ndarray) -> np.ndarray:
    """Normalize vector to unit length."""
    norm = np.linalg.norm(vector)
    if norm > 0:
        return vector / norm
    return vector

def add_function_terms_to_faiss(instance_id: int = 1739846342):
    """Add analysis-related terms to FAISS instance using GloVe embeddings."""
    terms = [
        "ambiance", "social", "environmental", "temporal", "profile",
        "analysis", "analyze", "sentiment", "crowd", "activity",
        "demographic", "weather", "noise", "lightning", "peak",
        "seasonal", "event", "energy", "comfort", "ambience",
        "suited", "audience", "age"
    ]
    
    logger.info("Starting to process terms for FAISS")
    
    try:
        # Load word vectors
        load_dotenv()
        project_root = os.getenv("PROJECT_ROOT")
        models_dir = os.path.join(project_root, "data", "models")
        word_vectors = KeyedVectors.load_word2vec_format(
            os.path.join(models_dir, "glove.6B.100d.txt.word2vec")
        )
        
        # Get FAISS index and metadata path
        faiss_index, metadata_path = get_faiss_index(instance_id)
        
        # Load existing metadata
        with open(metadata_path, 'rb') as f:
            existing_metadata = pickle.load(f)
        
        # Convert terms to embeddings
        embeddings = []
        new_metadata = []
        valid_terms = []
        
        for term in terms:
            try:
                # Get and normalize vector
                vector = word_vectors[term]
                normalized_vector = normalize_vector(vector)
                embeddings.append(normalized_vector)
                valid_terms.append(term)
                
                # Create metadata entry for the term
                metadata_entry = {
                    'term': term,  # Add the term itself
                    'function_name': 'analysis_terms1',
                    'file_path': 'memories/utils/earth/analysis_terms.py',
                }
                new_metadata.append(metadata_entry)
                
            except KeyError:
                logger.warning(f"Term '{term}' not found in vocabulary")
        
        if not embeddings:
            logger.error("No valid embeddings found")
            return
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings).astype('float32')
        
        # Create a new FAISS index with cosine similarity
        dimension = embeddings_array.shape[1]
        new_index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        
        # Add normalized vectors to new index
        new_index.add(embeddings_array)
        
        # Get existing vectors if any
        if faiss_index.ntotal > 0:
            try:
                # Get existing vectors safely
                existing_vectors = faiss.vector_to_array(faiss_index).reshape(-1, dimension)
                # Normalize existing vectors
                existing_vectors = np.array([normalize_vector(v) for v in existing_vectors])
                new_index.add(existing_vectors)
                
                # Update metadata to include existing metadata
                updated_metadata = existing_metadata + new_metadata
            except Exception as e:
                logger.warning(f"Error processing existing vectors: {str(e)}")
                # If there's an error, just use new metadata
                updated_metadata = new_metadata
        else:
            updated_metadata = new_metadata
        
        # Save updated index and metadata
        faiss_dir = os.path.join(project_root, "data", "faiss")
        index_path = os.path.join(faiss_dir, f"index_{instance_id}.faiss")
        
        # Save the new index
        faiss.write_index(new_index, index_path)
        
        # Save updated metadata
        with open(metadata_path, 'wb') as f:
            pickle.dump(updated_metadata, f)
        
        logger.info(f"Successfully added {len(valid_terms)} terms to FAISS")
        logger.info(f"Terms added: {', '.join(valid_terms)}")
        logger.info(f"Updated index saved to: {index_path}")
        logger.info(f"Updated metadata saved to: {metadata_path}")
        logger.info(f"Total vectors in index: {new_index.ntotal}")
        
    except Exception as e:
        logger.error(f"Error during FAISS update: {str(e)}", exc_info=True)
        raise

def main():
    """Main execution function."""
    try:
        add_function_terms_to_faiss(instance_id=1739846342)
        logger.info("Process completed successfully")
    except Exception as e:
        logger.error(f"Process failed: {str(e)}")

if __name__ == "__main__":
    main()