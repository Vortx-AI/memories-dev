"""
Test location ambience analyzer example functionality with Overture Maps data.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path
from examples.location_ambience import LocationAnalyzer, simulate_location_data
from memories.config import Config
from memories import MemoryStore
from memories.data_acquisition import DataManager

@pytest.fixture
def memory_store():
    """Create a memory store for testing."""
    config = Config(
        storage_path="test_location_data",
        hot_memory_size=10,
        warm_memory_size=20,
        cold_memory_size=50
    )
    return MemoryStore(config)

@pytest.fixture
def data_manager():
    """Create a data manager for testing."""
    return DataManager(cache_dir="test_location_data")

@pytest.fixture
def location_analyzer(data_manager, memory_store):
    """Create a location analyzer for testing."""
    return LocationAnalyzer(data_manager, memory_store)

@pytest.fixture
def mock_satellite_data():
    # Create mock satellite data with NDVI bands
    red_band = np.random.random((100, 100))  # B04
    nir_band = np.random.random((100, 100))  # B08
    
    # Ensure some areas have vegetation (NDVI > 0.3)
    ndvi = (nir_band - red_band) / (nir_band + red_band)
    nir_band[ndvi < 0.3] *= 2  # Increase NIR values to create vegetation
    
    return {
        "sentinel-2-l2a": {
            "data": [
                np.random.random((100, 100)),  # B02
                np.random.random((100, 100)),  # B03
                red_band,  # B04
                nir_band   # B08
            ],
            "metadata": {
                "datetime": datetime.now().isoformat(),
                "cloud_cover": 10.0,
                "bands": ["B02", "B03", "B04", "B08"],
                "resolution": 10.0
            }
        }
    }

@pytest.fixture
def mock_overture_data():
    return {
        "buildings": [{"id": f"b{i}"} for i in range(50)],
        "roads": [{"id": f"r{i}"} for i in range(30)],
        "amenities": [{"id": f"a{i}"} for i in range(10)]
    }

@pytest.fixture
def test_location():
    """Create test location data."""
    return {
        "id": "test-123",
        "name": "Test Location",
        "bbox": [-122.5, 37.5, -122.0, 38.0],
        "type": "residential"
    }

@pytest.mark.asyncio
async def test_analyze_location(location_analyzer, test_location, mock_overture_data, mock_satellite_data):
    """Test location analysis functionality using Overture data."""
    # Mock the API calls
    location_analyzer.overture_api.search = AsyncMock(return_value=mock_overture_data)
    location_analyzer.pc_api.search_and_download = AsyncMock(return_value=mock_satellite_data)
    
    # Test analysis
    insights = await location_analyzer.analyze_location(test_location)
    
    # Verify results structure
    assert "location_id" in insights
    assert "timestamp" in insights
    assert "ambience_analysis" in insights
    
    # Verify analysis components
    analysis = insights["ambience_analysis"]
    assert "environmental_scores" in analysis
    assert "urban_features" in analysis
    assert "noise_levels" in analysis
    assert "recommendations" in analysis
    assert "satellite_metadata" in analysis

@pytest.mark.asyncio
async def test_analyze_location_data(location_analyzer, test_location, mock_overture_data, mock_satellite_data):
    """Test the internal location data analysis method."""
    insights = await location_analyzer._analyze_location_data(test_location, mock_overture_data, mock_satellite_data)
    
    assert "scores" in insights
    assert "urban_features" in insights
    assert "environmental_scores" in insights
    assert "noise_levels" in insights
    assert "recommendations" in insights
    assert isinstance(insights["scores"], float)

@pytest.mark.asyncio
async def test_analyze_urban_features(location_analyzer, mock_overture_data):
    """Test urban features analysis."""
    features = await location_analyzer._analyze_urban_features(mock_overture_data)
    
    assert "building_characteristics" in features
    assert "road_characteristics" in features
    assert "amenity_characteristics" in features
    
    assert "count" in features["building_characteristics"]
    assert "density" in features["building_characteristics"]
    assert "types" in features["building_characteristics"]

@pytest.mark.asyncio
async def test_calculate_environmental_scores(location_analyzer, mock_overture_data, mock_satellite_data):
    """Test environmental scores calculation."""
    urban_features = await location_analyzer._analyze_urban_features(mock_overture_data)
    scores = await location_analyzer._calculate_environmental_scores(urban_features, mock_satellite_data)
    
    assert "green_space" in scores
    assert "air_quality" in scores
    assert "water_bodies" in scores
    assert "urban_density" in scores
    
    assert 0 <= scores["green_space"] <= 1
    assert 0 <= scores["air_quality"] <= 1
    assert 0 <= scores["urban_density"] <= 1

@pytest.mark.asyncio
async def test_estimate_noise_levels(location_analyzer, mock_overture_data):
    """Test noise level estimation."""
    urban_features = await location_analyzer._analyze_urban_features(mock_overture_data)
    noise_levels = await location_analyzer._estimate_noise_levels(urban_features)
    
    assert "average" in noise_levels
    assert "peak" in noise_levels
    assert "variability" in noise_levels
    
    assert noise_levels["peak"] >= noise_levels["average"]
    assert noise_levels["variability"] >= 0

@pytest.mark.asyncio
async def test_calculate_ambience_score(location_analyzer, mock_overture_data, mock_satellite_data):
    """Test ambience score calculation."""
    urban_features = await location_analyzer._analyze_urban_features(mock_overture_data)
    env_scores = await location_analyzer._calculate_environmental_scores(urban_features, mock_satellite_data)
    noise_levels = await location_analyzer._estimate_noise_levels(urban_features)
    
    score = await location_analyzer._calculate_ambience_score(env_scores, urban_features, noise_levels)
    
    assert isinstance(score, float)
    assert 0 <= score <= 1

@pytest.mark.asyncio
async def test_generate_recommendations(location_analyzer, mock_overture_data, mock_satellite_data):
    """Test recommendations generation."""
    urban_features = await location_analyzer._analyze_urban_features(mock_overture_data)
    env_scores = await location_analyzer._calculate_environmental_scores(urban_features, mock_satellite_data)
    noise_levels = await location_analyzer._estimate_noise_levels(urban_features)
    ambience_score = await location_analyzer._calculate_ambience_score(env_scores, urban_features, noise_levels)
    
    recommendations = await location_analyzer._generate_recommendations(
        env_scores=env_scores,
        urban_features=urban_features,
        noise_levels=noise_levels,
        ambience_score=ambience_score
    )
    
    assert isinstance(recommendations, list)
    assert all(isinstance(r, str) for r in recommendations)

@pytest.mark.asyncio
async def test_location_analysis_with_invalid_data(location_analyzer):
    """Test location analysis with invalid data."""
    invalid_data = {"name": "Invalid Location"}  # Missing bbox
    insights = await location_analyzer.analyze_location(invalid_data)
    assert "error" in insights
    assert insights["error"] == "Missing bbox data"

@pytest.mark.asyncio
async def test_location_analysis_with_empty_data(location_analyzer):
    """Test location analysis with empty data."""
    empty_data = None
    insights = await location_analyzer.analyze_location(empty_data)
    assert "error" in insights
    assert insights["error"] == "Missing bbox data"

@pytest.mark.asyncio
async def test_memory_storage_integration(location_analyzer, test_location, mock_overture_data, mock_satellite_data):
    """Test memory storage integration."""
    # Mock API calls
    location_analyzer.overture_api.search = AsyncMock(return_value=mock_overture_data)
    location_analyzer.pc_api.search_and_download = AsyncMock(return_value=mock_satellite_data)
    
    # Analyze location
    insights = await location_analyzer.analyze_location(test_location)
    
    # Store data
    stored_key = f"location_analysis_{test_location['id']}"
    memory_data = {
        "key": stored_key,
        "type": "location_analysis",
        "data": insights,
        "timestamp": datetime.now().isoformat(),
        "metadata": {
            "source": "location_analyzer"
        }
    }
    location_analyzer.memory_store.store(memory_data, memory_type="warm")
    
    # Verify storage
    stored_data = location_analyzer.memory_store.retrieve({"key": stored_key}, memory_type="warm")
    
    assert stored_data is not None
    assert "data" in stored_data
    assert "ambience_analysis" in stored_data["data"]

@pytest.mark.asyncio
async def test_analyze_location_with_satellite(location_analyzer, mock_satellite_data, mock_overture_data):
    """Test location analysis with satellite data."""
    test_location = {
        "id": "test-sat-123",
        "bbox": [-122.5, 37.5, -122.0, 38.0]
    }
    
    # Mock API calls
    location_analyzer.overture_api.search = AsyncMock(return_value=mock_overture_data)
    location_analyzer.pc_api.search_and_download = AsyncMock(return_value=mock_satellite_data)
    
    insights = await location_analyzer.analyze_location(test_location)
    analysis = insights["ambience_analysis"]
    
    assert "satellite_metadata" in analysis
    assert analysis["satellite_metadata"]["bands"] == ["B02", "B03", "B04", "B08"]
    assert "cloud_cover" in analysis["satellite_metadata"]

@pytest.mark.asyncio
async def test_environmental_scores_calculation(location_analyzer, mock_satellite_data):
    """Test environmental scores calculation with satellite data."""
    urban_features = {
        "building_characteristics": {"density": 5.0},
        "road_characteristics": {"density": 3.0},
        "amenity_characteristics": {"density": 2.0}
    }
    
    scores = await location_analyzer._calculate_environmental_scores(urban_features, mock_satellite_data)
    assert scores["green_space"] > 0
    assert scores["air_quality"] > 0
    assert scores["urban_density"] > 0

@pytest.mark.asyncio
async def test_environmental_scores_no_satellite_data(location_analyzer):
    """Test environmental scores calculation without satellite data."""
    urban_features = {
        "building_characteristics": {"density": 5.0},
        "road_characteristics": {"density": 3.0},
        "amenity_characteristics": {"density": 2.0}
    }
    
    scores = await location_analyzer._calculate_environmental_scores(urban_features)
    assert scores["green_space"] == 0
    assert scores["air_quality"] == 0
    assert scores["urban_density"] > 0

@pytest.mark.asyncio
async def test_noise_levels_with_urban_features(location_analyzer):
    """Test noise level estimation with urban features."""
    urban_features = {
        "building_characteristics": {"density": 5.0},
        "road_characteristics": {"density": 3.0},
        "amenity_characteristics": {"density": 2.0}
    }
    
    noise_levels = await location_analyzer._estimate_noise_levels(urban_features)
    assert noise_levels["average"] > 0
    assert noise_levels["peak"] >= noise_levels["average"]
    assert noise_levels["variability"] >= 0 