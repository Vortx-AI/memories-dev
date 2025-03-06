#!/usr/bin/env python3

import os
import pytest
from pathlib import Path
import duckdb
from dotenv import load_dotenv
from memories.core.memory_manager import MemoryManager
from memories.core.memory_retrieval import MemoryRetrieval
from memories.core.cold import ColdMemory
import shutil
import pandas as pd
import yaml
from unittest.mock import patch, MagicMock
import numpy as np

# Load environment variables from .env file
load_dotenv()

# Get geo_memories path from environment variable
GEO_MEMORIES_PATH = Path(os.getenv('GEO_MEMORIES_PATH', ''))

def list_cold_tables():
    """List all tables in cold memory directly without pytest."""
    print(f"\n=== Listing Tables in Cold Memory ===\n")
    
    try:
        # Use existing storage directory
        storage_dir = Path('data')
        if not storage_dir.exists():
            print("No existing storage directory found. Please run the import first.")
            return
            
        cold_dir = storage_dir / 'cold'
        if not cold_dir.exists():
            print("No existing cold storage directory found. Please run the import first.")
            return
            
        # Use existing database file
        db_path = cold_dir / 'cold.db'
        if not db_path.exists():
            print("No existing database file found. Please run the import first.")
            return
            
        print("Connecting to existing DuckDB database...")
        db_conn = duckdb.connect(str(db_path))
        
        # Initialize memory manager with existing connection
        memory_manager = MemoryManager()
        
        # Configure the manager
        memory_manager.config = {
            'memory': {
                'base_path': storage_dir,
                'cold': {
                    'max_size': int(os.getenv('COLD_STORAGE_MAX_SIZE', 10737418240)),
                    'path': cold_dir,
                    'duckdb': {
                        'db_conn': db_conn,
                        'enable_external_access': True
                    }
                }
            }
        }
        
        # Initialize memory retrieval
        memory_retrieval = MemoryRetrieval(memory_manager.cold)
        
        # List all tables
        print("\nListing available tables:")
        tables = memory_retrieval.list_available_data()
        
        if not tables:
            print("No tables found in cold memory")
        else:
            print(f"\nFound {len(tables)} tables:")
            for table in tables:
                print(f"\nTable: {table['table_name']}")
                print(f"Theme: {table.get('theme', 'N/A')}")
                print(f"Tag: {table.get('tag', 'N/A')}")
                print(f"Rows: {table['num_rows']}")
                print(f"Columns: {table['num_columns']}")
                print("Schema:")
                for col_name, col_type in table['schema'].items():
                    print(f"  - {col_name}: {col_type}")
                
                # Show preview of data
                print("\nData Preview:")
                preview = memory_retrieval.preview_data(table['table_name'], limit=3)
                if not preview.empty:
                    print(preview.to_string())
                else:
                    print("No preview data available")
                print("-" * 80)
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        raise
    
    finally:
        print("\nCleaning up...")
        if 'db_conn' in locals():
            db_conn.close()
        if 'memory_manager' in locals():
            memory_manager.cleanup()

@pytest.fixture
def mock_sentence_transformer():
    """Mock sentence transformer to avoid network calls."""
    with patch('sentence_transformers.SentenceTransformer') as mock:
        model = MagicMock()
        model.encode.return_value = np.random.rand(384)  # Random embeddings
        mock.return_value = model
        yield mock

@pytest.fixture
def memory_manager(tmp_path, mock_sentence_transformer):
    """Create a memory manager instance for testing."""
    config = {
        'cold': {
            'path': tmp_path / 'cold',
            'max_size': 1024 * 1024 * 1024  # 1GB
        }
    }
    manager = MemoryManager(config=config)
    yield manager
    
    # Cleanup
    if (tmp_path / 'cold').exists():
        for file in (tmp_path / 'cold').glob('*'):
            file.unlink()
        (tmp_path / 'cold').rmdir()

@pytest.fixture
def memory_retrieval(memory_manager, mock_sentence_transformer):
    """Create a memory retrieval instance for testing."""
    return MemoryRetrieval(memory_manager)

def test_query_files(memory_manager, tmp_path):
    """Test querying parquet files."""
    # Create test data
    df = pd.DataFrame({
        'id': range(10),
        'value': np.random.rand(10)
    })
    
    # Save as parquet
    parquet_dir = tmp_path / "test_data"
    parquet_dir.mkdir()
    df.to_parquet(parquet_dir / "test.parquet")
    
    # Import into cold storage
    memory_manager.cold.batch_import_parquet(parquet_dir)
    
    # Create retrieval instance
    retrieval = MemoryRetrieval(memory_manager)
    
    # Test simple query
    result = retrieval.query_files("SELECT * FROM test")
    assert len(result) == 10
    assert 'id' in result.columns
    assert 'value' in result.columns

def test_get_similar_vectors(memory_manager):
    """Test vector similarity search."""
    # Create test vectors
    query_vector = np.random.rand(384)
    
    # Create retrieval instance
    retrieval = MemoryRetrieval(memory_manager)
    
    # Test similarity search
    results = retrieval.get_similar_vectors(query_vector, k=5)
    assert isinstance(results, list)

def test_get_similar_words(memory_manager):
    """Test word similarity search."""
    # Create retrieval instance
    retrieval = MemoryRetrieval(memory_manager)
    
    # Test word similarity search
    results = retrieval.get_similar_words("test", k=5)
    assert isinstance(results, list)

def test_get_storage_stats(memory_manager, tmp_path):
    """Test getting storage statistics."""
    # Create test data
    df = pd.DataFrame({
        'id': range(10),
        'value': np.random.rand(10)
    })
    
    # Save as parquet
    parquet_dir = tmp_path / "test_data"
    parquet_dir.mkdir()
    df.to_parquet(parquet_dir / "test.parquet")
    
    # Import into cold storage
    memory_manager.cold.batch_import_parquet(parquet_dir)
    
    # Create retrieval instance
    retrieval = MemoryRetrieval(memory_manager)
    
    # Test getting stats
    stats = retrieval.get_storage_stats()
    assert isinstance(stats, dict)
    assert stats['total_files'] > 0
    assert stats['total_rows'] > 0
    assert stats['total_columns'] > 0

def test_list_registered_files(memory_manager, tmp_path):
    """Test listing registered files."""
    # Create test data
    df = pd.DataFrame({
        'id': range(10),
        'value': np.random.rand(10)
    })
    
    # Save as parquet
    parquet_dir = tmp_path / "test_data"
    parquet_dir.mkdir()
    df.to_parquet(parquet_dir / "test.parquet")
    
    # Import into cold storage
    memory_manager.cold.batch_import_parquet(parquet_dir)
    
    # Create retrieval instance
    retrieval = MemoryRetrieval(memory_manager)
    
    # Test listing files
    files = retrieval.list_registered_files()
    assert isinstance(files, list)
    assert len(files) > 0
    assert 'file_path' in files[0]
    assert 'table_name' in files[0]

def main():
    """List tables in cold memory."""
    print("\n=== Listing Tables in Cold Memory ===\n")
    
    storage_dir = Path('data')
    if not storage_dir.exists():
        print("No existing storage directory found. Please run the import first.")
        return
        
    try:
        # Create and configure DuckDB connection
        db_path = storage_dir / 'cold' / 'cold.db'
        if not db_path.exists():
            print("No existing database found. Please run the import first.")
            return
            
        # Create connection with external access enabled
        db_conn = duckdb.connect(str(db_path), config={'enable_external_access': True})
        db_conn.execute("SET memory_limit='8GB'")
        db_conn.execute("SET threads=4")
        
        # Initialize memory manager
        memory_manager = MemoryManager()
        
        # Configure the manager
        memory_manager.config = {
            'memory': {
                'base_path': storage_dir,
                'cold': {
                    'max_size': int(os.getenv('COLD_STORAGE_MAX_SIZE', 10737418240)),
                    'duckdb': {
                        'db_conn': db_conn,
                        'config': {
                            'enable_external_access': True
                        }
                    }
                }
            }
        }
        
        # List available tables
        tables = memory_manager.cold.list_tables()
        
        if not tables:
            print("No tables found in cold memory.")
            return
            
        print(f"Found {len(tables)} tables:\n")
        for table in tables:
            print(f"Table: {table['table_name']}")
            print(f"File: {table['file_path']}")
            print(f"Theme: {table['theme']}")
            print(f"Tag: {table['tag']}")
            print(f"Rows: {table['num_rows']}")
            print(f"Columns: {table['num_columns']}")
            print("\nSchema:")
            for col_name, col_type in table['schema'].items():
                print(f"  {col_name}: {col_type}")
            print("\n" + "-"*50 + "\n")
            
    except Exception as e:
        print(f"\nError listing tables: {str(e)}")
        raise

if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        # Run pytest if --test flag is provided
        pytest.main([__file__, "-v"])
    else:
        # Run direct table listing
        main() 