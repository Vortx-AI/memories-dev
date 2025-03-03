#!/usr/bin/env python3

import os
import pytest
from pathlib import Path
import duckdb
from dotenv import load_dotenv
from memories.core.memory_manager import MemoryManager
from memories.core.memory_retrieval import MemoryRetrieval
import shutil
import pandas as pd

# Load environment variables from .env file
load_dotenv()

# Get geo_memories path from environment variable
GEO_MEMORIES_PATH = Path(os.getenv('GEO_MEMORIES_PATH', '/home/jaya/geo_memories'))

def list_cold_tables():
    """List all tables in cold memory directly without pytest."""
    print(f"\n=== Listing Tables in Cold Memory ===\n")
    
    try:
        # Create storage directory
        storage_dir = Path('data')
        storage_dir.mkdir(exist_ok=True)
        
        # Create cold storage directory
        cold_dir = storage_dir / 'cold'
        cold_dir.mkdir(exist_ok=True)
        
        # Create and configure DuckDB database
        db_path = cold_dir / 'cold.db'
        
        # Remove any existing database file to avoid connection conflicts
        if db_path.exists():
            db_path.unlink()
            
        print("Creating DuckDB connection...")
        # First create connection without config
        db_conn = duckdb.connect(str(db_path))
        
        # Then set the configurations
        print("Configuring DuckDB settings...")
        db_conn.execute("SET memory_limit='8GB'")
        db_conn.execute("SET threads=4")
        
        print("Initializing memory manager...")
        memory_manager = MemoryManager(
            storage_path=storage_dir,
            vector_encoder=None,  # Not needed for this test
            enable_red_hot=False,
            enable_hot=False,
            enable_cold=True,
            enable_warm=False,
            enable_glacier=False,
            custom_config={
                'cold': {
                    'max_size': int(os.getenv('COLD_STORAGE_MAX_SIZE', 10737418240)),
                    'duckdb': {
                        'db_conn': db_conn
                    }
                }
            }
        )
        
        # Initialize memory retrieval
        print("Initializing memory retrieval...")
        memory_retrieval = MemoryRetrieval(memory_manager.cold)
        
        # Import some test data if GEO_MEMORIES_PATH exists
        if GEO_MEMORIES_PATH.exists():
            print(f"\nImporting test data from {GEO_MEMORIES_PATH}...")
            results = memory_manager.cold.batch_import_parquet(
                folder_path=GEO_MEMORIES_PATH,
                theme="geo",
                tag="location",
                recursive=True,
                pattern="*.parquet"
            )
            print(f"Imported {results['files_processed']} files")
        
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
        if storage_dir.exists():
            shutil.rmtree(storage_dir)

@pytest.fixture
def memory_retrieval(tmp_path):
    """Initialize memory retrieval with cold storage enabled."""
    
    # Create test directory
    test_cold_dir = tmp_path / "test_cold"
    test_cold_dir.mkdir(exist_ok=True)
    
    # Create and configure DuckDB database
    db_path = test_cold_dir / 'cold.db'
    if db_path.exists():
        db_path.unlink()
        
    # Create DuckDB connection
    db_conn = duckdb.connect(str(db_path))
    db_conn.execute("SET memory_limit='8GB'")
    db_conn.execute("SET threads=4")
    
    # Initialize memory manager
    manager = MemoryManager(
        storage_path=test_cold_dir,
        vector_encoder=None,  # Not needed for this test
        enable_red_hot=False,
        enable_hot=False,
        enable_cold=True,
        enable_warm=False,
        enable_glacier=False,
        custom_config={
            "cold": {
                "max_size": int(os.getenv("COLD_STORAGE_MAX_SIZE", 10737418240)),
                "duckdb": {
                    'db_conn': db_conn
                }
            }
        }
    )
    
    # Create memory retrieval instance
    retrieval = MemoryRetrieval(manager.cold)
    
    yield retrieval
    
    # Cleanup
    db_conn.close()
    manager.cleanup()
    if test_cold_dir.exists():
        shutil.rmtree(test_cold_dir)

def test_list_tables(memory_retrieval, tmp_path):
    """Test listing tables in cold memory."""
    
    # Create a test parquet file
    test_df = pd.DataFrame({
        'id': range(10),
        'value': [f"test_{i}" for i in range(10)]
    })
    
    test_file = tmp_path / "test.parquet"
    test_df.to_parquet(test_file)
    
    # Import the test file
    memory_retrieval.cold.batch_import_parquet(
        folder_path=tmp_path,
        theme="test",
        tag="unit_test",
        recursive=True,
        pattern="*.parquet"
    )
    
    # List tables
    tables = memory_retrieval.list_available_data()
    
    # Verify results
    assert len(tables) > 0, "Should have at least one table"
    
    table = tables[0]
    assert 'table_name' in table, "Table should have a name"
    assert 'theme' in table, "Table should have a theme"
    assert 'tag' in table, "Table should have a tag"
    assert table['theme'] == "test", "Theme should match"
    assert table['tag'] == "unit_test", "Tag should match"
    assert table['num_rows'] == 10, "Should have 10 rows"
    assert table['num_columns'] == 2, "Should have 2 columns"
    assert 'id' in table['schema'], "Should have id column"
    assert 'value' in table['schema'], "Should have value column"

def test_empty_tables(memory_retrieval):
    """Test listing tables when no tables exist."""
    tables = memory_retrieval.list_available_data()
    assert len(tables) == 0, "Should have no tables"

if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        # Run pytest if --test flag is provided
        pytest.main([__file__, "-v"])
    else:
        # Run direct table listing
        list_cold_tables() 