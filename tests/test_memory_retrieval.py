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
import yaml

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

@pytest.fixture(scope="function")
def memory_manager(tmp_path):
    """Create a memory manager instance for testing."""
    print("Creating DuckDB connection for tests...")
    
    # Create test database in temporary directory
    db_path = tmp_path / 'test.db'
    con = duckdb.connect(str(db_path))
    
    print("Initializing memory manager...")
    manager = MemoryManager()
    
    # Configure the memory tiers
    manager.configure_tiers(
        cold_config={
            'path': str(tmp_path / 'cold'),
            'max_size': 1073741824,  # 1GB
            'duckdb': {
                'memory_limit': '1GB',
                'threads': 2
            }
        },
        warm_config={
            'path': str(tmp_path / 'warm'),
            'max_size': 104857600,  # 100MB
            'duckdb': {
                'memory_limit': '512MB',
                'threads': 2
            }
        }
    )
    
    # Initialize cold memory with test connection
    manager.cold = manager.cold_memory
    manager.warm = manager.warm_memory
    
    yield manager
    
    # Cleanup
    con.close()
    if db_path.exists():
        db_path.unlink()
    if (tmp_path / 'cold').exists():
        shutil.rmtree(tmp_path / 'cold')
    if (tmp_path / 'warm').exists():
        shutil.rmtree(tmp_path / 'warm')

@pytest.fixture
def memory_retrieval(memory_manager):
    """Create a memory retrieval instance for testing."""
    return MemoryRetrieval(memory_manager=memory_manager)

def test_list_tables(memory_retrieval):
    """Test listing tables in cold memory."""
    tables = memory_retrieval.list_registered_files()
    assert isinstance(tables, list)

def test_empty_tables(memory_retrieval):
    """Test listing tables when none exist."""
    tables = memory_retrieval.list_registered_files()
    assert len(tables) == 0

def test_bbox_query(memory_retrieval):
    """Test querying data within a bounding box."""
    df = memory_retrieval.query_by_bbox(
        min_lon=-180,
        min_lat=-90,
        max_lon=180,
        max_lat=90
    )
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0  # Empty since no data loaded

def test_polygon_query(memory_retrieval):
    """Test querying data within a polygon."""
    polygon = "POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))"
    df = memory_retrieval.get_data_by_polygon(polygon)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0  # Empty since no data loaded

def test_empty_bbox_query(memory_retrieval):
    """Test querying empty bounding box."""
    df = memory_retrieval.query_by_bbox(
        min_lon=0,
        min_lat=0,
        max_lon=0,
        max_lat=0
    )
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0

def test_invalid_column_names(memory_retrieval):
    """Test querying with invalid column names."""
    df = memory_retrieval.get_data_by_bbox(
        min_lon=0,
        min_lat=0,
        max_lon=1,
        max_lat=1,
        lon_column="invalid_lon",
        lat_column="invalid_lat"
    )
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0

def test_search_geospatial_data_in_bbox(memory_retrieval):
    """Test searching geospatial data in bbox."""
    df = memory_retrieval.search_geospatial_data_in_bbox(
        query_word="test",
        bbox=(-180, -90, 180, 90),
        similarity_threshold=0.7
    )
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0  # Empty since no data loaded

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
    elif "--spatial" in sys.argv:
        # Run spatial queries test
        test_spatial_queries()
    else:
        # Run direct table listing
        main() 