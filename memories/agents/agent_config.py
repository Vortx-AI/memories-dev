"""Configuration settings for the Agent system"""

from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from memories.models.load_model import LoadModel
from memories.data_acquisition.data_connectors import parquet_connector
import os
import faiss
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from memories.core.memory import MemoryStore

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
TEST_QUERIES = [
    {
        "query": "Find restaurants near Bangalore",
        "coordinates": {"lat": 12.9716, "lon": 77.5946}
    },
    {
        "query": "Find cafes near Delhi",
        "coordinates": {"lat": 28.6139, "lon": 77.2090}
    },
    {
        "query": "Find hospitals near Mumbai",
        "coordinates": {"lat": 19.0760, "lon": 72.8777}
    }
]

AGENT_TEST_QUERIES = [
    "How do I write a Python function?",
    "What is the capital of France?",
    "Find restaurants near Central Park",
    "What cafes are within 2km of 12.9096437,77.6088268?"
]

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
    memory_store = MemoryStore()
    
    print("\nChecking Storage for Instance")
    print("=" * 50)
    print(f"Instance ID: {instance_id}")
    
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
    memory_store = MemoryStore()
    
    print("\nListing Available Instances")
    print("=" * 50)
    
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

def check_faiss_storage(instance_id: str):
    """
    Check FAISS storage details for a specific instance ID.
    
    Args:
        instance_id (str): The instance ID to check
    """
    memory_store = MemoryStore()
    
    print("\nChecking FAISS Storage")
    print("=" * 50)
    print(f"Instance ID: {instance_id}")
    
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

def create_memory_store(model: LoadModel, instance_id: str) -> Dict[str, Any]:
    """
    Create memory store with specified configuration.
    
    Args:
        model (LoadModel): Initialized model instance
        instance_id (str): Instance ID for the model
        
    Returns:
        Dict[str, Any]: Created memories data
    """
    memory_store = MemoryStore()
    import os
    from dotenv import load_dotenv
    import faiss
    
    # Load environment variables
    load_dotenv()
    
    # Get project root and data paths
    project_root = os.getenv("PROJECT_ROOT")
    osm_data_path = os.path.join(project_root, "data", "osm_data")
    faiss_dir = os.path.join(project_root, "data", "faiss")
    
    # Create directories if they don't exist
    os.makedirs(osm_data_path, exist_ok=True)
    os.makedirs(faiss_dir, exist_ok=True)
    
    # Create FAISS storage
    dimension = 768  # Standard embedding dimension
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
            
            # Get metadata about the parquet file
            parquet_info = parquet_connector(connector["file_path"], faiss_storage)
            
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
    memory_store = MemoryStore()
    import faiss
    import os
    
    print("\nCreating FAISS Storage")
    print("=" * 50)
    print(f"Instance ID: {instance_id}")
    
    try:
        # Get project root and FAISS directory
        project_root = os.getenv("PROJECT_ROOT")
        faiss_dir = os.path.join(project_root, "data", "faiss")
        os.makedirs(faiss_dir, exist_ok=True)
        
        # Create FAISS index (using dimension 768 for example, adjust as needed)
        dimension = 768  # Standard embedding dimension
        index = faiss.IndexFlatL2(dimension)
        
        # Save empty index
        index_path = os.path.join(faiss_dir, f"index_{instance_id}.faiss")
        faiss.write_index(index, index_path)
        
        print(f"\nFAISS Storage Created:")
        print(f"Index Path: {index_path}")
        print(f"Vector Dimension: {dimension}")
        print(f"Initial Size: {index.ntotal} vectors")
        
        return True
        
    except Exception as e:
        print(f"Error creating FAISS storage: {str(e)}")
        return False

class AgentConfig:
    def __init__(
        self,
        input: Dict[str, Any]
    ):
        """
        Initialize the AgentConfig with the provided parameters.

        Args:
            input (Dict[str, Any]): Dictionary containing configuration parameters
        """
        self.model_provider = input["model_provider"]
        self.deployment_type = input["deployment_type"]
        self.model_name = input["model_name"]
        self.use_gpu = input.get("use_gpu", True)
        self.data_connectors = input.get("data_connectors", [])
        self.project_root = input.get("project_root") or self._load_environment()
        
        # Initialize model
        self.model = self._load_model()
        
        # Create necessary directories
        self.osm_data_path = os.path.join(self.project_root, "data", "osm_data")
        self.faiss_dir = os.path.join(self.project_root, "data", "faiss")
        os.makedirs(self.osm_data_path, exist_ok=True)
        os.makedirs(self.faiss_dir, exist_ok=True)
        
        # Initialize dimensions
        self.dimension = 768  # FAISS vector dimension
        
        # Initialize memory store
        self.memory_store = MemoryStore()
        
        # FAISS storage will be initialized when needed
        self.faiss_storage = None

    def _load_environment(self) -> str:
        """Load environment variables and return the project root."""
        load_dotenv()
        project_root = os.getenv("PROJECT_ROOT")
        if not project_root:
            raise EnvironmentError("PROJECT_ROOT environment variable not set.")
        return project_root

    def _load_model(self) -> LoadModel:
        """Load the model using the LoadModel class."""
        return LoadModel(
            model_provider=self.model_provider,
            deployment_type=self.deployment_type,
            model_name=self.model_name,
            use_gpu=self.use_gpu
        )

    def _initialize_faiss_storage(self) -> Dict[str, Any]:
        """Initialize FAISS storage if not already initialized."""
        if self.faiss_storage is None:
            print(f"\nInitializing FAISS storage")
            index = faiss.IndexFlatL2(self.dimension)
            self.faiss_storage = {
                'index': index,
                'metadata': [],
                'vectors': []
            }
        return self.faiss_storage

    def _vectorize_data(self, data: Union[Dict[str, Any], pd.DataFrame]) -> np.ndarray:
        """
        Vectorize the data using the loaded model.
        
        Args:
            data (Union[Dict[str, Any], pd.DataFrame]): Data to vectorize
            
        Returns:
            np.ndarray: Vectorized data
        """
        # Convert dictionary data to DataFrame if it's not already
        if isinstance(data, dict):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")

        print(f"DataFrame shape: {df.shape}")
        print(f"DataFrame columns: {df.columns.tolist()}")

        # Convert data to text format for embedding
        texts = []
        for _, row in df.iterrows():
            # Combine relevant fields into a text representation
            text_parts = []
            for field in ['name', 'amenity', 'shop', 'description']:
                if field in row and pd.notna(row[field]):
                    text_parts.append(f"{field}: {row[field]}")
            texts.append(" | ".join(text_parts))

        print(f"Generated {len(texts)} text representations")

        # Get embeddings from the model
        embeddings = []
        batch_size = 32  # Adjust based on your memory constraints
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self.model.get_embeddings(batch)
            embeddings.extend(batch_embeddings)
            print(f"Processed batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")

        vectors = np.array(embeddings, dtype=np.float32)
        print(f"Generated vectors shape: {vectors.shape}")
        
        return vectors

    def create_memory_store(self) -> str:
        """
        Process data connectors and create FAISS index.
        
        Returns:
            str: The instance ID of the created memory store
        """
        # Initialize FAISS storage if not already initialized
        self._initialize_faiss_storage()
        
        instance_id = str(id(self.faiss_storage))
        print(f"\nCreating memory store with instance ID: {instance_id}")
        
        for connector in self.data_connectors:
            try:
                print(f"\nProcessing Data Connector: {connector['name']}")
                data = parquet_connector(connector['file_path'])
                
                # Vectorize the data
                vectors = self._vectorize_data(data)

                # Add vectors to FAISS index
                self.faiss_storage['index'].add(vectors)
                self.faiss_storage['vectors'].extend(vectors.tolist())

                # Update metadata
                self.faiss_storage['metadata'].append({
                    'name': connector['name'],
                    'type': connector['type'],
                    'path': connector['file_path'],
                    'num_vectors_added': vectors.shape[0]
                })

                print(f"Added {vectors.shape[0]} vectors to FAISS index from '{connector['name']}'")

            except Exception as e:
                print(f"Error processing {connector['name']}: {str(e)}")
                import traceback
                print(traceback.format_exc())
                continue

        # Save FAISS index and metadata
        index_path = os.path.join(self.faiss_dir, f"index_{instance_id}.faiss")
        metadata_path = os.path.join(self.faiss_dir, f"metadata_{instance_id}.pkl")
        
        faiss.write_index(self.faiss_storage['index'], index_path)
        with open(metadata_path, 'wb') as f:
            pickle.dump(self.faiss_storage, f)
            
        print(f"\nFAISS index and metadata saved successfully")
        print(f"Instance ID: {instance_id}")
        print(f"Total vectors: {self.faiss_storage['index'].ntotal}")
        
        return instance_id

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
