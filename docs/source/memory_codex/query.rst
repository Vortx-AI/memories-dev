======================
Memory Querying
======================


Introduction to Memory Querying
-------------------------------

The Memory Codex provides powerful capabilities for querying and retrieving Earth Memories. This guide covers the query API, spatial and temporal filtering, and advanced query techniques for accessing Earth observation data.

Basic Query Structure
--------------------

Memory queries in the Earth Memory framework follow a consistent structure:

.. code-block:: python

   from memories.earth import MemoryCodex
   
   # Initialize the Memory Codex
   codex = MemoryCodex()
   
   # Basic memory query
   result = codex.query(
       memory_types=["VegetationMemory"],  # Type of memory to query
       region=(40.7, -74.0, 41.0, -73.7),  # Spatial extent (N, W, S, E)
       time_range=("2023-01-01", "2023-12-31"),  # Temporal extent
       variables=["ndvi", "evi"],  # Data variables to retrieve
       resolution="30m",  # Desired spatial resolution
       aggregation=None  # No aggregation (raw data)
   )
   
   # Print basic information about the result
   print(f"Retrieved {result.size} memories")
   print(f"Spatial coverage: {result.spatial_coverage.area} km²")
   print(f"Temporal range: {result.temporal_range}")
   print(f"Variables: {result.variables}")

Spatial Queries
--------------

Query memories based on spatial criteria:

.. code-block:: python

   # Query by bounding box
   by_bbox = codex.query(
       region=(40.7, -74.0, 41.0, -73.7),  # NYC area bounding box
       time="latest"
   )
   
   # Query by geometry
   from shapely.geometry import Polygon
   
   # Define a polygon for the query region
   polygon = Polygon([(-74.0, 40.7), (-73.7, 40.7), 
                      (-73.7, 41.0), (-74.0, 41.0)])
   
   by_polygon = codex.query(
       region=polygon,
       time="latest"
   )
   
   # Query by named geographic area
   by_name = codex.query(
       region="amazon-basin",  # Named region
       time="latest"
   )
   
   # Query by distance from point
   near_point = codex.query(
       near_point=(40.7, -74.0),  # Latitude, longitude
       distance=50,  # km
       time="latest"
   )

Temporal Queries
---------------

Query memories based on temporal criteria:

.. code-block:: python

   # Query at a specific point in time
   at_time = codex.query(
       region="global",
       time="2023-06-15T12:00:00Z"  # Specific timestamp
   )
   
   # Query for the latest available data
   latest = codex.query(
       region="global",
       time="latest"
   )
   
   # Query for a time range
   date_range = codex.query(
       region="global",
       time_range=("2023-01-01", "2023-12-31")
   )
   
   # Query with temporal resolution
   monthly = codex.query(
       region="global",
       time_range=("2023-01-01", "2023-12-31"),
       temporal_resolution="monthly"
   )
   
   # Query relative to current time
   recent = codex.query(
       region="global",
       time_range="last-30-days"
   )
   
   # Query for a specific season across years
   summer_pattern = codex.query(
       region="global",
       time_pattern={
           "years": [2020, 2021, 2022, 2023],
           "months": [6, 7, 8]  # June, July, August
       }
   )

Filtering and Selection
----------------------

Filter memories based on specific criteria:

.. code-block:: python

   # Filter by variable values
   high_ndvi = codex.query(
       memory_types=["VegetationMemory"],
       region="amazon-basin",
       time_range=("2023-01-01", "2023-12-31"),
       filters={
           "ndvi": {"min": 0.6}  # Only areas with NDVI > 0.6
       }
   )
   
   # Filter by metadata attributes
   sentinel_data = codex.query(
       region="europe",
       time_range=("2023-01-01", "2023-12-31"),
       metadata_filters={
           "sensor": "sentinel-2",
           "cloud_cover": {"max": 20}
       }
   )
   
   # Filter by quality indicators
   quality_data = codex.query(
       region="africa",
       time_range=("2023-01-01", "2023-12-31"),
       quality_filters={
           "minimum_valid_pixels": 70,  # At least 70% valid pixels
           "qa_flags": ["clear", "water"]  # Only pixels with these QA flags
       }
   )
   
   # Complex filtering with logical operators
   from memories.earth.query import And, Or, Not
   
   complex_filter = codex.query(
       region="global",
       time="latest",
       complex_filter=And(
           Or(
               {"ndvi": {"min": 0.7}},
               {"evi": {"min": 0.6}}
           ),
           Not({"qa_flags": "cloud"})
       )
   )

Aggregation and Statistics
-------------------------

Retrieve aggregated statistics from memories:

.. code-block:: python

   # Spatial aggregation
   mean_by_region = codex.query(
       region="europe",
       time_range=("2023-01-01", "2023-12-31"),
       aggregation="spatial_mean"
   )
   
   # Temporal aggregation
   annual_means = codex.query(
       region="europe",
       time_range=("2020-01-01", "2023-12-31"),
       aggregation="temporal_mean",
       aggregation_period="yearly"
   )
   
   # Zonal statistics
   from memories.earth.query import ZonalAggregation
   import geopandas as gpd
   
   # Load administrative boundaries
   countries = gpd.read_file("path/to/countries.geojson")
   
   # Calculate zonal statistics by country
   zonal_stats = codex.query(
       region="europe",
       time="2023-06-15",
       aggregation=ZonalAggregation(
           zones=countries,
           statistics=["mean", "min", "max", "std"],
           zone_identity_field="ISO_A3"
       )
   )
   
   # Print results
   for country_code, stats in zonal_stats.items():
       print(f"Country: {country_code}")
       print(f"  Mean temperature: {stats['temperature']['mean']:.1f}°C")
       print(f"  Temperature range: {stats['temperature']['min']:.1f} - {stats['temperature']['max']:.1f}°C")

Query Across Memory Types
------------------------

Query multiple memory types in a single operation:

.. code-block:: python

   # Query across different memory types
   combined = codex.query(
       memory_types=["TemperatureMemory", "PrecipitationMemory", "VegetationMemory"],
       region="amazon-basin",
       time_range=("2023-01-01", "2023-12-31"),
       temporal_resolution="monthly"
   )
   
   # Calculate relationship between temperature and vegetation
   correlation = combined.calculate_correlation(
       variable_pairs=[("temperature", "ndvi")],
       method="pearson"
   )
   
   print(f"Temperature-NDVI correlation: {correlation['temperature']['ndvi']:.3f}")

Working with Query Results
-------------------------

Results from memory queries can be processed in various ways:

.. code-block:: python

   # Get query result as xarray Dataset
   result = codex.query(
       memory_types=["TemperatureMemory"],
       region="europe",
       time_range=("2023-01-01", "2023-12-31"),
       temporal_resolution="monthly"
   )
   
   # Convert to xarray for analysis
   ds = result.to_xarray()
   
   # Calculate monthly anomalies
   climatology = ds.groupby("time.month").mean()
   anomalies = ds.groupby("time.month") - climatology
   
   # Export to other formats
   result.to_netcdf("temperature_2023.nc")
   result.to_geotiff("temperature_2023.tif")
   result.to_zarr("temperature_2023.zarr")
   
   # Plot the data
   result.plot(
       variable="temperature",
       time="2023-07-15",
       cmap="RdBu_r",
       vmin=10, vmax=35,
       title="July 2023 Temperature"
   )

Advanced Query Capabilities
--------------------------

The Memory Codex supports advanced query capabilities for complex scenarios:

Spatiotemporal Patterns
~~~~~~~~~~~~~~~~~~~~~~

Search for specific spatiotemporal patterns:

.. code-block:: python

   from memories.earth.query import SpatiotemporalPattern
   
   # Define a pattern to search for
   drought_pattern = SpatiotemporalPattern(
       variables=["soil_moisture", "precipitation", "temperature"],
       pattern_definition={
           "soil_moisture": {"trend": "decreasing", "duration": "60 days", "magnitude": "severe"},
           "precipitation": {"anomaly": "negative", "duration": "60 days", "percentile": 10},
           "temperature": {"anomaly": "positive", "duration": "30 days", "percentile": 90}
       }
   )
   
   # Search for the pattern
   drought_events = codex.query_pattern(
       pattern=drought_pattern,
       region="western-us",
       time_range=("2000-01-01", "2023-12-31")
   )
   
   # Print detected events
   for event in drought_events:
       print(f"Drought event detected:")
       print(f"  Region: {event.region}")
       print(f"  Start date: {event.start_date}")
       print(f"  End date: {event.end_date}")
       print(f"  Severity: {event.severity}")

Memory Similarity Search
~~~~~~~~~~~~~~~~~~~~~~

Find memories similar to a reference memory:

.. code-block:: python

   from memories.earth.query import SimilarityQuery
   
   # Get a reference memory
   reference = codex.get_memory("amazon-drought-2015")
   
   # Find similar events
   similar_events = codex.query_similarity(
       reference=reference,
       search_space={
           "region": "south-america",
           "time_range": ("2000-01-01", "2023-12-31"),
           "memory_types": ["DroughtMemory"]
       },
       similarity_metrics=["pattern", "intensity", "spatial_extent"],
       top_k=5
   )
   
   # Print similar events
   for idx, event in enumerate(similar_events):
       print(f"#{idx+1} Similar event: {event.name}")
       print(f"  Similarity score: {event.similarity:.2f}")
       print(f"  Time period: {event.start_date} to {event.end_date}")
       print(f"  Pattern similarity: {event.similarity_components['pattern']:.2f}")
       print(f"  Intensity similarity: {event.similarity_components['intensity']:.2f}")

Anomaly Detection
~~~~~~~~~~~~~~~~

Detect anomalies in Earth memory data:

.. code-block:: python

   from memories.earth.query import AnomalyDetection
   
   # Configure anomaly detection
   anomaly_detector = AnomalyDetection(
       method="isolation_forest",
       baseline_period=("2000-01-01", "2020-12-31"),
       variables=["temperature", "precipitation"],
       contamination=0.05,  # Expected proportion of anomalies
       seasonality=True
   )
   
   # Detect anomalies
   anomalies = codex.query_anomalies(
       detector=anomaly_detector,
       region="global",
       time_range=("2021-01-01", "2023-12-31"),
       temporal_resolution="monthly"
   )
   
   # Print anomalies
   for anomaly in anomalies:
       print(f"Anomaly detected:")
       print(f"  Region: {anomaly.region}")
       print(f"  Time: {anomaly.time}")
       print(f"  Type: {anomaly.type}")
       print(f"  Severity: {anomaly.severity}")
       print(f"  Contributing variables: {anomaly.contributing_variables}")

Cross-modal Queries
~~~~~~~~~~~~~~~~~

Query across different data modalities:

.. code-block:: python

   # Query relating satellite imagery and ground measurements
   cross_modal = codex.cross_modal_query(
       primary_modal={
           "memory_types": ["SatelliteImagery"],
           "variables": ["rgb"]
       },
       secondary_modal={
           "memory_types": ["GroundSensorNetwork"],
           "variables": ["air_quality"]
       },
       region="urban-areas",
       time_range=("2023-01-01", "2023-12-31"),
       relationship="co-located",
       max_distance=1000,  # meters
       max_time_difference="1 day"
   )
   
   # Analyze the relationship between modalities
   for pair in cross_modal:
       print(f"Matching pair:")
       print(f"  Satellite image: {pair.primary.id}")
       print(f"  Ground measurement: {pair.secondary.id}")
       print(f"  Spatial distance: {pair.spatial_distance} meters")
       print(f"  Temporal distance: {pair.temporal_distance} hours")

Scheduled and Persistent Queries
------------------------------

Set up scheduled queries that run automatically:

.. code-block:: python

   from memories.earth.query import ScheduledQuery
   
   # Define a query to run daily
   daily_monitoring = ScheduledQuery(
       name="global-temperature-monitoring",
       query={
           "memory_types": ["TemperatureMemory"],
           "region": "global",
           "time": "latest",
           "variables": ["temperature"],
           "aggregation": "spatial_mean"
       },
       schedule="daily at 00:00 UTC",
       store_results=True,
       result_retention="90 days",
       notifications={
           "on_completion": True,
           "email": "alerts@example.org"
       }
   )
   
   # Register the scheduled query
   query_id = codex.register_scheduled_query(daily_monitoring)
   
   # Update an existing scheduled query
   codex.update_scheduled_query(
       query_id=query_id,
       updates={
           "schedule": "daily at 06:00 UTC",
           "notifications": {
               "on_completion": True,
               "on_error": True,
               "email": ["alerts@example.org", "admin@example.org"]
           }
       }
   )
   
   # List all scheduled queries
   scheduled_queries = codex.list_scheduled_queries()
   for query in scheduled_queries:
       print(f"Query: {query.name} (ID: {query.id})")
       print(f"  Schedule: {query.schedule}")
       print(f"  Last run: {query.last_run}")
       print(f"  Status: {query.status}")

Query Optimization
----------------

Optimize query performance for different scenarios:

.. code-block:: python

   # Standard query without optimization
   standard_query = codex.query(
       memory_types=["SatelliteImagery"],
       region="europe",
       time_range=("2023-01-01", "2023-12-31")
   )
   
   # Query with performance optimization
   optimized_query = codex.query(
       memory_types=["SatelliteImagery"],
       region="europe",
       time_range=("2023-01-01", "2023-12-31"),
       optimization={
           "strategy": "performance",
           "cache": True,
           "parallel": True,
           "chunk_size": (1024, 1024),
           "max_memory": "16GB"
       }
   )
   
   # Query with storage tier optimizations
   tier_optimized = codex.query(
       memory_types=["TemperatureMemory"],
       region="global",
       time_range=("2000-01-01", "2023-12-31"),
       optimization={
           "strategy": "storage_aware",
           "prefer_tiers": ["warm", "cold"],
           "allow_degraded_resolution": True,
           "max_retrieval_time": "5 minutes"
       }
   )

Building Search Indexes
---------------------

Create and use search indexes to accelerate common queries:

.. code-block:: python

   from memories.earth.index import MemorySearchIndex
   
   # Create a spatial search index
   spatial_index = MemorySearchIndex(
       name="vegetation-spatial-index",
       memory_types=["VegetationMemory"],
       index_type="spatial",
       resolution="1km",
       update_frequency="weekly"
   )
   
   # Register the index with the codex
   codex.register_index(spatial_index)
   
   # Create a temporal search index
   temporal_index = MemorySearchIndex(
       name="temperature-temporal-index",
       memory_types=["TemperatureMemory"],
       index_type="temporal",
       granularity="daily",
       update_frequency="daily"
   )
   
   # Register the index with the codex
   codex.register_index(temporal_index)
   
   # Use indexes in queries
   indexed_query = codex.query(
       memory_types=["VegetationMemory"],
       region="amazon-basin",
       time="latest",
       use_index=True  # Let system choose appropriate index
   )
   
   # Explicitly specify index
   specific_index_query = codex.query(
       memory_types=["VegetationMemory"],
       region="amazon-basin",
       time="latest",
       index="vegetation-spatial-index"
   )

Custom Query Extensions
---------------------

Extend the query system with custom functions:

.. code-block:: python

   from memories.earth.query import QueryExtension
   
   # Define a custom query extension
   class VegetationStressDetector(QueryExtension):
       """Custom extension to detect vegetation stress conditions."""
       
       def __init__(self, drought_threshold=-1.5, heat_threshold=35.0):
           self.drought_threshold = drought_threshold
           self.heat_threshold = heat_threshold
       
       def process(self, query_result):
           """Process query results to detect vegetation stress."""
           # Implementation details...
           return stress_areas
   
   # Register the extension
   codex.register_query_extension(VegetationStressDetector)
   
   # Use the extension in a query
   stress_query = codex.query(
       memory_types=["VegetationMemory", "TemperatureMemory", "PrecipitationMemory"],
       region="western-us",
       time="latest",
       extensions=[
           VegetationStressDetector(drought_threshold=-2.0, heat_threshold=37.0)
       ]
   )
   
   # Get the extension results
   stress_areas = stress_query.get_extension_result("VegetationStressDetector")
   print(f"Detected {len(stress_areas)} areas under vegetation stress")

Multi-source Data Fusion
----------------------

Fuse data from multiple sources in a single query:

.. code-block:: python

   from memories.earth.query import DataFusion
   
   # Define a data fusion operation
   drought_index_fusion = DataFusion(
       name="combined-drought-index",
       sources=[
           {"memory_type": "PrecipitationMemory", "variable": "spi", "weight": 0.4},
           {"memory_type": "SoilMoistureMemory", "variable": "percentile", "weight": 0.4},
           {"memory_type": "VegetationMemory", "variable": "vhi", "weight": 0.2}
       ],
       fusion_method="weighted_average",
       normalization="min_max",
       output_range=(0, 1)
   )
   
   # Execute a query with the fusion
   drought_conditions = codex.query(
       region="western-us",
       time="latest",
       fusion=drought_index_fusion
   )
   
   # Access the fused data
   fused_index = drought_conditions.get_fused_data()
   
   # Plot the results
   drought_conditions.plot(
       variable="combined-drought-index",
       cmap="YlOrBr_r",
       vmin=0, vmax=1,
       title="Combined Drought Index (Higher = More Severe)"
   )

Next Steps
---------

After learning about memory querying:

- Explore data visualization options in :doc:`visualization`
- Learn about creating custom analyses in :doc:`../analysis/custom_analyses`
- Set up automated processing workflows in :doc:`../integration/workflows` 