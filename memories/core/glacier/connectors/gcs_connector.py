"""
Google Cloud Storage connector for Glacier Memory.
"""

from typing import Any, Dict, Optional, Union, List, Tuple
from pathlib import Path
import logging
import json
from google.cloud import storage
from google.cloud.exceptions import NotFound
from ..base import GlacierConnector

class GCSConnector(GlacierConnector):
    """Connector for Google Cloud Storage buckets."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the GCS connector.
        
        Args:
            config (Optional[Dict[str, Any]]): Configuration dictionary containing:
                - bucket_name: Name of the GCS bucket
                - project_id: Google Cloud project ID
                - credentials_path: Path to service account credentials JSON file (optional)
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        if not config:
            raise ValueError("Config is required for GCS connector")
            
        self.bucket_name = config.get('bucket_name')
        if not self.bucket_name:
            raise ValueError("bucket_name is required in config")
            
        self.project_id = config.get('project_id')
        if not self.project_id:
            raise ValueError("project_id is required in config")
            
        self.credentials_path = config.get('credentials_path')
        self.client = None
        self.bucket = None
        
        # Connect to GCS
        self.connect()

    def connect(self) -> bool:
        """Connect to Google Cloud Storage.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            # Initialize GCS client
            if self.credentials_path:
                self.client = storage.Client.from_service_account_json(
                    self.credentials_path,
                    project=self.project_id
                )
            else:
                self.client = storage.Client(project=self.project_id)
                
            self.bucket = self.client.bucket(self.bucket_name)
            if not self.bucket.exists():
                self.logger.info(f"Creating bucket {self.bucket_name}")
                self.bucket.create()
                
            self.logger.info(f"Successfully connected to GCS bucket: {self.bucket_name}")
            return True
                
        except Exception as e:
            self.logger.error(f"Failed to initialize GCS client: {str(e)}")
            raise ConnectionError(f"Failed to initialize GCS client: {str(e)}")

    async def list_objects(self, prefix: Optional[str] = None) -> List[Tuple[str, Dict[str, Any]]]:
        """List objects in the bucket.
        
        Args:
            prefix: Optional prefix to filter objects by
            
        Returns:
            List[Tuple[str, Dict[str, Any]]]: List of (key, metadata) tuples
        """
        try:
            if not self.bucket:
                self.connect()
                
            blobs = self.bucket.list_blobs(prefix=prefix)
            
            result = []
            for blob in blobs:
                metadata = blob.metadata or {}
                # Add standard metadata
                metadata.update({
                    "size": blob.size,
                    "updated": blob.updated.isoformat() if blob.updated else None,
                    "content_type": blob.content_type
                })
                result.append((blob.name, metadata))
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error listing objects in GCS: {str(e)}")
            return []

    async def store(self, data: Any, key: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Store data in GCS bucket.
        
        Args:
            data: Data to store
            key: Key to store the data under
            metadata: Optional metadata to store with the object
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.bucket:
                self.connect()
                
            blob = self.bucket.blob(key)
            
            # Convert data to bytes if it's not already
            if isinstance(data, (dict, list)):
                data = json.dumps(data).encode('utf-8')
            elif isinstance(data, str):
                data = data.encode('utf-8')
            elif not isinstance(data, bytes):
                raise ValueError(f"Unsupported data type: {type(data)}")
                
            # Upload the data
            blob.upload_from_string(data)
            
            # Set metadata if provided
            if metadata:
                blob.metadata = metadata
                blob.patch()
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store data in GCS: {str(e)}")
            return False

    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve data from GCS bucket.
        
        Args:
            key: Key of the data to retrieve
            
        Returns:
            Optional[Any]: Retrieved data or None if not found
        """
        try:
            if not self.bucket:
                self.connect()
                
            blob = self.bucket.blob(key)
            
            if not blob.exists():
                return None
                
            # Download the data
            data = blob.download_as_bytes()
            
            # Try to decode as JSON, fallback to string, then bytes
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                try:
                    return data.decode('utf-8')
                except UnicodeDecodeError:
                    return data
                    
        except NotFound:
            return None
        except Exception as e:
            self.logger.error(f"Failed to retrieve data from GCS: {str(e)}")
            return None

    async def delete(self, key: str) -> bool:
        """Delete data from GCS bucket.
        
        Args:
            key: Key of the data to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.bucket:
                self.connect()
                
            blob = self.bucket.blob(key)
            
            if not blob.exists():
                return False
                
            blob.delete()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete data from GCS: {str(e)}")
            return False

    async def clear(self) -> None:
        """Clear all objects from the bucket."""
        try:
            if not self.bucket:
                self.connect()
                
            blobs = self.bucket.list_blobs()
            for blob in blobs:
                blob.delete()
        except Exception as e:
            self.logger.error(f"Failed to clear GCS bucket: {str(e)}")

    def cleanup(self) -> None:
        """Clean up resources."""
        # GCS client doesn't need explicit cleanup
        self.client = None
        self.bucket = None 