import os
import json
import pytest
import tempfile
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
from memories.data_acquisition.sources.overture_local import index_overture_parquet

@pytest.fixture
def test_data_dir():
    """Create a temporary directory with test parquet files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a valid parquet file
        table = pa.Table.from_pydict({
            'id': [1, 2, 3],
            'name': ['test1', 'test2', 'test3']
        })
        valid_file = Path(temp_dir) / 'valid.parquet'
        # Write using a simpler approach
        with open(valid_file, 'wb') as f:
            pq.write_table(table, f)
        
        # Create an invalid file
        invalid_file = Path(temp_dir) / 'invalid.parquet'
        with open(invalid_file, 'w') as f:
            f.write('This is not a valid parquet file')
            
        yield temp_dir

def test_index_overture_parquet(test_data_dir):
    """Test the Overture parquet indexing functionality."""
    # Run the indexing function
    results = index_overture_parquet(test_data_dir)
    
    # Verify the results structure
    assert isinstance(results, dict)
    assert 'processed_files' in results
    assert 'error_files' in results
    
    # Check that we have one processed file and one error file
    assert len(results['processed_files']) == 1
    assert len(results['error_files']) == 1
    
    # Verify processed file details
    processed = results['processed_files'][0]
    assert processed['file_name'] == 'valid.parquet'
    assert Path(processed['file_path']).name == 'valid.parquet'
    
    # Verify error file details
    error = results['error_files'][0]
    assert error['file_name'] == 'invalid.parquet'
    assert Path(error['file_path']).name == 'invalid.parquet'
    assert 'error' in error

def test_index_overture_parquet_empty_dir():
    """Test indexing with an empty directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        results = index_overture_parquet(temp_dir)
        assert len(results['processed_files']) == 0
        assert len(results['error_files']) == 0 