.. _memory_system:

=============
Memory System
=============

The Memory System is the core component of the ``memories-dev`` framework, responsible for storing, organizing, and retrieving data in a way that preserves temporal and spatial relationships. This page explains how the memory system works and how to use it effectively.

Overview
========

The Memory System in ``memories-dev`` is designed to mimic aspects of human memory, particularly the ability to:

1. Store and retrieve information across different time periods
2. Organize information spatially
3. Establish relationships between different pieces of information
4. Provide context for understanding data

The system consists of four main components:

1. **Temporal Memory**: Manages data across time
2. **Spatial Memory**: Organizes data geographically
3. **Context Memory**: Maintains contextual information
4. **Relationship Memory**: Tracks connections between data elements

.. mermaid::

                   B --> C1[Temporal Memory]
                   B --> C2[Spatial Memory]
                   B --> C3[Context Memory]
                   B --> C4[Relationship Memory]
                   C1 --> D[Query Interface]
                   C2 --> D
                   C3 --> D
                   C4 --> D
                   D --> E[Applications]
                   
                   classDef source fill:#3b82f6,color:#fff,stroke:#2563eb
                   classDef memory fill:#10b981,color:#fff,stroke:#059669
                   classDef component fill:#8b5cf6,color:#fff,stroke:#7c3aed
                   classDef interface fill:#f59e0b,color:#fff,stroke:#d97706
                   classDef app fill:#ef4444,color:#fff,stroke:#dc2626
                   
                   class A source
                   class B,C1,C2,C3,C4 memory
                   class D interface
                   class E app

Memory Tiers Architecture
=========================

The ``memories-dev`` framework implements a sophisticated multi-tiered memory architecture inspired by modern computing memory hierarchies and human memory systems. This design optimizes for both performance and cost-efficiency.

.. mermaid::

                   B --> C1[Hot Memory]
                   B --> C2[Warm Memory]
                   B --> C3[Cold Memory]
                   B --> C4[Glacier Memory]
                   
                   C1 -.-> B
                   C2 -.-> B
                   C3 -.-> B
                   C4 -.-> B
                   
                   classDef input fill:#3b82f6,color:#fff,stroke:#2563eb
                   classDef manager fill:#8b5cf6,color:#fff,stroke:#7c3aed
                   classDef hot fill:#ef4444,color:#fff,stroke:#dc2626
                   classDef warm fill:#f59e0b,color:#fff,stroke:#d97706
                   classDef cold fill:#10b981,color:#fff,stroke:#059669
                   classDef glacier fill:#1e40af,color:#fff,stroke:#1e3a8a
                   
                   class A input
                   class B manager
                   class C1 hot
                   class C2 warm
                   class C3 cold
                   class C4 glacier

Each memory tier serves a specific purpose:

.. list-table::
   :header-rows: 1
   :widths: 15 25 20 40

   * - Tier
     - Implementation
     - Access Speed
     - Purpose
   * - **Hot Memory**
     - GPU-accelerated memory
     - Microseconds
     - Immediate processing of active data, optimized for parallel computation and neural network operations
   * - **Warm Memory**
     - CPU memory & Redis
     - Milliseconds
     - Fast access to recently used data, supports complex queries and intermediate results
   * - **Cold Memory**
     - DuckDB
     - Milliseconds to seconds
     - Efficient on-device storage for structured data with SQL query capabilities
   * - **Glacier Memory**
     - Parquet files
     - Seconds to minutes
     - Long-term compressed storage for historical data, optimized for space efficiency

The memory system automatically manages data migration between tiers based on access patterns, importance, and age of data. This approach ensures optimal performance while minimizing resource usage.

Mathematical Foundations
========================

The memory system's design is based on several mathematical principles:

Vector Embeddings and Similarity
--------------------------------

Data retrieval in the memory system relies on vector embeddings and similarity metrics. The primary similarity measure used is cosine similarity:





.. math::
   

similarity(A, B) = \cos(\theta) = \frac{A \cdot B}{||A|| \cdot ||B||} = \frac{\sum_{i=1}^{n} A_i B_i}{\sqrt{\sum_{i=1}^{n} A_i^2} \sqrt{\sum_{i=1}^{n} B_i^2}} Where: - $A$ and $B$ are vector embeddings - $\theta$ is the angle between vectors - $||A||$ and $||B||$ are the magnitudes of the vectors For efficient nearest - neighbor search, the system uses FAISS (Facebook AI Similarity Search) with an L2 distance metric: 


.. math::
   

L2(A, B) = ||A - B||_2 = \sqrt{\sum_{i=1}^{n} (A_i - B_i)^2} Temporal Decay Function -------------------- The memory system implements a temporal decay function to model the importance of data over time: 

.. math::
   

importance(t) = \alpha \cdot e^{-\lambda (t_{now} - t)} Where: - $t$ is the timestamp of the data - $t_{now}$ is the current time - $\alpha$ is the initial importance - $\lambda$ is the decay rate parameter This function helps determine when data should be migrated between memory tiers. Spatial Indexing ------------- For efficient spatial queries, the system uses geospatial indexing techniques. The primary approach is based on geohash encoding, which maps 2D coordinates to a 1D string: 
.. math::
   

geohash(lat, lon, precision) = \text{base32\_encode}(\text{interleave\_bits}(lat, lon)) This enables efficient range queries and proximity searches in the spatial domain. Implementation Details =================== The memory system is implemented through several key classes: MemoryManager ----------- The ``MemoryManager`` class coordinates all memory operations across the different tiers: .. code-block:: python
         
            class MemoryManager:
                """Memory manager that handles different memory tiers:
                - Hot Memory: GPU-accelerated memory for immediate processing
                - Warm Memory: CPU and Redis for fast in-memory access
                - Cold Memory: DuckDB for efficient on-device storage
                - Glacier Memory: Parquet files for off-device compressed storage

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
       
       def __init__(
           self,
           storage_path: Path,
           redis_url: str = "redis://localhost:6379",
           redis_db: int = 0,
           hot_memory_size: int = 1000,
           warm_memory_size: int = 10000,
           cold_memory_size: int = 100000,
           glacier_memory_size: int = 1000000
       ):
           # Initialize memory tiers
           self.hot = HotMemory(storage_path=storage_path / "hot", max_size=hot_memory_size)
           self.warm = WarmMemory(redis_url=redis_url, redis_db=redis_db, max_size=warm_memory_size)
           self.cold = ColdMemory(storage_path=storage_path / "cold", max_size=cold_memory_size)
           self.glacier = GlacierMemory(storage_path=storage_path / "glacier", max_size=glacier_memory_size)

The manager provides unified methods for storing, retrieving, and managing data across all tiers:

.. code-block:: python

   # Store data in memory system
   memory_manager.store(data)
   
   # Retrieve data from specific tier
   result = memory_manager.retrieve(query, tier="hot")
   
   # Retrieve all data from a tier
   all_data = memory_manager.retrieve_all(tier="warm")
   
   # Clear specific tier or all tiers
   memory_manager.clear(tier="cold")

Memory Encoding
---------------

The ``MemoryEncoder`` class handles the conversion of various data types into vector embeddings:

.. code-block:: python

   class MemoryEncoder:
       """Encodes different types of data into vector embeddings"""
       
       def __init__(self, embedding_dim: int = 128):
           self.embedding_dim = embedding_dim
           # Initialize encoders for different data types
       
       def encode(self, data: Dict[str, Any]) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
           """Encode data into vector embeddings"""
           # Determine data type and use appropriate encoder
           if "image" in data:
               return self._encode_image(data["image"])
           elif "text" in data:
               return self._encode_text(data["text"])
           elif "vector" in data:
               return self._encode_vector(data["vector"])
           elif "coordinates" in data:
               return self._encode_coordinates(data["coordinates"])
           else:
               raise ValueError("Unsupported data type")

FAISS Integration
-----------------

The system uses FAISS for efficient similarity search:

.. code-block:: python

   def _init_index(self):
       """Initialize FAISS index"""
       index_file = self.index_path / "memory.index"
       if index_file.exists():
           self.index = faiss.read_index(str(index_file))
           with open(self.index_path / "metadata.pkl", "rb") as f:
               self.metadata = pickle.load(f)
       else:
           # Create new index
           self.index = faiss.IndexFlatL2(512)  # 512-dimensional embeddings
           self.metadata = {}

Temporal Memory
===============

Temporal Memory manages data across time, enabling efficient retrieval of historical states and temporal patterns.

Key Features
------------

- **Time Series Storage**: Efficient storage of time-series data with various temporal resolutions
- **Temporal Indexing**: Fast retrieval of data for specific time points or ranges
- **Versioning**: Tracking changes to data over time
- **Temporal Patterns**: Identification of patterns, trends, and anomalies across time
- **Interpolation**: Filling gaps in temporal data through interpolation

Basic Usage
-----------

.. code-block:: python

   from memories.memory import TemporalMemory
   
   # Initialize temporal memory
   temporal_memory = TemporalMemory()
   
   # Store data with temporal information
   temporal_memory.store(
       data=satellite_imagery,
       time_field="acquisition_date",
       location_field="coordinates",
       metadata={"source": "sentinel-2", "processing_level": "L2A"}
   )
   
   # Retrieve data for a specific time point
   image_2020 = temporal_memory.get_at(
       location=(37.7749, -122.4194),
       time="2020-01-01"
   )
   
   # Retrieve data for a time range
   images_2018_2022 = temporal_memory.get_range(
       location=(37.7749, -122.4194),
       start_time="2018-01-01",
       end_time="2022-12-31",
       interval="monthly"  # Options: daily, weekly, monthly, yearly, etc.
   )
   
   # Get temporal statistics
   stats = temporal_memory.get_statistics(
       location=(37.7749, -122.4194),
       time_range=("2018-01-01", "2022-12-31"),
       metrics=["mean", "min", "max", "trend"]
   )

Advanced Features
-----------------

Temporal Memory supports several advanced features:

Temporal Aggregation
^^^^^^^^^^^^^^^^^^^^

Aggregate data across different time periods:

.. code-block:: python

   # Aggregate monthly data to yearly
   yearly_data = temporal_memory.aggregate(
       data=monthly_data,
       aggregation="yearly",
       aggregation_method="mean"  # Options: mean, sum, min, max, etc.
   )

Temporal Interpolation
^^^^^^^^^^^^^^^^^^^^^^

Fill gaps in temporal data:

.. code-block:: python

   # Interpolate missing data points
   complete_series = temporal_memory.interpolate(
       data=sparse_data,
       method="linear",  # Options: linear, cubic, nearest, etc.
       target_resolution="daily"
   )

Change Detection
^^^^^^^^^^^^^^^^

Detect changes between different time points:

.. code-block:: python

   # Detect changes between two time points
   changes = temporal_memory.detect_changes(
       location=(37.7749, -122.4194),
       time1="2018-01-01",
       time2="2022-01-01",
       threshold=0.2,  # Significance threshold
       change_metrics=["area", "intensity"]
   )

Spatial Memory
==============

Spatial Memory organizes data geographically, supporting spatial queries and geographic relationships.

Key Features
------------

- **Spatial Indexing**: Efficient indexing of data by location using techniques like quadtrees or geohashes
- **Spatial Queries**: Support for various spatial queries (point, radius, polygon, etc.)
- **Spatial Relationships**: Identification of spatial relationships between features
- **Multi-resolution Storage**: Storage of data at different spatial resolutions
- **Coordinate System Management**: Handling of different coordinate systems and projections

Basic Usage
-----------

.. code-block:: python

   from memories.memory import SpatialMemory
   
   # Initialize spatial memory
   spatial_memory = SpatialMemory()
   
   # Store data with spatial information
   spatial_memory.store(
       data=buildings,
       geometry_field="geometry",
       metadata={"source": "openstreetmap", "feature_type": "building"}
   )
   
   # Retrieve data at a specific point
   point_data = spatial_memory.get_at(
       location=(37.7749, -122.4194)
   )
   
   # Retrieve data within a radius
   radius_data = spatial_memory.get_radius(
       center=(37.7749, -122.4194),
       radius_km=2,
       feature_types=["building", "road", "landuse"]
   )
   
   # Retrieve data within a polygon
   polygon_data = spatial_memory.get_polygon(
       polygon=city_boundary,
       feature_types=["building"]
   )

Advanced Features
-----------------

Spatial Memory supports several advanced features:

Spatial Analysis
^^^^^^^^^^^^^^^^

Perform spatial analysis operations:

.. code-block:: python

   # Calculate density of features
   density = spatial_memory.calculate_density(
       feature_type="building",
       area=neighborhood_boundary,
       resolution="100m"  # Grid cell size
   )
   
   # Find nearest features
   nearest = spatial_memory.find_nearest(
       location=(37.7749, -122.4194),
       feature_type="park",
       max_distance_km=5,
       limit=5
   )

Spatial Clustering
^^^^^^^^^^^^^^^^^^

Identify clusters of features:

.. code-block:: python

   # Cluster features
   clusters = spatial_memory.cluster(
       feature_type="building",
       area=city_boundary,
       method="dbscan",  # Options: dbscan, kmeans, hierarchical, etc.
       parameters={"eps": 0.1, "min_samples": 5}
   )

Spatial Joins
^^^^^^^^^^^^^

Join datasets based on spatial relationships:

.. code-block:: python

   # Join buildings with land use data
   joined_data = spatial_memory.spatial_join(
       left=buildings,
       right=landuse,
       how="inner",  # Options: inner, left, right
       predicate="intersects"  # Options: intersects, contains, within, etc.
   )

Performance Optimization
========================

The memory system includes several optimizations to ensure efficient operation:

Caching Strategies
------------------

The system implements intelligent caching to minimize redundant operations:

.. mermaid::


The caching strategy includes:

1. **Time-based Expiration**: Cache entries expire after a configurable time period
2. **LRU Eviction**: Least Recently Used entries are evicted when cache size limits are reached
3. **Selective Caching**: Only cache results that are expensive to compute or frequently accessed

Parallel Processing
-------------------

The memory system leverages parallel processing for improved performance:

.. code-block:: python

   async def process_batch(self, items):
       """Process a batch of items in parallel"""
       tasks = [self._process_item(item) for item in items]
       return await asyncio.gather(*tasks)
   
   async def _process_item(self, item):
       """Process a single item"""
       # Implementation details...

This approach significantly improves throughput for batch operations.

Monitoring and Metrics
======================

The memory system provides comprehensive monitoring capabilities:

.. code-block:: python

   # Get memory system statistics
   stats = memory_manager.get_stats()
   
   # Example output:
   # {
   #     "hot_memory": {"size": 256, "capacity": 1000, "utilization": 25.6},
   #     "warm_memory": {"size": 1024, "capacity": 10000, "utilization": 10.2},
   #     "cold_memory": {"size": 5120, "capacity": 100000, "utilization": 5.1},
   #     "glacier_memory": {"size": 10240, "capacity": 1000000, "utilization": 1.0},
   #     "operations": {"reads": 1500, "writes": 500, "cache_hits": 1200, "cache_misses": 300}
   # }

These metrics can be used to monitor system performance and optimize memory usage.

Conclusion
==========

The Memory System is a core component of the ``memories-dev`` framework, providing efficient storage, retrieval, and organization of data across temporal and spatial dimensions. By leveraging a multi-tiered architecture and sophisticated indexing techniques, it enables high-performance operations on large-scale geospatial datasets.

For more information on how to use the Memory System in your applications, see the 'api_reference' and :ref:`examples` sections. 