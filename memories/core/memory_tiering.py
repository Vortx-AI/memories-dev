"""Memory tiering functionality for moving data between different memory tiers.

This module provides functionality for managing data movement between memory tiers,
such as promoting data from colder tiers (Glacier) to warmer tiers (Cold, Warm, Hot, Red Hot)
or demoting data from warmer tiers to colder tiers based on access patterns and other policies.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List, Union, Tuple
import pandas as pd
import numpy as np
import uuid
from pathlib import Path
import json
import time
from datetime import datetime, timedelta

# Lazy imports to avoid circular dependencies
from memories.core.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

class MemoryTiering:
    """Handles operations for moving data between different memory tiers."""
    
    def __init__(self):
        """Initialize the MemoryTiering with connections to all memory tiers."""
        self.memory_manager = MemoryManager()
        self.red_hot = None
        self.hot = None
        self.warm = None
        self.cold = None
        self.glacier = None
        
    async def initialize_tiers(self):
        """Initialize connections to all memory tiers."""
        # Only initialize the tiers when they're needed
        if not self.red_hot:
            from memories.core.red_hot import RedHotMemory
            self.red_hot = RedHotMemory()
            
        if not self.hot:
            from memories.core.hot import HotMemory
            # HotMemory has a simple constructor, not a class method 'create'
            self.hot = HotMemory()
            
        if not self.warm:
            from memories.core.warm import WarmMemory
            self.warm = WarmMemory()
            
        if not self.cold:
            from memories.core.cold import ColdMemory
            self.cold = ColdMemory()
            
        if not self.glacier:
            from memories.core.glacier import GlacierMemory
            # Load GCS config from environment variables
            import os
            from dotenv import load_dotenv
            load_dotenv()
            
            config = {
                'storage': {
                    'type': 'gcs',
                    'config': {
                        'bucket_name': os.getenv('GCP_BUCKET_NAME', 'glacier_tier'),
                        'project_id': os.getenv('GCP_PROJECT_ID'),
                        'credentials_path': os.getenv('GCP_CREDENTIALS_PATH')
                    }
                }
            }
            self.glacier = GlacierMemory(config)
    
    async def glacier_to_cold(self, key: str, destination_path: Optional[str] = None) -> bool:
        """Move data from Glacier storage to Cold storage.
        
        Args:
            key: The key identifying the data in Glacier storage
            destination_path: Optional path where to store the data in Cold storage.
                If not provided, will use the key as the path.
                
        Returns:
            bool: True if successful, False otherwise
        """
        await self.initialize_tiers()
        
        try:
            # Retrieve data from Glacier storage
            logger.info(f"Retrieving data from Glacier storage with key: {key}")
            data = await self.glacier.retrieve_stored(key)
            
            if data is None:
                logger.error(f"Data with key {key} not found in Glacier storage")
                return False
                
            # Determine destination path in Cold storage
            if destination_path is None:
                # Use the key as the path, but ensure it doesn't have invalid characters
                destination_path = key.replace('/', '_').replace('\\', '_')
            
            # Prepare metadata for Cold storage
            metadata = {
                "id": str(uuid.uuid4()),
                "original_source": "glacier",
                "original_key": key,
                "transfer_date": datetime.now().isoformat(),
                "content_type": "application/octet-stream"  # Default, will be overridden if identifiable
            }
            
            success = False
            
            # If it's a DataFrame, store directly
            if isinstance(data, pd.DataFrame):
                logger.info(f"Storing DataFrame in Cold storage at {destination_path}")
                # Check if store is async
                if asyncio.iscoroutinefunction(self.cold.store):
                    success = await self.cold.store(data, metadata)
                else:
                    success = self.cold.store(data, metadata)
                
            # If it's a dictionary or list, store as JSON
            elif isinstance(data, (dict, list)):
                metadata["content_type"] = "application/json"
                logger.info(f"Storing JSON data in Cold storage at {destination_path}")
                
                # Convert to DataFrame if possible
                try:
                    df = pd.DataFrame(data)
                    # Check if store is async
                    if asyncio.iscoroutinefunction(self.cold.store):
                        success = await self.cold.store(df, metadata)
                    else:
                        success = self.cold.store(df, metadata)
                except (ValueError, TypeError):
                    # Create a simple DataFrame with the JSON data in a single column
                    df = pd.DataFrame({'data': [json.dumps(data)]})
                    logger.info("Converted JSON to single-column DataFrame for Cold storage")
                    
                    # Check if store is async
                    if asyncio.iscoroutinefunction(self.cold.store):
                        success = await self.cold.store(df, metadata)
                    else:
                        success = self.cold.store(df, metadata)
                    
            # If it's bytes, handle differently based on type
            elif isinstance(data, bytes):
                # Try to decode as JSON
                try:
                    json_data = json.loads(data.decode('utf-8'))
                    metadata["content_type"] = "application/json"
                    logger.info(f"Storing decoded JSON data in Cold storage at {destination_path}")
                    
                    # Try to convert to DataFrame
                    try:
                        df = pd.DataFrame(json_data)
                        # Check if store is async
                        if asyncio.iscoroutinefunction(self.cold.store):
                            success = await self.cold.store(df, metadata)
                        else:
                            success = self.cold.store(df, metadata)
                    except (ValueError, TypeError):
                        # Create a simple DataFrame with the JSON data in a single column
                        df = pd.DataFrame({'data': [json.dumps(json_data)]})
                        logger.info("Converted JSON to single-column DataFrame for Cold storage")
                        
                        # Check if store is async
                        if asyncio.iscoroutinefunction(self.cold.store):
                            success = await self.cold.store(df, metadata)
                        else:
                            success = self.cold.store(df, metadata)
                except:
                    # For binary data, encode as base64 and store in a DataFrame
                    import base64
                    logger.info(f"Storing binary data in Cold storage at {destination_path} (as base64)")
                    
                    # Create a DataFrame with the base64-encoded data
                    encoded_data = base64.b64encode(data).decode('ascii')
                    df = pd.DataFrame({
                        'data': [encoded_data],
                        'encoding': ['base64'],
                        'original_size': [len(data)],
                        'filename': [key.split('/')[-1]]
                    })
                    
                    # Update metadata
                    metadata["content_type"] = "application/octet-stream"
                    metadata["encoding"] = "base64"
                    metadata["original_size"] = len(data)
                    
                    # Check if store is async
                    if asyncio.iscoroutinefunction(self.cold.store):
                        success = await self.cold.store(df, metadata)
                    else:
                        success = self.cold.store(df, metadata)
            
            # For all other data types, create a DataFrame with string representation
            else:
                logger.info(f"Storing data (type: {type(data)}) in Cold storage at {destination_path}")
                # Convert to string and store in DataFrame
                str_data = str(data)
                df = pd.DataFrame({'data': [str_data], 'type': [str(type(data))]})
                
                # Check if store is async
                if asyncio.iscoroutinefunction(self.cold.store):
                    success = await self.cold.store(df, metadata)
                else:
                    success = self.cold.store(df, metadata)
                
            if success:
                logger.info(f"Successfully moved data from Glacier to Cold storage at {destination_path}")
                # Optionally, delete from Glacier after successful transfer
                # await self.glacier.delete_stored(key)
                return True
            else:
                logger.error(f"Failed to store data in Cold storage")
                return False
                
        except Exception as e:
            logger.error(f"Error moving data from Glacier to Cold: {str(e)}")
            return False
    
    async def cold_to_warm(self, path: str, table_name: str) -> bool:
        """Move data from Cold storage to Warm storage (SQLite).
        
        Args:
            path: The path identifying the data in Cold storage
            table_name: The name of the table to create in Warm storage
                
        Returns:
            bool: True if successful, False otherwise
        """
        await self.initialize_tiers()
        
        try:
            # Retrieve data from Cold storage - Cold.retrieve might be async but we need to check implementation
            logger.info(f"Retrieving data from Cold storage with path: {path}")
            # Check if retrieve is sync or async and call accordingly
            if hasattr(self.cold, 'retrieve') and callable(self.cold.retrieve):
                if asyncio.iscoroutinefunction(self.cold.retrieve):
                    data = await self.cold.retrieve(path)
                else:
                    data = self.cold.retrieve(path)
            else:
                logger.error("ColdMemory has no retrieve method")
                return False
            
            if data is None:
                logger.error(f"Data with path {path} not found in Cold storage")
                return False
            
            # Convert to DataFrame if not already
            if not isinstance(data, pd.DataFrame):
                try:
                    data = pd.DataFrame(data)
                except (ValueError, TypeError):
                    logger.error(f"Could not convert data to DataFrame for Warm storage")
                    return False
            
            # Store in Warm storage - WarmMemory.store is async
            logger.info(f"Storing data in Warm storage as table: {table_name}")
            success = await self.warm.store(data, table_name)
            
            if success:
                logger.info(f"Successfully moved data from Cold to Warm storage as table {table_name}")
                return True
            else:
                logger.error(f"Failed to store data in Warm storage")
                return False
                
        except Exception as e:
            logger.error(f"Error moving data from Cold to Warm: {str(e)}")
            return False
    
    async def warm_to_hot(self, table_name: str, hot_key: Optional[str] = None) -> bool:
        """Move data from Warm storage to Hot storage (in-memory).
        
        Args:
            table_name: The name of the table in Warm storage
            hot_key: Optional key to use in Hot storage. If not provided,
                will use the table_name as the key.
                
        Returns:
            bool: True if successful, False otherwise
        """
        await self.initialize_tiers()
        
        try:
            # Retrieve data from Warm storage
            logger.info(f"Retrieving data from Warm storage with table: {table_name}")
            data = await self.warm.retrieve(table_name)
            
            if data is None:
                logger.error(f"Table {table_name} not found in Warm storage")
                return False
            
            # Use table_name as hot_key if not provided
            if hot_key is None:
                hot_key = table_name
            
            # Store in Hot storage - HotMemory.store is async
            logger.info(f"Storing data in Hot storage with key: {hot_key}")
            success = await self.hot.store(data, hot_key)
            
            if success:
                logger.info(f"Successfully moved data from Warm to Hot storage with key {hot_key}")
                return True
            else:
                logger.error(f"Failed to store data in Hot storage")
                return False
                
        except Exception as e:
            logger.error(f"Error moving data from Warm to Hot: {str(e)}")
            return False
    
    async def hot_to_red_hot(self, hot_key: str, red_hot_key: Optional[str] = None) -> bool:
        """Move data from Hot storage to Red Hot storage (GPU memory if available).
        
        Args:
            hot_key: The key identifying the data in Hot storage
            red_hot_key: Optional key to use in Red Hot storage. If not provided,
                will use the hot_key as the key.
                
        Returns:
            bool: True if successful, False otherwise
        """
        await self.initialize_tiers()
        
        try:
            # Check if Red Hot memory is available (requires GPU)
            if not self.red_hot.is_available():
                logger.warning("Red Hot memory is not available (GPU required)")
                return False
            
            # Retrieve data from Hot storage - HotMemory.retrieve is async
            logger.info(f"Retrieving data from Hot storage with key: {hot_key}")
            data = await self.hot.retrieve(hot_key)
            
            if data is None:
                logger.error(f"Data with key {hot_key} not found in Hot storage")
                return False
            
            # Use hot_key as red_hot_key if not provided
            if red_hot_key is None:
                red_hot_key = hot_key
            
            # Store in Red Hot storage
            logger.info(f"Storing data in Red Hot storage with key: {red_hot_key}")
            success = self.red_hot.store(data, red_hot_key)
            
            if success:
                logger.info(f"Successfully moved data from Hot to Red Hot storage with key {red_hot_key}")
                return True
            else:
                logger.error(f"Failed to store data in Red Hot storage")
                return False
                
        except Exception as e:
            logger.error(f"Error moving data from Hot to Red Hot: {str(e)}")
            return False
    
    async def promote_to_tier(self, data_key: str, source_tier: str, target_tier: str, 
                         new_key: Optional[str] = None) -> bool:
        """Generic method to promote data from a colder tier to a warmer tier.
        
        Args:
            data_key: The key identifying the data in the source tier
            source_tier: The source tier ('glacier', 'cold', 'warm', 'hot')
            target_tier: The target tier ('cold', 'warm', 'hot', 'red_hot')
            new_key: Optional new key to use in the target tier
                
        Returns:
            bool: True if successful, False otherwise
        """
        # Validate tier names
        valid_tiers = ['glacier', 'cold', 'warm', 'hot', 'red_hot']
        if source_tier not in valid_tiers:
            logger.error(f"Invalid source tier: {source_tier}")
            return False
        if target_tier not in valid_tiers:
            logger.error(f"Invalid target tier: {target_tier}")
            return False
            
        # Check that we're moving to a warmer tier
        source_index = valid_tiers.index(source_tier)
        target_index = valid_tiers.index(target_tier)
        if target_index <= source_index:
            logger.error(f"Target tier {target_tier} is not warmer than source tier {source_tier}")
            return False
        
        # Call the appropriate method based on the tiers
        if source_tier == 'glacier' and target_tier == 'cold':
            return await self.glacier_to_cold(data_key, new_key)
        elif source_tier == 'cold' and target_tier == 'warm':
            return await self.cold_to_warm(data_key, new_key or data_key)
        elif source_tier == 'warm' and target_tier == 'hot':
            return await self.warm_to_hot(data_key, new_key)
        elif source_tier == 'hot' and target_tier == 'red_hot':
            return await self.hot_to_red_hot(data_key, new_key)
        else:
            # For tiers that are not adjacent, we need to move through intermediate tiers
            logger.warning(f"Moving from {source_tier} to {target_tier} requires intermediate steps")
            # Implementation for multi-step promotion would go here
            return False 
    
    async def glacier_to_cold_file(self, key: str, destination_filename: Optional[str] = None) -> Tuple[bool, str]:
        """Move data from Glacier storage to Cold storage as a file.
        
        This method retrieves data from Glacier storage and stores it directly as a file
        in the Cold storage location, rather than in the DuckDB database.
        
        Args:
            key: The key identifying the data in Glacier storage
            destination_filename: Optional filename to use when storing in Cold storage.
                If not provided, will use the key's filename component.
                
        Returns:
            Tuple[bool, str]: (Success flag, full file path if successful)
        """
        await self.initialize_tiers()
        
        try:
            # Retrieve data from Glacier storage
            logger.info(f"Retrieving data from Glacier storage with key: {key}")
            data = await self.glacier.retrieve_stored(key)
            
            if data is None:
                logger.error(f"Data with key {key} not found in Glacier storage")
                return False, ""
            
            # Determine filename
            if destination_filename is None:
                # Use the last part of the key as the filename
                destination_filename = key.split('/')[-1]
            
            # Prepare metadata for Cold storage
            metadata = {
                "original_source": "glacier",
                "original_key": key,
                "transfer_date": datetime.now().isoformat(),
            }
            
            # Add file extension based analysis if possible
            if '.' in destination_filename:
                extension = destination_filename.split('.')[-1].lower()
                if extension in ['json', 'csv', 'parquet', 'pkl', 'pickle']:
                    metadata["file_type"] = extension
            
            # Convert data to bytes if it's not already
            if not isinstance(data, bytes):
                if isinstance(data, pd.DataFrame):
                    # Convert DataFrame to pickle bytes
                    import pickle
                    data = pickle.dumps(data)
                    metadata["content_type"] = "application/python-pickle"
                    metadata["data_type"] = "dataframe"
                    if not destination_filename.endswith('.pkl'):
                        destination_filename += '.pkl'
                elif isinstance(data, (dict, list)):
                    # Convert dict/list to JSON bytes
                    data = json.dumps(data).encode('utf-8')
                    metadata["content_type"] = "application/json"
                    if not destination_filename.endswith('.json'):
                        destination_filename += '.json'
                else:
                    # Convert to string then bytes as last resort
                    data = str(data).encode('utf-8')
                    metadata["content_type"] = "text/plain"
                    if not '.' in destination_filename:
                        destination_filename += '.txt'
            
            # Add tags
            tags = ["glacier_transfer", f"source:{key}"]
            
            # Store as file in Cold storage
            logger.info(f"Storing data as file in Cold storage: {destination_filename}")
            success, file_path = self.cold.store_file(
                data=data,
                filename=destination_filename,
                metadata=metadata,
                tags=tags
            )
            
            if success:
                logger.info(f"Successfully moved data from Glacier to Cold storage as file: {file_path}")
                # Optionally, delete from Glacier after successful transfer
                # await self.glacier.delete_stored(key)
                return True, file_path
            else:
                logger.error(f"Failed to store data as file in Cold storage")
                return False, ""
                
        except Exception as e:
            logger.error(f"Error moving data from Glacier to Cold as file: {str(e)}")
            return False, "" 