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
import logging
from datetime import datetime

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
def memory_manager(tmp_path):
    """Create a memory manager instance for testing."""
    config = {
        'memory': {
            'base_path': str(tmp_path),
            'red_hot': {
                'path': str(tmp_path / 'red_hot'),
                'max_size': 1000000,  # 1M vectors
                'vector_dim': 384,    # Default for all-MiniLM-L6-v2
                'gpu_id': 0,
                'force_cpu': True,    # Default to CPU for stability
                'index_type': 'Flat'  # Simple Flat index
            },
            'hot': {
                'path': str(tmp_path / 'hot'),
                'max_size': 104857600,  # 100MB
                'redis_url': 'redis://localhost:6379',
                'redis_db': 0
            },
            'cold': {
                'path': str(tmp_path / 'cold'),
                'max_size': 10737418240,  # 10GB
                'duckdb': {
                    'memory_limit': '4GB',
                    'threads': 4,
                    'config': {
                        'enable_progress_bar': True,
                        'enable_object_cache': True
                    }
                }
            }
        }
    }
    manager = MemoryManager(config=config)
    yield manager
    
    # Cleanup
    manager.cleanup()

@pytest.fixture
def memory_retrieval(memory_manager, mock_sentence_transformer):
    """Create a memory retrieval instance for testing."""
    return MemoryRetrieval(memory_manager)

def test_vector_storage_and_retrieval(memory_manager):
    """Test storing and retrieving vectors from red hot memory."""
    # Create test vector and metadata
    vector = np.random.rand(384).astype(np.float32)
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'source': 'test',
        'type': 'vector'
    }
    
    # Store vector in red hot memory
    memory_manager.add_to_tier('red_hot', vector, metadata=metadata)
    
    # Search for similar vectors using search_vectors
    results = memory_manager.search_vectors(vector, k=1)
    
    assert len(results) == 1
    assert np.allclose(results[0]['distance'], 0.0, atol=1e-5)
    assert results[0]['metadata']['source'] == 'test'
    assert results[0]['metadata']['type'] == 'vector'
    
    # Test retrieval using retrieve method
    result = memory_manager.retrieve({'vector': vector}, tier='red_hot')
    
    assert result is not None
    assert np.allclose(result['distance'], 0.0, atol=1e-5)
    assert result['metadata']['source'] == 'test'
    assert result['metadata']['type'] == 'vector'

def test_hot_memory_storage_and_retrieval(memory_manager):
    """Test storing and retrieving data from hot memory."""
    test_data = {'key': 'value', 'number': 42}
    memory_manager.add_to_tier('hot', test_data)
    
    # Test retrieval through memory manager
    result = memory_manager.retrieve({'key': 'value'}, tier='hot')
    assert result is not None
    assert result.get('number') == 42

def test_warm_memory_storage_and_retrieval(memory_manager):
    """Test storing and retrieving data from warm memory."""
    test_data = {'id': 1, 'name': 'test'}
    memory_manager.add_to_tier('warm', test_data)
    
    # Test retrieval through memory manager
    result = memory_manager.retrieve({'id': 1}, tier='warm')
    assert result is not None
    assert result.get('name') == 'test'
    
    # Test retrieval through DuckDB
    results = memory_manager.db_connection.execute("""
        SELECT COUNT(*) FROM warm_data
    """).fetchone()
    
    assert results[0] == 1

def test_cold_memory_storage_and_retrieval(memory_manager):
    """Test storing and retrieving data from cold memory."""
    # Create a test parquet file
    test_dir = Path(memory_manager.config['memory']['cold']['path'])
    test_dir.mkdir(exist_ok=True)
    
    df = pd.DataFrame({'id': [1], 'value': ['test']})
    parquet_path = test_dir / 'test.parquet'
    df.to_parquet(parquet_path)
    
    # Import the parquet file
    result = memory_manager.batch_import_parquet(
        test_dir,
        theme='test',
        tag='test'
    )
    
    assert result['num_files'] == 1
    assert result['num_records'] == 1
    assert result['total_size'] > 0
    
    # Test retrieval through memory manager
    result = memory_manager.retrieve({'id': 1}, tier='cold')
    assert result is not None
    assert result.get('value') == 'test'

def test_retrieve_all(memory_manager):
    """Test retrieving all data from each memory tier."""
    # Store test data in hot and warm memory
    test_data = {'id': 1, 'value': 'test'}
    memory_manager.add_to_tier('hot', test_data)
    memory_manager.add_to_tier('warm', test_data)
    
    # Create test data in cold memory
    test_dir = Path(memory_manager.config['memory']['cold']['path'])
    test_dir.mkdir(exist_ok=True)
    df = pd.DataFrame({'id': [1], 'value': ['test']})
    parquet_path = test_dir / 'test.parquet'
    df.to_parquet(parquet_path)
    memory_manager.batch_import_parquet(test_dir)
    
    # Test retrieving from each tier
    hot_results = memory_manager.retrieve_all(tier='hot')
    warm_results = memory_manager.retrieve_all(tier='warm')
    cold_results = memory_manager.retrieve_all(tier='cold')
    
    # Verify results
    assert len(hot_results) > 0
    assert any(r.get('value') == 'test' for r in hot_results)
    
    assert len(warm_results) > 0
    assert any(r.get('value') == 'test' for r in warm_results)
    
    assert len(cold_results) > 0
    assert any(r.get('value') == 'test' for r in cold_results)
    
    # Clean up
    memory_manager.clear()

def test_clear_memory(memory_manager):
    """Test clearing data from each memory tier."""
    # Store test data in each tier
    vector = np.random.rand(384).astype(np.float32)
    memory_manager.add_to_tier('red_hot', vector, metadata={'source': 'test'})
    
    test_data = {'id': 1, 'value': 'test'}
    memory_manager.add_to_tier('hot', test_data)
    memory_manager.add_to_tier('warm', test_data)
    
    # Create test data in cold memory
    test_dir = Path(memory_manager.config['memory']['cold']['path'])
    test_dir.mkdir(exist_ok=True)
    df = pd.DataFrame({'id': [1], 'value': ['test']})
    df.to_parquet(test_dir / 'test.parquet')
    memory_manager.batch_import_parquet(test_dir)
    
    # Clear all memory
    memory_manager.clear()
    
    # Verify all tiers are empty
    red_hot_result = memory_manager.retrieve({'vector': vector}, tier='red_hot')
    hot_results = memory_manager.retrieve_all(tier='hot')
    warm_results = memory_manager.retrieve_all(tier='warm')
    cold_results = memory_manager.retrieve_all(tier='cold')
    
    assert red_hot_result is None
    assert len(hot_results) == 0
    assert len(warm_results) == 0
    assert len(cold_results) == 0

def test_clear_all_memory(memory_manager):
    """Test clearing all memory tiers."""
    # Store test data in each tier
    vector = np.random.rand(384).astype(np.float32)
    memory_manager.add_to_tier('red_hot', vector, metadata={'source': 'test'})
    
    test_data = {'id': 1, 'value': 'test'}
    memory_manager.add_to_tier('hot', test_data)
    memory_manager.add_to_tier('warm', test_data)
    
    # Create test data in cold memory
    test_dir = Path(memory_manager.config['memory']['cold']['path'])
    test_dir.mkdir(exist_ok=True)
    df = pd.DataFrame({'id': [1], 'value': ['test']})
    df.to_parquet(test_dir / 'test.parquet')
    memory_manager.batch_import_parquet(test_dir)
    
    # Clear all memory
    memory_manager.clear()
    
    # Verify all tiers are empty
    red_hot_result = memory_manager.retrieve({'vector': vector}, tier='red_hot')
    hot_results = memory_manager.retrieve_all(tier='hot')
    warm_results = memory_manager.retrieve_all(tier='warm')
    cold_results = memory_manager.retrieve_all(tier='cold')
    
    assert red_hot_result is None
    assert len(hot_results) == 0
    assert len(warm_results) == 0
    assert len(cold_results) == 0

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