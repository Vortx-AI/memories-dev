#!/usr/bin/env python3

import os
import pytest
from pathlib import Path
import duckdb
from dotenv import load_dotenv
from memories.core.memory_manager import MemoryManager
from memories.utils.text.embeddings import get_encoder

# Load environment variables from .env file
load_dotenv()

# Get geo_memories path from environment variable
GEO_MEMORIES_PATH = Path(os.getenv('GEO_MEMORIES_PATH', '/Users/jaya/geo_memories'))

if not GEO_MEMORIES_PATH:
    raise ValueError("GEO_MEMORIES_PATH not set in environment variables")

@pytest.fixture
def memory_manager():
    """Initialize memory manager with cold storage enabled."""
    vector_encoder = get_encoder()
    manager = MemoryManager(
        vector_encoder=vector_encoder,
        enable_hot=False,     # Disable Redis dependency
        enable_cold=True,     # Enable cold storage for parquet files
        enable_warm=False,    # Disable warm storage
        enable_glacier=False  # Disable glacier storage
    )
    
    # Configure cold storage
    manager.configure_tiers(
        cold_config={
            'path': 'test_cold',
            'max_size': 10737418240,  # 10GB
            'duckdb_config': {
                'memory_limit': '8GB',
                'threads': 4,
                'enable_external_access': True
            }
        }
    )
    
    yield manager
    
    # Cleanup
    manager.cleanup()
    if Path('test_cold').exists():
        import shutil
        shutil.rmtree('test_cold')

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
    # Run only the geo memories import test
    pytest.main([__file__, "-v", "-k", "test_geo_memories_import"]) 