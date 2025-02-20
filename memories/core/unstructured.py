"""
Unstructured data storage implementation for the Memories system.
"""

import uuid
import zlib
import gzip
import json
import logging
from typing import Dict, Any, Optional, List, Generator, Union
from pathlib import Path
from datetime import datetime
import shutil
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)

class BinaryStorage:
    """Storage manager for binary data (images, videos, etc.)"""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path / "binary"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
    def store(self, data: bytes, metadata: Dict[str, Any]) -> str:
        """Store binary data with metadata"""
        try:
            # Generate unique ID
            file_id = str(uuid.uuid4())
            
            # Store compressed binary data
            file_path = self.storage_path / f"{file_id}.bin"
            with open(file_path, "wb") as f:
                f.write(zlib.compress(data))
                
            # Store metadata
            meta_path = self.storage_path / f"{file_id}.meta.json"
            with open(meta_path, "w") as f:
                json.dump(metadata, f)
                
            return file_id
        except Exception as e:
            logger.error(f"Failed to store binary data: {e}")
            raise

    def retrieve(self, file_id: str) -> Optional[tuple[bytes, Dict[str, Any]]]:
        """Retrieve binary data and metadata"""
        try:
            file_path = self.storage_path / f"{file_id}.bin"
            meta_path = self.storage_path / f"{file_id}.meta.json"
            
            if not file_path.exists() or not meta_path.exists():
                return None
                
            # Read binary data
            with open(file_path, "rb") as f:
                data = zlib.decompress(f.read())
                
            # Read metadata
            with open(meta_path) as f:
                metadata = json.load(f)
                
            return data, metadata
        except Exception as e:
            logger.error(f"Failed to retrieve binary data: {e}")
            return None

class TextStorage:
    """Storage manager for large text documents"""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path / "text"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
    def store(self, text: str, metadata: Dict[str, Any]) -> str:
        """Store text data with metadata"""
        try:
            file_id = str(uuid.uuid4())
            
            # Store compressed text
            file_path = self.storage_path / f"{file_id}.txt.gz"
            with gzip.open(file_path, "wt", encoding="utf-8") as f:
                f.write(text)
                
            # Store metadata
            meta_path = self.storage_path / f"{file_id}.meta.json"
            with open(meta_path, "w") as f:
                json.dump(metadata, f)
                
            return file_id
        except Exception as e:
            logger.error(f"Failed to store text data: {e}")
            raise

    def retrieve(self, file_id: str) -> Optional[tuple[str, Dict[str, Any]]]:
        """Retrieve text data and metadata"""
        try:
            file_path = self.storage_path / f"{file_id}.txt.gz"
            meta_path = self.storage_path / f"{file_id}.meta.json"
            
            if not file_path.exists() or not meta_path.exists():
                return None
                
            # Read text data
            with gzip.open(file_path, "rt", encoding="utf-8") as f:
                text = f.read()
                
            # Read metadata
            with open(meta_path) as f:
                metadata = json.load(f)
                
            return text, metadata
        except Exception as e:
            logger.error(f"Failed to retrieve text data: {e}")
            return None

class ModelStorage:
    """Storage manager for 3D models and point clouds"""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path / "models"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
    def store(self, model_data: bytes, format: str, metadata: Dict[str, Any]) -> str:
        """Store model data with metadata"""
        try:
            file_id = str(uuid.uuid4())
            
            # Store compressed model data
            file_path = self.storage_path / f"{file_id}.{format}.gz"
            with gzip.open(file_path, "wb") as f:
                f.write(model_data)
                
            # Store metadata
            meta_path = self.storage_path / f"{file_id}.meta.json"
            metadata["format"] = format
            with open(meta_path, "w") as f:
                json.dump(metadata, f)
                
            return file_id
        except Exception as e:
            logger.error(f"Failed to store model data: {e}")
            raise

    def retrieve(self, file_id: str) -> Optional[tuple[bytes, Dict[str, Any]]]:
        """Retrieve model data and metadata"""
        try:
            meta_path = self.storage_path / f"{file_id}.meta.json"
            
            # Read metadata first to get format
            if not meta_path.exists():
                return None
                
            with open(meta_path) as f:
                metadata = json.load(f)
                
            format = metadata.get("format")
            if not format:
                return None
                
            file_path = self.storage_path / f"{file_id}.{format}.gz"
            if not file_path.exists():
                return None
                
            # Read model data
            with gzip.open(file_path, "rb") as f:
                data = f.read()
                
            return data, metadata
        except Exception as e:
            logger.error(f"Failed to retrieve model data: {e}")
            return None

class ParquetStorage:
    """Storage manager for Parquet data"""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path / "parquet"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
    def store(self, data: Union[pd.DataFrame, pa.Table], metadata: Dict[str, Any]) -> str:
        """Store data in Parquet format with metadata"""
        try:
            # Generate unique ID
            file_id = str(uuid.uuid4())
            
            # Convert DataFrame to PyArrow Table if needed
            if isinstance(data, pd.DataFrame):
                table = pa.Table.from_pandas(data)
                metadata["original_type"] = "pandas"
            else:
                table = data
                metadata["original_type"] = "pyarrow"
            
            # Store Parquet file with compression
            file_path = self.storage_path / f"{file_id}.parquet"
            pq.write_table(
                table,
                file_path,
                compression='snappy',
                write_statistics=True
            )
            
            # Store metadata
            meta_path = self.storage_path / f"{file_id}.meta.json"
            metadata.update({
                "schema": table.schema.to_string(),
                "num_rows": table.num_rows,
                "num_columns": table.num_columns,
                "column_names": table.column_names
            })
            with open(meta_path, "w") as f:
                json.dump(metadata, f)
                
            return file_id
        except Exception as e:
            logger.error(f"Failed to store Parquet data: {e}")
            raise

    def retrieve(self, file_id: str) -> Optional[tuple[Union[pd.DataFrame, pa.Table], Dict[str, Any]]]:
        """Retrieve Parquet data and metadata"""
        try:
            file_path = self.storage_path / f"{file_id}.parquet"
            meta_path = self.storage_path / f"{file_id}.meta.json"
            
            if not file_path.exists() or not meta_path.exists():
                return None
                
            # Read metadata
            with open(meta_path) as f:
                metadata = json.load(f)
                
            # Read Parquet data
            table = pq.read_table(file_path)
            
            # Convert back to original type if needed
            if metadata.get("original_type") == "pandas":
                data = table.to_pandas()
            else:
                data = table
                
            return data, metadata
        except Exception as e:
            logger.error(f"Failed to retrieve Parquet data: {e}")
            return None

    def stream(self, file_id: str, batch_size: int = 1000) -> Generator[pd.DataFrame, None, None]:
        """Stream Parquet data in batches"""
        try:
            file_path = self.storage_path / f"{file_id}.parquet"
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            parquet_file = pq.ParquetFile(str(file_path))
            for batch in parquet_file.iter_batches(batch_size=batch_size):
                yield batch.to_pandas()
        except Exception as e:
            logger.error(f"Failed to stream Parquet data: {e}")
            raise

class UnstructuredStorage:
    """Unified storage manager for different types of unstructured data"""
    
    def __init__(self, storage_path: Path):
        """Initialize storage managers for different data types"""
        self.storage_path = storage_path
        self.binary_storage = BinaryStorage(storage_path)
        self.text_storage = TextStorage(storage_path)
        self.model_storage = ModelStorage(storage_path)
        self.parquet_storage = ParquetStorage(storage_path)
        
    def store(self, data: Union[bytes, str, pd.DataFrame, pa.Table], 
             data_type: str, metadata: Dict[str, Any]) -> str:
        """Store data of specified type with metadata"""
        if data_type == "binary":
            return self.binary_storage.store(data, metadata)
        elif data_type == "text":
            return self.text_storage.store(data, metadata)
        elif data_type == "model":
            if not isinstance(data, bytes):
                raise ValueError("Model data must be bytes")
            format = metadata.get("format", "obj")
            return self.model_storage.store(data, format, metadata)
        elif data_type == "parquet":
            return self.parquet_storage.store(data, metadata)
        else:
            raise ValueError(f"Unsupported data type: {data_type}")
            
    def retrieve(self, file_id: str, data_type: str) -> Optional[tuple[Any, Dict[str, Any]]]:
        """Retrieve data of specified type"""
        if data_type == "binary":
            return self.binary_storage.retrieve(file_id)
        elif data_type == "text":
            return self.text_storage.retrieve(file_id)
        elif data_type == "model":
            return self.model_storage.retrieve(file_id)
        elif data_type == "parquet":
            return self.parquet_storage.retrieve(file_id)
        else:
            raise ValueError(f"Unsupported data type: {data_type}")
            
    def store_version(self, parent_id: str, data: Any, metadata: Dict[str, Any]) -> str:
        """Store a new version of existing data"""
        # Get parent metadata to determine data type
        parent_result = None
        for data_type in ["binary", "text", "model", "parquet"]:
            try:
                parent_result = self.retrieve(parent_id, data_type)
                if parent_result is not None:
                    break
            except:
                continue
                
        if parent_result is None:
            raise ValueError(f"Parent file not found: {parent_id}")
            
        # Update version metadata
        _, parent_metadata = parent_result
        metadata.update({
            "parent_id": parent_id,
            "version": parent_metadata.get("version", 0) + 1,
            "previous_versions": parent_metadata.get("previous_versions", []) + [parent_id]
        })
        
        # Store new version
        return self.store(data, data_type, metadata)
        
    def stream(self, file_id: str, data_type: str, chunk_size: int = 8192) -> Generator[bytes, None, None]:
        """Stream data in chunks"""
        result = self.retrieve(file_id, data_type)
        if result is None:
            raise FileNotFoundError(f"File not found: {file_id}")
            
        data, _ = result
        if isinstance(data, (str, bytes)):
            data_bytes = data.encode() if isinstance(data, str) else data
            for i in range(0, len(data_bytes), chunk_size):
                yield data_bytes[i:i + chunk_size]
        else:
            raise ValueError(f"Streaming not supported for data type: {data_type}")

    def clear(self) -> None:
        """Clear all unstructured data"""
        try:
            shutil.rmtree(self.storage_path)
            self.storage_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to clear unstructured storage: {e}")
            raise 