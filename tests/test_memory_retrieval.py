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
        
        print("Initializing memory retrieval...")
        # Initialize memory manager with existing connection
        memory_manager = MemoryManager(
            vector_encoder=None,  # Not needed for listing
            enable_red_hot=False,
            enable_hot=False,
            enable_cold=True,
            enable_warm=False,
            enable_glacier=False,
            custom_config={
                'cold': {
                    'max_size': int(os.getenv('COLD_STORAGE_MAX_SIZE', 10737418240)),
                    'path': cold_dir,  # Set the cold storage path in config
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
        vector_encoder=None,  # Not needed for this test
        enable_red_hot=False,
        enable_hot=False,
        enable_cold=True,
        enable_warm=False,
        enable_glacier=False,
        custom_config={
            "cold": {
                "max_size": int(os.getenv("COLD_STORAGE_MAX_SIZE", 10737418240)),
                "path": test_cold_dir,  # Set the cold storage path in config
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

def test_bbox_query(memory_retrieval, tmp_path):
    """Test querying data within a bounding box."""
    
    # Create a test DataFrame with geographic coordinates
    test_df = pd.DataFrame({
        'id': range(10),
        'latitude': [40.7, 40.75, 40.8, 40.85, 40.9, 41.0, 41.1, 41.2, 41.3, 41.4],
        'longitude': [-74.0, -73.95, -73.9, -73.85, -73.8, -73.75, -73.7, -73.65, -73.6, -73.55]
    })
    
    test_file = tmp_path / "geo_test.parquet"
    test_df.to_parquet(test_file)
    
    # Create another test DataFrame with geometry column
    # First create the geometry using DuckDB spatial functions
    memory_retrieval.cold.con.execute("INSTALL spatial;")
    memory_retrieval.cold.con.execute("LOAD spatial;")
    
    # Create points and convert to WKB
    points_query = """
        SELECT 
            row_id as id,
            ST_AsBinary(ST_Point(lon, lat)) as geometry
        FROM (
            VALUES
                (0, -73.95, 40.75),
                (1, -73.90, 40.80),
                (2, -73.85, 40.85),
                (3, -74.10, 41.00),
                (4, -74.20, 41.10)
        ) AS t(row_id, lon, lat)
    """
    geom_df = memory_retrieval.cold.con.execute(points_query).fetchdf()
    
    geom_file = tmp_path / "geom_test.parquet"
    geom_df.to_parquet(geom_file)
    
    # Import both test files
    memory_retrieval.cold.batch_import_parquet(
        folder_path=tmp_path,
        theme="test",
        tag="geo_test",
        recursive=True,
        pattern="*.parquet"
    )
    
    # Test bounding box query with lat/lon columns
    results = memory_retrieval.get_data_by_bbox(
        min_lon=-74.0,
        min_lat=40.7,
        max_lon=-73.8,
        max_lat=40.9
    )
    
    # Verify lat/lon results
    assert not results.empty, "Should return matching records"
    assert len(results) == 5, "Should return exactly 5 records within the bounding box"
    assert all(results['latitude'] >= 40.7), "All latitudes should be >= min_lat"
    assert all(results['latitude'] <= 40.9), "All latitudes should be <= max_lat"
    assert all(results['longitude'] >= -74.0), "All longitudes should be >= min_lon"
    assert all(results['longitude'] <= -73.8), "All longitudes should be <= max_lon"
    
    # Test bounding box query with geometry column
    geom_results = memory_retrieval.get_data_by_bbox(
        min_lon=-74.0,
        min_lat=40.7,
        max_lon=-73.8,
        max_lat=40.9,
        geom_column='geometry'
    )
    
    # Verify geometry results
    assert not geom_results.empty, "Should return matching records for geometry"
    assert 'source_table' in geom_results.columns, "Should include source table information"

def test_polygon_query(memory_retrieval, tmp_path):
    """Test querying data within a polygon."""
    
    # Create a test DataFrame with geometry column using DuckDB spatial functions
    memory_retrieval.cold.con.execute("INSTALL spatial;")
    memory_retrieval.cold.con.execute("LOAD spatial;")
    
    # Create points and convert to WKB
    points_query = """
        SELECT 
            row_id as id,
            ST_AsBinary(ST_Point(lon, lat)) as geometry
        FROM (
            VALUES
                (0, -73.95, 40.75),
                (1, -73.90, 40.80),
                (2, -73.85, 40.85),
                (3, -74.10, 41.00),
                (4, -74.20, 41.10)
        ) AS t(row_id, lon, lat)
    """
    test_df = memory_retrieval.cold.con.execute(points_query).fetchdf()
    
    test_file = tmp_path / "geom_test.parquet"
    test_df.to_parquet(test_file)
    
    # Import the test file
    memory_retrieval.cold.batch_import_parquet(
        folder_path=tmp_path,
        theme="test",
        tag="geom_test",
        recursive=True,
        pattern="*.parquet"
    )
    
    # Test polygon query with a simple triangle
    polygon = """POLYGON((-74.0 40.7, -73.8 40.7, -73.9 40.9, -74.0 40.7))"""
    results = memory_retrieval.get_data_by_polygon(polygon_wkt=polygon)
    
    # Verify results
    assert not results.empty, "Should return matching records"
    assert 'source_table' in results.columns, "Should include source table information"

def test_empty_bbox_query(memory_retrieval):
    """Test bounding box query with no matching data."""
    results = memory_retrieval.get_data_by_bbox(
        min_lon=0,
        min_lat=0,
        max_lon=1,
        max_lat=1
    )
    assert results.empty, "Should return empty DataFrame when no data matches"

def test_invalid_column_names(memory_retrieval, tmp_path):
    """Test querying with non-existent column names."""
    
    # Create a test DataFrame with different column names
    test_df = pd.DataFrame({
        'id': range(5),
        'lat': [40.7, 40.75, 40.8, 40.85, 40.9],  # Different from default 'latitude'
        'lon': [-74.0, -73.95, -73.9, -73.85, -73.8]  # Different from default 'longitude'
    })
    
    test_file = tmp_path / "custom_cols.parquet"
    test_df.to_parquet(test_file)
    
    # Import the test file
    memory_retrieval.cold.batch_import_parquet(
        folder_path=tmp_path,
        theme="test",
        tag="custom_cols",
        recursive=True,
        pattern="*.parquet"
    )
    
    # Query with default column names (should return empty)
    results = memory_retrieval.get_data_by_bbox(
        min_lon=-74.0,
        min_lat=40.7,
        max_lon=-73.8,
        max_lat=40.9
    )
    assert results.empty, "Should return empty DataFrame with wrong column names"
    
    # Query with correct column names (should return data)
    results = memory_retrieval.get_data_by_bbox(
        min_lon=-74.0,
        min_lat=40.7,
        max_lon=-73.8,
        max_lat=40.9,
        lon_column='lon',
        lat_column='lat'
    )
    assert not results.empty, "Should return data with correct column names"

def test_spatial_queries():
    """Run spatial queries directly without pytest."""
    print("\n=== Testing Spatial Queries ===\n")
    
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
        db_conn.execute("SET memory_limit='8GB'")
        db_conn.execute("SET threads=4")
        
        # Install and load spatial extension
        print("Installing and loading DuckDB spatial extension...")
        db_conn.execute("INSTALL spatial;")
        db_conn.execute("LOAD spatial;")
        
        print("Initializing memory manager...")
        memory_manager = MemoryManager(
            vector_encoder=None,
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
        memory_retrieval = MemoryRetrieval(memory_manager.cold)
        
        # Test bounding box query
        print("\nTesting bounding box query...")
        bbox_results = memory_retrieval.get_data_by_bbox(
            min_lon=72.0,  # Rough bounding box for India
            min_lat=8.0,
            max_lon=88.0,
            max_lat=37.0,
            lon_column='longitude',
            lat_column='latitude',
            geom_column='geometry'  # Will try both geometry and lat/lon columns
        )
        
        if not bbox_results.empty:
            print(f"\nFound {len(bbox_results)} records within bounding box")
            print("\nSample of results:")
            print(bbox_results.head().to_string())
        else:
            print("No records found within bounding box")
        
        # Test polygon query if geometry data is available
        print("\nTesting polygon query...")
        india_polygon = """POLYGON((72.0 8.0, 88.0 8.0, 88.0 37.0, 72.0 37.0, 72.0 8.0))"""
        
        polygon_results = memory_retrieval.get_data_by_polygon(
            polygon_wkt=india_polygon,
            geom_column='geometry'
        )
        
        if not polygon_results.empty:
            print(f"\nFound {len(polygon_results)} records intersecting with polygon")
            print("\nSample of results:")
            print(polygon_results.head().to_string())
        else:
            print("No records found intersecting with polygon")
        
    except Exception as e:
        print(f"\nError during spatial queries: {str(e)}")
        raise
    
    finally:
        if 'db_conn' in locals():
            db_conn.close()

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
    elif "--spatial" in sys.argv:
        # Run spatial queries test
        test_spatial_queries()
    else:
        # Run direct table listing
        main() 