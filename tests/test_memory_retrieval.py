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
        
        print("Initializing memory retrieval...")
        # Initialize memory manager with existing connection
        memory_manager = MemoryManager(
            storage_path=storage_dir,
            vector_encoder=None,  # Not needed for listing
            enable_red_hot=False,
            enable_hot=False,
            enable_cold=True,
            enable_warm=False,
            enable_glacier=False,
            custom_config={
                'cold': {
                    'max_size': int(os.getenv('COLD_STORAGE_MAX_SIZE', 10737418240)),
                    'duckdb': {
                        'db_conn': db_conn,
                        'enable_external_access': True  # Enable external access for parquet files
                    }
                }
            }
        )
        
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
        memory_manager = MemoryManager(
            storage_path=storage_dir,
            vector_encoder=None,  # Not needed for listing
            enable_red_hot=False,
            enable_hot=False,
            enable_cold=True,
            enable_warm=False,
            enable_glacier=False,
            custom_config={
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
        )
        
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