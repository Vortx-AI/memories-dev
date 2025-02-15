import pytest
import numpy as np
import rasterio
from rasterio.io import MemoryFile
import mercantile
from shapely.geometry import box
from memories.utils.earth.raster_processor import RasterTileProcessor
from memories.utils.types import Bounds

@pytest.fixture
def sample_raster_data():
    """Create sample raster data for testing"""
    data = np.random.randint(0, 255, (3, 256, 256), dtype=np.uint8)
    transform = rasterio.transform.from_bounds(
        -122.4194, 37.7749, -122.4093, 37.7850, 256, 256
    )
    return data, transform

@pytest.fixture
def sample_bounds():
    """Create sample bounds for testing"""
    return mercantile.LngLatBbox(west=-122.4194, south=37.7749, east=-122.4093, north=37.7850)

@pytest.fixture
def raster_processor():
    """Create RasterTileProcessor instance"""
    return RasterTileProcessor()

@pytest.mark.gpu
@pytest.mark.earth
class TestRasterProcessor:
    def test_raster_processor_initialization(self, raster_processor):
        """Test that RasterTileProcessor initializes correctly"""
        assert raster_processor is not None
        assert isinstance(raster_processor._styles, dict)
        assert isinstance(raster_processor._transformations, dict)
        assert isinstance(raster_processor._filters, dict)
        assert raster_processor.db is not None

    def test_available_transformations(self, raster_processor):
        """Test that available_transformations returns correct list"""
        transformations = raster_processor.available_transformations
        assert isinstance(transformations, list)
        assert 'flip_vertical' in transformations
        assert 'flip_horizontal' in transformations
        assert 'rotate_90' in transformations

    def test_available_filters(self, raster_processor):
        """Test that available_filters returns correct list"""
        filters = raster_processor.available_filters
        assert isinstance(filters, list)
        assert 'median' in filters
        assert 'mean' in filters
        assert 'gaussian' in filters

    def test_process_tile(self, raster_processor, sample_bounds):
        """Test processing a tile"""
        result = raster_processor.process_tile(sample_bounds)
        assert result is not None
        assert isinstance(result, np.ndarray)
        assert result.shape == (256, 256)  # Standard tile size

    def test_apply_filter(self, raster_processor, sample_bounds):
        """Test applying a filter"""
        data = np.random.rand(256, 256)
        filtered = raster_processor._apply_filter(data, sample_bounds, 'median')
        assert filtered is not None
        assert isinstance(filtered, np.ndarray)
        assert filtered.shape == (256, 256)

    def test_apply_transformation(self, raster_processor, sample_bounds):
        """Test applying a transformation"""
        data = np.random.rand(256, 256)
        transformed = raster_processor._apply_transformation(data, sample_bounds, 'flip_vertical')
        assert transformed is not None
        assert isinstance(transformed, np.ndarray)
        assert transformed.shape == (256, 256)

    def test_calculate_hillshade(self, raster_processor, sample_bounds):
        """Test calculating hillshade"""
        data = np.random.rand(256, 256)
        hillshade = raster_processor._calculate_hillshade(data, sample_bounds)
        assert hillshade is not None
        assert isinstance(hillshade, np.ndarray)
        assert hillshade.shape == (256, 256)

    def test_to_format(self, raster_processor, sample_bounds):
        """Test converting to a specific format"""
        data = np.random.rand(256, 256)
        # Convert to xarray DataArray
        import xarray as xr
        data = xr.DataArray(data, dims=('y', 'x'))
        formatted = raster_processor._to_format(data, sample_bounds, 'png')
        assert formatted is not None
        assert isinstance(formatted, bytes)

    def test_apply_style(self, raster_processor, sample_raster_data):
        """Test _apply_style method"""
        data, _ = sample_raster_data
        # Convert to xarray DataArray
        import xarray as xr
        data = xr.DataArray(data, dims=('band', 'y', 'x'))
        styled = raster_processor._apply_style(data, 'default')
        assert styled is not None
        assert isinstance(styled, xr.DataArray) 