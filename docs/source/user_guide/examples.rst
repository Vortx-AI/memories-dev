Examples
========

The Memories-Dev framework includes several example applications that demonstrate its capabilities and usage patterns.

Property Analyzer
-----------------

The Property Analyzer example demonstrates how to analyze real estate properties using satellite imagery and local context.

.. code-block:: python

    from memories import MemoryStore, Config
    from examples.property_analyzer import Property

    # Initialize memory store
    config = Config(
        storage_path="./property_data",
        hot_memory_size=50,
        warm_memory_size=200,
        cold_memory_size=1000
    )
    memory_store = MemoryStore(config)

    # Create memory
    property = Property(memory_store)

    # Analyze property
    insights = await property.analyze_property(property_data)

Key features:
- Property condition analysis using satellite imagery
- Location scoring based on amenities and environment
- Investment potential calculation
- Automated recommendations generation

Location Ambience Analyzer
--------------------------

The Location Ambience Analyzer evaluates the environmental and urban characteristics of locations.

.. code-block:: python

    from examples.location_ambience import LocationAnalyzer

    analyzer = LocationAnalyzer(memory_store)
    insights = await analyzer.analyze_location(location_data)

Features:
- Environmental quality assessment
- Urban feature analysis
- Noise level estimation
- Ambience scoring
- Location-specific recommendations

Traffic Analyzer
----------------

The Traffic Analyzer monitors and analyzes traffic patterns and road conditions.

.. code-block:: python

    from examples.traffic_analyzer import TrafficAnalyzer

    analyzer = TrafficAnalyzer(memory_store)
    insights = await analyzer.analyze_traffic(road_segment)

Features:
- Traffic pattern analysis
- Road condition monitoring
- Congestion prediction
- Hazard detection
- Traffic-based recommendations

Water Bodies Monitor
--------------------

The Water Bodies Monitor tracks changes in water bodies using satellite data.

.. code-block:: python

    from examples.water_bodies_monitor import WaterBody

    water_body = WaterBody(memory_store)
    insights = await water_body.analyze_water_body(water_body_data)

Features:
- Water body change detection
- Water quality analysis
- Surface area calculation
- Environmental impact assessment

Common Usage Patterns
---------------------

All examples follow these common patterns:

1. Memory Store Initialization
    - Configure storage paths and memory tiers
    - Initialize appropriate memory store


2. Data Processing
    - Collect data from various sources
    - Process and analyze data
    - Generate insights

3. Memory Management
    - Store insights in appropriate memory tiers
    - Retrieve and update stored information
    - Clean up old or irrelevant data

Requirements
------------

To run the examples, you need:

1. Python 3.8 or higher
2. Memories-Dev framework installed
3. Required environment variables:
    - ``PLANETARY_COMPUTER_API_KEY``
    - ``GEO_MEMORIES`` path set
4. Dependencies from ``requirements.txt``

Installation:

.. code-block:: bash

    pip install -r examples/requirements.txt

For more detailed information about each example, refer to their respective source files in the ``examples/`` directory. 