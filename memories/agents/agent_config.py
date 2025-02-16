"""Configuration settings for the Agent system"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from memories.models.load_model import LoadModel
from memories.data_acquisition.data_connectors import parquet_connector
import pickle
import pandas as pd
import numpy as np
import os
import faiss
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

class AgentConfig:
    def __init__(self, model: Any, instance_id: str):
        """
        Initialize the AgentConfig with the provided model and instance ID.

        Args:
            model (Any): The model to be used for creating memories.
            instance_id (str): Unique identifier for the memory store instance.
        """
        self.model = model
        self.instance_id = instance_id
        self.project_root = self._load_environment()
        self.osm_data_path = os.path.join(self.project_root, "data", "osm_data")
        self.faiss_dir = os.path.join(self.project_root, "data", "faiss")
        self.index_path = os.path.join(self.faiss_dir, f"index_{self.instance_id}.faiss")
        self.metadata_path = os.path.join(self.faiss_dir, f"metadata_{self.instance_id}.pkl")
        self.dimension = 768  # FAISS vector dimension
        self.faiss_storage = self._initialize_faiss_storage()
        self.memory_store = MemoryStore()
        self._create_directories()

    def _load_environment(self) -> str:
        """Load environment variables and return the project root."""
        load_dotenv()
        project_root = os.getenv("PROJECT_ROOT")
        if not project_root:
            raise EnvironmentError("PROJECT_ROOT environment variable not set.")
        print(f"[MemoryStore] Project root: {project_root}")
        return project_root

    def _create_directories(self):
        """Create necessary directories if they don't exist."""
        os.makedirs(self.osm_data_path, exist_ok=True)
        os.makedirs(self.faiss_dir, exist_ok=True)
        print(f"[MemoryStore] Directories ensured at: {self.osm_data_path} and {self.faiss_dir}")

    def _initialize_faiss_storage(self) -> Dict[str, Any]:
        """
        Initialize or load the FAISS storage.

        Returns:
            Dict[str, Any]: FAISS storage containing index, metadata, and vectors.
        """
        if Path(self.index_path).exists() and Path(self.metadata_path).exists():
            print(f"\nLoading existing FAISS storage for instance: {self.instance_id}")
            index = faiss.read_index(self.index_path)
            with open(self.metadata_path, 'rb') as f:
                faiss_storage = pickle.load(f)
            print(f"Loaded FAISS index with {index.ntotal} vectors.")
        else:
            print(f"\nCreating new FAISS storage for instance: {self.instance_id}")
            index = faiss.IndexFlatL2(self.dimension)
            faiss_storage = {
                'index': index,
                'instance_id': self.instance_id,
                'metadata': [],
                'vectors': []
            }
            print(f"Created FAISS index with dimension: {self.dimension} and {index.ntotal} vectors.")
        return faiss_storage

    def create_memory_store(self) -> Dict[str, Any]:
        """
        Create or update the memory store with FAISS indices.

        Returns:
            Dict[str, Any]: Updated FAISS storage information.
        """
        print(f"Vector dimension: {self.dimension}")
        print(f"Initial vectors: {self.faiss_storage['index'].ntotal}")

        # Define data connectors
        data_connectors = [
            {
                "name": "india_points_processed",
                "type": "parquet",
                "file_path": os.path.join(self.osm_data_path, "india_points_processed.parquet")
            }
        ]

        # Process each parquet file and add to FAISS
        print("\nProcessing data files...")
        for connector in data_connectors:
            if connector["type"] == "parquet" and os.path.exists(connector["file_path"]):
                print(f"\nProcessing {connector['name']}:")
                print(f"File: {connector['file_path']}")
                print(f"Current vector count: {self.faiss_storage['index'].ntotal}")

                try:
                    # Process the parquet file and add vectors to FAISS
                    file_info = parquet_connector(connector["file_path"], self.faiss_storage)

                    print(f"Processed file info:")
                    print(f"Columns: {len(file_info['columns'])}")
                    print(f"Rows: {file_info['num_rows']}")
                    print(f"New vector count: {self.faiss_storage['index'].ntotal}")

                    # Save FAISS index after each file
                    faiss.write_index(self.faiss_storage['index'], self.index_path)

                    # Save metadata
                    with open(self.metadata_path, 'wb') as f:
                        pickle.dump(self.faiss_storage, f)

                    print(f"[ParquetConnector] Saved FAISS index and metadata.")

                except Exception as e:
                    print(f"Error processing {connector['name']}: {str(e)}")
                    import traceback
                    print(traceback.format_exc())
            else:
                print(f"\nSkipping {connector['name']}: File not found or wrong type")

        print(f"\nFinal FAISS Storage Summary:")
        print(f"Total vectors: {self.faiss_storage['index'].ntotal}")
        print(f"Total metadata entries: {len(self.faiss_storage['metadata'])}")
        print(f"Vector dimension: {self.dimension}")

        # Create memory entry in the MemoryStore
        print("[MemoryStore] Processed metadata for india_points_processed")
        print(f"[MemoryStore] Created memory with ID: {self.instance_id}")

        print("\nCreating FAISS Storage")
        print("==================================================")
        print(f"Instance ID: {self.instance_id}")
        print(f"[MemoryStore] Connected to DuckDB at {os.path.join(self.project_root, 'data', 'memory.db')}")
        print(f"[MemoryStore] Memories table initialized\n")

        print("FAISS Storage Created:")
        print(f"Index Path: {self.index_path}")
        print(f"Vector Dimension: {self.dimension}")
        print(f"Initial Size: {self.faiss_storage['index'].ntotal} vectors\n")

        print("Memories and FAISS storage created successfully")
        print(f"Instance ID: {self.instance_id}")

        return self.faiss_storage

def main():
    """Main function to create memories."""
    import argparse

    parser = argparse.ArgumentParser(description='Create memories with FAISS storage')
    parser.add_argument('--instance-id', type=str, required=True, help='Instance ID for the memory store')
    parser.add_argument('--model', type=str, required=True, help='Model to load for creating memories')

    args = parser.parse_args()

    # Load your model here
    # Replace with actual model loading logic as per your application
    model, _ = get_model_config()  # Assuming there's a get_model_config function

    # Instantiate AgentConfig with required inputs
    agent_config = AgentConfig(model=model, instance_id=args.instance_id)
    agent_config.create_memory_store()

if __name__ == "__main__":
    main()
