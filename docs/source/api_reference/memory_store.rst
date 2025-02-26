MemoryStore
===========

Core Memory Management
----------------------

.. automodule:: memories.core.memory
   :members:
   :undoc-members:
   :show-inheritance:

MemoryStore Class
-----------------

.. autoclass:: memories.core.memory.MemoryStore
   :members:
   :undoc-members:
   :show-inheritance:

Memory Tiers
------------

Hot Memory
~~~~~~~~~~

.. autoclass:: memories.core.hot.HotMemory
   :members:
   :undoc-members:
   :show-inheritance:

Warm Memory
~~~~~~~~~~~

.. autoclass:: memories.core.warm.WarmMemory
   :members:
   :undoc-members:
   :show-inheritance:

Cold Memory
~~~~~~~~~~~

.. autoclass:: memories.core.cold.ColdMemory
   :members:
   :undoc-members:
   :show-inheritance:

Glacier Memory
~~~~~~~~~~~~~~

.. autoclass:: memories.core.glacier.GlacierMemory
   :members:
   :undoc-members:
   :show-inheritance:

Example Usage
-------------

.. code-block:: python

    from memories import MemoryStore, Config
    
    # Initialize configuration
    config = Config(
        storage_path="./data",
        hot_memory_size=50,  # MB
        warm_memory_size=200,  # MB
        cold_memory_size=1000  # MB
    )
    
    # Create memory store
    memory_store = MemoryStore(config)
    
    # Store data
    data = {
        "timestamp": "2025-02-17T12:00:00",
        "location": {"lat": 40.7128, "lon": -74.0060},
        "measurements": {"temperature": 25.5, "humidity": 60}
    }
    memory_store.store(data)
    
    # Retrieve data
    result = memory_store.retrieve(
        query={"location.lat": {"$gt": 40}},
        time_range=("2025-02-17T00:00:00", "2025-02-17T23:59:59")
    )

Configuration Options
---------------------

The MemoryStore can be configured with various options:

- ``storage_path``: Base path for storing memory data
- ``hot_memory_size``: Size limit for hot memory in MB
- ``warm_memory_size``: Size limit for warm memory in MB
- ``cold_memory_size``: Size limit for cold memory in MB
- ``enable_compression``: Enable data compression (default: True)
- ``compression_level``: Compression level (1-9, default: 6)
- ``enable_encryption``: Enable data encryption (default: False)
- ``encryption_key``: Encryption key for secure storage 