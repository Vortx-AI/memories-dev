Welcome to Memories-Dev's documentation!
=====================================

Memories-Dev is a powerful Python framework for managing and processing earth observation data. It provides a flexible and efficient system for handling various types of geospatial data, with a focus on satellite imagery and vector data.

Version: 1.1.9

Key Features
-----------

- Multi-tiered memory system (Hot, Warm, Cold)
- Satellite imagery processing
- Vector data analysis
- Intelligent data management
- Specialized analysis agents
- Example applications for various use cases

Example Applications
------------------

- Property Analyzer: Real estate analysis using satellite data
- Location Ambience: Environmental and urban characteristic analysis
- Traffic Analyzer: Traffic patterns and road conditions monitoring
- Water Bodies Monitor: Water body change detection and analysis

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   user_guide/index
   api_reference/index
   examples/index
   contributing
   changelog

Getting Started
-------------

Installation
^^^^^^^^^^^

.. code-block:: bash

    pip install memories-dev

Basic Usage
^^^^^^^^^^

.. code-block:: python

    from memories import MemoryStore, Config
    
    # Initialize memory store
    config = Config(
        storage_path="./data",
        hot_memory_size=50,
        warm_memory_size=200,
        cold_memory_size=1000
    )
    memory_store = MemoryStore(config)
    
    # Store data
    memory_store.store({
        "timestamp": "2024-02-17T12:00:00",
        "data": {"key": "value"}
    })

For more detailed information, check out the :doc:`quickstart` guide.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search` 