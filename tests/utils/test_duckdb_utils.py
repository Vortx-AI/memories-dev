import pytest
import os
import tempfile
import pandas as pd
import duckdb
from memories.utils.duckdb_utils import query_multiple_parquet

@pytest.fixture
def sample_parquet_files(tmp_path):
    """Create sample Parquet files for testing"""
    # Create first dataframe
    df1 = pd.DataFrame({
        'id': [1, 2, 3],
        'value': [10, 20, 30],
        'category': ['A', 'B', 'C']
    })
    
    # Create second dataframe with slightly different schema
    df2 = pd.DataFrame({
        'id': [4, 5, 6],
        'value': [40, 50, 60],
        'category': ['D', 'E', 'F'],
        'extra_column': [1, 2, 3]
    })
    
    # Save to parquet files
    file1 = tmp_path / "data1.parquet"
    file2 = tmp_path / "data2.parquet"
    
    df1.to_parquet(file1)
    df2.to_parquet(file2)
    
    # Set environment variable
    os.environ['GEO_MEMORIES'] = str(tmp_path)
    
    return [file1, file2]

def test_query_multiple_parquet_basic(sample_parquet_files):
    """Test basic query functionality"""
    try:
        result = query_multiple_parquet("SELECT * FROM combined_data")
        assert result is not None
        assert len(result) == 6  # Total rows from both files
        
    except Exception as e:
        pytest.fail(f"Basic query test failed: {str(e)}")

def test_query_multiple_parquet_with_filter(sample_parquet_files):
    """Test query with filter"""
    try:
        result = query_multiple_parquet(
            "SELECT * FROM combined_data WHERE value > 30"
        )
        assert result is not None
        assert len(result) == 3  # Only rows with value > 30
        
    except Exception as e:
        pytest.fail(f"Query with filter test failed: {str(e)}")

def test_query_multiple_parquet_aggregation(sample_parquet_files):
    """Test aggregation query"""
    try:
        result = query_multiple_parquet(
            "SELECT category, SUM(value) as total FROM combined_data GROUP BY category"
        )
        assert result is not None
        assert len(result) == 6  # One row per category
        
    except Exception as e:
        pytest.fail(f"Aggregation query test failed: {str(e)}")

def test_query_multiple_parquet_missing_env():
    """Test handling of missing environment variable"""
    # Remove environment variable
    if 'GEO_MEMORIES' in os.environ:
        del os.environ['GEO_MEMORIES']
    
    with pytest.raises(ValueError) as excinfo:
        query_multiple_parquet("SELECT * FROM combined_data")
    assert "GEO_MEMORIES path is not set" in str(excinfo.value)

def test_query_multiple_parquet_invalid_query(sample_parquet_files):
    """Test handling of invalid SQL query"""
    with pytest.raises(Exception) as excinfo:
        query_multiple_parquet("INVALID SQL QUERY")
    assert "Parser Error" in str(excinfo.value)

def test_query_multiple_parquet_schema_handling(sample_parquet_files):
    """Test handling of different schemas across files"""
    try:
        # Query including the extra column
        result = query_multiple_parquet(
            "SELECT id, value, category, extra_column FROM combined_data"
        )
        assert result is not None
        
        # First three rows should have NULL in extra_column
        first_three = [row for row in result[:3]]
        assert all(row[-1] is None for row in first_three)
        
        # Last three rows should have values in extra_column
        last_three = [row for row in result[3:]]
        assert all(row[-1] is not None for row in last_three)
        
    except Exception as e:
        pytest.fail(f"Schema handling test failed: {str(e)}")

def test_query_multiple_parquet_empty_result(sample_parquet_files):
    """Test query that returns no results"""
    try:
        result = query_multiple_parquet(
            "SELECT * FROM combined_data WHERE value > 1000"
        )
        assert result is not None
        assert len(result) == 0
        
    except Exception as e:
        pytest.fail(f"Empty result test failed: {str(e)}")

def test_query_multiple_parquet_connection_cleanup(sample_parquet_files):
    """Test that database connections are properly cleaned up"""
    try:
        # Make multiple queries
        for _ in range(5):
            result = query_multiple_parquet("SELECT * FROM combined_data")
            assert result is not None
        
        # Try to create a new connection
        conn = duckdb.connect(':memory:')
        assert conn is not None
        conn.close()
        
    except Exception as e:
        pytest.fail(f"Connection cleanup test failed: {str(e)}")

@pytest.mark.gpu
class TestDuckDBGPUUtils:
    def test_gpu_acceleration(self):
        """Test GPU acceleration for DuckDB queries"""
        pytest.skip("Skipping GPU test as it's optional")

    def test_gpu_memory_management(self):
        """Test GPU memory management in DuckDB"""
        pytest.skip("Skipping GPU test as it's optional")

    def test_gpu_query_optimization(self):
        """Test query optimization with GPU"""
        pytest.skip("Skipping GPU test as it's optional")

    def test_gpu_error_handling(self):
        """Test error handling for GPU operations in DuckDB"""
        pytest.skip("Skipping GPU test as it's optional") 