"""Tests for GPU functionality across models."""

import pytest
import torch
import gc
import numpy as np
from unittest.mock import Mock, patch
from memories.models.load_model import LoadModel
from memories.models.base_model import BaseModel
from memories.utils.earth.processors import gpu_stat
from memories.utils.processors.gpu_stat import check_gpu_memory, allocate_gpu_memory

@pytest.fixture(autouse=True)
def cleanup_gpu():
    """Cleanup GPU memory after each test."""
    yield
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        gc.collect()

@pytest.fixture
def memory_manager(tmp_path):
    """Create a memory manager instance for testing."""
    config = {
        'memory': {
            'base_path': str(tmp_path),
            'red_hot': {
                'path': str(tmp_path / 'red_hot'),
                'max_size': 1000000,
                'vector_dim': 384,
                'gpu_id': 0,
                'force_cpu': False,  # Allow GPU for these tests
                'index_type': 'Flat'
            }
        }
    }
    from memories.core.memory_manager import MemoryManager
    manager = MemoryManager(config=config)
    yield manager
    manager.cleanup()

def test_gpu_memory_tracking():
    """Test GPU memory tracking functionality."""
    if not torch.cuda.is_available():
        pytest.skip("CUDA not available")
    
    # Check initial memory state
    total, used, free = check_gpu_memory()
    assert total > 0
    assert used >= 0
    assert free > 0
    
    # Allocate memory
    size_mb = 100
    tensor = allocate_gpu_memory(size_mb)
    
    # Check memory increased
    _, new_used, _ = check_gpu_memory()
    assert new_used > used
    
    # Free memory
    del tensor
    torch.cuda.empty_cache()

def test_model_gpu_memory_management(memory_manager):
    """Test model GPU memory management."""
    if not torch.cuda.is_available():
        pytest.skip("CUDA not available")
    
    # Get initial memory state
    _, initial_used, _ = check_gpu_memory()
    
    # Create and store vectors
    num_vectors = 1000
    dim = memory_manager.config['memory']['red_hot']['vector_dim']
    vectors = np.random.rand(num_vectors, dim).astype(np.float32)
    
    # Store vectors in batches to test memory management
    batch_size = 100
    for i in range(0, num_vectors, batch_size):
        batch = vectors[i:i+batch_size]
        for j, vec in enumerate(batch):
            memory_manager.store(
                f'test_key_{i+j}',
                vec,
                tier='red_hot',
                metadata={'batch': i//batch_size, 'index': j}
            )
    
    # Check memory usage after storage
    _, after_storage_used, _ = check_gpu_memory()
    assert after_storage_used > initial_used
    
    # Perform searches to test memory during inference
    query = np.random.rand(dim).astype(np.float32)
    for _ in range(10):
        results = memory_manager.search_vectors(query, k=5)
        assert len(results) == 5
    
    # Check memory during search operations
    _, during_search_used, _ = check_gpu_memory()
    assert during_search_used >= after_storage_used
    
    # Clear memory
    memory_manager.clear(tier='red_hot')
    torch.cuda.empty_cache()
    
    # Check memory returned to near initial state
    _, final_used, _ = check_gpu_memory()
    assert abs(final_used - initial_used) < 100  # Allow some overhead

@pytest.mark.gpu
def test_gpu_memory_limits():
    """Test GPU memory limit handling."""
    if not torch.cuda.is_available():
        pytest.skip("CUDA not available")
    
    total, used, _ = check_gpu_memory()
    available = total - used
    
    # Try to allocate slightly less than available memory
    safe_size = int(available * 0.9)  # 90% of available memory
    tensor = allocate_gpu_memory(safe_size)
    assert tensor is not None
    
    # Try to allocate more than available memory
    with pytest.raises(RuntimeError):
        overflow_tensor = allocate_gpu_memory(total * 2)
    
    # Cleanup
    del tensor
    torch.cuda.empty_cache()

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