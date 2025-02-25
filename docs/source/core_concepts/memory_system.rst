.. _memory_system:

=============
Memory System
=============

The Memory System is the core component of the ``memories-dev`` framework, responsible for storing, organizing, and retrieving data in a way that preserves temporal and spatial relationships. This page explains how the memory system works and how to use it effectively.

Overview
=======

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
   :caption: Memory System Components
   :align: center

   graph TD
       A[Data Sources] --> B[Memory System]
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

Temporal Memory
=============

Temporal Memory manages data across time, enabling efficient retrieval of historical states and temporal patterns.

Key Features
----------

- **Time Series Storage**: Efficient storage of time-series data with various temporal resolutions
- **Temporal Indexing**: Fast retrieval of data for specific time points or ranges
- **Versioning**: Tracking changes to data over time
- **Temporal Patterns**: Identification of patterns, trends, and anomalies across time
- **Interpolation**: Filling gaps in temporal data through interpolation

Basic Usage
---------

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
--------------

Temporal Memory supports several advanced features:

Temporal Aggregation
^^^^^^^^^^^^^^^^^^

Aggregate data across different time periods:

.. code-block:: python

   # Aggregate monthly data to yearly
   yearly_data = temporal_memory.aggregate(
       data=monthly_data,
       aggregation="yearly",
       aggregation_method="mean"  # Options: mean, sum, min, max, etc.
   )

Temporal Interpolation
^^^^^^^^^^^^^^^^^^^

Fill gaps in temporal data:

.. code-block:: python

   # Interpolate missing data points
   complete_series = temporal_memory.interpolate(
       data=sparse_data,
       method="linear",  # Options: linear, cubic, nearest, etc.
       target_resolution="daily"
   )

Change Detection
^^^^^^^^^^^^^

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
============

Spatial Memory organizes data geographically, supporting spatial queries and geographic relationships.

Key Features
----------

- **Spatial Indexing**: Efficient indexing of data by location using techniques like quadtrees or geohashes
- **Spatial Queries**: Support for various spatial queries (point, radius, polygon, etc.)
- **Spatial Relationships**: Identification of spatial relationships between features
- **Multi-resolution Storage**: Storage of data at different spatial resolutions
- **Coordinate System Management**: Handling of different coordinate systems and projections

Basic Usage
---------

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
--------------

Spatial Memory supports several advanced features:

Spatial Analysis
^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^

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
^^^^^^^^^^^

Join datasets based on spatial relationships:

.. code-block:: python

   # Join buildings with census tracts
   joined_data = spatial_memory.spatial_join(
       left=buildings,
       right=census_tracts,
       join_type="within",  # Options: within, intersects, contains, etc.
       fields_to_join=["population", "median_income", "housing_density"]
   )

Context Memory
============

Context Memory maintains contextual information about locations, events, and entities, providing a richer understanding of the data.

Key Features
----------

- **Entity Recognition**: Identification of entities (buildings, roads, natural features, etc.)
- **Attribute Storage**: Storage of attributes and properties for entities
- **Historical Context**: Maintenance of historical context for locations and entities
- **Semantic Information**: Storage of semantic information and descriptions
- **External Knowledge Integration**: Integration with external knowledge sources

Basic Usage
---------

.. code-block:: python

   from memories.memory import ContextMemory
   
   # Initialize context memory
   context_memory = ContextMemory()
   
   # Store contextual information for a location
   context_memory.store(
       location="San Francisco",
       context_type="city",
       attributes={
           "population": 874961,
           "area_sq_km": 121.4,
           "founded": "1776-06-29",
           "climate": "mediterranean",
           "major_industries": ["technology", "tourism", "finance"]
       }
   )
   
   # Retrieve context for a location
   sf_context = context_memory.get(
       location="San Francisco",
       context_type="city"
   )
   
   # Retrieve specific attributes
   population = context_memory.get_attribute(
       location="San Francisco",
       attribute="population"
   )
   
   # Find locations with specific context
   tech_cities = context_memory.find(
       context_type="city",
       query={"major_industries": "technology"}
   )

Advanced Features
--------------

Context Memory supports several advanced features:

Hierarchical Context
^^^^^^^^^^^^^^^^^

Navigate hierarchical relationships:

.. code-block:: python

   # Get parent context
   california = context_memory.get_parent(
       location="San Francisco",
       parent_type="state"
   )
   
   # Get child contexts
   neighborhoods = context_memory.get_children(
       location="San Francisco",
       child_type="neighborhood"
   )

Temporal Context
^^^^^^^^^^^^^

Access historical context:

.. code-block:: python

   # Get historical context
   sf_1950 = context_memory.get_historical(
       location="San Francisco",
       time="1950-01-01",
       attributes=["population", "major_industries"]
   )
   
   # Get context evolution over time
   population_history = context_memory.get_attribute_history(
       location="San Francisco",
       attribute="population",
       time_range=("1900-01-01", "2020-01-01"),
       interval="decade"
   )

Semantic Context
^^^^^^^^^^^^^

Access semantic information:

.. code-block:: python

   # Get semantic description
   description = context_memory.get_description(
       location="San Francisco",
       detail_level="medium"  # Options: brief, medium, detailed
   )
   
   # Get related concepts
   related = context_memory.get_related_concepts(
       concept="Golden Gate Bridge",
       relationship_types=["part_of", "located_in", "associated_with"]
   )

Relationship Memory
================

Relationship Memory tracks connections between different data elements across time and space, enabling complex queries and insights.

Key Features
----------

- **Relationship Types**: Support for various relationship types (spatial, temporal, causal, etc.)
- **Relationship Attributes**: Storage of attributes for relationships
- **Relationship Queries**: Ability to query based on relationships
- **Graph Representation**: Internal graph representation of relationships
- **Relationship Inference**: Inference of implicit relationships from explicit ones

Basic Usage
---------

.. code-block:: python

   from memories.memory import RelationshipMemory
   
   # Initialize relationship memory
   relationship_memory = RelationshipMemory()
   
   # Define a relationship
   relationship_memory.create(
       source="Golden Gate Bridge",
       target="San Francisco",
       relationship_type="located_in",
       attributes={
           "since": "1937-05-27",
           "distance_to_downtown_km": 8.4
       }
   )
   
   # Retrieve relationships for an entity
   bridge_relationships = relationship_memory.get_relationships(
       entity="Golden Gate Bridge"
   )
   
   # Find entities with specific relationships
   sf_landmarks = relationship_memory.find_related(
       target="San Francisco",
       relationship_type="located_in",
       entity_type="landmark"
   )
   
   # Check if a relationship exists
   is_in_sf = relationship_memory.has_relationship(
       source="Golden Gate Bridge",
       target="San Francisco",
       relationship_type="located_in"
   )

Advanced Features
--------------

Relationship Memory supports several advanced features:

Path Finding
^^^^^^^^^^

Find paths between entities:

.. code-block:: python

   # Find path between entities
   path = relationship_memory.find_path(
       source="Golden Gate Bridge",
       target="Fisherman's Wharf",
       relationship_types=["connected_to", "near"],
       max_depth=3
   )

Relationship Inference
^^^^^^^^^^^^^^^^^^^

Infer relationships based on existing ones:

.. code-block:: python

   # Infer new relationships
   inferred = relationship_memory.infer_relationships(
       entity="Golden Gate Bridge",
       inference_rules=[
           {"if": "located_in", "then": "part_of"},
           {"if": ["connected_to", "located_in"], "then": "accessible_from"}
       ]
   )

Relationship Analytics
^^^^^^^^^^^^^^^^^^^

Analyze relationship patterns:

.. code-block:: python

   # Analyze relationship network
   analytics = relationship_memory.analyze_network(
       center_entity="San Francisco",
       max_depth=2,
       metrics=["centrality", "clustering", "community"]
   )

Integrated Memory Queries
======================

The real power of the Memory System comes from integrated queries that combine temporal, spatial, contextual, and relationship aspects.

Basic Integrated Queries
---------------------

.. code-block:: python

   from memories.memory import MemorySystem
   
   # Initialize the memory system
   memory = MemorySystem()
   
   # Perform an integrated query
   results = memory.query(
       location="San Francisco",
       time_range=("2010-01-01", "2020-01-01"),
       spatial_extent="city_boundary",
       context_types=["urban_development", "climate"],
       relationships=["contains", "affected_by"],
       query_parameters={
           "feature_types": ["building", "park", "road"],
           "metrics": ["area_change", "density_change"],
           "min_significance": 0.2
       }
   )

Advanced Integrated Queries
------------------------

Complex queries combining multiple memory aspects:

.. code-block:: python

   # Find areas with significant urban growth near water bodies
   urban_growth_near_water = memory.query(
       # Spatial component
       region="Bay Area",
       spatial_relationship={
           "near": {
               "feature_type": "water_body",
               "max_distance_km": 2
           }
       },
       
       # Temporal component
       time_range=("2000-01-01", "2020-01-01"),
       temporal_metrics=["growth_rate", "change_acceleration"],
       
       # Context component
       context_filters={
           "land_use": "urban",
           "development_type": ["residential", "commercial"]
       },
       
       # Relationship component
       relationship_filters=[
           {
               "type": "affected_by",
               "target_type": "policy",
               "target_attributes": {
                   "category": "zoning",
                   "year": {"$gte": 2000}
               }
           }
       ],
       
       # Query parameters
       threshold=0.3,
       sort_by="growth_rate",
       limit=10
   )

Memory System Configuration
========================

The Memory System can be configured to optimize for different use cases:

.. code-block:: python

   from memories.memory import configure_memory
   
   # Configure the memory system
   configure_memory(
       # Storage configuration
       storage_type="hybrid",  # Options: local, database, cloud, hybrid
       local_path="./memories_data",
       database_uri="postgresql://user:password@localhost:5432/memories",
       cloud_config={
           "provider": "aws",
           "bucket": "memories-data",
           "region": "us-west-2"
       },
       
       # Performance configuration
       cache_size_gb=2,
       max_memory_gb=8,
       index_type="rtree",  # Options: rtree, quadtree, geohash
       
       # Feature configuration
       enable_versioning=True,
       enable_compression=True,
       enable_encryption=False,
       
       # Advanced configuration
       temporal_resolution="auto",  # Options: auto, daily, weekly, monthly, etc.
       spatial_resolution="auto",  # Options: auto, high, medium, low
       relationship_depth=3
   )

Best Practices
============

Here are some best practices for using the Memory System effectively:

Data Organization
---------------

- **Consistent Time Formats**: Use consistent time formats (ISO 8601 recommended) for all temporal data
- **Standardized Coordinates**: Use standardized coordinate systems (WGS 84 recommended) for spatial data
- **Hierarchical Context**: Organize contextual information hierarchically for efficient navigation
- **Meaningful Relationships**: Define clear, meaningful relationship types that capture important connections

Performance Optimization
---------------------

- **Appropriate Indexing**: Choose appropriate indexing strategies based on your query patterns
- **Caching Strategy**: Configure caching based on your data access patterns
- **Batch Operations**: Use batch operations for storing and retrieving large amounts of data
- **Query Optimization**: Structure queries to minimize data retrieval and processing

Data Quality
----------

- **Validation**: Validate data before storing it in the memory system
- **Uncertainty Tracking**: Track and propagate uncertainty in data and derived insights
- **Provenance**: Maintain provenance information for all data
- **Regular Updates**: Keep data up-to-date with regular updates and versioning

Integration with Other Components
------------------------------

- **Data Acquisition Integration**: Seamlessly integrate with the Data Acquisition Layer for automatic data storage
- **Model Integration**: Connect with the Model Integration Layer for advanced analysis
- **Application Integration**: Provide optimized query interfaces for applications

Next Steps
=========

* Explore the :ref:`data_sources` available for acquiring data to store in the memory system
* Learn about :ref:`async_processing` for efficient data handling
* Understand how to use the memory system with :ref:`ai_capabilities` for advanced analysis
* Check out the :ref:`examples` to see the memory system in action 