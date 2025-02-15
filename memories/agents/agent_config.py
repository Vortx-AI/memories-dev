"""Configuration settings for the Agent system"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from memories.models.load_model import LoadModel

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
            "name": "india_points",
            "type": "parquet",
            "file_path": f"{osm_data_path}/india_points.parquet"
        },
        {
            "name": "india_lines",
            "type": "parquet",
            "file_path": f"{osm_data_path}/india_lines.parquet"
        },
        {
            "name": "india_multipolygons",
            "type": "parquet",
            "file_path": f"{osm_data_path}/india_multipolygons.parquet"
        }
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

def main():
    """Print current model instance ID when run directly."""
    print("\nTesting Model Configuration")
    print("=" * 50)
    
    # Get model and instance ID with default configuration
    model, instance_id = get_model_config()
    
    print(f"\nModel Configuration:")
    print(f"Provider: {model.model_provider}")
    print(f"Model: {model.model_name}")
    print(f"Deployment: {model.deployment_type}")
    print(f"GPU Enabled: {model.use_gpu}")
    print(f"\nInstance ID: {instance_id}")
    
    # Print memory configuration
    memory_config = get_memory_config()
    print(f"\nMemory Configuration:")
    print(f"Time Range: {memory_config['time_range'][0]} to {memory_config['time_range'][1]}")
    print(f"Location: India Bounding Box")
    print(f"Artifacts: {memory_config['artifacts']}")

if __name__ == "__main__":
    main()
