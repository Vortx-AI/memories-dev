#!/usr/bin/env python3

import os
import pytest
from pathlib import Path
import duckdb
from dotenv import load_dotenv
from memories.core.memory_manager import MemoryManager
from memories.utils.text.embeddings import get_encoder
import shutil

# Load environment variables from .env file
load_dotenv()

# Get geo_memories path from environment variable
GEO_MEMORIES_PATH = Path(os.getenv('GEO_MEMORIES_PATH', '/Users/jaya/geo_memories'))

def run_import():
    """Run the parquet import directly without pytest."""
    if not GEO_MEMORIES_PATH.exists():
        print(f"Error: Directory not found: {GEO_MEMORIES_PATH}")
        return

    print(f"\n=== Importing Geo Memories from {GEO_MEMORIES_PATH} ===\n")
    
    try:
        # Initialize vector encoder
        print("Initializing vector encoder...")
        vector_encoder = get_encoder()
        
        # Create storage directory
        storage_dir = Path('cold_storage')
        storage_dir.mkdir(exist_ok=True)
        
        # Pre-configure DuckDB settings
        duckdb.execute("SET enable_external_access=true")
        duckdb.execute("SET external_access=true")
        
        # Initialize memory manager
        print("Initializing memory manager...")
        memory_manager = MemoryManager(
            storage_path=storage_dir,
            vector_encoder=vector_encoder,
            enable_red_hot=False,  # Disable vector storage
            enable_hot=False,      # Disable Redis
            enable_cold=True,      # Enable cold storage for parquet files
            enable_warm=False,     # Disable warm storage
            enable_glacier=False,  # Disable glacier storage
            custom_config={
                'cold': {
                    'max_size': int(os.getenv('COLD_STORAGE_MAX_SIZE', 10737418240)),  # 10GB
                    'duckdb_config': {
                        'memory_limit': os.getenv('DUCKDB_MEMORY_LIMIT', '8GB'),
                        'threads': int(os.getenv('DUCKDB_THREADS', 4))
                    }
                }
            }
        )
        
        print("\nStarting parquet file import...")
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
    
    finally:
        print("\nCleaning up...")
        if 'memory_manager' in locals():
            memory_manager.cleanup()
        if storage_dir.exists():
            shutil.rmtree(storage_dir)

@pytest.fixture
def memory_manager():
    """Initialize memory manager with cold storage enabled."""
    vector_encoder = get_encoder()
    
    # First create the test directory if it doesn't exist
    test_cold_dir = Path('test_cold')
    test_cold_dir.mkdir(exist_ok=True)
    
    # Pre-configure DuckDB settings
    duckdb.execute("SET enable_external_access=true")
    duckdb.execute("SET external_access=true")
    
    manager = MemoryManager(
        storage_path=test_cold_dir,  # Specify storage path
        vector_encoder=vector_encoder,
        enable_red_hot=False,  # Disable vector storage
        enable_hot=False,      # Disable Redis
        enable_cold=True,      # Enable cold storage for parquet files
        enable_warm=False,     # Disable warm storage
        enable_glacier=False,  # Disable glacier storage
        custom_config={
            'cold': {
                'max_size': int(os.getenv('COLD_STORAGE_MAX_SIZE', 10737418240)),  # 10GB
                'duckdb_config': {
                    'memory_limit': os.getenv('DUCKDB_MEMORY_LIMIT', '8GB'),
                    'threads': int(os.getenv('DUCKDB_THREADS', 4))
                }
            }
        }
    )
    
    yield manager
    
    # Cleanup after tests
    manager.cleanup()
    if test_cold_dir.exists():
        shutil.rmtree(test_cold_dir)

@pytest.mark.skipif(not GEO_MEMORIES_PATH.exists(), 
                    reason="Geo memories directory not found")
def test_geo_memories_import(memory_manager):
    """Test importing actual geo memories data."""
    print(f"\n=== Importing Geo Memories from {GEO_MEMORIES_PATH} ===\n")
    
    try:
        # Import parquet files
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
        
        # Verify results
        assert results['files_processed'] > 0, "Should process at least one file"
        
        print("\nGeo memories import completed successfully!")
        
    except Exception as e:
        print(f"\nError during geo memories import: {str(e)}")
        raise

def test_batch_parquet_import(memory_manager, tmp_path):
    """Test batch import of parquet files to cold memory."""
    
    # Create test directory structure
    test_dir = tmp_path / "test_parquet_data"
    test_dir.mkdir()
    (test_dir / "divisions").mkdir()
    
    # Create some dummy parquet files (just for testing structure)
    (test_dir / "test1.parquet").touch()
    (test_dir / "test2.parquet").touch()
    (test_dir / "divisions" / "test3.parquet").touch()
    
    print(f"\n=== Testing Batch Parquet Import ===\n")
    print(f"Test directory: {test_dir}")
    
    try:
        # Import parquet files
        results = memory_manager.batch_import_parquet(
            folder_path=test_dir,
            theme="test",
            tag="batch_import",
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
        
        # Verify results
        assert results['files_processed'] == 3, "Should process 3 parquet files"
        assert len(results['errors']) == 0, "Should not have any errors"
        
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"\nError during test: {str(e)}")
        raise

def test_batch_import_with_invalid_files(memory_manager, tmp_path):
    """Test batch import with invalid parquet files."""
    
    # Create test directory
    test_dir = tmp_path / "invalid_parquet_data"
    test_dir.mkdir()
    
    # Create an invalid parquet file
    with open(test_dir / "invalid.parquet", "w") as f:
        f.write("This is not a parquet file")
    
    try:
        results = memory_manager.batch_import_parquet(
            folder_path=test_dir,
            theme="test",
            tag="invalid",
            recursive=True,
            pattern="*.parquet"
        )
        
        # Verify error handling
        assert len(results['errors']) > 0, "Should detect invalid parquet file"
        assert results['files_processed'] == 0, "Should not process invalid files"
        
    except Exception as e:
        print(f"\nError during invalid file test: {str(e)}")
        raise

def test_batch_import_empty_directory(memory_manager, tmp_path):
    """Test batch import with empty directory."""
    
    # Create empty test directory
    test_dir = tmp_path / "empty_dir"
    test_dir.mkdir()
    
    results = memory_manager.batch_import_parquet(
        folder_path=test_dir,
        theme="test",
        tag="empty",
        recursive=True,
        pattern="*.parquet"
    )
    
    # Verify empty directory handling
    assert results['files_processed'] == 0, "Should handle empty directory"
    assert len(results['errors']) == 0, "Should not have errors for empty directory"

if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        # Run pytest if --test flag is provided
        pytest.main([__file__, "-v", "-k", "test_geo_memories_import"])
    else:
        # Run direct import
        run_import() 