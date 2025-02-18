"""
Test water bodies monitor example functionality.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path
from examples.water_bodies_monitor import WaterBodyAgent
from memories.core.config import Config
from memories import MemoryStore

@pytest.fixture
def config():
    """Create a config for testing."""
    return Config(config_path="examples/config/db_config.yml")

@pytest.fixture
def memory_store(config):
    """Create a memory store for testing."""
    return MemoryStore(config)

@pytest.fixture
def water_body_agent(memory_store, config):
    """Create a water body agent for testing."""
    return WaterBodyAgent(memory_store, config)

@pytest.fixture
def mock_data():
    """Create mock satellite and vector data."""
    return {
        "satellite_data": {
            "pc": {
                "sentinel-2-l2a": [{
                    "data": np.random.random((4, 100, 100)),  # Mock satellite bands
                    "metadata": {
                        "datetime": datetime.now().isoformat(),
                        "cloud_cover": 5.0
                    }
                }]
            }
        },
        "vector_data": {
            "osm": {
                "waterways": [{
                    "type": "Feature",
                    "properties": {
                        "area": 1000.0,
                        "type": "water"
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]
                    }
                }]
            }
        },
        "bbox": [0, 0, 1, 1]
    }

@pytest.mark.asyncio
async def test_analyze_water_body(water_body_agent, mock_data):
    """Test water body analysis functionality."""
    # Mock the data manager's prepare_training_data method
    water_body_agent.data_manager.prepare_training_data = AsyncMock(return_value=mock_data)
    
    # Mock the image processor's calculate_ndwi method
    water_body_agent.image_processor.calculate_ndwi = Mock(
        return_value=np.random.uniform(0, 1, (100, 100))
    )
    
    # Test analysis
    insights = await water_body_agent.analyze_water_body(
        bbox=[0, 0, 1, 1],
        start_date=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
        end_date=datetime.now().strftime("%Y-%m-%d")
    )
    
    # Verify results
    assert "surface_area" in insights
    assert "ndwi_mean" in insights
    assert "quality_metrics" in insights
    assert isinstance(insights["surface_area"], (int, float))
    assert isinstance(insights["ndwi_mean"], float)
    assert all(metric in insights["quality_metrics"] for metric in ["clarity", "water_presence", "variability"])

@pytest.mark.asyncio
async def test_process_water_data(water_body_agent, mock_data):
    """Test water data processing."""
    # Mock the image processor
    water_body_agent.image_processor.calculate_ndwi = Mock(
        return_value=np.random.uniform(0, 1, (100, 100))
    )
    
    # Test processing
    processed_data = await water_body_agent._process_water_data(mock_data)
    
    # Verify results
    assert isinstance(processed_data, dict)
    assert "location" in processed_data
    assert "surface_area" in processed_data
    assert "quality_metrics" in processed_data
    assert processed_data["surface_area"] == 1000.0  # From mock data

def test_is_significant_change(water_body_agent):
    """Test significant change detection."""
    # Test with significant change
    assert water_body_agent._is_significant_change({
        "ndwi_mean": 0.4  # Above threshold
    }) is True
    
    # Test with insignificant change
    assert water_body_agent._is_significant_change({
        "ndwi_mean": 0.2  # Below threshold
    }) is False
    
    # Test with missing data
    assert water_body_agent._is_significant_change({
        "ndwi_mean": None
    }) is False

def test_analyze_quality(water_body_agent):
    """Test water quality analysis."""
    # Test with valid NDWI data
    ndwi_data = np.random.uniform(0, 1, (100, 100))
    quality = water_body_agent._analyze_quality(ndwi_data)
    
    assert "clarity" in quality
    assert "water_presence" in quality
    assert "variability" in quality
    assert all(isinstance(v, float) for v in quality.values())
    
    # Test with None data
    quality = water_body_agent._analyze_quality(None)
    assert all(v is None for v in quality.values()) 