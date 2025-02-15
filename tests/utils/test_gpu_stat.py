import pytest
import torch
from memories.utils.processors.gpu_stat import check_gpu_memory
from memories.models.llama.llama import llama_vision_extraction

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

@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
def test_gpu_memory_check():
    """Test GPU memory checking functionality"""
    try:
        check_gpu_memory()
        assert torch.cuda.is_available()
        assert torch.cuda.get_device_properties(0).total_memory > 0
    except Exception as e:
        pytest.fail(f"GPU memory check failed: {str(e)}")

@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
def test_gpu_memory_allocation():
    """Test GPU memory allocation and deallocation"""
    if torch.cuda.is_available():
        try:
            # Record initial memory
            initial_memory = torch.cuda.memory_allocated()
            
            # Allocate a large tensor
            tensor = torch.zeros(1000, 1000, device='cuda')
            
            # Check memory increased
            assert torch.cuda.memory_allocated() > initial_memory
            
            # Free memory
            del tensor
            torch.cuda.empty_cache()
            
            # Check memory decreased
            final_memory = torch.cuda.memory_allocated()
            assert final_memory <= initial_memory
            
        except Exception as e:
            pytest.fail(f"GPU memory allocation test failed: {str(e)}")

@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
def test_llama_vision_extraction(sample_image_path):
    """Test Llama vision extraction on GPU"""
    try:
        prompt = "Describe this image"
        result = llama_vision_extraction(sample_image_path, prompt)
        
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
        
    except Exception as e:
        pytest.fail(f"Llama vision extraction test failed: {str(e)}")

@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
def test_gpu_out_of_memory_handling():
    """Test handling of GPU out of memory situations"""
    if torch.cuda.is_available():
        try:
            # Try to allocate more memory than available
            with pytest.raises(RuntimeError) as excinfo:
                # This should raise an out of memory error
                tensor = torch.zeros(1000000, 1000000, device='cuda')
            
            assert "out of memory" in str(excinfo.value).lower()
            
        except Exception as e:
            if "out of memory" not in str(e).lower():
                pytest.fail(f"GPU out of memory test failed unexpectedly: {str(e)}")

@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
def test_gpu_error_recovery():
    """Test recovery from GPU errors"""
    if torch.cuda.is_available():
        try:
            # Cause an error
            try:
                invalid_tensor = torch.cuda.FloatTensor([1, 2, 3])[10]
            except IndexError:
                pass
            
            # Check we can still use GPU
            tensor = torch.zeros(10, 10, device='cuda')
            assert tensor.device.type == 'cuda'
            
            # Clean up
            del tensor
            torch.cuda.empty_cache()
            
        except Exception as e:
            pytest.fail(f"GPU error recovery test failed: {str(e)}") 