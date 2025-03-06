"""Tests for GPU utility functions."""

import pytest
import torch
import gc
from unittest.mock import Mock, patch
from memories.utils.earth.processors import gpu_stat
from memories.utils.gpu_utils import check_gpu_memory, allocate_gpu_memory
import numpy as np

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

def test_check_gpu_memory():
    """Test GPU memory checking functionality."""
    if not torch.cuda.is_available():
        pytest.skip("CUDA not available")
    
    # Check initial memory state
    total, used, free = check_gpu_memory()
    assert isinstance(total, int)
    assert isinstance(used, int)
    assert isinstance(free, int)
    assert total > 0
    assert used >= 0
    assert free > 0
    assert total >= used + free

def test_gpu_memory_allocation():
    """Test GPU memory allocation and deallocation."""
    if not torch.cuda.is_available():
        pytest.skip("CUDA not available")
    
    # Get initial memory state
    _, initial_used, _ = check_gpu_memory()
    
    # Allocate memory
    size_mb = 100
    tensor = allocate_gpu_memory(size_mb)
    
    # Check memory increased
    _, new_used, _ = check_gpu_memory()
    assert new_used > initial_used
    
    # Free memory
    del tensor
    torch.cuda.empty_cache()
    
    # Check memory returned to initial state
    _, final_used, _ = check_gpu_memory()
    assert abs(final_used - initial_used) < size_mb * 1.1  # Allow some overhead

def test_gpu_memory_with_red_hot(memory_manager):
    """Test GPU memory usage with RedHotMemory."""
    if not torch.cuda.is_available():
        pytest.skip("CUDA not available")
    
    # Get initial memory state
    _, initial_used, _ = check_gpu_memory()
    
    # Create and store vectors
    num_vectors = 1000
    dim = memory_manager.config['memory']['red_hot']['vector_dim']
    vectors = np.random.rand(num_vectors, dim).astype(np.float32)
    
    for i in range(num_vectors):
        memory_manager.store(
            f'test_key_{i}',
            vectors[i],
            tier='red_hot',
            metadata={'index': i}
        )
    
    # Check memory increased
    _, new_used, _ = check_gpu_memory()
    assert new_used > initial_used
    
    # Search vectors
    query = np.random.rand(dim).astype(np.float32)
    results = memory_manager.search_vectors(query, k=5)
    assert len(results) == 5
    
    # Clear memory
    memory_manager.clear(tier='red_hot')
    torch.cuda.empty_cache()
    
    # Check memory returned to near initial state
    _, final_used, _ = check_gpu_memory()
    assert abs(final_used - initial_used) < 100  # Allow some overhead

@pytest.mark.gpu
def test_gpu_error_handling():
    """Test GPU error handling for out of memory conditions."""
    if not torch.cuda.is_available():
        pytest.skip("CUDA not available")
    
    # Get total available memory
    total, _, _ = check_gpu_memory()
    
    # Try to allocate more than available
    with pytest.raises(RuntimeError):
        tensor = allocate_gpu_memory(total * 2)

@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
def test_multi_gpu_detection():
    """Test multi-GPU detection and properties."""
    device_count = torch.cuda.device_count()
    assert device_count > 0
    
    for i in range(device_count):
        device = torch.device(f"cuda:{i}")
        assert torch.cuda.get_device_properties(device).total_memory > 0
        assert isinstance(torch.cuda.get_device_name(device), str)

@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
def test_gpu_compute_capability():
    """Test GPU compute capability detection."""
    for i in range(torch.cuda.device_count()):
        device = torch.device(f"cuda:{i}")
        props = torch.cuda.get_device_properties(device)
        assert props.major >= 0
        assert props.minor >= 0
        assert f"{props.major}.{props.minor}" >= "3.5"  # Minimum CUDA capability for most DL frameworks

@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
def test_gpu_synchronization():
    """Test GPU synchronization mechanisms."""
    tensor = torch.zeros(100, 100).cuda()
    
    # Record events
    start = torch.cuda.Event(enable_timing=True)
    end = torch.cuda.Event(enable_timing=True)
    
    start.record()
    # Perform some computation
    result = torch.matmul(tensor, tensor)
    end.record()
    
    # Synchronize and get time
    torch.cuda.synchronize()
    elapsed_time = start.elapsed_time(end)
    
    assert elapsed_time >= 0
    assert not torch.cuda.is_current_stream_capturing()
    del tensor, result 