#!/usr/bin/env python3

import os
import pytest
from pathlib import Path
import duckdb
from dotenv import load_dotenv
from memories.core.memory_manager import MemoryManager
from memories.core.cold import ColdMemory
from memories.utils.text.embeddings import get_encoder
import shutil
import tempfile
import yaml
import pandas as pd
import numpy as np

# Load environment variables from .env file
load_dotenv()

# Get geo_memories path from environment variable
GEO_MEMORIES_PATH = Path(os.getenv('GEO_MEMORIES_PATH', '/Users/jaya/geo_memories'))


def cleanup_cold_memory():
    """Clean up any existing cold memory data."""
    print("\n=== Cleaning up existing cold memory ===\n")
    
    try:
        storage_dir = Path('data')
        if not storage_dir.exists():
            print("No existing storage directory found.")
            return
            
        # Create and configure DuckDB connection
        db_path = storage_dir / 'cold' / 'cold.db'
        if db_path.exists():
            print("Found existing database, connecting to clean up...")
            db_conn = duckdb.connect(str(db_path))
            
            # Initialize memory manager
            memory_manager = MemoryManager()
            
            # Configure the manager
            memory_manager.config = {
                'memory': {
                    'base_path': storage_dir,
                    'cold': {
                        'max_size': int(os.getenv('COLD_STORAGE_MAX_SIZE', 10737418240)),
                        'path': storage_dir / 'cold',
                        'duckdb': {
                            'db_conn': db_conn
                        }
                    }
                }
            }
            
            # Use the new cleanup method
            memory_manager.cleanup_cold_memory(remove_storage=True)
            print("Cleanup completed successfully!")
            
    except Exception as e:
        print(f"Error during cleanup: {e}")
        raise

def run_import():
    """Run the parquet import directly without pytest."""
    if not GEO_MEMORIES_PATH.exists():
        print(f"Error: Directory not found: {GEO_MEMORIES_PATH}")
        return

    print(f"\n=== Importing Geo Memories from {GEO_MEMORIES_PATH} ===\n")
    
    try:
        # Create storage directory
        storage_dir = Path('data')
        storage_dir.mkdir(exist_ok=True)
        
        # Create cold storage directory
        cold_dir = storage_dir / 'cold'
        cold_dir.mkdir(exist_ok=True)
        
        # Create and configure DuckDB database
        db_path = cold_dir / 'cold.db'
        
        print("Creating DuckDB connection...")
        # Create connection with external access enabled
        db_conn = duckdb.connect(str(db_path), config={'enable_external_access': True})
        db_conn.execute("SET memory_limit='8GB'")
        db_conn.execute("SET threads=4")
        
        print("Initializing memory manager...")
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
                        'config': {
                            'enable_external_access': True
                        }
                    }
                }
            }
        }
        
        print("\nStarting parquet file import...")
        print(f"Looking for parquet files in: {GEO_MEMORIES_PATH}")
        
        results = memory_manager.batch_import_parquet(
            folder_path=GEO_MEMORIES_PATH,
            theme="geo",
            tag="location",
            recursive=True,
            pattern="*.parquet"
        )
        
        # Print detailed results
        print("\nImport Results:")
        print(f"Files processed: {results['files_processed']}")
        print(f"Records imported: {results['records_imported']}")
        print(f"Total size: {results['total_size'] / (1024*1024):.2f} MB")
        
        if results['errors']:
            print("\nErrors encountered:")
            for error in results['errors']:
                print(f"- {error}")
        
        print("\nImport completed successfully!")
        
    except Exception as e:
        print(f"\nError during import: {str(e)}")
        raise

@pytest.fixture
def memory_manager(tmp_path):
    """Create a memory manager instance for testing."""
    config = {
        'memory': {
            'cold': {
                'path': str(tmp_path / 'cold'),
                'max_size': 1024 * 1024 * 1024,  # 1GB
                'duckdb': {
                    'memory_limit': '4GB',
                    'threads': 4
                }
            }
        }
    }
    manager = MemoryManager(config=config)
    return manager

def test_batch_parquet_import(memory_manager, tmp_path):
    """Test importing multiple parquet files."""
    # Create test directory
    test_dir = tmp_path / "test_parquet_data"
    test_dir.mkdir()
    divisions_dir = test_dir / "divisions"
    divisions_dir.mkdir()
    
    # Create test DataFrames
    df1 = pd.DataFrame({
        'id': range(10),
        'value': np.random.rand(10),
        'division': 'A'
    })
    
    df2 = pd.DataFrame({
        'id': range(10, 20),
        'value': np.random.rand(10),
        'division': 'B'
    })
    
    df3 = pd.DataFrame({
        'id': range(20, 30),
        'value': np.random.rand(10),
        'division': 'C'
    })
    
    # Save as parquet files
    df1.to_parquet(divisions_dir / "test1.parquet")
    df2.to_parquet(divisions_dir / "test2.parquet")
    df3.to_parquet(divisions_dir / "test3.parquet")
    
    # Import files
    result = memory_manager.cold.batch_import_parquet(
        test_dir,
        theme="test_theme",
        tag="test_tag",
        recursive=True
    )
    
    # Check results
    assert result['num_files'] == 3
    assert result['num_records'] == 30
    assert result['total_size'] > 0
    assert len(result['errors']) == 0
    
    # Check metadata
    files = memory_manager.cold.con.execute("""
        SELECT * FROM cold_metadata
    """).fetchall()
    
    assert len(files) == 3
    for file in files:
        assert file[1] == "test_theme"  # theme
        assert file[2] == "test_tag"    # tag
        assert file[3] == 10            # num_rows
        assert file[4] == 3             # num_columns
        assert isinstance(file[5], str)  # schema
        assert file[7] is not None      # table_name

def test_empty_directory(memory_manager, tmp_path):
    """Test importing from an empty directory."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    
    result = memory_manager.cold.batch_import_parquet(empty_dir)
    
    assert result['num_files'] == 0
    assert result['num_records'] == 0
    assert result['total_size'] == 0
    assert len(result['errors']) == 0

def test_invalid_parquet_file(memory_manager, tmp_path):
    """Test handling invalid parquet files."""
    test_dir = tmp_path / "test_invalid"
    test_dir.mkdir()
    
    # Create invalid file
    invalid_file = test_dir / "invalid.parquet"
    invalid_file.write_text("This is not a parquet file")
    
    result = memory_manager.cold.batch_import_parquet(test_dir)
    
    assert result['num_files'] == 0
    assert result['num_records'] == 0
    assert result['total_size'] == 0
    assert len(result['errors']) == 1

def test_nonexistent_directory(memory_manager):
    """Test importing from a nonexistent directory."""
    with pytest.raises(ValueError):
        memory_manager.cold.batch_import_parquet("nonexistent_dir")

def test_recursive_import(memory_manager, tmp_path):
    """Test recursive import of parquet files."""
    # Create nested directory structure
    root_dir = tmp_path / "nested"
    root_dir.mkdir()
    sub_dir1 = root_dir / "sub1"
    sub_dir1.mkdir()
    sub_dir2 = root_dir / "sub2"
    sub_dir2.mkdir()
    
    # Create test DataFrames
    df1 = pd.DataFrame({'id': range(5), 'value': np.random.rand(5)})
    df2 = pd.DataFrame({'id': range(5, 10), 'value': np.random.rand(5)})
    
    # Save as parquet files in different directories
    df1.to_parquet(sub_dir1 / "test1.parquet")
    df2.to_parquet(sub_dir2 / "test2.parquet")
    
    # Test recursive import
    result = memory_manager.cold.batch_import_parquet(root_dir, recursive=True)
    assert result['num_files'] == 2
    assert result['num_records'] == 10
    
    # Test non-recursive import
    result = memory_manager.cold.batch_import_parquet(root_dir, recursive=False)
    assert result['num_files'] == 0

if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        # Run pytest if --test flag is provided
        pytest.main([__file__, "-v", "-k", "test_geo_memories_import"])
    elif "--cleanup" in sys.argv:
        # Run only cleanup if --cleanup flag is provided
        cleanup_cold_memory()
    else:
        # Run direct import without cleanup
        run_import() 