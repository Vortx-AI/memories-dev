import pytest
import numpy as np
import cupy as cp
import torch
from memories.utils.processors.comp import calculate_ndvi, transformer_process

@pytest.fixture
def sample_image_data():
    """Create sample image data for testing"""
    # Create random image data with red and NIR bands
    height, width = 256, 256
    red_band = np.random.randint(0, 255, (height, width), dtype=np.uint8)
    nir_band = np.random.randint(0, 255, (height, width), dtype=np.uint8)
    
    # Stack bands to create 3D array
    image = np.stack([red_band, nir_band, np.zeros_like(red_band)], axis=-1)
    return image

@pytest.mark.skipif(not cp.is_available(), reason="CuPy not available")
def test_calculate_ndvi(sample_image_data):
    """Test NDVI calculation"""
    try:
        # Calculate NDVI
        ndvi = calculate_ndvi(sample_image_data)
        
        # Verify output
        assert isinstance(ndvi, np.ndarray)
        assert ndvi.shape == (256, 256)
        assert ndvi.dtype == np.uint8
        assert np.all(ndvi >= 0)
        assert np.all(ndvi <= 255)
        
    except Exception as e:
        pytest.fail(f"NDVI calculation test failed: {str(e)}")

@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
def test_transformer_process(sample_image_data):
    """Test transformer-based image processing"""
    try:
        # Convert to CuPy array
        image_cp = cp.asarray(sample_image_data)
        
        # Process image
        output = transformer_process(image_cp)
        
        # Verify output
        assert output is not None
        assert isinstance(output, np.ndarray)
        assert len(output.shape) == 2  # Should be a 2D array
        assert not np.any(np.isnan(output))
        
    except Exception as e:
        pytest.fail(f"Transformer process test failed: {str(e)}")

def test_ndvi_edge_cases(sample_image_data):
    """Test NDVI calculation with edge cases"""
    try:
        # Test with zero values
        zero_image = np.zeros_like(sample_image_data)
        ndvi_zero = calculate_ndvi(zero_image)
        assert not np.any(np.isnan(ndvi_zero))
        
        # Test with maximum values
        max_image = np.full_like(sample_image_data, 255)
        ndvi_max = calculate_ndvi(max_image)
        assert not np.any(np.isnan(ndvi_max))
        
    except Exception as e:
        pytest.fail(f"NDVI edge cases test failed: {str(e)}")

@pytest.mark.skipif(not cp.is_available(), reason="CuPy not available")
def test_memory_cleanup():
    """Test proper memory cleanup after processing"""
    try:
        # Record initial memory usage
        initial_memory = cp.get_default_memory_pool().used_bytes()
        
        # Create and process large array
        large_image = np.random.randint(0, 255, (1024, 1024, 3), dtype=np.uint8)
        _ = calculate_ndvi(large_image)
        
        # Force memory cleanup
        cp.get_default_memory_pool().free_all_blocks()
        
        # Check memory usage
        final_memory = cp.get_default_memory_pool().used_bytes()
        assert final_memory <= initial_memory
        
    except Exception as e:
        pytest.fail(f"Memory cleanup test failed: {str(e)}")

@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
def test_transformer_memory_cleanup():
    """Test memory cleanup after transformer processing"""
    try:
        # Record initial GPU memory
        initial_memory = torch.cuda.memory_allocated()
        
        # Process image
        image = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
        image_cp = cp.asarray(image)
        _ = transformer_process(image_cp)
        
        # Force memory cleanup
        torch.cuda.empty_cache()
        
        # Check memory
        final_memory = torch.cuda.memory_allocated()
        assert final_memory <= initial_memory
        
    except Exception as e:
        pytest.fail(f"Transformer memory cleanup test failed: {str(e)}")

def test_input_validation():
    """Test input validation for processing functions"""
    try:
        # Test with invalid shapes
        invalid_image = np.random.randint(0, 255, (256, 256), dtype=np.uint8)  # Missing channel dimension
        
        with pytest.raises(Exception):
            calculate_ndvi(invalid_image)
            
        # Test with invalid types
        invalid_type_image = [[1, 2, 3], [4, 5, 6]]  # Not a numpy array
        
        with pytest.raises(Exception):
            calculate_ndvi(invalid_type_image)
            
    except Exception as e:
        pytest.fail(f"Input validation test failed: {str(e)}")

@pytest.mark.skipif(not cp.is_available(), reason="CuPy not available")
def test_large_image_processing():
    """Test processing of large images"""
    try:
        # Create large image
        large_image = np.random.randint(0, 255, (2048, 2048, 3), dtype=np.uint8)
        
        # Process image
        result = calculate_ndvi(large_image)
        
        # Verify output
        assert result.shape == (2048, 2048)
        assert not np.any(np.isnan(result))
        
    except Exception as e:
        pytest.fail(f"Large image processing test failed: {str(e)}") 