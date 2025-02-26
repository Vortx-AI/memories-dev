GPU Utilities
=============

The GPU Utilities module provides essential tools for GPU resource management, monitoring, and optimization within the memories.dev framework. These utilities ensure efficient memory processing and model inference on GPU hardware while maintaining optimal performance and stability.

🔑 Key Features
--------------

- **Resource Management**:
  - Real-time GPU monitoring
  - Automatic memory management
  - Multi-GPU support
  - Resource optimization

- **Performance Tools**:
  - CUDA optimization utilities
  - Memory caching strategies
  - Batch processing optimization
  - Performance profiling

- **System Integration**:
  - Seamless PyTorch integration
  - Automatic device selection
  - Error recovery mechanisms
  - Resource cleanup

GPU Resource Management
-----------------------

.. automodule:: memories.utils.processors
   :members:
   :undoc-members:
   :show-inheritance:

gpu_stat
--------

.. autofunction:: memories.utils.processors.gpu_stat

Return Value Details
~~~~~~~~~~~~~~~~~~~~

dict: A comprehensive dictionary containing GPU statistics:

- **Core Metrics**:
  - **memory_used** (int): Used GPU memory in MB
  - **memory_total** (int): Total GPU memory in MB
  - **utilization** (float): GPU utilization percentage

- **System Information**:
  - **cuda_available** (bool): CUDA availability status
  - **cuda_version** (str): Installed CUDA version
  - **device_name** (str): GPU device identifier

- **Hardware Metrics**:
  - **temperature** (int): GPU temperature in Celsius
  - **power_usage** (float): Power consumption in watts
  - **fan_speed** (int): Fan speed percentage
  - **memory_bandwidth** (float): Memory bandwidth utilization

Exceptions
~~~~~~~~~~

- **RuntimeError**: 
  - GPU monitoring system failure
  - Driver communication errors
  - Hardware access issues

- **ImportError**: 
  - Missing GPU libraries
  - CUDA installation issues
  - Version incompatibilities

📊 Usage Examples
----------------

Basic Monitoring
~~~~~~~~~~~~~~~~

.. code-block:: python

    from memories.utils.processors import gpu_stat
    
    def monitor_gpu_health():
        """Monitor GPU health and performance metrics."""
        gpu_info = gpu_stat()
        
        if gpu_info['cuda_available']:
            # Core metrics
            print(f"GPU Device: {gpu_info['device_name']}")
            print(f"Memory Usage: {gpu_info['memory_used']}/{gpu_info['memory_total']} MB")
            print(f"Utilization: {gpu_info['utilization']}%")
            
            # Hardware status
            print(f"Temperature: {gpu_info['temperature']}°C")
            print(f"Power Draw: {gpu_info['power_usage']}W")
            print(f"Fan Speed: {gpu_info['fan_speed']}%")
            
            # Alert on high temperature
            if gpu_info['temperature'] > 80:
                print("⚠️ WARNING: High GPU temperature detected!")
        else:
            print("❌ No GPU available - operations will run on CPU")

Advanced Monitoring
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from memories.utils.processors import gpu_stat, set_gpu_device, clear_gpu_memory
    import time
    
    class GPUMonitor:
        def __init__(self, threshold_temp=80, threshold_memory=0.9):
            self.threshold_temp = threshold_temp
            self.threshold_memory = threshold_memory
            
        def monitor_all_gpus(self):
            """Monitor all available GPUs with health checks."""
            for gpu_id in range(torch.cuda.device_count()):
                set_gpu_device(gpu_id)
                gpu_info = gpu_stat()
                
                # Calculate memory usage percentage
                memory_usage = gpu_info['memory_used'] / gpu_info['memory_total']
                
                print(f"\n=== GPU {gpu_id}: {gpu_info['device_name']} ===")
                print(f"Memory: {memory_usage:.1%} used")
                print(f"Temperature: {gpu_info['temperature']}°C")
                print(f"Utilization: {gpu_info['utilization']}%")
                
                # Health checks
                self._check_temperature(gpu_info['temperature'], gpu_id)
                self._check_memory(memory_usage, gpu_id)
                
        def _check_temperature(self, temp, gpu_id):
            if temp > self.threshold_temp:
                print(f"⚠️ WARNING: GPU {gpu_id} temperature ({temp}°C) above threshold!")
                
        def _check_memory(self, usage, gpu_id):
            if usage > self.threshold_memory:
                print(f"⚠️ WARNING: GPU {gpu_id} memory usage ({usage:.1%}) above threshold!")
                self._attempt_memory_cleanup(gpu_id)
                
        def _attempt_memory_cleanup(self, gpu_id):
            set_gpu_device(gpu_id)
            clear_gpu_memory()
            time.sleep(1)  # Allow time for cleanup
            
            # Verify cleanup
            gpu_info = gpu_stat()
            new_usage = gpu_info['memory_used'] / gpu_info['memory_total']
            print(f"Memory usage after cleanup: {new_usage:.1%}")

⚡ Performance Optimization
--------------------------

1. **Memory Management**
   - Monitor usage patterns
   - Implement caching strategies
   - Use appropriate batch sizes
   - Clear unused memory

2. **Workload Optimization**
   - Balance GPU utilization
   - Optimize data transfers
   - Use mixed precision
   - Implement gradient checkpointing

3. **Multi-GPU Strategies**
   - Distribute workloads effectively
   - Manage memory across devices
   - Optimize communication
   - Handle device synchronization

🔧 Troubleshooting Guide
-----------------------

Common Issues
~~~~~~~~~~~~~

1. **Memory Problems**
   - **Symptoms**:
     - Out of memory errors
     - Slow performance
     - Unexpected crashes
   - **Solutions**:
     - Reduce batch sizes
     - Clear GPU cache
     - Monitor memory usage
     - Use gradient checkpointing

2. **Performance Issues**
   - **Symptoms**:
     - Low GPU utilization
     - Slow processing speed
     - High latency
   - **Solutions**:
     - Optimize data transfer
     - Use appropriate CUDA versions
     - Balance workloads
     - Monitor system metrics

3. **Hardware Problems**
   - **Symptoms**:
     - Driver errors
     - Device not found
     - System crashes
   - **Solutions**:
     - Update GPU drivers
     - Check CUDA installation
     - Verify hardware status
     - Monitor temperature

📚 Additional Resources
----------------------

- 'gpu_optimization' - Comprehensive GPU optimization guide
- 'multi_gpu_guide' - Multi-GPU processing strategies
- 'memory_management' - Memory management best practices
- 'troubleshooting' - Detailed troubleshooting guide

GPU Memory Management
---------------------

.. automodule:: memories.utils.processors.gpu_stat
   :members:
   :undoc-members:
   :show-inheritance:

GPU Acceleration
----------------

The memories-dev library provides comprehensive GPU acceleration support for model inference and data processing. The system automatically handles GPU memory management, device selection, and resource cleanup.

Basic GPU Usage
~~~~~~~~~~~~~~~

.. code-block:: python

    from memories.models.load_model import LoadModel
    
    # Initialize model with GPU support
    model = LoadModel(
        use_gpu=True,
        model_provider="deepseek-ai",
        deployment_type="local",
        model_name="deepseek-coder-small"
    )
    
    # Generate text
    response = model.get_response("Write a function to calculate factorial")
    
    # Clean up GPU resources
    model.cleanup()

Multi-GPU Support
~~~~~~~~~~~~~~~~~

For systems with multiple GPUs, you can specify which device to use:

.. code-block:: python

    # Use the second GPU (index 1)
    model = LoadModel(
        use_gpu=True,
        device="cuda:1",
        model_provider="deepseek-ai",
        deployment_type="local",
        model_name="deepseek-coder-small"
    )

GPU Memory Monitoring
---------------------

You can monitor GPU memory usage with the provided utilities:

.. code-block:: python

    from memories.utils.processors.gpu_stat import check_gpu_memory
    
    # Get memory statistics for all GPUs
    memory_stats = check_gpu_memory()
    
    for device_id, stats in memory_stats.items():
        print(f"GPU {device_id}:")
        print(f"  Total memory: {stats['total']} MB")
        print(f"  Used memory: {stats['used']} MB")
        print(f"  Free memory: {stats['free']} MB")

Error Handling
--------------

The system includes robust error handling for GPU-related issues:

.. code-block:: python

    try:
        model = LoadModel(
            use_gpu=True,
            model_provider="deepseek-ai",
            deployment_type="local",
            model_name="deepseek-coder-small"
        )
    except RuntimeError as e:
        if "CUDA out of memory" in str(e):
            print("Not enough GPU memory available. Falling back to CPU.")
            model = LoadModel(
                use_gpu=False,
                model_provider="deepseek-ai",
                deployment_type="local",
                model_name="deepseek-coder-small"
            )
        else:
            raise

Performance Comparison
----------------------

When available, GPU acceleration can significantly improve performance:

.. code-block:: python

    import time
    import torch
    
    # Create test data
    data = torch.randn(1000, 1000)
    
    # CPU computation
    start_time = time.time()
    cpu_result = torch.matmul(data, data)
    cpu_time = time.time() - start_time
    
    # GPU computation
    data_gpu = data.cuda()
    start_time = time.time()
    gpu_result = torch.matmul(data_gpu, data_gpu)
    torch.cuda.synchronize()  # Wait for GPU computation to complete
    gpu_time = time.time() - start_time
    
    print(f"CPU time: {cpu_time:.4f} seconds")
    print(f"GPU time: {gpu_time:.4f} seconds")
    print(f"Speedup: {cpu_time / gpu_time:.2f}x") 