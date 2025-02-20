Welcome to Memories-Dev's documentation!
=====================================

Memories-Dev is a powerful Python framework for Earth Memory Synthesis, designed to capture, process, and understand the evolving story of our planet through data. It provides a sophisticated system for synthesizing and managing Earth observations across multiple temporal and spatial scales.

Version: 2.0.1

Key Features
-----------

- Multi-tiered Memory Architecture
  - Hot Memory: Real-time, high-priority Earth observations
  - Warm Memory: Recent historical data and frequently accessed patterns
  - Cold Memory: Long-term Earth observation archives
  - Glacier Memory: Deep historical records and baseline data

- Earth Memory Synthesis
  - Temporal Pattern Recognition
  - Spatial Relationship Analysis
  - Multi-source Data Integration
  - Contextual Understanding
  - Adaptive Learning from Historical Patterns

- Specialized Analysis Agents
  - Property Analysis: Understanding urban development patterns
  - Location Ambience: Environmental and social context synthesis
  - Traffic Patterns: Transportation network evolution
  - Water Bodies: Hydrological system monitoring
  - Custom Agent Framework for specialized applications

Example Applications
------------------

- Property Analyzer: Synthesize property evolution patterns
- Location Ambience: Environmental and urban characteristic synthesis
- Traffic Analyzer: Transportation network memory patterns
- Water Bodies Monitor: Hydrological system memory synthesis

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
        storage_path="./earth_memories",
        hot_memory_size=50,  # Recent observations
        warm_memory_size=200,  # Historical patterns
        cold_memory_size=1000  # Long-term records
    )
    memory_store = MemoryStore(config)
    
    # Store Earth observation data
    memory_store.store({
        "timestamp": "2024-02-17T12:00:00",
        "location": {"lat": 40.7128, "lon": -74.0060},
        "observation_type": "environmental",
        "data": {
            "temperature": 25.5,
            "vegetation_index": 0.68,
            "urban_density": 0.85
        }
    })

For more detailed information, check out the :doc:`quickstart` guide.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search` 