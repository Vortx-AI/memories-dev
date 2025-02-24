"""Tests for traffic analyzer's Overture API integration."""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

from memories import MemoryStore, Config
from memories.data_acquisition import DataManager
from memories.data_acquisition.sources.overture_api import OvertureAPI
from examples.traffic_analyzer import TrafficAnalyzer, simulate_road_segment

@pytest.fixture
def mock_overture_data():
    """Mock Overture data for testing."""
    return {
        'transportation': [
            {
                'id': 'road_123',
                'road_type': 'motorway',
                'geometry': {
                    'type': 'LineString',
                    'coordinates': [[-122.4, 37.8], [-122.3, 37.9]]
                },
                'properties': {
                    'lanes': 4,
                    'surface': 'asphalt'
                }
            },
            {
                'id': 'road_456',
                'road_type': 'arterial',
                'geometry': {
                    'type': 'LineString',
                    'coordinates': [[-122.41, 37.81], [-122.31, 37.91]]
                },
                'properties': {
                    'lanes': 2,
                    'surface': 'concrete'
                }
            }
        ],
        'buildings': [
            {
                'id': 'building_1',
                'building_type': 'commercial',
                'height': 50.0
            }
        ],
        'places': [
            {
                'id': 'place_1',
                'place_type': 'parking',
                'name': 'Downtown Parking'
            }
        ]
    }

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return Config(
        storage_path="./test_traffic_data",
        hot_memory_size=10,
        warm_memory_size=20,
        cold_memory_size=50
    )

@pytest.fixture
def mock_memory_store(mock_config):
    """Mock memory store for testing."""
    return MemoryStore(mock_config)

@pytest.fixture
def mock_data_manager():
    """Mock data manager for testing."""
    return Mock(spec=DataManager)

@pytest.mark.asyncio
async def test_traffic_analyzer_initialization(mock_memory_store, mock_data_manager):
    """Test TrafficAnalyzer initialization."""
    analyzer = TrafficAnalyzer(mock_memory_store, mock_data_manager)
    assert analyzer.memory_store == mock_memory_store
    assert analyzer.data_manager == mock_data_manager
    assert isinstance(analyzer.overture_api, OvertureAPI)

@pytest.mark.asyncio
async def test_analyze_traffic_with_valid_data(mock_memory_store, mock_data_manager, mock_overture_data):
    """Test analyze_traffic with valid data."""
    analyzer = TrafficAnalyzer(mock_memory_store, mock_data_manager)
    
    # Mock the Overture API methods
    analyzer.overture_api.download_data = Mock(return_value={'transportation': True})
    analyzer.overture_api.search = Mock(return_value=mock_overture_data)
    
    # Create test road data
    road_data = simulate_road_segment()
    road_data['id'] = 'road_123'  # Match with mock data
    
    # Run analysis
    insights = await analyzer.analyze_traffic(road_data)
    
    # Verify API calls
    analyzer.overture_api.download_data.assert_called_once_with(road_data['bbox'])
    analyzer.overture_api.search.assert_called_once_with(road_data['bbox'])
    
    # Verify results
    assert insights['road_id'] == 'road_123'
    assert 'timestamp' in insights
    assert 'traffic_metrics' in insights
    assert 'road_conditions' in insights
    assert 'recommendations' in insights

@pytest.mark.asyncio
async def test_analyze_traffic_with_missing_bbox(mock_memory_store, mock_data_manager):
    """Test analyze_traffic with missing bbox."""
    analyzer = TrafficAnalyzer(mock_memory_store, mock_data_manager)
    road_data = simulate_road_segment()
    road_data.pop('bbox')
    
    with pytest.raises(ValueError, match="Missing bbox data"):
        await analyzer.analyze_traffic(road_data)

@pytest.mark.asyncio
async def test_analyze_traffic_with_download_failure(mock_memory_store, mock_data_manager):
    """Test analyze_traffic when download fails."""
    analyzer = TrafficAnalyzer(mock_memory_store, mock_data_manager)
    
    # Mock download failure
    analyzer.overture_api.download_data = Mock(return_value={'transportation': False})
    
    road_data = simulate_road_segment()
    
    with pytest.raises(ValueError, match="Failed to download Overture data"):
        await analyzer.analyze_traffic(road_data)

@pytest.mark.asyncio
async def test_analyze_traffic_with_empty_overture_data(mock_memory_store, mock_data_manager):
    """Test analyze_traffic with empty Overture data."""
    analyzer = TrafficAnalyzer(mock_memory_store, mock_data_manager)
    
    # Mock successful download but empty data
    analyzer.overture_api.download_data = Mock(return_value={'transportation': True})
    analyzer.overture_api.search = Mock(return_value={'transportation': []})
    
    road_data = simulate_road_segment()
    insights = await analyzer.analyze_traffic(road_data)
    
    assert insights['traffic_metrics']['congestion_level'] == 0.0
    assert insights['road_conditions']['maintenance_status'] == 'unknown'
    assert "No transportation data available for analysis" in insights['recommendations']

@pytest.mark.asyncio
async def test_extract_road_features(mock_memory_store, mock_data_manager, mock_overture_data):
    """Test _extract_road_features method."""
    analyzer = TrafficAnalyzer(mock_memory_store, mock_data_manager)
    
    features = analyzer._extract_road_features(mock_overture_data['transportation'])
    
    assert features is not None
    assert 'surface_condition' in features
    assert 'weather_impact' in features
    assert 'visibility' in features
    assert 'condition_score' in features
    assert 'road_types' in features
    assert len(features['road_types']) == 2  # motorway and arterial
    assert features['complexity_score'] > 0

@pytest.mark.asyncio
async def test_analyze_traffic_data_processing(mock_memory_store, mock_data_manager, mock_overture_data):
    """Test the complete traffic data processing pipeline."""
    analyzer = TrafficAnalyzer(mock_memory_store, mock_data_manager)
    
    road_segment = simulate_road_segment()
    road_segment['id'] = 'road_123'
    
    insights = await analyzer._analyze_traffic_data(road_segment, mock_overture_data)
    
    assert insights['traffic_metrics'] is not None
    assert insights['road_conditions'] is not None
    assert insights['congestion_patterns'] is not None
    assert insights['hazards'] is not None
    assert insights['predictions'] is not None
    assert insights['recommendations'] is not None
    
    # Verify road type extraction
    road_conditions = insights['road_conditions']
    assert road_conditions['maintenance_status'] in ['good', 'fair', 'needs_inspection']
    assert isinstance(road_conditions['surface_quality'], float)
    assert isinstance(road_conditions['risk_factors'], list) 