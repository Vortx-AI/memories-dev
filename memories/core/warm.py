"""
Warm memory implementation using file-based storage.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import shutil

logger = logging.getLogger(__name__)

class WarmMemory:
    """Warm memory layer using file-based storage."""
    
    def __init__(self, storage_path: Path, max_size: int):
        """Initialize warm memory.
        
        Args:
            storage_path: Path to store data files
            max_size: Maximum number of items to store
        """
        self.storage_path = storage_path
        self.max_size = max_size
        
        # Create storage directory
        self.storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized warm memory at {storage_path}")
    
    def store(self, data: Dict[str, Any]) -> None:
        """Store data in a file.
        
        Args:
            data: Data to store
        """
        try:
            # Use timestamp as filename
            timestamp = data.get("timestamp", "")
            if not timestamp:
                logger.error("Data must have a timestamp")
                return
            
            filename = self.storage_path / f"{timestamp}.json"
            
            # Store as JSON
            with open(filename, "w") as f:
                json.dump(data, f, indent=2)
            
            # Maintain max size by removing oldest files
            files = list(self.storage_path.glob("*.json"))
            if len(files) > self.max_size:
                # Sort by modification time and remove oldest
                files.sort(key=lambda x: x.stat().st_mtime)
                for old_file in files[:-self.max_size]:
                    old_file.unlink()
        except Exception as e:
            logger.error(f"Failed to store data in file: {e}")
    
    def retrieve(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Retrieve data from files.
        
        Args:
            query: Query to match against stored data
            
        Returns:
            Retrieved data or None if not found
        """
        try:
            # Use timestamp as filename if provided
            if "timestamp" in query:
                filename = self.storage_path / f"{query['timestamp']}.json"
                if filename.exists():
                    with open(filename) as f:
                        return json.load(f)
            
            # Otherwise, search through all files
            for file in self.storage_path.glob("*.json"):
                with open(file) as f:
                    data = json.load(f)
                    # Check if all query items match
                    if all(data.get(k) == v for k, v in query.items()):
                        return data
            
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve data from file: {e}")
            return None
    
    def retrieve_all(self) -> List[Dict[str, Any]]:
        """Retrieve all data from files.
        
        Returns:
            List of all stored data
        """
        try:
            result = []
            for file in self.storage_path.glob("*.json"):
                with open(file) as f:
                    result.append(json.load(f))
            return result
        except Exception as e:
            logger.error(f"Failed to retrieve all data from files: {e}")
            return []
    
    def clear(self) -> None:
        """Clear all data files."""
        try:
            shutil.rmtree(self.storage_path)
            self.storage_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to clear files: {e}")
