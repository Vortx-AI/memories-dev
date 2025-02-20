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
            file_id = str(uuid.uuid4())
            
            # Convert DataFrame to PyArrow Table if needed
            if isinstance(data, pd.DataFrame):
                table = pa.Table.from_pandas(data)
            else:
                table = data
            
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

    def retrieve(self, file_id: str, columns: List[str] = None) -> Optional[tuple[Union[pd.DataFrame, pa.Table], Dict[str, Any]]]:
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
            if columns:
                table = pq.read_table(file_path, columns=columns)
            else:
                table = pq.read_table(file_path)
                
            # Convert to pandas if original data was DataFrame
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
            
            parquet_file = pq.ParquetFile(file_path)
            for batch in parquet_file.iter_batches(batch_size=batch_size):
                yield batch.to_pandas()
        except Exception as e:
            logger.error(f"Failed to stream Parquet data: {e}")
            raise

class UnstructuredStorage:
    """Main storage manager for all unstructured data types"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path / "unstructured"
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.binary_storage = BinaryStorage(self.base_path)
        self.text_storage = TextStorage(self.base_path)
        self.model_storage = ModelStorage(self.base_path)
        self.parquet_storage = ParquetStorage(self.base_path)
        
    def store(self, data: Any, data_type: str, metadata: Dict[str, Any]) -> str:
        """Store unstructured data of any supported type"""
        try:
            if data_type == "binary":
                return self.binary_storage.store(data, metadata)
            elif data_type == "text":
                return self.text_storage.store(data, metadata)
            elif data_type == "model":
                format = metadata.pop("format", "obj")  # Default to OBJ format
                return self.model_storage.store(data, format, metadata)
            elif data_type == "parquet":
                if isinstance(data, pd.DataFrame):
                    metadata["original_type"] = "pandas"
                elif isinstance(data, pa.Table):
                    metadata["original_type"] = "pyarrow"
                else:
                    raise ValueError("Parquet data must be DataFrame or PyArrow Table")
                return self.parquet_storage.store(data, metadata)
            else:
                raise ValueError(f"Unsupported data type: {data_type}")
        except Exception as e:
            logger.error(f"Failed to store unstructured data: {e}")
            raise

    def retrieve(self, file_id: str, data_type: str, **kwargs) -> Optional[tuple[Any, Dict[str, Any]]]:
        """Retrieve unstructured data of specified type"""
        try:
            if data_type == "binary":
                return self.binary_storage.retrieve(file_id)
            elif data_type == "text":
                return self.text_storage.retrieve(file_id)
            elif data_type == "model":
                return self.model_storage.retrieve(file_id)
            elif data_type == "parquet":
                columns = kwargs.get("columns")
                return self.parquet_storage.retrieve(file_id, columns)
            else:
                raise ValueError(f"Unsupported data type: {data_type}")
        except Exception as e:
            logger.error(f"Failed to retrieve unstructured data: {e}")
            return None

    def stream(self, file_id: str, data_type: str, **kwargs) -> Generator[Any, None, None]:
        """Stream unstructured data in chunks"""
        try:
            if data_type == "parquet":
                batch_size = kwargs.get("batch_size", 1000)
                yield from self.parquet_storage.stream(file_id, batch_size)
            else:
                chunk_size = kwargs.get("chunk_size", 8192)
                if data_type == "binary":
                    file_path = self.binary_storage.storage_path / f"{file_id}.bin"
                elif data_type == "text":
                    file_path = self.text_storage.storage_path / f"{file_id}.txt.gz"
                elif data_type == "model":
                    meta_path = self.model_storage.storage_path / f"{file_id}.meta.json"
                    with open(meta_path) as f:
                        format = json.load(f)["format"]
                    file_path = self.model_storage.storage_path / f"{file_id}.{format}.gz"
                else:
                    raise ValueError(f"Unsupported data type: {data_type}")

                if not file_path.exists():
                    raise FileNotFoundError(f"File not found: {file_path}")

                with open(file_path, "rb") as f:
                    while chunk := f.read(chunk_size):
                        yield chunk
        except Exception as e:
            logger.error(f"Failed to stream unstructured data: {e}")
            raise

    def store_version(self, file_id: str, new_data: Any, version_metadata: Dict[str, Any]) -> str:
        """Store a new version of existing unstructured data"""
        try:
            # Get original metadata and data type
            data_type = self._get_data_type(file_id)
            original_metadata = self._get_metadata(file_id)
            
            if not original_metadata:
                raise ValueError(f"Original file not found: {file_id}")
            
            # Update version information
            version_number = original_metadata.get("version", 0) + 1
            new_metadata = {
                **original_metadata,
                "version": version_number,
                "parent_id": file_id,
                **version_metadata,
                "created_at": datetime.now().isoformat()
            }
            
            # Store new version
            return self.store(new_data, data_type, new_metadata)
        except Exception as e:
            logger.error(f"Failed to store version: {e}")
            raise

    def _get_data_type(self, file_id: str) -> Optional[str]:
        """Determine data type from file ID"""
        if (self.binary_storage.storage_path / f"{file_id}.bin").exists():
            return "binary"
        elif (self.text_storage.storage_path / f"{file_id}.txt.gz").exists():
            return "text"
        elif any(p.name.startswith(file_id) for p in self.model_storage.storage_path.glob(f"{file_id}.*")):
            return "model"
        return None

    def _get_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for any data type"""
        try:
            data_type = self._get_data_type(file_id)
            if not data_type:
                return None
                
            meta_path = getattr(self, f"{data_type}_storage").storage_path / f"{file_id}.meta.json"
            if not meta_path.exists():
                return None
                
            with open(meta_path) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to get metadata: {e}")
            return None

    def clear(self) -> None:
        """Clear all unstructured data"""
        try:
            shutil.rmtree(self.base_path)
            self.base_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to clear unstructured storage: {e}")
            raise 