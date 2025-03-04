"""
Test script for Overture API functionality.
"""

import logging
import json
from pathlib import Path
import pytest
from memories.data_acquisition.sources.overture_api import OvertureAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def overture_api():
    """Fixture to create an OvertureAPI instance."""
    api = OvertureAPI(data_dir="data/overture_test")
    return api

@pytest.fixture
def nyc_bbox():
    """Fixture for New York City bounding box."""
    return {
        "xmin": -74.0060,  # NYC longitude bounds
        "ymin": 40.7128,   # NYC latitude bounds
        "xmax": -73.9350,
        "ymax": 40.8075
    }

def test_overture_download(overture_api, nyc_bbox):
    """Test the Overture API download_theme_type function."""
    # Test downloading buildings data
    theme = "buildings"
    tag = "building"
    
    logger.info("-" * 50)
    logger.info(f"Testing download for {theme}/{tag} in NYC area")
    logger.info(f"Bounding box: {json.dumps(nyc_bbox, indent=2)}")
    logger.info("-" * 50)
    
    # Attempt the download
    success = overture_api.download_theme_type(
        theme=theme,
        tag=tag,
        bbox=nyc_bbox,
        storage_path="data/overture_test",
        max_size=2*1024*1024*1024  # 2GB max size
    )
    
    assert success, "Download should be successful"
    
    # Verify the downloaded data
    output_file = Path("data/overture_test/overture") / theme / tag / f"{tag}_filtered.parquet"
    assert output_file.exists(), "Output file should exist"
    
    # Check the data content
    count_query = f"SELECT COUNT(*) as count FROM read_parquet('{output_file}')"
    count = overture_api.con.execute(count_query).fetchone()[0]
    assert count > 0, "Should have downloaded some features"
    
    # Check data structure
    sample_query = f"""
    SELECT 
        id, 
        names.primary AS name,
        geometry
    FROM read_parquet('{output_file}')
    LIMIT 1
    """
    sample = overture_api.con.execute(sample_query).fetchdf()
    assert not sample.empty, "Should be able to read the data"
    assert "id" in sample.columns, "Data should have an id column"
    assert "name" in sample.columns, "Data should have a name column"
    assert "geometry" in sample.columns, "Data should have a geometry column"

def test_invalid_theme(overture_api, nyc_bbox):
    """Test downloading with an invalid theme."""
    success = overture_api.download_theme_type(
        theme="invalid_theme",
        tag="building",
        bbox=nyc_bbox,
        storage_path="data/overture_test"
    )
    assert not success, "Should fail with invalid theme"

def test_invalid_tag(overture_api, nyc_bbox):
    """Test downloading with an invalid tag."""
    success = overture_api.download_theme_type(
        theme="buildings",
        tag="invalid_tag",
        bbox=nyc_bbox,
        storage_path="data/overture_test"
    )
    assert not success, "Should fail with invalid tag"

def test_invalid_bbox(overture_api):
    """Test downloading with an invalid bbox."""
    invalid_bbox = {
        "xmin": 200,  # Invalid longitude
        "ymin": 40.7128,
        "xmax": 201,
        "ymax": 40.8075
    }
    success = overture_api.download_theme_type(
        theme="buildings",
        tag="building",
        bbox=invalid_bbox,
        storage_path="data/overture_test"
    )
    assert not success, "Should fail with invalid bbox" 