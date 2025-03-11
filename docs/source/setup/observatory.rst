===========================
Setting Up Your Observatory
===========================


Introduction
------------

The Observatory is the central component of the Memory Codex framework, serving as your connection to Earth's observable reality. This guide will help you set up and configure your observatory for optimal Earth memory collection.

Installation Requirements
--------------------------

Before setting up your Observatory, ensure you have the following requirements:

- Python 3.8 or higher
- memories-dev package installed
- Required system dependencies for geospatial processing
- Adequate storage for Earth observation data

Basic Observatory Setup
------------------------

Creating your first Observatory is straightforward:

.. code-block:: python

   from memories.earth import Observatory
   
   # Create a basic observatory
   observatory = Observatory(
       name="my-first-observatory",
       location="global",  # Can be "global" or specific coordinates
       data_sources=["satellite", "climate"]
   )
   
   # Initialize the observatory
   observatory.initialize()
   
   # Verify it's working
   status = observatory.check_status()
   print(f"Observatory status: {status}")

Configuration Options
----------------------

The Observatory can be configured with various options:

.. list-table::
   :header-rows: 1
   :widths: 30 70
   
   * - Parameter
     - Description
   * - **name**
     - Unique identifier for your observatory
   * - **location**
     - Geographic focus (global, regional, or coordinates)
   * - **data_sources**
     - List of data sources to connect to
   * - **temporal_range**
     - Time period to observe (e.g., "current", "last-5-years")
   * - **resolution**
     - Desired spatial resolution of observations
   * - **update_frequency**
     - How often to update Earth memory
   * - **storage_config**
     - Configuration for data storage backends

Advanced Configuration
-----------------------

For more advanced use cases, you can configure the Observatory with detailed parameters:

.. code-block:: python

   from memories.earth import Observatory, DataSource, Resolution
   
   # Advanced observatory configuration
   observatory = Observatory(
       name="advanced-observatory",
       location={
           "type": "region",
           "coordinates": [
               [32.0, -120.0],
               [32.0, -110.0],
               [42.0, -110.0],
               [42.0, -120.0]
           ]
       },
       data_sources=[
           DataSource(
               name="sentinel-2",
               provider="copernicus",
               products=["l2a"],
               bands=["B02", "B03", "B04", "B08"],
               cloud_cover_max=20
           ),
           DataSource(
               name="era5",
               provider="ecmwf",
               variables=["temperature", "precipitation"]
           )
       ],
       resolution=Resolution.MEDIUM,  # 10-30m resolution
       update_frequency="daily",
       storage_config={
           "vector_store": "postgres",
           "raster_store": "cloud-optimized-geotiff",
           "connection_string": "postgresql://user:password@localhost:5432/earth_memory"
       }
   )

Connecting to Data Sources
---------------------------

Your Observatory needs to connect to Earth observation data sources. The following example shows how to connect to common sources:

.. code-block:: python

   # Connect to data sources
   observatory.connect_data_source(
       name="sentinel-hub",
       api_key="your-api-key-here",
       collections=["sentinel-2-l2a"]
   )
   
   observatory.connect_data_source(
       name="nasa-gibs",
       collections=["MODIS_Terra_CorrectedReflectance_TrueColor"]
   )
   
   observatory.connect_data_source(
       name="noaa-gfs",
       variables=["temperature", "precipitation", "wind"]
   )

Testing Your Observatory
-------------------------

After setup, you should test that your Observatory is functioning correctly:

.. code-block:: python

   # Test data acquisition
   test_result = observatory.test_data_acquisition(
       source="sentinel-2",
       location=[37.7749, -122.4194],  # San Francisco
       time_range=("2023-01-01", "2023-01-10")
   )
   
   if test_result.success:
       print(f"Successfully acquired {test_result.data_points} observations")
       print(f"Coverage: {test_result.coverage_percent}%")
   else:
       print(f"Error: {test_result.error_message}")

Observatory Management
-----------------------

Manage your Observatory's lifecycle with these commands:

.. code-block:: python

   # Start observation collection
   observatory.start()
   
   # Pause observation collection
   observatory.pause()
   
   # Resume observation collection
   observatory.resume()
   
   # Stop and clean up resources
   observatory.shutdown()
   
   # Check observatory health
   health = observatory.get_health_metrics()
   print(f"Memory usage: {health.memory_usage_mb}MB")
   print(f"Storage used: {health.storage_used_gb}GB")
   print(f"API rate limit: {health.api_rate_limit_percent}% consumed")

Next Steps
----------

After setting up your Observatory, you're ready to start creating Earth Memories:

- Learn how to create different types of memories in :doc:`../memory_types/index`
- Set up data processing pipelines in :doc:`../integration/data_processing`
- Configure memory retention policies in :doc:`../memory_architecture/retention` 