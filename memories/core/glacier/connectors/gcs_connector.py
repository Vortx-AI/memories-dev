"""
Google Cloud Storage connector for Glacier Memory.
"""

from typing import Any, Dict, Optional, Union, List, Tuple
from pathlib import Path
import logging
import json
import uuid
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
        # Ensure config is a dict
        if config is None:
            config = {}
            
        # Initialize parent with config
        super().__init__(config)
        
        # Get required configuration parameters
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

    def list_objects(self, prefix: str = "") -> List[Dict[str, Any]]:
        """List objects in the bucket.
        
        Args:
            prefix: Optional prefix to filter objects by
            
        Returns:
            List[Dict[str, Any]]: List of object metadata dictionaries
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
                    "key": blob.name,
                    "size": blob.size,
                    "updated": blob.updated.isoformat() if blob.updated else None,
                    "content_type": blob.content_type
                })
                result.append(metadata)
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error listing objects in GCS: {str(e)}")
            return []

    def store(self, data: Any, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store data in GCS bucket.
        
        Args:
            data: Data to store
            metadata: Optional metadata to store with the object
            
        Returns:
            str: Key for the stored data
        """
        try:
            if not self.bucket:
                self.connect()
            
            # Generate a key if not provided in metadata
            key = metadata.get("key") if metadata and "key" in metadata else f"data/{str(uuid.uuid4())}"
            
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
                # Filter out key from metadata if present
                metadata_to_store = {k: v for k, v in metadata.items() if k != "key"}
                blob.metadata = metadata_to_store
                blob.patch()
                
            return key
            
        except Exception as e:
            self.logger.error(f"Failed to store data in GCS: {str(e)}")
            raise

    def retrieve(self, key: str) -> Optional[Any]:
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
                
            # Get content type if available
            content_type = blob.content_type
            
            # Check if this is likely binary data based on the key or content type
            is_likely_binary = (
                key.endswith(('.pkl', '.bin', '.dat', '.model', '.gz', '.zip')) or
                (content_type and 'octet-stream' in content_type) or
                (content_type and 'application/x-pickle' in content_type)
            )
            
            # Download the data
            data = blob.download_as_bytes()
            
            # For binary files, just return the bytes without trying to decode
            if is_likely_binary:
                self.logger.info(f"Returning binary data for key: {key} (size: {len(data)} bytes)")
                return data
                
            # For other files, try to decode as JSON, fallback to string, then bytes
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                try:
                    return data.decode('utf-8')
                except UnicodeDecodeError:
                    # If decoding fails, return the raw bytes
                    self.logger.info(f"Could not decode data as UTF-8, returning as bytes")
                    return data
                    
        except NotFound:
            return None
        except Exception as e:
            self.logger.error(f"Failed to retrieve data from GCS: {str(e)}")
            return None

    async def store_async(self, data: Any, key: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Async version of store method for compatibility with async interfaces.
        
        Args:
            data: Data to store
            key: Key to store the data under
            metadata: Optional metadata to store with the object
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if metadata is None:
                metadata = {}
            
            # Add key to metadata
            metadata["key"] = key
            
            # Call the synchronous version
            self.store(data, metadata)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store data in GCS: {str(e)}")
            return False

    async def retrieve_async(self, key: str) -> Optional[Any]:
        """Async version of retrieve method for compatibility with async interfaces.
        
        Args:
            key: Key of the data to retrieve
            
        Returns:
            Optional[Any]: Retrieved data or None if not found
        """
        return self.retrieve(key)

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