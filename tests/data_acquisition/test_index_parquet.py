import pytest
import pandas as pd
import pyarrow.parquet as pq
import json
from pathlib import Path
from memories.data_acquisition.index_parquet import analyze_parquet_files

@pytest.fixture
def test_parquet_dir(tmp_path):
    """Create test Parquet files for testing."""
    # Create valid Parquet files
    df1 = pd.DataFrame({
        'id': range(3),
        'value': ['a', 'b', 'c']
    })
    df1.to_parquet(tmp_path / "valid1.parquet")
    
    df2 = pd.DataFrame({
        'id': range(3, 6),
        'value': ['d', 'e', 'f']
    })
    df2.to_parquet(tmp_path / "valid2.parquet")
    
    # Create a corrupted Parquet file
    with open(tmp_path / "corrupted.parquet", "w") as f:
        f.write("This is not a valid Parquet file")
    
    # Create subdirectory with more files
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    df3 = pd.DataFrame({
        'id': range(6, 9),
        'value': ['g', 'h', 'i']
    })
    df3.to_parquet(subdir / "valid3.parquet")
    
    return tmp_path

def test_analyze_valid_files(test_parquet_dir, tmp_path):
    """Test analyzing valid Parquet files."""
    output_dir = tmp_path / "output"
    results = analyze_parquet_files(
        base_path=str(test_parquet_dir),
        output_dir=str(output_dir)
    )
    
    # Check that valid files were processed
    processed_files = [item['file_name'] for item in results['processed_files']]
    assert 'valid1.parquet' in processed_files
    assert 'valid2.parquet' in processed_files
    assert 'valid3.parquet' in processed_files
    
    # Check that output directory was created
    assert output_dir.exists()

def test_analyze_corrupted_files(test_parquet_dir, tmp_path):
    """Test handling of corrupted Parquet files."""
    output_dir = tmp_path / "output"
    results = analyze_parquet_files(
        base_path=str(test_parquet_dir),
        output_dir=str(output_dir)
    )
    
    # Check that corrupted file was caught
    error_files = [item['file_name'] for item in results['error_files']]
    assert 'corrupted.parquet' in error_files
    
    # Verify error message
    error_entry = next(item for item in results['error_files'] 
                      if item['file_name'] == 'corrupted.parquet')
    assert 'error' in error_entry
    assert len(error_entry['error']) > 0

def test_empty_directory(tmp_path):
    """Test handling of empty directory."""
    results = analyze_parquet_files(
        base_path=str(tmp_path),
        output_dir=str(tmp_path / "output")
    )
    
    assert len(results['processed_files']) == 0
    assert len(results['error_files']) == 0

def test_recursive_directory_scan(test_parquet_dir, tmp_path):
    """Test recursive scanning of directories."""
    output_dir = tmp_path / "output"
    results = analyze_parquet_files(
        base_path=str(test_parquet_dir),
        output_dir=str(output_dir)
    )
    
    # Check that file in subdirectory was processed
    subdir_file = next((item for item in results['processed_files'] 
                       if 'subdir' in item['file_path']), None)
    assert subdir_file is not None
    assert subdir_file['file_name'] == 'valid3.parquet'

def test_file_paths_in_results(test_parquet_dir, tmp_path):
    """Test that file paths in results are correct."""
    output_dir = tmp_path / "output"
    results = analyze_parquet_files(
        base_path=str(test_parquet_dir),
        output_dir=str(output_dir)
    )
    
    for file_info in results['processed_files']:
        assert 'file_path' in file_info
        file_path = Path(file_info['file_path'])
        assert file_path.exists()
        assert file_path.is_file()

def test_non_parquet_files(test_parquet_dir, tmp_path):
    """Test handling of non-Parquet files."""
    # Create a non-Parquet file
    with open(test_parquet_dir / "test.txt", "w") as f:
        f.write("This is a text file")
    
    output_dir = tmp_path / "output"
    results = analyze_parquet_files(
        base_path=str(test_parquet_dir),
        output_dir=str(output_dir)
    )
    
    # Check that non-Parquet file was ignored
    all_files = [item['file_name'] for item in results['processed_files']] + \
                [item['file_name'] for item in results['error_files']]
    assert 'test.txt' not in all_files

def test_output_directory_creation(test_parquet_dir, tmp_path):
    """Test creation of output directory."""
    output_dir = tmp_path / "output" / "nested" / "dir"
    results = analyze_parquet_files(
        base_path=str(test_parquet_dir),
        output_dir=str(output_dir)
    )
    
    assert output_dir.exists()
    assert output_dir.is_dir()

def test_default_parameters():
    """Test default parameter values."""
    # This test just verifies that the function can be called with defaults
    # We don't actually want to write to the default locations in a test
    with pytest.raises(Exception):
        analyze_parquet_files()

def test_error_details(test_parquet_dir, tmp_path):
    """Test that error details are properly captured."""
    output_dir = tmp_path / "output"
    results = analyze_parquet_files(
        base_path=str(test_parquet_dir),
        output_dir=str(output_dir)
    )
    
    for error_file in results['error_files']:
        assert 'file_name' in error_file
        assert 'file_path' in error_file
        assert 'error' in error_file
        assert isinstance(error_file['error'], str)
        assert len(error_file['error']) > 0 