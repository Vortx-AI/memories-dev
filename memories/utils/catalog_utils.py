import os
import sys
import asyncio
from datetime import datetime

async def register_with_memory_catalog(settings_module):
    """Register all paths specified in settings with the memory catalog."""
    # Import memory_catalog
    try:
        # Try to import from the memories package first
        from memories.core.memory_catalog import MemoryCatalog
    except ImportError:
        # If not available, try to import using relative path resolution
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
        
        if project_root not in sys.path:
            sys.path.append(project_root)
        
        from memories.core.memory_catalog import MemoryCatalog
    
    memory_catalog = MemoryCatalog()
    print("Registering data sources with memory catalog...")
    
    # Reference the settings from the provided module
    COLD = settings_module.COLD
    
    # Register paths from COLD storage
    if "pkl_files" in COLD and COLD["pkl_files"].get("enabled", False):
        for data_name, data_config in COLD["pkl_files"].items():
            if data_name == "enabled":
                continue
                
            file_path = data_config.get("file_path")
            if not file_path:
                continue
                
            # Determine file size if it exists
            size = 0
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                
            # Extract metadata
            metadata = data_config.get("metadata", {})
            if metadata.get("last_updated") == "auto":
                metadata["last_updated"] = datetime.now().isoformat()
                
            # Extract tags from tiering configuration
            tags = []
            if data_config.get("tiering_red_hot"):
                tags.append("red_hot")
            if data_config.get("tiering_hot"):
                tags.append("hot")
                
            try:
                # Register in catalog
                await memory_catalog.register_data(
                    tier="cold",
                    location=file_path,
                    size=size,
                    data_type="pickle",
                    tags=tags,
                    metadata=metadata,
                    table_name=data_name
                )
                print(f"Registered {data_name} ({file_path}) in cold tier")
            except Exception as e:
                print(f"Error registering {data_name}: {e}")
    
    # Add similar blocks for other tiers as needed (HOT, WARM, RED_HOT, GLACIER)
    
    print("Finished registering data sources with memory catalog") 