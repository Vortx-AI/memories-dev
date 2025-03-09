"""
Warm memory implementation using file-based storage for intermediate data.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class WarmMemory:
    """Warm memory layer using file-based storage."""
    
    def __init__(self, storage_path: str = "data/memory/warm"):
        """Initialize warm memory.
        
        Args:
            storage_path: Path to store warm memory files
        """
        self.logger = logger
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Initialized warm memory storage at {storage_path}")

    async def store(
        self,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Store data in warm memory with metadata and tags.
        
        Args:
            data: Data to store
            metadata: Optional metadata about the data
            tags: Optional tags for categorizing the data
            
        Returns:
            bool: True if storage was successful, False otherwise
        """
        try:
            # Generate filename from tags or timestamp
            filename = f"{tags[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json" if tags else f"warm_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.storage_path / filename

            # Prepare data for storage
            storage_data = {
                "data": data,
                "metadata": metadata or {},
                "tags": tags or [],
                "stored_at": datetime.now().isoformat()
            }

            # Store as JSON
            with open(filepath, 'w') as f:
                json.dump(storage_data, f)

            # Create tag index files
            if tags:
                for tag in tags:
                    tag_dir = self.storage_path / "tags"
                    tag_dir.mkdir(exist_ok=True)
                    tag_file = tag_dir / f"{tag}.txt"
                    with open(tag_file, 'a') as f:
                        f.write(f"{filename}\n")

            return True

        except Exception as e:
            self.logger.error(f"Error storing in warm storage: {e}")
            return False

    async def retrieve(
        self,
        query: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        """Retrieve data from warm memory.
        
        Args:
            query: Optional query parameters
            tags: Optional tags to filter by
            
        Returns:
            Retrieved data or None if not found
        """
        try:
            results = []
            
            if tags:
                # Get files by tags
                tag_dir = self.storage_path / "tags"
                for tag in tags:
                    tag_file = tag_dir / f"{tag}.txt"
                    if tag_file.exists():
                        with open(tag_file, 'r') as f:
                            filenames = f.read().splitlines()
                            for filename in filenames:
                                filepath = self.storage_path / filename
                                if filepath.exists():
                                    with open(filepath, 'r') as data_file:
                                        results.append(json.load(data_file))
            else:
                # Get all files or filter by query
                pattern = "*.json"
                for filepath in self.storage_path.glob(pattern):
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        if query:
                            # Apply query filters
                            matches = True
                            for key, value in query.items():
                                if key in data and data[key] != value:
                                    matches = False
                                    break
                            if matches:
                                results.append(data)
                        else:
                            results.append(data)

            return results[0] if len(results) == 1 else results if results else None

        except Exception as e:
            self.logger.error(f"Error retrieving from warm storage: {e}")
            return None

    def clear(self) -> None:
        """Clear all data from warm memory."""
        try:
            # Remove all files in storage path
            for file in self.storage_path.glob("*"):
                if file.is_file():
                    file.unlink()
            # Remove tag directory
            tag_dir = self.storage_path / "tags"
            if tag_dir.exists():
                for file in tag_dir.glob("*"):
                    file.unlink()
                tag_dir.rmdir()
        except Exception as e:
            self.logger.error(f"Failed to clear warm memory: {e}")

    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            self.clear()
            if self.storage_path.exists():
                self.storage_path.rmdir()
        except Exception as e:
            self.logger.error(f"Failed to cleanup warm memory: {e}")

    def __del__(self):
        """Destructor to ensure cleanup is performed."""
        self.cleanup()

    async def get_schema(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get schema information for stored data.
        
        Args:
            filename: Name of the file to get schema for
            
        Returns:
            Dictionary containing schema information or None if not found
        """
        try:
            filepath = self.storage_path / filename
            if not filepath.exists():
                return None
                
            # Read JSON file
            with open(filepath, 'r') as f:
                stored_data = json.load(f)
                
            data_value = stored_data.get('data')
            
            if isinstance(data_value, dict):
                schema = {
                    'fields': list(data_value.keys()),
                    'types': {k: type(v).__name__ for k, v in data_value.items()},
                    'type': 'dict',
                    'source': 'json_file'
                }
            elif isinstance(data_value, list):
                if data_value:
                    if all(isinstance(x, dict) for x in data_value):
                        # List of dictionaries - combine all keys
                        all_keys = set().union(*(d.keys() for d in data_value))
                        schema = {
                            'fields': list(all_keys),
                            'types': {k: type(next(d[k] for d in data_value if k in d)).__name__ 
                                    for k in all_keys},
                            'type': 'list_of_dicts',
                            'source': 'json_file'
                        }
                    else:
                        schema = {
                            'type': 'list',
                            'element_type': type(data_value[0]).__name__,
                            'length': len(data_value),
                            'source': 'json_file'
                        }
                else:
                    schema = {
                        'type': 'list',
                        'length': 0,
                        'source': 'json_file'
                    }
            else:
                schema = {
                    'type': type(data_value).__name__,
                    'source': 'json_file'
                }
                
            # Add metadata if available
            if 'metadata' in stored_data:
                schema['metadata'] = stored_data['metadata']
                
            return schema
            
        except Exception as e:
            self.logger.error(f"Failed to get schema for {filename}: {e}")
            return None