from memories.models.load_model import LoadModel
from memories.core.memory import MemoryStore

def main():
    # Initialize with advanced models
    load_model = LoadModel(
        use_gpu=True,
        model_provider="deepseek-ai",  # "deepseek" or "openai"
        deployment_type="local",  # "local" or "api"
        model_name="deepseek-r1-zero"  # "deepseek-r1-zero" or "gpt-4o" or "deepseek-coder-3.1b-base"
    )

    # Create Earth memories
    memory_store = MemoryStore()

    # Example coordinates for San Francisco
    memories = memory_store.create_memories(
        model=load_model,
        location=(37.7749, -122.4194),  # San Francisco coordinates
        time_range=("2024-01-01", "2024-02-01"),
        artifacts={
            "satellite": ["sentinel-2", "landsat8"],
            "landuse": ["osm", "overture"]
        }
    )

    print("Created memories:", memories)

if __name__ == "__main__":
    main() 