=================
Code Catalog
=================

Welcome to the Code Catalog section of the memories-dev documentation. This comprehensive catalog provides an organized view of the codebase, allowing developers to navigate the framework's components with ease.

.. note::
   The Code Catalog is designed to help developers understand the structure and organization of the memories-dev codebase. It is particularly useful for those looking to extend or modify the framework.

Package Structure
-----------------

The memories-dev framework is organized into several key packages and modules:

.. code-block:: text

    memories/
    ├── __init__.py                  # Package initialization and version info
    ├── config.py                    # Global configuration
    ├── cli.py                       # Command-line interface
    ├── agents/                      # AI agents for domain-specific tasks
    ├── core/                        # Core functionality and base classes
    ├── data/                        # Data storage and management
    ├── data_acquisition/            # APIs and tools for acquiring Earth data
    ├── deployments/                 # Deployment configurations and utilities
    ├── models/                      # AI model integrations and abstractions
    ├── scripts/                     # Utility scripts
    ├── synthetic/                   # Synthetic data generation
    └── utils/                       # Utility functions and helpers

Core Components
---------------

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Component
     - Description
   * - Memory Store
     - Central storage system implementing the tiered memory architecture
   * - Earth Analyzers
     - Specialized modules for analyzing Earth observation data
   * - Model Integrations
     - Connectors for various AI models and providers
   * - Data Acquisition
     - Tools for acquiring and processing Earth observation data
   * - Memory Manager
     - Manages the memory system, including tiering and retrieval

Core Modules
------------

memory_store
^^^^^^^^^^^^

.. code-block:: python

    from memories import MemoryStore, Config

    # Configure the memory store
    config = Config(
        storage_path="./earth_memory",
        hot_memory_size=50,  # GB
        warm_memory_size=200,  # GB
        cold_memory_size=1000,  # GB
    )

    # Initialize the memory store
    memory_store = MemoryStore(config)

    # Store data in memory
    memory_store.store(
        key="location_123",
        data={
            "satellite_imagery": imagery_data,
            "environmental_metrics": metrics_data,
            "temporal_series": time_series_data
        },
        metadata={
            "location": {"lat": 37.7749, "lon": -122.4194},
            "timestamp": "2023-06-15T14:30:00Z",
            "source": "sentinel-2"
        }
    )

earth_analyzers
^^^^^^^^^^^^^^^

.. code-block:: python

    from memories.core.analyzers import TerrainAnalyzer, ClimateAnalyzer, WaterResourceAnalyzer

    # Initialize analyzers
    terrain = TerrainAnalyzer()
    climate = ClimateAnalyzer()
    water = WaterResourceAnalyzer()

    # Analyze location
    terrain_analysis = await terrain.analyze(
        location={"lat": 37.7749, "lon": -122.4194},
        resolution="high"
    )

    climate_analysis = await climate.analyze(
        location={"lat": 37.7749, "lon": -122.4194},
        time_range={"start": "2020-01-01", "end": "2023-01-01"}
    )

    water_analysis = await water.analyze(
        location={"lat": 37.7749, "lon": -122.4194},
        include_forecast=True
    )

model_integration
^^^^^^^^^^^^^^^^^

.. code-block:: python

    from memories.models.load_model import LoadModel
    from memories.models.multi_model import MultiModelInference

    # Initialize multiple models
    models = {
        "openai": LoadModel(model_provider="openai", model_name="gpt-4"),
        "anthropic": LoadModel(model_provider="anthropic", model_name="claude-3-opus"),
        "local": LoadModel(model_provider="local", model_name="llama-3-8b")
    }

    # Create multi-model inference engine
    multi_model = MultiModelInference(models=models)

    # Get responses with Earth memory integration
    responses = await multi_model.get_responses_with_earth_memory(
        query="Analyze this location for climate resilience",
        location={"lat": 37.7749, "lon": -122.4194},
        earth_memory_analyzers=["terrain", "climate", "water"]
    )

Directory Catalog
-----------------

.. toctree::
   :maxdepth: 1
   
   agents
   core
   data
   data_acquisition
   deployments
   models
   utils

Module Index
------------

This section provides direct links to the API documentation for key modules:

* :py:mod:`memories.core.memory_store`
* :py:mod:`memories.core.analyzers`
* :py:mod:`memories.data_acquisition.satellite`
* :py:mod:`memories.models.load_model`
* :py:mod:`memories.models.multi_model`
* :py:mod:`memories.utils.geo_utils`

For a complete list of all modules, see the 'modindex'.

File Types
----------

The memories-dev codebase consists of various file types:

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Extension
     - Description
   * - .py
     - Python source code files
   * - .pyx
     - Cython source files for performance-critical components
   * - .json
     - Configuration files and data schemas
   * - .md
     - Markdown documentation files
   * - .rst
     - reStructuredText documentation files
   * - .yaml/.yml
     - YAML configuration files
   * - .sh
     - Shell scripts for various utilities
   * - .ipynb
     - Jupyter notebook examples and tutorials

Development Tools
-----------------

The memories-dev project uses several development tools:

* **Black**: Code formatting
* **isort**: Import sorting
* **mypy**: Static type checking
* **pytest**: Testing framework
* **sphinx**: Documentation generation
* **pre-commit**: Pre-commit hooks for code quality

Code Statistics
---------------

.. list-table::
   :widths: 50 50
   :header-rows: 1

   * - Metric
     - Value
   * - Total Python Files
     - 200+
   * - Lines of Code
     - 50,000+
   * - Test Coverage
     - 85%+
   * - Documentation Coverage
     - 90%+ 