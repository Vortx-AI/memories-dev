import pytest
import pandas as pd
import duckdb
import os
from pathlib import Path
from memories.data_acquisition.duckdb_utils import query_multiple_parquet, list_parquet_files

@pytest.fixture
def test_data_dir(tmp_path):
    """Create test Parquet files for testing."""
    # Create first Parquet file
    df1 = pd.DataFrame({
        'id': range(1, 4),
        'value': ['a', 'b', 'c'],
        'common': [1.0, 2.0, 3.0]
    })
    df1.to_parquet(tmp_path / "data1.parquet")
    
    # Create second Parquet file with slightly different schema
    df2 = pd.DataFrame({
        'id': range(4, 7),
        'value': ['d', 'e', 'f'],
        'common': [4.0, 5.0, 6.0],
        'extra': ['x', 'y', 'z']
    })
    df2.to_parquet(tmp_path / "data2.parquet")
    
    return tmp_path

def test_query_multiple_parquet(test_data_dir, monkeypatch):
    """Test querying multiple Parquet files."""
    # Set up environment variable
    monkeypatch.setenv('GEO_MEMORIES', str(test_data_dir))
    
    # Test basic query
    result = query_multiple_parquet("SELECT * FROM combined_data ORDER BY id")
    assert len(result) == 6
    assert result[0][0] == 1  # First row, id column
    assert result[-1][0] == 6  # Last row, id column

def test_schema_alignment(test_data_dir, monkeypatch):
    """Test schema alignment with union_by_name."""
    monkeypatch.setenv('GEO_MEMORIES', str(test_data_dir))
    
    # Query should handle different schemas
    result = query_multiple_parquet(
        "SELECT id, value, common, extra FROM combined_data ORDER BY id"
    )
    assert len(result) == 6
    # First three rows should have NULL in extra column
    assert result[0][3] is None
    # Last three rows should have values in extra column
    assert result[-1][3] == 'z'

def test_aggregation_query(test_data_dir, monkeypatch):
    """Test aggregation queries."""
    monkeypatch.setenv('GEO_MEMORIES', str(test_data_dir))
    
    result = query_multiple_parquet(
        "SELECT COUNT(*) as count, AVG(common) as avg_common FROM combined_data"
    )
    assert result[0][0] == 6  # Total count
    assert result[0][1] == 3.5  # Average of common column

def test_filtered_query(test_data_dir, monkeypatch):
    """Test filtered queries."""
    monkeypatch.setenv('GEO_MEMORIES', str(test_data_dir))
    
    result = query_multiple_parquet(
        "SELECT * FROM combined_data WHERE id > 3"
    )
    assert len(result) == 3
    assert all(row[0] > 3 for row in result)  # All ids should be > 3

def test_missing_env_variable(monkeypatch):
    """Test handling of missing environment variable."""
    monkeypatch.delenv('GEO_MEMORIES', raising=False)
    
    with pytest.raises(ValueError, match="GEO_MEMORIES path is not set"):
        query_multiple_parquet()

def test_invalid_query(test_data_dir, monkeypatch):
    """Test handling of invalid SQL query."""
    monkeypatch.setenv('GEO_MEMORIES', str(test_data_dir))
    
    with pytest.raises(Exception):
        query_multiple_parquet("INVALID SQL QUERY")

def test_empty_directory(tmp_path):
    """Test handling of empty directory."""
    # Create test directory structure
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Test empty directory
    result = list_parquet_files(str(data_dir))
    assert len(result) == 0

def test_complex_query(test_data_dir, monkeypatch):
    """Test more complex SQL queries."""
    monkeypatch.setenv('GEO_MEMORIES', str(test_data_dir))
    
    result = query_multiple_parquet("""
        SELECT 
            value,
            COUNT(*) as count,
            AVG(common) as avg_common
        FROM combined_data
        GROUP BY value
        HAVING COUNT(*) > 0
        ORDER BY avg_common DESC
    """)
    assert len(result) == 6  # One row per unique value
    
def test_connection_cleanup(test_data_dir, monkeypatch):
    """Test that database connection is properly cleaned up."""
    monkeypatch.setenv('GEO_MEMORIES', str(test_data_dir))
    
    # Run query multiple times to ensure connections are cleaned up
    for _ in range(3):
        result = query_multiple_parquet()
        assert result is not None 