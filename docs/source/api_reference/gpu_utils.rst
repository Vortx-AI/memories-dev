GPU Utilities
============

GPU Statistics
-------------

.. automodule:: memories.utils.processors
   :members:
   :undoc-members:
   :show-inheritance:

gpu_stat Function
--------------

.. autofunction:: memories.utils.processors.gpu_stat

Example Usage
-----------

.. code-block:: python

    from memories import gpu_stat
    
    # Get GPU statistics
    gpu_info = gpu_stat()
    
    # Print GPU information
    print(f"GPU Memory Used: {gpu_info['memory_used']} MB")
    print(f"GPU Memory Total: {gpu_info['memory_total']} MB")
    print(f"GPU Utilization: {gpu_info['utilization']}%")
    
    # Check if CUDA is available
    if gpu_info['cuda_available']:
        print(f"CUDA Version: {gpu_info['cuda_version']}")
        print(f"GPU Device: {gpu_info['device_name']}")
    else:
        print("CUDA is not available") 