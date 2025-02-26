Sentinel API
============

Overview
--------

The ``SentinelAPI`` class provides a comprehensive interface for accessing and downloading Sentinel-2 satellite imagery data through the Planetary Computer STAC API. This module handles authentication, data discovery, filtering, and downloading.

Class Reference
---------------

.. autoclass:: memories.data_acquisition.sources.sentinel_api.SentinelAPI
   :members:
   :undoc-members:
   :show-inheritance:

Key Features
------------

- **Cloud Cover Filtering**: Filter imagery based on cloud coverage percentage
- **Spatial Filtering**: Query data for specific geographic regions using bounding boxes
- **Temporal Filtering**: Filter data by acquisition date ranges
- **Band Selection**: Download specific spectral bands as needed
- **Asynchronous Operations**: Support for concurrent downloads
- **Error Handling**: Robust validation and error reporting

Basic Usage
-----------

Initialization
~~~~~~~~~~~~~~

.. code-block:: python

    from memories.data_acquisition.sources.sentinel_api import SentinelAPI
    
    # Initialize the API with a local data directory
    api = SentinelAPI(data_dir="/path/to/data")
    
    # Initialize the client
    await api.initialize()

Downloading Data
~~~~~~~~~~~~~~~~

.. code-block:: python

    # Define area of interest (bounding box)
    bbox = [-122.5, 37.7, -122.3, 37.9]  # [min_lon, min_lat, max_lon, max_lat]
    
    # Define time range
    start_date = "2023-01-01"
    end_date = "2023-01-31"
    
    # Download specific bands with cloud cover filter
    result = await api.download_data(
        bbox=bbox,
        start_date=start_date,
        end_date=end_date,
        bands=["B04", "B08"],  # Red and NIR bands
        cloud_cover=10.0  # Maximum 10% cloud cover
    )
    
    if result["status"] == "success":
        print(f"Downloaded files: {result['files']}")
        print(f"Metadata: {result['metadata']}")
    else:
        print(f"Error: {result['error']}")

Advanced Usage
--------------

Error Handling
~~~~~~~~~~~~~~

.. code-block:: python

    try:
        result = await api.download_data(
            bbox=bbox,
            start_date=start_date,
            end_date=end_date,
            bands=["B04", "B08"]
        )
    except ValueError as e:
        print(f"Input validation error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

Concurrent Operations
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import asyncio
    
    async def process_multiple_regions():
        # Define multiple regions
        regions = [
            {
                "name": "San Francisco",
                "bbox": [-122.5, 37.7, -122.3, 37.9]
            },
            {
                "name": "Los Angeles",
                "bbox": [-118.5, 33.9, -118.1, 34.1]
            }
        ]
        
        # Process regions concurrently
        tasks = []
        for region in regions:
            task = asyncio.create_task(api.download_data(
                bbox=region["bbox"],
                start_date="2023-01-01",
                end_date="2023-01-31",
                bands=["B04", "B08"],
                cloud_cover=20.0
            ))
            tasks.append((region["name"], task))
        
        # Wait for all tasks to complete
        results = {}
        for name, task in tasks:
            results[name] = await task
        
        return results

Input Validation
~~~~~~~~~~~~~~~~

The API performs validation on all inputs:

- **Bounding Box**: Must be a list of 4 float values [min_lon, min_lat, max_lon, max_lat]
- **Dates**: Must be in ISO format (YYYY-MM-DD)
- **Bands**: Must be valid Sentinel-2 band identifiers
- **Cloud Cover**: Must be a float between 0 and 100

Example:

.. code-block:: python

    # This will raise a ValueError due to invalid bbox format
    try:
        result = await api.download_data(
            bbox=[-200, 37.7, -122.3, 37.9],  # Invalid longitude
            start_date="2023-01-01",
            end_date="2023-01-31",
            bands=["B04", "B08"]
        )
    except ValueError as e:
        print(f"Validation error: {e}")

Best Practices
--------------

1. **Minimize Data Volume**: Request only the bands you need for your analysis
2. **Use Cloud Cover Filtering**: Set appropriate cloud cover thresholds to get usable imagery
3. **Handle Errors Gracefully**: Implement proper error handling for all API calls
4. **Clean Up Resources**: Delete temporary files after processing
5. **Use Concurrent Operations**: For processing multiple regions or time periods
6. **Cache Results**: Implement caching to avoid redundant downloads 