"""Tests for GPU utility functions."""

import pytest
import torch
import gc
from unittest.mock import Mock, patch
from memories.utils.processors.gpu_stat import check_gpu_memory

@pytest.fixture(autouse=True)
def cleanup_gpu():
    """Cleanup GPU memory after each test."""
    yield
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        gc.collect()

@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
def test_check_gpu_memory():
    """Test GPU memory checking functionality."""
    memory_stats = check_gpu_memory()
    if memory_stats:
        assert isinstance(memory_stats, dict)
        assert all(key in memory_stats for key in ['total', 'free', 'used'])
        assert memory_stats['total'] > 0
        assert memory_stats['free'] >= 0
        assert memory_stats['used'] >= 0
        assert memory_stats['total'] >= memory_stats['used']

@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
def test_gpu_memory_allocation():
    """Test GPU memory allocation and deallocation."""
    initial_memory = torch.cuda.memory_allocated()
    
    # Allocate a large tensor
    tensor = torch.zeros(1000, 1000).cuda()
    allocated_memory = torch.cuda.memory_allocated()
    
    assert allocated_memory > initial_memory
    
    # Delete tensor and clear cache
    del tensor
    torch.cuda.empty_cache()
    gc.collect()
    
    final_memory = torch.cuda.memory_allocated()
    assert final_memory <= initial_memory

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
def test_gpu_error_handling():
    """Test GPU error handling for out of memory conditions."""
    initial_memory = torch.cuda.memory_allocated()
    
    try:
        # Try to allocate more memory than available
        huge_tensor = torch.zeros(1000000, 1000000).cuda()
        del huge_tensor
    except RuntimeError as e:
        assert "out of memory" in str(e).lower()
    finally:
        torch.cuda.empty_cache()
        gc.collect()
        
    final_memory = torch.cuda.memory_allocated()
    assert final_memory <= initial_memory

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