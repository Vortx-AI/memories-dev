Data Utilities
==============

The Data Utilities module provides a comprehensive suite of tools for efficient data processing, querying, and manipulation within the memories.dev framework. These utilities are designed to handle large-scale data operations with optimal performance and memory efficiency.

🔑 Key Features
--------------

- **High-Performance Querying**:
  - Efficient processing of large-scale parquet datasets
  - Optimized query execution
  - Parallel processing support
  - Memory-aware operations

- **Data Management**:
  - Automatic schema inference
  - Type-safe operations
  - Data validation
  - Error handling

- **Resource Optimization**:
  - Memory usage control
  - Parallel execution
  - Caching strategies
  - Performance monitoring

Data Acquisition
----------------

Data Manager
~~~~~~~~~~~~

.. automodule:: memories.data_acquisition.data_manager
   :members:
   :undoc-members:
   :show-inheritance:

Sentinel API
~~~~~~~~~~~~

.. automodule:: memories.data_acquisition.sources.sentinel_api
   :members:
   :undoc-members:
   :show-inheritance:

Landsat API
~~~~~~~~~~~

.. automodule:: memories.data_acquisition.sources.landsat_api
   :members:
   :undoc-members:
   :show-inheritance:

OpenStreetMap API
~~~~~~~~~~~~~~~~~

.. automodule:: memories.data_acquisition.sources.osm_api
   :members:
   :undoc-members:
   :show-inheritance:

Overture API
~~~~~~~~~~~~

.. automodule:: memories.data_acquisition.sources.overture_api
   :members:
   :undoc-members:
   :show-inheritance:

Data Processing
---------------

Image Processing
~~~~~~~~~~~~~~~~

.. automodule:: memories.utils.processors.image_processor
   :members:
   :undoc-members:
   :show-inheritance:

Vector Processing
~~~~~~~~~~~~~~~~~

.. automodule:: memories.utils.processors.vector_processor
   :members:
   :undoc-members:
   :show-inheritance:

Data Fusion
~~~~~~~~~~~

.. automodule:: memories.utils.processors.data_fusion
   :members:
   :undoc-members:
   :show-inheritance:

Caching System
--------------

.. automodule:: memories.utils.cache
   :members:
   :undoc-members:
   :show-inheritance:

DuckDB Query Utilities
----------------------

.. automodule:: memories.utils.duckdb_utils
   :members:
   :undoc-members:
   :show-inheritance:

query_multiple_parquet
----------------------

.. autofunction:: memories.utils.duckdb_utils.query_multiple_parquet

Parameters
~~~~~~~~~~

- **parquet_files** (List[str]): 
  - List of parquet file paths or glob patterns
  - Supports both absolute and relative paths
  - Accepts wildcards for pattern matching

- **query** (str): 
  - SQL query to execute against the parquet files
  - Supports standard SQL syntax
  - Allows complex aggregations and joins

- **parallel** (bool, optional): 
  - Enable parallel execution
  - Defaults to True
  - Recommended for large datasets

- **memory_limit** (str, optional): 
  - Memory limit for query execution
  - Defaults to '75%'
  - Format: percentage or bytes (e.g., '75%', '8GB')

Returns
~~~~~~~

pandas.DataFrame:
  - Query results as a DataFrame
  - Column types preserved from source
  - Index automatically generated
  - NaN values handled appropriately

Raises
~~~~~~

- **FileNotFoundError**: 
  - No parquet files found at specified paths
  - Invalid file patterns
  - Permission issues

- **QueryExecutionError**: 
  - Invalid SQL syntax
  - Unsupported operations
  - Runtime errors

- **MemoryError**: 
  - Memory limit exceeded
  - System resources exhausted
  - Large result sets

📊 Example Usage
-------------------

Basic Queries
~~~~~~~~~~~~~

.. code-block:: python

    from memories.utils import query_multiple_parquet
    
    # Simple time-based query
    recent_data = query_multiple_parquet(
        parquet_files=["data/2025-02-*.parquet"],
        query="""
            SELECT 
                timestamp,
                location,
                measurements
            FROM parquet_files
            WHERE timestamp >= '2025-02-01'
            ORDER BY timestamp DESC
            LIMIT 1000
""""""""""
    )
    
    # Spatial query with aggregation
    location_stats = query_multiple_parquet(
        parquet_files=["data/locations/*.parquet"],
        query="""
            SELECT 
                location,
                COUNT(*) as event_count,
                AVG(temperature) as avg_temp
            FROM parquet_files
            GROUP BY location
            HAVING event_count > 100
            ORDER BY avg_temp DESC
""""""""""""""""""""""
    )

Advanced Operations
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Complex time-series analysis
    results = query_multiple_parquet(
        parquet_files=[
            "data/environmental/*.parquet",
            "data/sensors/*.parquet"
        ],
        query="""
            WITH hourly_stats AS (
                SELECT 
                    date_trunc('hour', timestamp) as hour,
                    location,
                    avg(temperature) as avg_temp,
                    max(temperature) as max_temp,
                    min(temperature) as min_temp,
                    count(*) as readings,
                    stddev(temperature) as temp_stddev
                FROM parquet_files
                WHERE 
                    timestamp >= '2025-02-01' AND
                    timestamp < '2025-03-01' AND
                    temperature BETWEEN -50 AND 50
                GROUP BY 
                    date_trunc('hour', timestamp),
                    location
            )
            SELECT 
                hour,
                location,
                avg_temp,
                max_temp,
                min_temp,
                readings,
                temp_stddev,
                CASE 
                    WHEN temp_stddev > 5 THEN 'High Variance'
                    WHEN temp_stddev > 2 THEN 'Moderate Variance'
                    ELSE 'Stable'
                END as stability
            FROM hourly_stats
            WHERE readings >= 10
            ORDER BY hour DESC, location
        """,
        parallel=True,
        memory_limit='50%'
    )

⚡ Performance Optimization
----------------------------

1. **Data Organization**
   - Partition files by date/time
   - Use consistent naming patterns
   - Maintain optimal file sizes
   - Implement proper compression

2. **Query Optimization**
   - Use appropriate filters
   - Leverage indexes effectively
   - Optimize join operations
   - Minimize data movement

3. **Resource Management**
   - Monitor memory usage
   - Use chunked processing
   - Implement proper error handling
   - Clean up resources

🔧 Troubleshooting
------------------

Common Issues
~~~~~~~~~~~~~

1. **Performance Problems**
   - Reduce result set size
   - Optimize query patterns
   - Adjust memory limits
   - Use appropriate indexes

2. **Memory Issues**
   - Implement chunking
   - Reduce parallel operations
   - Clear unused resources
   - Monitor memory usage

3. **Data Quality**
   - Validate input data
   - Handle missing values
   - Check data types
   - Verify results

📚 See Also
-----------

- 'memory_store' - Core memory storage interface
- 'data_processing' - Data processing utilities
- 'query_optimization' - Query optimization guide
- 'performance_tuning' - Performance tuning tips

Example Usage
-------------

.. code-block:: python

    from memories.data_acquisition.data_manager import DataManager
    import asyncio
    
    # Initialize data manager
    data_manager = DataManager(cache_dir="./data_cache")
    
    # Define area of interest
    bbox = {
        'xmin': -122.4018,
        'ymin': 37.7914,
        'xmax': -122.3928,
        'ymax': 37.7994
    }
    
    # Define async function to get data
    async def get_data():
        # Get satellite data
        satellite_data = await data_manager.get_satellite_data(
            bbox_coords=bbox,
            start_date="2023-01-01",
            end_date="2023-02-01"
        )
        
        # Get vector data
        vector_data = await data_manager.get_vector_data(
            bbox=bbox,
            layers=["buildings", "roads"]
        )
        
        # Prepare training data
        training_data = await data_manager.prepare_training_data(
            bbox=bbox,
            start_date="2023-01-01",
            end_date="2023-02-01",
            satellite_collections=["sentinel-2-l2a"],
            vector_layers=["buildings", "roads"],
            cloud_cover=10.0
        )
        
        return satellite_data, vector_data, training_data
    
    # Run the async function
    satellite_data, vector_data, training_data = asyncio.run(get_data()) 