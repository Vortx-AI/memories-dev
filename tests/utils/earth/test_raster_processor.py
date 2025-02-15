import pytest
import numpy as np
import rasterio
from rasterio.io import MemoryFile
import mercantile
from shapely.geometry import box
from memories.utils.earth.raster_processor import RasterTileProcessor

@pytest.fixture
def sample_raster_data():
    """Create sample raster data for testing"""
    data = np.random.randint(0, 255, (3, 256, 256), dtype=np.uint8)
    transform = rasterio.transform.from_bounds(
        -122.4194, 37.7749, -122.4093, 37.7850, 256, 256
    )
    return data, transform

@pytest.fixture
def raster_processor():
    """Create RasterTileProcessor instance"""
    return RasterTileProcessor()

def test_raster_processor_initialization(raster_processor):
    """Test that RasterTileProcessor initializes correctly"""
    assert raster_processor is not None
    assert raster_processor.styles == {}  # Empty since no style files exist yet
    assert isinstance(raster_processor.transformations, dict)
    assert isinstance(raster_processor.filters, dict)
    assert raster_processor.db is not None

def test_available_transformations(raster_processor):
    """Test that available_transformations returns correct list"""
    transformations = raster_processor.available_transformations()
    assert isinstance(transformations, list)
    assert 'normalize' in transformations
    assert 'hillshade' in transformations
    assert 'resample:mean' in transformations

def test_available_filters(raster_processor):
    """Test that available_filters returns correct list"""
    filters = raster_processor.available_filters()
    assert isinstance(filters, list)
    assert 'cloud_mask' in filters
    assert 'nodata_mask' in filters
    assert 'threshold' in filters

@pytest.mark.asyncio
async def test_process_tile(raster_processor, sample_raster_data):
    """Test process_tile method"""
    data, transform = sample_raster_data
    bounds = mercantile.Bounds(-122.4194, 37.7749, -122.4093, 37.7850)
    
    # Create temporary raster file
    with MemoryFile() as memfile:
        with memfile.open(
            driver='GTiff',
            height=256,
            width=256,
            count=3,
            dtype=data.dtype,
            crs='EPSG:4326',
            transform=transform
        ) as dataset:
            dataset.write(data)
        
        # Process tile
        result = await raster_processor.process_tile(
            bounds=bounds,
            format='png',
            style=None
        )
        
        assert result is not None
        assert isinstance(result, bytes)

def test_apply_filter(raster_processor, sample_raster_data):
    """Test _apply_filter method"""
    data, _ = sample_raster_data
    
    # Test cloud mask filter
    filtered = raster_processor._apply_filter(data, 'cloud_mask')
    assert filtered.shape == data.shape
    
    # Test threshold filter
    filtered = raster_processor._apply_filter(data, 'threshold:128')
    assert filtered.shape == data.shape

def test_apply_transformation(raster_processor, sample_raster_data):
    """Test _apply_transformation method"""
    data, _ = sample_raster_data
    
    # Test normalize transformation
    transformed = raster_processor._apply_transformation(data, 'normalize')
    assert transformed.shape == data.shape
    assert transformed.min() >= 0
    assert transformed.max() <= 1
    
    # Test hillshade transformation
    transformed = raster_processor._apply_transformation(data, 'hillshade')
    assert transformed.shape == data.shape

def test_calculate_hillshade(raster_processor, sample_raster_data):
    """Test _calculate_hillshade method"""
    data, _ = sample_raster_data
    
    hillshade = raster_processor._calculate_hillshade(
        data[0],  # Use first band
        azimuth=315.0,
        altitude=45.0
    )
    
    assert hillshade.shape == data[0].shape
    assert not np.isnan(hillshade).any()

def test_apply_style(raster_processor, sample_raster_data):
    """Test _apply_style method"""
    data, _ = sample_raster_data
    
    # Test with default style (should return unchanged)
    styled = raster_processor._apply_style(data, 'default')
    assert styled.shape == data.shape

def test_to_format(raster_processor, sample_raster_data):
    """Test _to_format method"""
    data, _ = sample_raster_data
    
    # Test PNG format
    png_bytes = raster_processor._to_format(data, 'png')
    assert isinstance(png_bytes, bytes)
    assert len(png_bytes) > 0 