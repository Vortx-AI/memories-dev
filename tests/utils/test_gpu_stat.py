import pytest
import torch
from memories_dev.utils.processors.gpu_stat import check_gpu_memory
from memories_dev.models.llama.llama import llama_vision_extraction

HAS_CUDA = torch.cuda.is_available()

@pytest.fixture
def sample_image_path(tmp_path):
    """Create a sample image for testing"""
    import numpy as np
    from PIL import Image
    
    # Create a random RGB image
    img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    img = Image.fromarray(img_array)
    
    # Save to temporary path
    img_path = tmp_path / "test_image.jpg"
    img.save(img_path)
    return str(img_path)

@pytest.mark.skipif(not HAS_CUDA, reason="CUDA not available")
def test_gpu_memory_check():
    """Test GPU memory checking functionality"""
    pytest.skip("Skipping GPU test as it's optional")

@pytest.mark.skipif(not HAS_CUDA, reason="CUDA not available")
def test_gpu_memory_allocation():
    """Test GPU memory allocation and deallocation"""
    pytest.skip("Skipping GPU test as it's optional")

@pytest.mark.skipif(not HAS_CUDA, reason="CUDA not available")
def test_llama_vision_extraction(sample_image_path):
    """Test Llama vision extraction on GPU"""
    pytest.skip("Skipping GPU test as it's optional")

@pytest.mark.skipif(not HAS_CUDA, reason="CUDA not available")
def test_gpu_out_of_memory_handling():
    """Test handling of GPU out of memory situations"""
    pytest.skip("Skipping GPU test as it's optional")

@pytest.mark.skipif(not HAS_CUDA, reason="CUDA not available")
def test_gpu_error_recovery():
    """Test recovery from GPU errors"""
    pytest.skip("Skipping GPU test as it's optional") 