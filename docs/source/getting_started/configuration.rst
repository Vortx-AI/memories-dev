.. _configuration:

=============
Configuration
=============

The ``memories-dev`` framework is highly configurable to adapt to different use cases, data sources, and computing environments. This guide covers the various configuration options available and how to use them effectively.

Global Configuration
====================

The framework provides a central configuration system that can be accessed and modified throughout your application:

.. code-block:: python

   from memories.config import config, update_config

   # View current configuration
   print(config)

   # Update multiple configuration options at once
   update_config({
       "data_sources.satellite.default_provider": "sentinel",
       "processing.use_gpu": True,
       "storage.cache_size_gb": 5,
       "logging.level": "INFO"
   })

   # Access individual configuration options
   satellite_provider = config.get("data_sources.satellite.default_provider")
   print(f"Using satellite provider: {satellite_provider}")

Configuration File
------------------

You can also create a configuration file in YAML format:

.. code-block:: yaml
   :caption: memories_config.yaml

   data_sources:
     satellite:
       default_provider: sentinel
       api_key: ${SATELLITE_API_KEY}
       max_cloud_cover: 20
     gis:
       default_provider: osm
       cache_ttl_days: 30
   
   processing:
     use_gpu: true
     precision: float32
     batch_size: 16
     num_workers: 4
   
   storage:
     type: local
     base_path: . / memories_data
     cache_size_gb: 5
     compression: true
   
   logging:
     level: INFO
     file: memories.log
     rotation: 5MB

Load this configuration file in your application:

.. code-block:: python

   from memories.config import load_config_file

   # Load configuration from file
   load_config_file("memories_config.yaml")

Environment Variables
---------------------

The framework supports environment variables for configuration, which is especially useful for sensitive information like API keys:

.. code-block:: bash

   # Set environment variables
   export MEMORIES_SATELLITE_API_KEY=your_api_key
   export MEMORIES_USE_GPU=true
   export MEMORIES_STORAGE_TYPE=s3
   export MEMORIES_STORAGE_BUCKET=my-memories-bucket

These environment variables will be automatically loaded when the framework initializes. You can also reference environment variables in your YAML configuration file using the ``${VARIABLE_NAME}`` syntax.

Data Source Configuration
=========================

Satellite Imagery
-----------------

Configure satellite imagery providers and their parameters:

.. code-block:: python

   from memories.earth import configure_satellite_provider

   # Configure Sentinel-2 provider
   configure_satellite_provider(
       provider="sentinel",
       api_key="your_sentinel_api_key",
       collection="sentinel-2-l2a",
       max_cloud_cover=20,
       bands=["B02", "B03", "B04", "B08"],
       cache_ttl_days=30
   )

   # Configure Landsat provider
   configure_satellite_provider(
       provider="landsat",
       api_key="your_landsat_api_key",
       collection="landsat-8-c2-l2",
       max_cloud_cover=15,
       bands=["SR_B2", "SR_B3", "SR_B4", "SR_B5"],
       cache_ttl_days=30
   )

GIS Data
--------

Configure GIS data providers:

.. code-block:: python

   from memories.earth import configure_gis_provider

   # Configure OpenStreetMap provider
   configure_gis_provider(
       provider="osm",
       cache_ttl_days=30,
       timeout=60,
       max_retries=3
   )

   # Configure custom GIS provider
   configure_gis_provider(
       provider="custom",
       api_url="https://api.custom-gis.com/v1",
       api_key="your_custom_api_key",
       features=["buildings", "roads", "landuse"],
       cache_ttl_days=15
   )

Environmental Data
------------------

Configure environmental data sources:

.. code-block:: python

   from memories.earth import configure_environmental_provider

   # Configure climate data provider
   configure_environmental_provider(
       provider="noaa",
       dataset="climate",
       api_key="your_noaa_api_key",
       variables=["temperature", "precipitation", "wind"],
       temporal_resolution="monthly",
       spatial_resolution="0.25deg"
   )

Processing Configuration
========================

GPU Configuration
-----------------

Configure GPU usage for processing:

.. code-block:: python

   from memories.config import configure_gpu

   # Use all available GPUs
   configure_gpu(enabled=True)

   # Use specific GPU devices
   configure_gpu(
       enabled=True,
       devices=[0, 1],  # Use GPU devices 0 and 1
       memory_limit="80%",  # Limit memory usage to 80% per GPU
       precision="mixed"  # Use mixed precision (float16/float32)
   )

Parallel Processing
-------------------

Configure parallel processing options:

.. code-block:: python

   from memories.config import configure_parallel_processing

   # Configure parallel processing
   configure_parallel_processing(
       num_workers=8,  # Number of worker processes/threads
       batch_size=16,  # Batch size for processing
       prefetch_factor=2,  # Number of batches to prefetch
       pin_memory=True,  # Pin memory for faster GPU transfer
       timeout=300  # Timeout in seconds for operations
   )

Memory Management
-----------------

Configure memory usage and caching:

.. code-block:: python

   from memories.config import configure_memory

   # Configure memory management
   configure_memory(
       max_memory_gb=16,  # Maximum memory usage in GB
       cache_size_gb=5,   # Cache size in GB
       swap_enabled=True, # Enable swap to disk for large datasets
       swap_path="./memories_swap",  # Path for swap files
       cleanup_on_exit=True  # Clean up temporary files on exit
   )

Storage Configuration
=====================

Local Storage
-------------

Configure local storage options:

.. code-block:: python

   from memories.storage import configure_local_storage

   # Configure local storage
   configure_local_storage(
       base_path="./memories_data",
       structure="hierarchical",  # Options: flat, hierarchical, dated
       compression=True,  # Enable compression
       compression_level=6,  # Compression level (1-9)
       backup_enabled=True,  # Enable automatic backups
       backup_interval_days=7  # Backup interval in days
   )

Cloud Storage
-------------

Configure cloud storage options:

.. code-block:: python

   from memories.storage import configure_cloud_storage

   # Configure AWS S3 storage
   configure_cloud_storage(
       provider="s3",
       bucket="memories-data",
       region="us-west-2",
       access_key="your_access_key",  # Or use AWS environment variables
       secret_key="your_secret_key",  # Or use AWS environment variables
       prefix="memories/",  # Optional prefix for all objects
       encryption=True,  # Enable server-side encryption
       public_access=False  # Disable public access
   )

   # Configure Google Cloud Storage
   configure_cloud_storage(
       provider="gcs",
       bucket="memories-data",
       project_id="your-project-id",
       credentials_file="path/to/credentials.json",  # Or use GCP environment variables
       prefix="memories/",
       encryption=True,
       public_access=False
   )

Database Configuration
----------------------

Configure database connections for metadata and results:

.. code-block:: python

   from memories.storage import configure_database

   # Configure PostgreSQL database
   configure_database(
       type="postgresql",
       host="localhost",
       port=5432,
       database="memories",
       user="memories_user",
       password="your_password",
       ssl=True,
       pool_size=10,
       timeout=30
   )

   # Configure MongoDB database
   configure_database(
       type="mongodb",
       connection_string="mongodb://localhost:27017",
       database="memories",
       collection_prefix="memories_",
       authentication_source="admin",
       timeout_ms=5000
   )

Logging Configuration
=====================

Configure logging options:

.. code-block:: python

   from memories.config import configure_logging

   # Configure logging
   configure_logging(
       level="INFO",  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
       file="memories.log",  # Log file path (None for console only)
       format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
       rotation="5MB",  # Log rotation size
       backup_count=5,  # Number of backup logs to keep
       capture_warnings=True,  # Capture Python warnings
       log_to_console=True  # Also log to console
   )

Advanced Configuration
======================

Model Configuration
-------------------

Configure AI models used by the framework:

.. code-block:: python

   from memories.ai import configure_model

   # Configure computer vision model
   configure_model(
       type="computer_vision",
       name="change_detection",
       model_path="path/to/model.pth",  # Local model path
       # Or use a pre-trained model
       pretrained="change_detection_v2",
       precision="float16",
       device="cuda",
       batch_size=8,
       num_workers=4
   )

   # Configure NLP model
   configure_model(
       type="nlp",
       name="location_description",
       pretrained="gpt-3.5-turbo",
       api_key="your_openai_api_key",
       max_tokens=500,
       temperature=0.7
   )

Pipeline Configuration
----------------------

Configure processing pipelines:

.. code-block:: python

   from memories.pipeline import configure_pipeline

   # Configure a custom pipeline
   configure_pipeline(
       name="urban_change_detection",
       steps=[
           {
               "name": "cloud_removal",
               "type": "processor",
               "config": {"method": "deep_learning"}
           },
           {
               "name": "ndvi_calculation",
               "type": "processor",
               "config": {"bands": ["B04", "B08"]}
           },
           {
               "name": "urban_detection",
               "type": "model",
               "config": {"model": "urban_detector_v1", "threshold": 0.7}
           },
           {
               "name": "change_classification",
               "type": "processor",
               "config": {"classes": ["urban", "vegetation", "water"]}
           }
       ],
       parallel=True,
       cache_intermediate=True
   )

Configuration Profiles
======================

You can create and switch between different configuration profiles for different use cases:

.. code-block:: python

   from memories.config import create_profile, use_profile

   # Create a high-performance profile
   create_profile(
       name="high_performance",
       config={
           "processing.use_gpu": True,
           "processing.precision": "mixed",
           "processing.batch_size": 32,
           "processing.num_workers": 8,
           "storage.compression": False
       }
   )

   # Create a low-resource profile
   create_profile(
       name="low_resource",
       config={
           "processing.use_gpu": False,
           "processing.precision": "float32",
           "processing.batch_size": 4,
           "processing.num_workers": 2,
           "storage.compression": True
       }
   )

   # Switch to a profile
   use_profile("high_performance")

Configuration Validation
========================

Validate your configuration to ensure it's correct:

.. code-block:: python

   from memories.config import validate_config

   # Validate the current configuration
   validation_result = validate_config()

   if validation_result.valid:
       print("Configuration is valid!")
   else:
       print("Configuration issues found:")
       for issue in validation_result.issues:
           print(f"- {issue}")

Best Practices
==============

1. **Environment-Specific Configuration**: Use different configuration files for development, testing, and production environments.

2. **Sensitive Information**: Store API keys and credentials in environment variables or secure vaults, not in configuration files.

3. **Resource Optimization**: Adjust batch sizes, worker counts, and memory limits based on your hardware capabilities.

4. **Caching Strategy**: Configure appropriate cache sizes and TTLs based on your data access patterns and storage constraints.

5. **Logging Levels**: Use DEBUG level during development and INFO or WARNING in production.

6. **Configuration Versioning**: Version your configuration files alongside your code to track changes.

7. **Validation**: Always validate your configuration before running important processing tasks.

Next Steps
==========

* Learn about 'data_sources' to configure specific data providers
* Explore 'ai_capabilities' to configure AI models
* Check out :ref:`examples` for configuration examples for specific use cases 