"""Tests for OSM local data functionality."""

import pytest
from pathlib import Path
import geopandas as gpd
from shapely.geometry import box, Polygon
import os

from memories.data_acquisition.sources.osm_local import (
    get_landuse_data,
    get_specific_tags,
    index_osm_parquet,
    ALL_TAGS
)

@pytest.fixture
def test_bbox():
    """Create a test bounding box for Bangalore city center."""
    return (77.5946, 12.9716, 77.5993, 12.9763)  # Small area in Bangalore

@pytest.fixture
def test_polygon():
    """Create a test polygon."""
    return box(77.5946, 12.9716, 77.5993, 12.9763)

def test_get_landuse_data_with_bbox(test_bbox, tmp_path):
    """Test fetching landuse data with bounding box."""
    save_path = tmp_path / "test_landuse.geoparquet"
    
    # Test with bbox coordinates
    gdf = get_landuse_data(
        bbox=test_bbox,
        save_path=str(save_path)
    )
    
    assert gdf is not None
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert len(gdf) > 0
    assert 'landuse_type' in gdf.columns
    assert save_path.exists()

def test_get_landuse_data_with_polygon(test_polygon, tmp_path):
    """Test fetching landuse data with polygon."""
    save_path = tmp_path / "test_landuse_polygon.geoparquet"
    
    gdf = get_landuse_data(
        bbox=test_polygon,
        save_path=str(save_path)
    )
    
    assert gdf is not None
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert len(gdf) > 0
    assert save_path.exists()

def test_get_landuse_data_with_specific_tags(test_bbox, tmp_path):
    """Test fetching landuse data with specific tags."""
    save_path = tmp_path / "test_landuse_tags.geoparquet"
    
    # Test with only landuse and leisure tags
    specific_tags = get_specific_tags(['landuse', 'leisure'])
    
    gdf = get_landuse_data(
        bbox=test_bbox,
        tags=specific_tags,
        save_path=str(save_path)
    )
    
    assert gdf is not None
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert all(tag in ['landuse', 'leisure', 'unclassified'] 
              for tag in gdf['landuse_type'].str.split('_').str[0])

def test_get_specific_tags():
    """Test getting specific tag categories."""
    # Test getting single category
    landuse_tags = get_specific_tags(['landuse'])
    assert 'landuse' in landuse_tags
    assert len(landuse_tags) == 1
    assert landuse_tags['landuse'] == ALL_TAGS['landuse']
    
    # Test getting multiple categories
    selected_tags = get_specific_tags(['landuse', 'leisure'])
    assert 'landuse' in selected_tags
    assert 'leisure' in selected_tags
    assert len(selected_tags) == 2
    
    # Test with invalid category
    invalid_tags = get_specific_tags(['invalid_category'])
    assert len(invalid_tags) == 0

def test_get_landuse_data_append(test_bbox, tmp_path):
    """Test appending new data to existing file."""
    save_path = tmp_path / "test_landuse_append.geoparquet"
    
    # First save
    gdf1 = get_landuse_data(
        bbox=test_bbox,
        tags=get_specific_tags(['landuse']),
        save_path=str(save_path)
    )
    
    # Second save with different tags
    gdf2 = get_landuse_data(
        bbox=test_bbox,
        tags=get_specific_tags(['leisure']),
        save_path=str(save_path)
    )
    
    # Read final file
    final_gdf = gpd.read_parquet(save_path)
    
    assert len(final_gdf) >= len(gdf1)  # Should have at least as many rows as first save

def test_invalid_bbox():
    """Test handling of invalid bbox."""
    with pytest.raises(ValueError):
        get_landuse_data(bbox="invalid")

def test_index_osm_parquet(tmp_path):
    """Test indexing OSM parquet files."""
    # Create test parquet files
    test_gdf = gpd.GeoDataFrame(
        {'geometry': [box(0, 0, 1, 1)]},
        crs="EPSG:4326"
    )
    
    # Save valid file
    valid_file = tmp_path / "valid.parquet"
    test_gdf.to_parquet(valid_file)
    
    # Create invalid file
    invalid_file = tmp_path / "invalid.parquet"
    with open(invalid_file, 'w') as f:
        f.write("invalid content")
    
    # Run indexing
    results = index_osm_parquet(str(tmp_path))
    
    assert len(results["processed_files"]) == 1
    assert len(results["error_files"]) == 1
    assert results["processed_files"][0]["file_name"] == "valid.parquet"
    assert results["error_files"][0]["file_name"] == "invalid.parquet" 