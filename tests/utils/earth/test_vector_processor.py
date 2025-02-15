import pytest
import mercantile
import geopandas as gpd
from shapely.geometry import box
from memories.utils.earth.vector_processor import VectorTileProcessor, VectorProcessor
from memories.utils.types import Bounds

@pytest.fixture
def sample_bounds():
    """Create sample bounds for testing"""
    return mercantile.LngLatBbox(west=-122.4194, south=37.7749, east=-122.4093, north=37.7850)

@pytest.fixture
def sample_layers():
    return ["buildings", "roads"]

@pytest.fixture
def vector_processor(sample_bounds, sample_layers):
    return VectorTileProcessor(bounds=sample_bounds, layers=sample_layers)

def test_vector_processor_init(vector_processor, sample_bounds, sample_layers):
    assert vector_processor.bounds == sample_bounds
    assert vector_processor.layers == sample_layers

def test_available_layers(vector_processor, sample_layers):
    assert vector_processor.available_layers == sample_layers

@pytest.mark.asyncio
async def test_process_tile():
    bounds = mercantile.LngLatBbox(west=-122.4194, south=37.7749, east=-122.4093, north=37.7850)
    processor = VectorTileProcessor(bounds=bounds, layers=["buildings"])
    tile = mercantile.Tile(z=15, x=5242, y=12663)
    
    result = await processor.process_tile(tile)
    assert result is not None

def test_vector_processor_initialization(vector_processor):
    """Test that VectorTileProcessor initializes correctly"""
    assert vector_processor is not None
    assert isinstance(vector_processor._styles, dict)
    assert isinstance(vector_processor._transformations, dict)
    assert isinstance(vector_processor._filters, dict)
    assert vector_processor.db is not None

def test_available_transformations(vector_processor):
    """Test that available_transformations returns correct list"""
    transformations = vector_processor.available_transformations
    assert isinstance(transformations, list)
    assert 'reproject_web_mercator' in transformations
    assert 'centroid' in transformations
    assert 'boundary' in transformations

def test_available_filters(vector_processor):
    """Test that available_filters returns correct list"""
    filters = vector_processor.available_filters
    assert isinstance(filters, list)
    assert 'spatial:simplify' in filters
    assert 'spatial:buffer' in filters
    assert 'attribute' in filters

def test_process_tile(vector_processor, sample_bounds):
    """Test processing a tile"""
    result = vector_processor.process_tile(sample_bounds)
    assert result is not None
    assert isinstance(result, gpd.GeoDataFrame)

def test_apply_filter(vector_processor, sample_bounds):
    """Test _apply_filter method"""
    # Create sample GeoDataFrame
    data = gpd.GeoDataFrame(
        {
            'geometry': [box(0, 0, 1, 1)],
            'value': [10]
        },
        crs='EPSG:4326'
    )
    
    # Test spatial filter
    result = vector_processor._apply_filter(data, sample_bounds, 'spatial:simplify')
    assert isinstance(result, gpd.GeoSeries)
    
    # Test attribute filter
    result = vector_processor._apply_filter(data, sample_bounds, 'value > 5')
    assert isinstance(result, gpd.GeoDataFrame)
    assert len(result) == 1
    
    result = vector_processor._apply_filter(data, sample_bounds, 'value < 5')
    assert isinstance(result, gpd.GeoDataFrame)
    assert len(result) == 0

def test_apply_transformation(vector_processor, sample_bounds):
    """Test _apply_transformation method"""
    # Create sample GeoDataFrame
    data = gpd.GeoDataFrame(
        {
            'geometry': [box(0, 0, 1, 1)],
            'value': [10]
        },
        crs='EPSG:4326'
    )
    
    # Test reproject transformation
    result = vector_processor._apply_transformation(data, sample_bounds, 'reproject_web_mercator')
    assert result.crs == 'EPSG:3857'
    
    # Test centroid transformation
    result = vector_processor._apply_transformation(data, sample_bounds, 'centroid')
    assert all(result.geom_type == 'Point')
    
    # Test boundary transformation
    result = vector_processor._apply_transformation(data, sample_bounds, 'boundary')
    assert all(result.geom_type == 'LineString')

@pytest.mark.gpu
@pytest.mark.earth
class TestVectorProcessor:
    def test_vector_processor_initialization(self, vector_processor):
        """Test that VectorProcessor initializes correctly"""
        assert vector_processor is not None
        assert vector_processor.db is not None

    def test_available_transformations(self, vector_processor):
        """Test that available_transformations returns correct list"""
        transformations = vector_processor.available_transformations
        assert isinstance(transformations, list)
        assert len(transformations) > 0
        assert 'boundary' in transformations

    def test_process_feature(self, vector_processor, sample_feature):
        """Test processing a feature"""
        result = vector_processor.process_feature(sample_feature)
        assert result is not None
        assert 'geometry' in result

    def test_apply_transformation(self, vector_processor, sample_feature):
        """Test applying a transformation"""
        result = vector_processor.apply_transformation(sample_feature, 'boundary')
        assert result is not None
        assert 'geometry' in result 