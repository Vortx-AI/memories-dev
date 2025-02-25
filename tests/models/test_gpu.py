"""Tests for GPU functionality across models."""

import pytest
import torch
import gc
from unittest.mock import Mock, patch
from memories.models.load_model import LoadModel
from memories.models.base_model import BaseModel
from memories.utils.processors.gpu_stat import check_gpu_memory

@pytest.fixture(autouse=True)
def cleanup_gpu():
    """Cleanup GPU memory after each test."""
    yield
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        gc.collect()

@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
def test_gpu_memory_tracking():
    """Test GPU memory tracking functionality."""
    memory_stats = check_gpu_memory()
    if memory_stats:
        assert 'total' in memory_stats
        assert 'free' in memory_stats
        assert 'used' in memory_stats
        assert memory_stats['total'] > 0
        assert memory_stats['free'] >= 0
        assert memory_stats['used'] >= 0
        assert memory_stats['total'] >= memory_stats['used']

@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
def test_model_gpu_memory_management():
    """Test model GPU memory management."""
    initial_memory = torch.cuda.memory_allocated() if torch.cuda.is_available() else 0
    
    with patch("memories.models.load_model.BaseModel") as mock_base_model_class:
        mock_base_model = Mock()
        mock_base_model_class.get_instance.return_value = mock_base_model
        mock_base_model.initialize_model.return_value = True
        
        model = LoadModel(
            model_provider="deepseek-ai",
            deployment_type="local",
            model_name="deepseek-coder-small",
            use_gpu=True
        )
        
        # Simulate model loading
        mock_tensor = torch.zeros(1000, 1000).cuda()
        mock_base_model.model = mock_tensor
        
        # Check memory increased
        assert torch.cuda.memory_allocated() > initial_memory
        
        # Cleanup
        model.cleanup()
        torch.cuda.empty_cache()
        gc.collect()
        
        # Check memory released
        final_memory = torch.cuda.memory_allocated()
        assert final_memory <= initial_memory

@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
def test_multi_gpu_support():
    """Test multi-GPU support if available."""
    if torch.cuda.device_count() > 1:
        with patch("memories.models.load_model.BaseModel") as mock_base_model_class:
            mock_base_model = Mock()
            mock_base_model_class.get_instance.return_value = mock_base_model
            mock_base_model.initialize_model.return_value = True
            
            # Test on first GPU
            model1 = LoadModel(
                model_provider="deepseek-ai",
                deployment_type="local",
                model_name="deepseek-coder-small",
                use_gpu=True,
                device="cuda:0"
            )
            assert model1.device == "cuda:0"
            
            # Test on second GPU
            model2 = LoadModel(
                model_provider="deepseek-ai",
                deployment_type="local",
                model_name="deepseek-coder-small",
                use_gpu=True,
                device="cuda:1"
            )
            assert model2.device == "cuda:1"
            
            # Cleanup
            model1.cleanup()
            model2.cleanup()

@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
def test_gpu_error_handling():
    """Test GPU error handling."""
    with patch("memories.models.load_model.BaseModel") as mock_base_model_class:
        mock_base_model = Mock()
        mock_base_model_class.get_instance.return_value = mock_base_model
        mock_base_model.initialize_model.side_effect = RuntimeError("CUDA out of memory")
        
        with pytest.raises(RuntimeError) as exc_info:
            model = LoadModel(
                model_provider="deepseek-ai",
                deployment_type="local",
                model_name="deepseek-coder-small",
                use_gpu=True
            )
            model.get_response("Test prompt")
        
        assert "CUDA out of memory" in str(exc_info.value)

@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
def test_gpu_performance():
    """Test GPU vs CPU performance comparison."""
    with patch("memories.models.load_model.BaseModel") as mock_base_model_class:
        mock_base_model = Mock()
        mock_base_model_class.get_instance.return_value = mock_base_model
        mock_base_model.initialize_model.return_value = True
        
        # Create large tensor for testing
        test_tensor = torch.randn(1000, 1000)
        
        # GPU computation
        start_time = torch.cuda.Event(enable_timing=True)
        end_time = torch.cuda.Event(enable_timing=True)
        
        start_time.record()
        gpu_tensor = test_tensor.cuda()
        gpu_result = torch.matmul(gpu_tensor, gpu_tensor)
        end_time.record()
        
        torch.cuda.synchronize()
        gpu_time = start_time.elapsed_time(end_time)
        
        # CPU computation
        cpu_start = torch.cuda.Event(enable_timing=True)
        cpu_end = torch.cuda.Event(enable_timing=True)
        
        cpu_start.record()
        cpu_result = torch.matmul(test_tensor, test_tensor)
        cpu_end.record()
        
        torch.cuda.synchronize()
        cpu_time = cpu_start.elapsed_time(cpu_end)
        
        # GPU should be faster
        assert gpu_time < cpu_time 