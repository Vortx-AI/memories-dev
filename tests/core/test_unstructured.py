"""Tests for unstructured data storage functionality."""

import pytest
from pathlib import Path
import shutil
import json
from datetime import datetime
import pandas as pd
import numpy as np
import pyarrow as pa

from memories.core.unstructured import (
    BinaryStorage,
    TextStorage,
    ModelStorage,
    ParquetStorage,
    UnstructuredStorage
)

@pytest.fixture
def temp_storage_path(tmp_path):
    """Create a temporary storage path."""
    storage_path = tmp_path / "test_storage"
    storage_path.mkdir()
    yield storage_path
    shutil.rmtree(storage_path)

@pytest.fixture
def binary_storage(temp_storage_path):
    """Create a binary storage instance."""
    return BinaryStorage(temp_storage_path)

@pytest.fixture
def text_storage(temp_storage_path):
    """Create a text storage instance."""
    return TextStorage(temp_storage_path)

@pytest.fixture
def model_storage(temp_storage_path):
    """Create a model storage instance."""
    return ModelStorage(temp_storage_path)

@pytest.fixture
def unstructured_storage(temp_storage_path):
    """Create an unstructured storage instance."""
    return UnstructuredStorage(temp_storage_path)

@pytest.fixture
def parquet_storage(temp_storage_path):
    """Create a parquet storage instance."""
    return ParquetStorage(temp_storage_path)

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'id': range(100),
        'name': [f'item_{i}' for i in range(100)],
        'value': np.random.rand(100),
        'timestamp': pd.date_range('2024-01-01', periods=100)
    })

@pytest.fixture
def sample_pyarrow_table(sample_dataframe):
    """Create a sample PyArrow Table for testing."""
    return pa.Table.from_pandas(sample_dataframe)

def test_binary_storage(binary_storage):
    """Test binary data storage and retrieval."""
    # Test data
    binary_data = b"Hello, World!"
    metadata = {
        "filename": "test.bin",
        "size": len(binary_data),
        "created_at": datetime.now().isoformat()
    }
    
    # Store data
    file_id = binary_storage.store(binary_data, metadata)
    assert file_id is not None
    
    # Verify files exist
    assert (binary_storage.storage_path / f"{file_id}.bin").exists()
    assert (binary_storage.storage_path / f"{file_id}.meta.json").exists()
    
    # Retrieve data
    result = binary_storage.retrieve(file_id)
    assert result is not None
    
    retrieved_data, retrieved_metadata = result
    assert retrieved_data == binary_data
    assert retrieved_metadata == metadata

def test_text_storage(text_storage):
    """Test text data storage and retrieval."""
    # Test data
    text_data = "Hello, World!"
    metadata = {
        "filename": "test.txt",
        "length": len(text_data),
        "created_at": datetime.now().isoformat()
    }
    
    # Store data
    file_id = text_storage.store(text_data, metadata)
    assert file_id is not None
    
    # Verify files exist
    assert (text_storage.storage_path / f"{file_id}.txt.gz").exists()
    assert (text_storage.storage_path / f"{file_id}.meta.json").exists()
    
    # Retrieve data
    result = text_storage.retrieve(file_id)
    assert result is not None
    
    retrieved_text, retrieved_metadata = result
    assert retrieved_text == text_data
    assert retrieved_metadata == metadata

def test_model_storage(model_storage):
    """Test model data storage and retrieval."""
    # Test data
    model_data = b"fake model data"
    format = "obj"
    metadata = {
        "filename": "test.obj",
        "size": len(model_data),
        "created_at": datetime.now().isoformat()
    }
    
    # Store data
    file_id = model_storage.store(model_data, format, metadata)
    assert file_id is not None
    
    # Verify files exist
    assert (model_storage.storage_path / f"{file_id}.{format}.gz").exists()
    assert (model_storage.storage_path / f"{file_id}.meta.json").exists()
    
    # Retrieve data
    result = model_storage.retrieve(file_id)
    assert result is not None
    
    retrieved_data, retrieved_metadata = result
    assert retrieved_data == model_data
    assert retrieved_metadata["format"] == format
    assert "filename" in retrieved_metadata

def test_unstructured_storage(unstructured_storage):
    """Test unified unstructured storage."""
    # Test binary data
    binary_data = b"binary data"
    binary_metadata = {"type": "image/jpeg"}
    binary_id = unstructured_storage.store(binary_data, "binary", binary_metadata)
    
    # Test text data
    text_data = "text data"
    text_metadata = {"type": "text/plain"}
    text_id = unstructured_storage.store(text_data, "text", text_metadata)
    
    # Test model data
    model_data = b"model data"
    model_metadata = {"format": "obj", "type": "model/obj"}
    model_id = unstructured_storage.store(model_data, "model", model_metadata)
    
    # Test retrieval
    binary_result = unstructured_storage.retrieve(binary_id, "binary")
    assert binary_result is not None
    assert binary_result[0] == binary_data
    
    text_result = unstructured_storage.retrieve(text_id, "text")
    assert text_result is not None
    assert text_result[0] == text_data
    
    model_result = unstructured_storage.retrieve(model_id, "model")
    assert model_result is not None
    assert model_result[0] == model_data

def test_streaming(unstructured_storage):
    """Test streaming functionality."""
    # Create large test data
    large_data = b"x" * 1000000  # 1MB of data
    
    # Store data
    file_id = unstructured_storage.store(large_data, "binary", {"size": len(large_data)})
    
    # Stream data
    chunks = []
    for chunk in unstructured_storage.stream(file_id, "binary", chunk_size=8192):
        chunks.append(chunk)
    
    # Verify streamed data
    reassembled = b"".join(chunks)
    assert reassembled == large_data

def test_versioning(unstructured_storage):
    """Test versioning functionality."""
    # Store original version
    original_data = "version 1"
    original_metadata = {"version_desc": "initial version"}
    original_id = unstructured_storage.store(original_data, "text", original_metadata)
    
    # Store new version
    new_data = "version 2"
    version_metadata = {"version_desc": "updated version"}
    new_id = unstructured_storage.store_version(original_id, new_data, version_metadata)
    
    # Verify both versions
    original_result = unstructured_storage.retrieve(original_id, "text")
    assert original_result is not None
    assert original_result[0] == original_data
    
    new_result = unstructured_storage.retrieve(new_id, "text")
    assert new_result is not None
    assert new_result[0] == new_data
    assert new_result[1]["version"] == 1
    assert new_result[1]["parent_id"] == original_id

def test_error_handling(unstructured_storage):
    """Test error handling."""
    # Test invalid data type
    with pytest.raises(ValueError):
        unstructured_storage.store("data", "invalid_type", {})
    
    # Test invalid file ID
    assert unstructured_storage.retrieve("invalid_id", "binary") is None
    
    # Test missing metadata
    with pytest.raises(ValueError):
        unstructured_storage.store_version("invalid_id", "data", {})

def test_parquet_storage_dataframe(parquet_storage, sample_dataframe):
    """Test Parquet storage with pandas DataFrame."""
    metadata = {
        "description": "Test DataFrame",
        "created_at": datetime.now().isoformat()
    }
    
    # Store DataFrame
    file_id = parquet_storage.store(sample_dataframe, metadata)
    assert file_id is not None
    
    # Verify files exist
    assert (parquet_storage.storage_path / f"{file_id}.parquet").exists()
    assert (parquet_storage.storage_path / f"{file_id}.meta.json").exists()
    
    # Retrieve full data
    result = parquet_storage.retrieve(file_id)
    assert result is not None
    
    retrieved_data, retrieved_metadata = result
    pd.testing.assert_frame_equal(retrieved_data, sample_dataframe)
    assert retrieved_metadata["description"] == metadata["description"]
    assert retrieved_metadata["num_rows"] == len(sample_dataframe)
    assert retrieved_metadata["num_columns"] == len(sample_dataframe.columns)
    
    # Test column selection
    columns = ["id", "name"]
    result = parquet_storage.retrieve(file_id, columns=columns)
    assert result is not None
    
    retrieved_data, _ = result
    pd.testing.assert_frame_equal(retrieved_data, sample_dataframe[columns])

def test_parquet_storage_pyarrow(parquet_storage, sample_pyarrow_table):
    """Test Parquet storage with PyArrow Table."""
    metadata = {
        "description": "Test PyArrow Table",
        "created_at": datetime.now().isoformat()
    }
    
    # Store PyArrow Table
    file_id = parquet_storage.store(sample_pyarrow_table, metadata)
    assert file_id is not None
    
    # Retrieve data
    result = parquet_storage.retrieve(file_id)
    assert result is not None
    
    retrieved_data, retrieved_metadata = result
    assert isinstance(retrieved_data, pa.Table)
    assert retrieved_data.equals(sample_pyarrow_table)
    assert retrieved_metadata["original_type"] == "pyarrow"

def test_parquet_streaming(parquet_storage, sample_dataframe):
    """Test Parquet streaming functionality."""
    # Store large DataFrame
    file_id = parquet_storage.store(sample_dataframe, {"description": "Test streaming"})
    
    # Stream data in small batches
    chunks = list(parquet_storage.stream(file_id, batch_size=10))
    assert len(chunks) == 10  # 100 rows / 10 batch_size
    
    # Verify streamed data
    reassembled = pd.concat(chunks, ignore_index=True)
    pd.testing.assert_frame_equal(reassembled, sample_dataframe)

def test_unstructured_parquet_support():
    """Test Parquet file support in unstructured storage."""
    storage = UnstructuredStorage()
    
    # Create test data
    df = pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['a', 'b', 'c']
    })
    
    # Store data
    file_id = storage.store(df, "test_data")
    
    # Retrieve with column selection
    result = storage.retrieve(file_id, format="parquet", columns=["id", "name"])
    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ["id", "name"]
    
def test_parquet_error_handling():
    """Test error handling for Parquet operations."""
    storage = UnstructuredStorage()
    
    # Store invalid data
    with pytest.raises(Exception):
        storage.store("invalid_data", "test_invalid")
    
    # Try to retrieve non-existent file
    with pytest.raises(FileNotFoundError):
        storage.retrieve("non_existent", format="parquet") 