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

def test_list_parquet_files_empty_dir(tmp_path):
    """Test listing Parquet files in an empty directory."""
    files = list_parquet_files(str(tmp_path))
    assert len(files) == 0

def test_list_parquet_files_nested(tmp_path):
    """Test listing Parquet files in nested directories."""
    # Create nested directory structure
    nested_dir = tmp_path / "level1" / "level2"
    nested_dir.mkdir(parents=True)
    
    # Create Parquet files at different levels
    df = pd.DataFrame({'test': [1, 2, 3]})
    df.to_parquet(tmp_path / "root.parquet")
    df.to_parquet(tmp_path / "level1" / "mid.parquet")
    df.to_parquet(nested_dir / "deep.parquet")
    
    files = list_parquet_files(str(tmp_path))
    assert len(files) == 3
    assert any("root.parquet" in f for f in files)
    assert any("mid.parquet" in f for f in files)
    assert any("deep.parquet" in f for f in files)

def test_list_parquet_files_non_parquet(tmp_path):
    """Test listing Parquet files when directory contains non-Parquet files."""
    # Create a mix of Parquet and non-Parquet files
    df = pd.DataFrame({'test': [1, 2, 3]})
    df.to_parquet(tmp_path / "data.parquet")
    
    # Create some non-Parquet files
    (tmp_path / "text.txt").write_text("test")
    (tmp_path / "data.csv").write_text("a,b,c")
    
    files = list_parquet_files(str(tmp_path))
    assert len(files) == 1
    assert "data.parquet" in files[0]

def test_corrupted_parquet_handling(tmp_path, monkeypatch):
    """Test handling of corrupted Parquet files."""
    # Create a valid Parquet file
    df1 = pd.DataFrame({'id': [1, 2, 3], 'value': ['a', 'b', 'c']})
    df1.to_parquet(tmp_path / "valid.parquet")
    
    # Create a corrupted Parquet file
    (tmp_path / "corrupted.parquet").write_text("This is not a valid Parquet file")
    
    # Set environment variable
    monkeypatch.setenv("GEO_MEMORIES", str(tmp_path))
    
    # Test query handling of corrupted file
    with pytest.raises(Exception) as exc_info:
        query_multiple_parquet()
    assert "Parquet file is corrupted" in str(exc_info.value)

def test_list_parquet_files_permissions(tmp_path):
    """Test handling of permission errors when listing Parquet files."""
    # Create a directory with restricted permissions
    restricted_dir = tmp_path / "restricted"
    restricted_dir.mkdir()
    df = pd.DataFrame({'test': [1, 2, 3]})
    df.to_parquet(restricted_dir / "data.parquet")
    
    # Remove read permissions (on Unix-like systems)
    if os.name != 'nt':  # Skip on Windows
        restricted_dir.chmod(0o000)
        try:
            files = list_parquet_files(str(tmp_path))
            assert len(files) == 0
        finally:
            # Restore permissions for cleanup
            restricted_dir.chmod(0o755) 