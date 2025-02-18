import os
import numpy as np
import logging
import faiss
from typing import Dict, List
from pathlib import Path
from dotenv import load_dotenv
from gensim.models import KeyedVectors

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_glove_path() -> str:
    """Get the GloVe model path from environment settings."""
    load_dotenv()
    project_root = os.getenv("PROJECT_ROOT")
    if not project_root:
        raise ValueError("PROJECT_ROOT not found in environment variables")
    
    models_dir = os.path.join(project_root, "data", "models")
    vectors_path = os.path.join(models_dir, "glove.6B.100d.txt.word2vec")
    
    if not os.path.exists(vectors_path):
        raise FileNotFoundError(f"GloVe vectors not found at {vectors_path}")
    
    return vectors_path

def load_glove_model() -> KeyedVectors:
    """Load the GloVe model using the same approach as agent_config."""
    vectors_path = get_glove_path()
    logger.info(f"Loading GloVe model from {vectors_path}")
    return KeyedVectors.load_word2vec_format(vectors_path)

def get_faiss_index(instance_id: int) -> faiss.Index:
    """Get FAISS index for the specified instance."""
    load_dotenv()
    project_root = os.getenv("PROJECT_ROOT")
    if not project_root:
        raise ValueError("PROJECT_ROOT not found in environment variables")
    
    faiss_dir = os.path.join(project_root, "data", "faiss")
    index_path = os.path.join(faiss_dir, f"index_{instance_id}.faiss")
    
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"FAISS index not found at {index_path}")
    
    return faiss.read_index(index_path)

def add_function_terms_to_faiss(faiss_instance_id: int = 1739846342):
    """Add analysis-related terms to FAISS instance using GloVe embeddings."""
    terms = [
        "ambiance", "social", "environmental", "temporal", "profile",
        "analysis", "analyze", "sentiment", "crowd", "activity",
        "demographic", "weather", "noise", "lightning", "peak",
        "seasonal", "event", "energy", "comfort", "ambience",
        "suited", "audience", "age"
    ]
    
    metadata = {
        "function": "analyze_location_ambience",
        "run_type": "function"
    }
    
    logger.info("Starting to process terms for FAISS")
    
    try:
        # Load GloVe model
        glove = load_glove_model()
        
        # Convert terms to embeddings
        embeddings = []
        valid_terms = []
        
        for term in terms:
            try:
                embeddings.append(glove[term])
                valid_terms.append(term)
            except KeyError:
                logger.warning(f"Term '{term}' not found in GloVe vocabulary")
        
        if not embeddings:
            logger.error("No valid embeddings found")
            return
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings).astype('float32')
        
        # Get FAISS index
        faiss_index = get_faiss_index(faiss_instance_id)
        
        # Add to FAISS
        faiss_index.add(embeddings_array)
        
        # Save updated index
        load_dotenv()
        project_root = os.getenv("PROJECT_ROOT")
        faiss_dir = os.path.join(project_root, "data", "faiss")
        index_path = os.path.join(faiss_dir, f"index_{faiss_instance_id}.faiss")
        faiss.write_index(faiss_index, index_path)
        
        logger.info(f"Successfully added {len(valid_terms)} terms to FAISS")
        logger.info(f"Terms added: {', '.join(valid_terms)}")
        logger.info(f"Updated index saved to: {index_path}")
        
    except Exception as e:
        logger.error(f"Error during FAISS update: {str(e)}")
        raise

def main():
    """Main execution function."""
    try:
        add_function_terms_to_faiss(faiss_instance_id=1739846342)
        logger.info("Process completed successfully")
    except Exception as e:
        logger.error(f"Process failed: {str(e)}")

if __name__ == "__main__":
    main() 