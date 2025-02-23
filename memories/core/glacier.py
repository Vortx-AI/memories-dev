"""
Glacier memory implementation using parquet files.
"""

import json
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime

logger = logging.getLogger(__name__)

class GlacierMemory:
    """Glacier memory layer using parquet files for long-term storage."""
    
    def __init__(self, storage_path: Path, max_size: int):
        """Initialize glacier memory.
        
        Args:
            storage_path: Path to store parquet files
            max_size: Maximum number of items to store
        """
        self.storage_path = storage_path
        self.max_size = max_size
        self.metadata_file = storage_path / "metadata.json"
        
        # Create storage directory
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Load or initialize metadata
        self.metadata = self._load_metadata()
        logger.info(f"Initialized glacier memory at {storage_path}")
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata from file or create new."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load metadata: {e}")
        return {}
    
    def _save_metadata(self):
        """Save metadata to file."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def store(self, data: Dict[str, Any]) -> None:
        """Store data in parquet format.
        
        Args:
            data: Data to store
        """
        try:
            # Use timestamp as key
            timestamp = data.get("timestamp", "")
            if not timestamp:
                logger.error("Data must have a timestamp")
                return
            
            # Convert dict to DataFrame
            df = pd.DataFrame([data])
            
            # Store as parquet with compression
            file_path = self.storage_path / f"{timestamp}.parquet"
            table = pa.Table.from_pandas(df)
            pq.write_table(table, str(file_path), compression='ZSTD', compression_level=9)
            
            # Update metadata
            self.metadata[timestamp] = {
                "file_path": str(file_path),
                "created_at": datetime.now().isoformat(),
                "size_bytes": file_path.stat().st_size
            }
            self._save_metadata()
            
            # Maintain max size by removing oldest files
            if len(self.metadata) > self.max_size:
                # Sort by creation time and remove oldest
                sorted_items = sorted(self.metadata.items(), 
                                   key=lambda x: x[1]['created_at'])
                for timestamp, meta in sorted_items[:-self.max_size]:
                    file_path = Path(meta['file_path'])
                    if file_path.exists():
                        file_path.unlink()
                    del self.metadata[timestamp]
                self._save_metadata()
                
        except Exception as e:
            logger.error(f"Failed to store data in parquet: {e}")
    
    def retrieve(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Retrieve data from parquet files.
        
        Args:
            query: Query to match against stored data
            
        Returns:
            Retrieved data or None if not found
        """
        try:
            # Use timestamp for direct lookup if provided
            if "timestamp" in query:
                timestamp = query["timestamp"]
                if timestamp in self.metadata:
                    file_path = Path(self.metadata[timestamp]['file_path'])
                    if file_path.exists():
                        df = pd.read_parquet(file_path)
                        if not df.empty:
                            return df.iloc[0].to_dict()
            
            # Otherwise, search through all files
            for timestamp, meta in self.metadata.items():
                file_path = Path(meta['file_path'])
                if file_path.exists():
                    df = pd.read_parquet(file_path)
                    if not df.empty:
                        row = df.iloc[0]
                        if all(row.get(k) == v for k, v in query.items()):
                            return row.to_dict()
            
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve data from parquet: {e}")
            return None
    
    def retrieve_all(self) -> List[Dict[str, Any]]:
        """Retrieve all data from parquet files.
        
        Returns:
            List of all stored data
        """
        try:
            result = []
            for meta in self.metadata.values():
                file_path = Path(meta['file_path'])
                if file_path.exists():
                    df = pd.read_parquet(file_path)
                    if not df.empty:
                        result.append(df.iloc[0].to_dict())
            return result
        except Exception as e:
            logger.error(f"Failed to retrieve all data from parquet: {e}")
            return []
    
    def clear(self) -> None:
        """Clear all parquet files and metadata."""
        try:
            # Remove all parquet files
            for meta in self.metadata.values():
                file_path = Path(meta['file_path'])
                if file_path.exists():
                    file_path.unlink()
            
            # Clear metadata
            self.metadata = {}
            self._save_metadata()
        except Exception as e:
            logger.error(f"Failed to clear glacier storage: {e}")
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        try:
            total_size = sum(meta['size_bytes'] for meta in self.metadata.values())
            return {
                'total_files': len(self.metadata),
                'total_size_bytes': total_size,
                'oldest_file': min((meta['created_at'] for meta in self.metadata.values()), 
                                 default=None),
                'newest_file': max((meta['created_at'] for meta in self.metadata.values()),
                                 default=None)
            }
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {}
