Memory System
=============

.. code-block:: text
   :caption: Memory System Workflow
   
Overview
--------

The Memory System is the core component of the memories-dev framework, providing efficient storage, retrieval, and management of data across different memory tiers. It is designed to optimize performance by keeping frequently accessed data in faster memory while moving less frequently accessed data to slower, more cost-effective storage.

Memory Tiers
------------

The system implements a 4-tier memory architecture:

.. code-block:: text
   :caption: Memory System Visualization
   
1. **Hot Memory (GPU Memory)**
   - Fastest access time (< 1ms)
   - Limited capacity (typically 8-32GB)
   - Used for active models and current processing
   - Automatically managed by the MemoryManager

2. **Warm Memory (RAM)**
   - Fast access time (~10ms)
   - Medium capacity (typically 16-128GB)
   - Used for recent data and cached results
   - Configurable size and eviction policies

3. **Cold Memory (On-Device Storage)**
   - Medium access time (~100ms)
   - Large capacity (typically 500GB-2TB)
   - Used for historical data and processed results
   - Supports compression and indexing

4. **Glacier Memory (Off-Device Storage)**
   - Slow access time (1-10 seconds)
   - Virtually unlimited capacity
   - Used for archived data and rarely accessed datasets
   - Supports high compression ratios

Basic Usage
-----------

Using the MemoryManager
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from memories.core.memory_manager import MemoryManager
    import numpy as np
    
    # Initialize memory manager with custom tier sizes
    memory_manager = MemoryManager(
        hot_memory_size=8,  # GB
        warm_memory_size=32,  # GB
        cold_memory_size=500,  # GB
        glacier_memory_enabled=True
    )
    
    # Store data in memory
    data = np.random.rand(1000, 1000)  # 8MB array
    key = "random_matrix_1"
    
    # Store in hot memory initially
    memory_manager.store(key, data, tier="hot")
    
    # Retrieve data
    retrieved_data = memory_manager.retrieve(key)
    print(f"Data shape: {retrieved_data.shape}")
    
    # Check memory usage
    usage = memory_manager.get_memory_usage()
    print(f"Hot memory usage: {usage['hot']:.2f}%")
    print(f"Warm memory usage: {usage['warm']:.2f}%")
    print(f"Cold memory usage: {usage['cold']:.2f}%")
    
    # Clean up when done
    memory_manager.cleanup()

Example Output:

.. code-block:: text

    Data shape: (1000, 1000)
    Hot memory usage: 0.10%
    Warm memory usage: 0.00%
    Cold memory usage: 0.00%

Advanced Usage
--------------

Memory Tier Migration
~~~~~~~~~~~~~~~~~~~~~

The system automatically migrates data between tiers based on access patterns:

.. code-block:: python

    from memories.core.memory_manager import MemoryManager
    import numpy as np
    import time
    
    # Initialize memory manager
    memory_manager = MemoryManager()
    
    # Create some test data
    data_sizes = [100, 200, 300, 400, 500]  # MB
    
    # Store multiple items in hot memory
    for i, size in enumerate(data_sizes):
        # Create array of specified size
        mb_size = size * 1024 * 1024 // 8  # Convert MB to number of float64 elements
        dim = int(np.sqrt(mb_size))
        data = np.random.rand(dim, dim)
        
        key = f"data_{i}"
        memory_manager.store(key, data, tier="hot")
        print(f"Stored {size}MB array with key '{key}' in hot memory")
    
    # Check memory usage after storing all items
    usage = memory_manager.get_memory_usage()
    print(f"\nHot memory usage: {usage['hot']:.2f}%")
    
    # Access some items frequently to keep them in hot memory
    for _ in range(10):
        memory_manager.retrieve("data_0")
        memory_manager.retrieve("data_1")
        time.sleep(0.1)
    
    # Wait for automatic migration to occur
    print("\nWaiting for automatic migration...")
    time.sleep(5)
    
    # Check which tier each item is in
    for i in range(len(data_sizes)):
        key = f"data_{i}"
        tier = memory_manager.get_tier(key)
        print(f"'{key}' is now in {tier} memory")
    
    # Clean up
    memory_manager.cleanup()

Example Output:

.. code-block:: text

    Stored 100MB array with key 'data_0' in hot memory
    Stored 200MB array with key 'data_1' in hot memory
    Stored 300MB array with key 'data_2' in hot memory
    Stored 400MB array with key 'data_3' in hot memory
    Stored 500MB array with key 'data_4' in hot memory
    
    Hot memory usage: 18.75%
    
    Waiting for automatic migration...
    'data_0' is now in hot memory
    'data_1' is now in hot memory
    'data_2' is now in warm memory
    'data_3' is now in warm memory
    'data_4' is now in warm memory

Memory Snapshots
~~~~~~~~~~~~~~~~

Create and restore memory snapshots:

.. code-block:: python

    from memories.core.memory_manager import MemoryManager
    import numpy as np
    import os
    
    # Initialize memory manager
    memory_manager = MemoryManager()
    
    # Store some test data
    for i in range(5):
        data = np.random.rand(100, 100) * i
        memory_manager.store(f"matrix_{i}", data, tier="hot")
    
    # Create a snapshot
    snapshot_path = "./memory_snapshot.bin"
    memory_manager.create_snapshot(snapshot_path)
    print(f"Created snapshot at {snapshot_path}")
    print(f"Snapshot size: {os.path.getsize(snapshot_path) / (1024 * 1024):.2f} MB")
    
    # Clear memory
    memory_manager.clear()
    
    # Verify data is gone
    try:
        memory_manager.retrieve("matrix_0")
        print("Data still exists (unexpected)")
    except KeyError:
        print("Data was successfully cleared")
    
    # Restore from snapshot
    memory_manager.restore_snapshot(snapshot_path)
    print("Restored from snapshot")
    
    # Verify data is back
    for i in range(5):
        data = memory_manager.retrieve(f"matrix_{i}")
        print(f"Retrieved matrix_{i}, mean value: {data.mean():.2f}")
    
    # Clean up
    memory_manager.cleanup()
    os.remove(snapshot_path)

Memory Analytics
~~~~~~~~~~~~~~~~

Monitor and analyze memory usage:

.. code-block:: python

    from memories.core.memory_manager import MemoryManager
    import numpy as np
    import time
    import matplotlib.pyplot as plt
    
    # Initialize memory manager
    memory_manager = MemoryManager()
    
    # Enable analytics
    memory_manager.enable_analytics()
    
    # Simulate memory operations
    for i in range(20):
        # Store data
        data = np.random.rand(100, 100) * i
        key = f"data_{i}"
        memory_manager.store(key, data, tier="hot")
        
        # Retrieve some data randomly
        if i > 0:
            for _ in range(3):
                random_key = f"data_{np.random.randint(0, i)}"
                memory_manager.retrieve(random_key)
        
        # Sleep to allow migrations to occur
        time.sleep(0.5)
    
    # Get analytics data
    analytics = memory_manager.get_analytics()
    
    # Plot memory usage over time
    plt.figure(figsize=(12, 6))
    
    plt.subplot(1, 2, 1)
    plt.plot(analytics['timestamps'], analytics['hot_usage'], 'r-', label='Hot')
    plt.plot(analytics['timestamps'], analytics['warm_usage'], 'g-', label='Warm')
    plt.plot(analytics['timestamps'], analytics['cold_usage'], 'b-', label='Cold')
    plt.xlabel('Time (s)')
    plt.ylabel('Usage (%)')
    plt.title('Memory Usage Over Time')
    plt.legend()
    
    plt.subplot(1, 2, 2)
    plt.plot(analytics['timestamps'], analytics['hit_rate'], 'k-')
    plt.xlabel('Time (s)')
    plt.ylabel('Hit Rate (%)')
    plt.title('Cache Hit Rate')
    
    plt.tight_layout()
    plt.savefig('memory_analytics.png')
    
    print("Analytics visualization saved to memory_analytics.png")
    
    # Clean up
    memory_manager.cleanup()

Distributed Memory
~~~~~~~~~~~~~~~~~~

For multi-node deployments:

.. code-block:: python

    from memories.core.memory_manager import DistributedMemoryManager
    import numpy as np
    
    # Initialize distributed memory manager
    memory_manager = DistributedMemoryManager(
        nodes=["node1:6379", "node2:6379", "node3:6379"],
        replication_factor=2
    )
    
    # Store data with distribution
    large_data = np.random.rand(10000, 10000)
    memory_manager.store_distributed("large_matrix", large_data)
    
    # Retrieve data from the distributed system
    retrieved_data = memory_manager.retrieve_distributed("large_matrix")
    
    print(f"Successfully retrieved distributed data with shape {retrieved_data.shape}")
    
    # Check node status
    node_status = memory_manager.get_node_status()
    for node, status in node_status.items():
        print(f"Node {node}: {'Online' if status['online'] else 'Offline'}, "
              f"Memory usage: {status['memory_usage']:.2f}%")
    
    # Clean up
    memory_manager.cleanup()

Best Practices
--------------

1. **Memory Sizing**:
   - Allocate appropriate sizes for each memory tier based on your workload
   - Monitor memory usage and adjust tier sizes as needed
   - Consider your hardware constraints when configuring memory tiers

2. **Data Organization**:
   - Use consistent key naming conventions
   - Group related data with prefix keys
   - Consider data lifecycle when choosing initial memory tier

3. **Performance Optimization**:
   - Use compression for cold and glacier memory
   - Implement predictive caching for frequently accessed data
   - Use memory snapshots for critical application states

4. **Resource Management**:
   - Always call `cleanup()` when done with the memory manager
   - Implement proper error handling for memory operations
   - Monitor memory usage to prevent out-of-memory errors
