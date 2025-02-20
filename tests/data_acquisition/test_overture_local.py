"""Tests for Overture local data functionality."""

import pytest
from pathlib import Path
import geopandas as gpd
from shapely.geometry import box, Polygon
import os
import json
import tempfile

from memories.data_acquisition.sources.overture_local import (
    get_overture_data,
    get_specific_themes,
    index_overture_parquet,
    ALL_THEMES
)

@pytest.fixture
def test_bbox():
    """Create a test bounding box for San Francisco city center."""
    return (-122.4018, 37.7914, -122.3928, 37.7994)

@pytest.fixture
def test_polygon():
    """Create a test polygon."""
    return box(-122.4018, 37.7914, -122.3928, 37.7994)

@pytest.fixture
def test_data_dir(tmp_path):
    """Create a test data directory with sample files."""
    # Create test GeoDataFrame
    test_gdf = gpd.GeoDataFrame(
        {'geometry': [box(0, 0, 1, 1)]},
        crs="EPSG:4326"
    )
    
    # Create valid parquet file
    valid_file = tmp_path / "valid.parquet"
    test_gdf.to_parquet(valid_file)
    
    # Create invalid parquet file
    invalid_file = tmp_path / "invalid.parquet"
    with open(invalid_file, 'w') as f:
        f.write("invalid content")
    
    return tmp_path

def test_get_overture_data_with_bbox(test_bbox, tmp_path):
    """Test downloading Overture data with bounding box."""
    results = get_overture_data(
        bbox=test_bbox,
        save_path=str(tmp_path)
    )
    
    assert isinstance(results, dict)
    assert all(theme in results for theme in ALL_THEMES)
    assert any(success for success in results.values())
    
    # Check if files were created
    for theme in ALL_THEMES:
        theme_file = tmp_path / theme / f"{theme}.geojsonseq"
        if results[theme]:
            assert theme_file.exists()

def test_get_overture_data_with_polygon(test_polygon, tmp_path):
    """Test downloading Overture data with polygon."""
    results = get_overture_data(
        bbox=test_polygon,
        save_path=str(tmp_path)
    )
    
    assert isinstance(results, dict)
    assert all(theme in results for theme in ALL_THEMES)
    
    # Check if files were created
    for theme in ALL_THEMES:
        if results[theme]:
            theme_file = tmp_path / theme / f"{theme}.geojsonseq"
            assert theme_file.exists()

def test_get_overture_data_with_specific_themes(test_bbox, tmp_path):
    """Test downloading specific Overture themes."""
    themes = ['buildings', 'places']
    results = get_overture_data(
        bbox=test_bbox,
        themes=themes,
        save_path=str(tmp_path)
    )
    
    assert isinstance(results, dict)
    assert all(theme in results for theme in themes)
    assert not any(theme in results for theme in ALL_THEMES if theme not in themes)
    
    # Check if only specified theme files were created
    for theme in ALL_THEMES:
        theme_file = tmp_path / theme / f"{theme}.geojsonseq"
        if theme in themes and results[theme]:
            assert theme_file.exists()
        else:
            assert not theme_file.exists()

def test_get_specific_themes():
    """Test getting specific themes."""
    # Test getting single theme
    themes = get_specific_themes(['buildings'])
    assert len(themes) == 1
    assert 'buildings' in themes
    
    # Test getting multiple themes
    themes = get_specific_themes(['buildings', 'places'])
    assert len(themes) == 2
    assert 'buildings' in themes
    assert 'places' in themes
    
    # Test with invalid theme
    themes = get_specific_themes(['invalid_theme'])
    assert len(themes) == 0
    
    # Test with 'all' theme
    themes = get_specific_themes(['all'])
    assert len(themes) == 1
    assert 'all' in themes

def test_get_overture_data_invalid_bbox():
    """Test handling of invalid bbox."""
    with pytest.raises(ValueError):
        get_overture_data(bbox="invalid")

def test_get_overture_data_invalid_themes(test_bbox, tmp_path):
    """Test handling of invalid themes."""
    results = get_overture_data(
        bbox=test_bbox,
        themes=['invalid_theme'],
        save_path=str(tmp_path)
    )
    
    assert isinstance(results, dict)
    assert len(results) == 0

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