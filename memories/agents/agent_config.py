"""Configuration settings for the Agent system"""

import os
from pathlib import Path
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from gensim.models import KeyedVectors
import faiss
import numpy as np
from memories.core.model import LoadModel
from memories.data_acquisition.data_connectors import get_data_connectors, parquet_connector

def get_model_config(
    use_gpu: Optional[bool] = True,
    model_provider: Optional[str] = "deepseek-ai",
    deployment_type: Optional[str] = "deployment",
    model_name: Optional[str] = "deepseek-coder-1.3b-base"
) -> Tuple[LoadModel, str]:
    """
    Get model configuration and initialize the model.
    
    Args:
        use_gpu (bool, optional): Whether to use GPU. Defaults to True.
        model_provider (str, optional): The model provider. Defaults to "deepseek-ai".
        deployment_type (str, optional): Type of deployment. Defaults to "deployment".
        model_name (str, optional): Name of the model. Defaults to "deepseek-coder-1.3b-base".
    
    Returns:
        Tuple[LoadModel, str]: Initialized model instance and its instance ID
    """
    config = {
        "use_gpu": use_gpu,
        "model_provider": model_provider,
        "deployment_type": deployment_type,
        "model_name": model_name
    }
    
    # Initialize the model
    model = LoadModel(**config)
    
    # Get the instance ID
    instance_id = str(id(model))
    
    return model, instance_id

# Memory Configuration
def get_memory_config() -> Dict[str, Any]:
    """
    Get memory configuration including time range, location, and artifacts.
    
    Returns:
        Dict[str, Any]: Memory configuration settings
    """
    # Time range (last 30 days)
    end_time = datetime.now()
    start_time = end_time - timedelta(days=30)
    time_range = (start_time.isoformat(), end_time.isoformat())
    
    # Location (India bounding box)
    location = {
        "type": "Polygon",
        "coordinates": [[[68.1766451354, 7.96553477623], 
                        [97.4025614766, 7.96553477623],
                        [97.4025614766, 35.4940095078],
                        [68.1766451354, 35.4940095078],
                        [68.1766451354, 7.96553477623]]]
    }
    
    # Artifacts configuration
    artifacts = {
        "osm_data": ["points", "lines", "multipolygons"]
    }
    
    return {
        "time_range": time_range,
        "location": location,
        "artifacts": artifacts
    }

# Data Connector Configuration
def get_data_connectors(osm_data_path: str) -> List[Dict[str, str]]:
    """
    Get data connector configurations.
    
    Args:
        osm_data_path (str): Path to OSM data directory
        
    Returns:
        List[Dict[str, str]]: List of data connector configurations
    """
    return [
        {
            "name": "india_points_processed",
            "type": "parquet",
            "file_path": f"{osm_data_path}/india_points_processed.parquet"
        },
       # {
       #     "name": "india_lines",
        #    "type": "parquet",
       #     "file_path": f"{osm_data_path}/india_lines.parquet"
       # },
       # {
       #     "name": "india_multipolygons",
       #     "type": "parquet",
       #     "file_path": f"{osm_data_path}/india_multipolygons.parquet"
       # }
    ]

# Test Query Configuration

# Memory Store Settings
MEMORY_STORE_SETTINGS = {
    "batch_size": 10000,  # Number of records to process at once
    "top_k": 5,          # Number of results to return in similarity search
}

def check_instance_storage(instance_id: str):
    """
    Check storage details for a specific instance ID.
    
    Args:
        instance_id (str): The instance ID to check
    """
    from memories.core.memory import MemoryStore
    
    print("\nChecking Storage for Instance")
    print("=" * 50)
    print(f"Instance ID: {instance_id}")
    
    # Initialize memory store
    memory_store = MemoryStore()
    
    # Get stored memories
    stored_data = memory_store.get_stored_memories(instance_id)
    
    if stored_data:
        print("\nStorage Details:")
        print(f"FAISS Index Size: {stored_data['faiss_data'].get('index_size', 0)} vectors")
        print(f"Vector Dimension: {stored_data['faiss_data'].get('dimension', 'N/A')}")
        print(f"Database Records: {len(stored_data['database_records'])}")
        
        # Print first database record details
        if stored_data['database_records']:
            record = stored_data['database_records'][0]
            print("\nDatabase Record Details:")
            print(f"Created At: {record['created_at']}")
            print(f"Time Range: {record['start_date']} to {record['end_date']}")
            print(f"Data Connectors: {list(record['data_connectors'].keys())}")
    else:
        print("\nNo data found for this instance ID")

def list_available_instances():
    """List all available instance IDs in the database."""
    from memories.core.memory import MemoryStore
    
    print("\nListing Available Instances")
    print("=" * 50)
    
    # Initialize memory store
    memory_store = MemoryStore()
    
    try:
        # Query all instance IDs
        instances = memory_store.conn.execute("""
            SELECT 
                instance_id,
                created_at,
                start_date,
                end_date
            FROM memories
            ORDER BY created_at DESC
        """).fetchall()
        
        if instances:
            print(f"\nFound {len(instances)} instances:")
            for instance in instances:
                print(f"\nInstance ID: {instance[0]}")
                print(f"Created At: {instance[1]}")
                print(f"Time Range: {instance[2]} to {instance[3]}")
        else:
            print("\nNo instances found in the database")
            
    except Exception as e:
        print(f"Error listing instances: {str(e)}")

def check_faiss_storage(instance_id: str):
    """
    Check FAISS storage details for a specific instance ID.
    
    Args:
        instance_id (str): The instance ID to check
    """
    from memories.core.memory import MemoryStore
    import os
    
    print("\nChecking FAISS Storage")
    print("=" * 50)
    print(f"Instance ID: {instance_id}")
    
    # Initialize memory store
    memory_store = MemoryStore()
    
    # Check if FAISS index exists
    faiss_dir = os.path.join(memory_store.project_root, "data", "faiss")
    index_path = os.path.join(faiss_dir, f"index_{instance_id}.faiss")
    data_path = os.path.join(faiss_dir, f"data_{instance_id}.pkl")
    
    if os.path.exists(index_path):
        # Load the FAISS index
        if memory_store.load_faiss_index(instance_id):
            print("\nFAISS Storage Details:")
            print(f"Index Size: {memory_store.index.ntotal} vectors")
            print(f"Vector Dimension: {memory_store.index.d}")
            print(f"Index Type: {memory_store.index.__class__.__name__}")
            print(f"\nIndex File: {index_path}")
            print(f"Data File: {data_path if os.path.exists(data_path) else 'Not found'}")
    else:
        print(f"\nNo FAISS index found for instance ID: {instance_id}")
        print(f"Looked in: {faiss_dir}")

def download_word_vectors(model_path: str, model_type: str = 'glove') -> None:
    """
    Download word vectors model if it doesn't exist.
    
    Args:
        model_path (str): Path where the model should be saved
        model_type (str): Type of model to download ('glove' or 'fasttext')
    """
    import os
    import requests
    from pathlib import Path
    import zipfile
    
    model_dir = Path(model_path).parent
    model_dir.mkdir(parents=True, exist_ok=True)
    
    if not os.path.exists(model_path):
        print(f"Downloading {model_type} vectors to {model_path}...")
        
        if model_type == 'glove':
            # GloVe 100d (~150MB)
            url = "https://nlp.stanford.edu/data/glove.6B.zip"
            zip_path = model_dir / "glove.6B.zip"
        else:
            # FastText 100d (~150MB)
            url = "https://dl.fbaipublicfiles.com/fasttext/vectors-english/wiki-news-100d-1M.vec.zip"
            zip_path = model_dir / "wiki-news-100d-1M.vec.zip"
        
        # Download
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024
        
        with open(zip_path, 'wb') as f:
            for data in response.iter_content(block_size):
                f.write(data)
                
        # Extract
        print("Extracting vectors...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            if model_type == 'glove':
                # Extract only the 100d vectors
                for file in zip_ref.namelist():
                    if '100d' in file:
                        zip_ref.extract(file, model_dir)
                os.rename(model_dir / "glove.6B.100d.txt", model_path)
            else:
                zip_ref.extractall(model_dir)
                os.rename(model_dir / "wiki-news-100d-1M.vec", model_path)
        
        # Clean up
        os.remove(zip_path)
        print("Download completed!")
    else:
        print(f"Word vectors already exist at {model_path}")

def load_word_vectors(model_path: str, model_type: str = 'glove') -> KeyedVectors:
    """
    Load word vectors from file.
    
    Args:
        model_path (str): Path to the model file
        model_type (str): Type of model ('glove' or 'fasttext')
        
    Returns:
        KeyedVectors: Loaded word vectors
    """
    from gensim.scripts.glove2word2vec import glove2word2vec
    from gensim.models import KeyedVectors
    import os
    
    if model_type == 'glove':
        # Convert GloVe format to Word2Vec format if needed
        word2vec_path = model_path + '.word2vec'
        if not os.path.exists(word2vec_path):
            glove2word2vec(model_path, word2vec_path)
        return KeyedVectors.load_word2vec_format(word2vec_path)
    else:
        # FastText is already in Word2Vec format
        return KeyedVectors.load_word2vec_format(model_path)

def create_memory_store(model: LoadModel, instance_id: str) -> Dict[str, Any]:
    """
    Create memory store with specified configuration.
    
    Args:
        model (LoadModel): Initialized model instance
        instance_id (str): Instance ID for the model
        
    Returns:
        Dict[str, Any]: Created memories data
    """
    from memories.core.memory import MemoryStore
    import os
    from dotenv import load_dotenv
    import faiss
    from gensim.models import KeyedVectors
    
    # Load environment variables
    load_dotenv()
    
    # Initialize memory store
    memory_store = MemoryStore()
    
    # Get project root and data paths
    project_root = os.getenv("PROJECT_ROOT")
    osm_data_path = os.path.join(project_root, "data", "osm_data")
    faiss_dir = os.path.join(project_root, "data", "faiss")
    models_dir = os.path.join(project_root, "data", "models")
    
    # Create directories if they don't exist
    os.makedirs(osm_data_path, exist_ok=True)
    os.makedirs(faiss_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)
    
    # Choose model type ('glove' or 'fasttext')
    model_type = 'glove'
    
    # Load word vectors
    print("Setting up word vectors...")
    if model_type == 'glove':
        vectors_path = os.path.join(models_dir, "glove.6B.100d.txt")
    else:
        vectors_path = os.path.join(models_dir, "wiki-news-100d-1M.vec")
    
    # Download model if it doesn't exist
    download_word_vectors(vectors_path, model_type)
    
    print("Loading word vectors...")
    word_vectors = load_word_vectors(vectors_path, model_type)
    print("Word vectors loaded successfully")
    
    # Create FAISS storage
    dimension = 100  # Using 100d vectors
    faiss_storage = {
        'index': faiss.IndexFlatL2(dimension),
        'instance_id': instance_id,
        'metadata': []
    }
    
    print(f"\nCreated FAISS storage for instance: {instance_id}")
    print(f"Vector dimension: {dimension}")
    print(f"Initial vectors: {faiss_storage['index'].ntotal}")
    
    # Define time range (last 30 days)
    end_time = datetime.now()
    start_time = end_time - timedelta(days=30)
    time_range = (start_time.isoformat(), end_time.isoformat())
    
    # Define location (India bounding box)
    location = {
        "type": "Polygon",
        "coordinates": [[[68.1766451354, 7.96553477623], 
                        [97.4025614766, 7.96553477623],
                        [97.4025614766, 35.4940095078],
                        [68.1766451354, 35.4940095078],
                        [68.1766451354, 7.96553477623]]]
    }
    
    # Define artifacts
    artifacts = {
        "osm_data": ["points_processed", "lines", "multipolygons"]
    }
    
    # Get data connectors
    data_connectors = get_data_connectors(osm_data_path)
    
    # Create memories with FAISS storage
    memories = memory_store.create_memories(
        model=model,
        location=location,
        time_range=time_range,
        artifacts=artifacts,
        data_connectors=data_connectors,
        faiss_storage=faiss_storage
    )
    
    # Process each parquet file
    for connector in data_connectors:
        if connector["type"] == "parquet":
            print(f"\nProcessing {connector['name']}:")
            print(f"Current vector count: {faiss_storage['index'].ntotal}")
            
            # Pass word_vectors to parquet_connector
            parquet_info = parquet_connector(
                connector["file_path"], 
                faiss_storage=faiss_storage,
                word_vectors=word_vectors
            )
            
            print(f"After processing {connector['name']}:")
            print(f"Vector count: {faiss_storage['index'].ntotal}")
            print(f"Metadata entries: {len(faiss_storage['metadata'])}")
    
    print(f"\nFinal FAISS Storage Summary:")
    print(f"Total vectors: {faiss_storage['index'].ntotal}")
    print(f"Total metadata entries: {len(faiss_storage['metadata'])}")
    print(f"Vector dimension: {dimension}")
    
    return memories

def create_faiss_storage(instance_id: str) -> bool:
    """
    Create FAISS storage for a specific instance ID.
    
    Args:
        instance_id (str): Instance ID to create storage for
        
    Returns:
        bool: True if successful, False otherwise
    """
    from memories.core.memory import MemoryStore
    import faiss
    import numpy as np
    import os
    
    
def main():
    """Print current model instance ID when run directly."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Check model configuration and storage')
    parser.add_argument('--instance-id', type=str, help='Check storage for specific instance ID')
    parser.add_argument('--list-instances', action='store_true', help='List all available instances')
    parser.add_argument('--check-faiss', type=str, help='Check FAISS storage for specific instance ID')
    parser.add_argument('--create-memories', action='store_true', help='Create new memories with default configuration')
    parser.add_argument('--create-faiss', type=str, help='Create FAISS storage for specific instance ID')
    
    args = parser.parse_args()
    
    if args.create_faiss:
        print("create faiss storage")
        create_faiss_storage(args.create_faiss)
    elif args.create_memories:
        # Initialize model and create memories
        model, instance_id = get_model_config()
        print(f"\nCreating memories for instance ID: {instance_id}")
        memories = create_memory_store(model, instance_id)
        
        # Create FAISS storage for this instance
        create_faiss_storage(instance_id)
        
        print(f"\nMemories and FAISS storage created successfully")
        print(f"Instance ID: {instance_id}")
        
    elif args.check_faiss:
        check_faiss_storage(args.check_faiss)
    elif args.list_instances:
        list_available_instances()
    elif args.instance_id:
        check_instance_storage(args.instance_id)
    else:
        # Original configuration display code...
        print("\nTesting Model Configuration")
        print("=" * 50)
        
        model, instance_id = get_model_config()
        
        print(f"\nModel Configuration:")
        print(f"Provider: {model.model_provider}")
        print(f"Model: {model.model_name}")
        print(f"Deployment: {model.deployment_type}")
        print(f"GPU Enabled: {model.use_gpu}")
        print(f"\nInstance ID: {instance_id}")
        
        memory_config = get_memory_config()
        print(f"\nMemory Configuration:")
        print(f"Time Range: {memory_config['time_range'][0]} to {memory_config['time_range'][1]}")
        print(f"Location: India Bounding Box")
        print(f"Artifacts: {memory_config['artifacts']}")

if __name__ == "__main__":
    main()
