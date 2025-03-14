"""
Google Cloud Storage connector for Glacier Memory.
"""

from typing import Any, Dict, Optional, Union
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
            
        # Initialize GCS client
        try:
            if 'credentials_path' in config:
                self.client = storage.Client.from_service_account_json(
                    config['credentials_path'],
                    project=self.project_id
                )
            else:
                self.client = storage.Client(project=self.project_id)
                
            self.bucket = self.client.bucket(self.bucket_name)
            if not self.bucket.exists():
                self.logger.info(f"Creating bucket {self.bucket_name}")
                self.bucket.create()
                
        except Exception as e:
            raise ConnectionError(f"Failed to initialize GCS client: {str(e)}")

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
            blobs = self.bucket.list_blobs()
            for blob in blobs:
                blob.delete()
        except Exception as e:
            self.logger.error(f"Failed to clear GCS bucket: {str(e)}")

    def cleanup(self) -> None:
        """Clean up resources."""
        # GCS client doesn't need explicit cleanup
        pass 