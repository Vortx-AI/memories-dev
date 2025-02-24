"""
Test Overture data download and filtering functionality.
"""

import pytest
from unittest.mock import Mock, patch, call, AsyncMock
import os
import shutil
import duckdb
from pathlib import Path
import subprocess
from memories.data_acquisition.sources.overture_api import OvertureAPI

@pytest.fixture
def bbox():
    """Sample bounding box for testing."""
    return {
        'xmin': -122.4018,
        'ymin': 37.7914,
        'xmax': -122.3928,
        'ymax': 37.7994
    }

@pytest.fixture
def overture_api(tmp_path):
    """Create an Overture API instance with Azure as default."""
    return OvertureAPI(data_dir=str(tmp_path), use_azure=True)

@pytest.fixture
def overture_api_aws(tmp_path):
    """Create an Overture API instance with AWS."""
    return OvertureAPI(data_dir=str(tmp_path), use_azure=False)

@pytest.fixture
def mock_duckdb_connection():
    """Create a mock DuckDB connection."""
    mock_con = Mock()
    mock_con.execute = Mock()
    mock_con.fetchdf = Mock(return_value=Mock(to_dict=Mock(return_value=[])))
    return mock_con

def test_init_azure(tmp_path):
    """Test initialization with Azure source."""
    api = OvertureAPI(data_dir=str(tmp_path), use_azure=True)
    assert api.use_azure is True
    assert isinstance(api.data_dir, Path)
    assert str(api.data_dir) == str(tmp_path)

def test_init_aws(tmp_path):
    """Test initialization with AWS source."""
    api = OvertureAPI(data_dir=str(tmp_path), use_azure=False)
    assert api.use_azure is False
    assert isinstance(api.data_dir, Path)
    assert str(api.data_dir) == str(tmp_path)

def test_theme_definitions():
    """Test that all required themes are defined."""
    api = OvertureAPI()
    required_themes = {
        'buildings', 'places', 'transportation',
        'addresses', 'base', 'divisions'
    }
    assert set(api.THEMES.keys()) == required_themes
    
    # Check each theme has required columns
    required_columns = {'id', 'bbox.xmin', 'bbox.ymin', 'bbox.xmax', 'bbox.ymax', 'geometry'}
    for theme, columns in api.THEMES.items():
        for col in required_columns:
            assert col in columns, f"Theme {theme} missing required column {col}"

@pytest.mark.asyncio
async def test_download_theme_azure(overture_api, bbox, mock_duckdb_connection):
    """Test theme download using Azure."""
    with patch('duckdb.connect', return_value=mock_duckdb_connection):
        result = overture_api.download_theme('buildings', bbox)
        assert result is True
        
        # Verify Azure URL was used
        execute_calls = mock_duckdb_connection.execute.call_args_list
        azure_url_used = any(
            'overturemapswestus2.dfs.core.windows.net' in str(call)
            for call in execute_calls
        )
        assert azure_url_used

@pytest.mark.asyncio
async def test_download_theme_aws(overture_api_aws, bbox, mock_duckdb_connection):
    """Test theme download using AWS."""
    with patch('duckdb.connect', return_value=mock_duckdb_connection):
        result = overture_api_aws.download_theme('buildings', bbox)
        assert result is True
        
        # Verify AWS URL was used
        execute_calls = mock_duckdb_connection.execute.call_args_list
        aws_url_used = any(
            'overturemaps-us-west-2' in str(call)
            for call in execute_calls
        )
        assert aws_url_used

@pytest.mark.asyncio
async def test_download_theme_invalid(overture_api, bbox):
    """Test download with invalid theme."""
    result = overture_api.download_theme('invalid_theme', bbox)
    assert result is False

@pytest.mark.asyncio
async def test_download_all_themes(overture_api, bbox, mock_duckdb_connection):
    """Test downloading all themes."""
    with patch('duckdb.connect', return_value=mock_duckdb_connection):
        results = overture_api.download_data(bbox)
        assert isinstance(results, dict)
        assert all(theme in results for theme in overture_api.THEMES)
        assert all(results.values())

@pytest.mark.asyncio
async def test_search_with_list_bbox(overture_api, mock_duckdb_connection):
    """Test search with list-format bbox."""
    bbox_list = [-122.4018, 37.7914, -122.3928, 37.7994]
    
    with patch('duckdb.connect', return_value=mock_duckdb_connection):
        results = await overture_api.search(bbox_list)
        assert isinstance(results, dict)
        assert all(theme in results for theme in overture_api.THEMES)

@pytest.mark.asyncio
async def test_search_with_dict_bbox(overture_api, bbox, mock_duckdb_connection):
    """Test search with dictionary-format bbox."""
    with patch('duckdb.connect', return_value=mock_duckdb_connection):
        results = await overture_api.search(bbox)
        assert isinstance(results, dict)
        assert all(theme in results for theme in overture_api.THEMES)

def test_cleanup(overture_api):
    """Test cleanup of DuckDB connection."""
    mock_close = Mock()
    overture_api.con.close = mock_close
    overture_api.__del__()
    mock_close.assert_called_once()

@pytest.mark.asyncio
async def test_error_handling(overture_api, bbox, mock_duckdb_connection):
    """Test error handling in various scenarios."""
    # Test DuckDB connection error
    with patch('duckdb.connect', side_effect=Exception("Connection error")):
        results = await overture_api.search(bbox)
        assert all(not features for features in results.values())
    
    # Test download error
    mock_duckdb_connection.execute.side_effect = Exception("Download error")
    with patch('duckdb.connect', return_value=mock_duckdb_connection):
        results = overture_api.download_data(bbox)
        assert all(not status for status in results.values())

@pytest.mark.asyncio
async def test_memory_settings(overture_api, bbox, mock_duckdb_connection):
    """Test memory and thread settings."""
    with patch('duckdb.connect', return_value=mock_duckdb_connection):
        overture_api.download_theme('buildings', bbox)
        
        # Verify memory settings were applied
        mock_duckdb_connection.execute.assert_any_call("SET memory_limit='1GB';")
        mock_duckdb_connection.execute.assert_any_call("SET threads=4;")

@pytest.mark.asyncio
async def test_file_management(overture_api, bbox, tmp_path):
    """Test file creation and cleanup."""
    theme = 'buildings'
    theme_dir = tmp_path / theme
    theme_dir.mkdir(parents=True)
    theme_file = theme_dir / f"{theme}.geojsonseq"
    theme_file.touch()
    
    with patch('duckdb.connect', return_value=mock_duckdb_connection):
        overture_api.download_theme(theme, bbox)
        assert not theme_file.exists()  # Should be removed before download
        
@pytest.mark.integration
async def test_end_to_end_azure(overture_api, bbox):
    """Integration test for Azure workflow."""
    results = await overture_api.search(bbox)
    assert isinstance(results, dict)
    assert all(theme in results for theme in overture_api.THEMES)
    
    # Verify file structure
    for theme in overture_api.THEMES:
        theme_dir = overture_api.data_dir / theme
        assert theme_dir.exists()
        theme_file = theme_dir / f"{theme}.geojsonseq"
        if results[theme]:  # If features were found
            assert theme_file.exists()

@pytest.mark.integration
async def test_end_to_end_aws(overture_api_aws, bbox):
    """Integration test for AWS workflow."""
    results = await overture_api_aws.search(bbox)
    assert isinstance(results, dict)
    assert all(theme in results for theme in overture_api.THEMES)
    
    # Verify file structure
    for theme in overture_api_aws.THEMES:
        theme_dir = overture_api_aws.data_dir / theme
        assert theme_dir.exists()
        theme_file = theme_dir / f"{theme}.geojsonseq"
        if results[theme]:  # If features were found
            assert theme_file.exists()

def test_show_data_locations(overture_api, overture_api_aws, capsys):
    """Show where data will be stored for both Azure and AWS instances."""
    print(f"\nAzure data directory: {overture_api.data_dir}")
    print(f"AWS data directory: {overture_api_aws.data_dir}")
    print(f"Temporary directory base: {os.path.dirname(str(overture_api.data_dir))}")
    
    # Create a test file to show it works
    test_dir = overture_api.data_dir / "test"
    test_dir.mkdir(parents=True)
    test_file = test_dir / "test.txt"
    test_file.write_text("Test content")
    
    assert test_file.exists()
    print(f"Test file created at: {test_file}")
    
    # The file and directory will be automatically cleaned up after the test