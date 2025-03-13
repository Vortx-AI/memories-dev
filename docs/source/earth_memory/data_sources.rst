=============
Data Sources
=============

.. image:: https://img.shields.io/badge/version-2.0.6-blue.svg
   :target: https://github.com/Vortx-AI/memories-dev/releases/tag/v2.0.6
   :alt: Version
   :align: right

.. contents:: Table of Contents
   :depth: 2
   :local:
   :backlinks: none

Introduction
============

The Earth Memory system integrates a diverse range of data sources to create a comprehensive understanding of the physical world. This document provides detailed information about the data sources supported by the memories-dev framework, including configuration options, usage examples, and best practices.

Satellite Imagery
=================

Satellite imagery provides visual data of the Earth's surface, enabling analysis of land cover, urban development, environmental changes, and more.

Supported Providers
-------------------

The memories-dev framework supports multiple satellite imagery providers:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Provider
     - Description
     - Data Types
   * - **Sentinel-2**
     - European Space Agency's Earth observation mission
     - Multispectral imagery (10m-60m resolution)
   * - **Landsat**
     - NASA/USGS Earth observation program
     - Multispectral imagery (15m-100m resolution)
   * - **MODIS**
     - NASA's Moderate Resolution Imaging Spectroradiometer
     - Daily global imagery (250m-1km resolution)
   * - **Planet**
     - Commercial high-resolution satellite imagery
     - High-resolution imagery (0.5m-5m resolution)
   * - **Maxar**
     - Commercial very high-resolution satellite imagery
     - Very high-resolution imagery (0.3m-0.5m resolution)
   * - **NAIP**
     - USDA National Agriculture Imagery Program
     - Aerial imagery of US agricultural lands (1m resolution)
   * - **Sentinel-1**
     - European Space Agency's radar imaging mission
     - Synthetic Aperture Radar (SAR) imagery

Configuration
-------------

Configure satellite imagery providers using the following options:

.. code-block:: python

    from memories.earth.satellite import SatelliteImagery
    
    # Initialize with default providers
    imagery = SatelliteImagery()
    
    # Initialize with specific providers and API keys
    imagery = SatelliteImagery(
        providers={
            "sentinel2": {
                "api_key": "your_sentinel_hub_api_key",
                "collection": "sentinel-2-l2a",
                "max_cloud_cover": 20
            },
            "landsat": {
                "api_key": "your_usgs_api_key",
                "collection": "landsat-8-c2-l2",
                "max_cloud_cover": 20
            },
            "planet": {
                "api_key": "your_planet_api_key",
                "item_types": ["PSScene4Band"],
                "max_cloud_cover": 15
            }
        },
        default_provider="sentinel2"
    )

Usage Example
-------------

.. code-block:: python

    from memories.earth.satellite import SatelliteImagery
    
    # Initialize satellite imagery client
    imagery = SatelliteImagery()
    
    # Fetch historical imagery for a location
    images = await imagery.get_historical_imagery(
        location=(37.7749, -122.4194),  # San Francisco
        time_range=("2000-01-01", "2023-01-01"),
        interval="yearly",
        provider="landsat",
        bands=["red", "green", "blue", "nir"],
        max_cloud_cover=10
    )
    
    # Process imagery
    processed_images = imagery.process_imagery(
        images=images,
        operations=["cloud_removal", "atmospheric_correction", "normalization"]
    )
    
    # Calculate vegetation index
    ndvi = imagery.calculate_index(
        images=processed_images,
        index_type="ndvi"
    )
    
    # Visualize results
    imagery.visualize(
        data=ndvi,
        colormap="RdYlGn",
        output="vegetation_changes.html"
    )

Geospatial Vector Data
======================

Geospatial vector data represents discrete geographic features like buildings, roads, administrative boundaries, and points of interest.

Supported Sources
-----------------

The memories-dev framework supports multiple vector data sources:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Source
     - Description
     - Data Types
   * - **OpenStreetMap**
     - Collaborative mapping project
     - Buildings, roads, land use, points of interest
   * - **Natural Earth**
     - Public domain map dataset
     - Administrative boundaries, physical features
   * - **GADM**
     - Database of global administrative areas
     - Administrative boundaries
   * - **Microsoft Building Footprints**
     - AI-generated building footprints
     - Building polygons
   * - **TIGER/Line**
     - US Census Bureau geographic database
     - US administrative boundaries, roads, addresses
   * - **Overture Maps**
     - Open map data foundation
     - Buildings, places, transportation, administrative areas

Configuration
-------------

Configure vector data sources using the following options:

.. code-block:: python

    from memories.earth.vector import VectorData
    
    # Initialize with default sources
    vector_data = VectorData()
    
    # Initialize with specific sources and options
    vector_data = VectorData(
        sources={
            "osm": {
                "download_method": "overpass",
                "cache_directory": "./data/osm_cache"
            },
            "natural_earth": {
                "scale": "10m",  # 10m, 50m, or 110m
                "cache_directory": "./data/natural_earth_cache"
            },
            "microsoft_buildings": {
                "regions": ["usa"],
                "cache_directory": "./data/building_cache"
            }
        },
        default_source="osm"
    )

Usage Example
-------------

.. code-block:: python

    from memories.earth.vector import VectorData
    
    # Initialize vector data client
    vector_data = VectorData()
    
    # Fetch buildings for a location
    buildings = await vector_data.get_features(
        location=(37.7749, -122.4194),  # San Francisco
        feature_type="building",
        radius_km=2,
        source="osm"
    )
    
    # Fetch administrative boundaries
    admin_boundaries = await vector_data.get_admin_boundaries(
        location="San Francisco, CA",
        admin_levels=[2, 4, 8],  # Country, state, city
        source="gadm"
    )
    
    # Calculate spatial metrics
    metrics = vector_data.calculate_metrics(
        features=buildings,
        metrics=["count", "density", "average_area"]
    )
    
    # Visualize results
    vector_data.visualize(
        features=buildings,
        style={"color": "blue", "fillOpacity": 0.5},
        output="buildings.html"
    )

Environmental Data
==================

Environmental data includes climate, weather, air quality, water resources, and other environmental metrics.

Supported Sources
-----------------

The memories-dev framework supports multiple environmental data sources:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Source
     - Description
     - Data Types
   * - **NOAA**
     - US National Oceanic and Atmospheric Administration
     - Weather, climate, ocean data
   * - **NASA POWER**
     - NASA Prediction of Worldwide Energy Resources
     - Solar radiation, meteorology, climate data
   * - **WorldClim**
     - Global climate data
     - Temperature, precipitation, bioclimatic variables
   * - **EPA**
     - US Environmental Protection Agency
     - Air quality, water quality, environmental hazards
   * - **Copernicus Climate Data Store**
     - European climate data service
     - Climate reanalysis, projections, observations
   * - **USGS Water Data**
     - US Geological Survey water data
     - Stream flow, groundwater, water quality

Configuration
-------------

Configure environmental data sources using the following options:

.. code-block:: python

    from memories.earth.environmental import EnvironmentalData
    
    # Initialize with default sources
    env_data = EnvironmentalData()
    
    # Initialize with specific sources and API keys
    env_data = EnvironmentalData(
        sources={
            "noaa": {
                "api_key": "your_noaa_api_key",
                "datasets": ["GHCND", "GSOD"]
            },
            "nasa_power": {
                "parameters": ["T2M", "PRECTOT", "RH2M"],
                "cache_directory": "./data/nasa_power_cache"
            },
            "epa": {
                "api_key": "your_epa_api_key",
                "datasets": ["air_quality", "water_quality"]
            }
        },
        default_source="noaa"
    )

Usage Example
-------------

.. code-block:: python

    from memories.earth.environmental import EnvironmentalData
    
    # Initialize environmental data client
    env_data = EnvironmentalData()
    
    # Fetch climate data for a location
    climate_data = await env_data.get_climate_data(
        location=(37.7749, -122.4194),  # San Francisco
        time_range=("2000-01-01", "2023-01-01"),
        variables=["temperature", "precipitation", "humidity"],
        source="noaa"
    )
    
    # Fetch air quality data
    air_quality = await env_data.get_air_quality(
        location="San Francisco, CA",
        time_range=("2020-01-01", "2023-01-01"),
        pollutants=["pm25", "ozone", "no2"],
        source="epa"
    )
    
    # Analyze climate trends
    trends = env_data.analyze_trends(
        data=climate_data,
        variables=["temperature"],
        trend_type="linear"
    )
    
    # Visualize results
    env_data.visualize(
        data=climate_data,
        variables=["temperature"],
        output="temperature_trends.html"
    )

Historical Maps and Imagery
===========================

Historical maps and imagery provide views of locations from the past, enabling analysis of changes over time.

Supported Sources
-----------------

The memories-dev framework supports multiple historical data sources:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Source
     - Description
     - Data Types
   * - **USGS Historical Topographic Maps**
     - US Geological Survey historical maps
     - Topographic maps (1880s-present)
   * - **David Rumsey Map Collection**
     - Historical map collection
     - Historical maps worldwide
   * - **Old Maps Online**
     - Aggregator of historical maps
     - Historical maps from multiple sources
   * - **Historical Aerial Photos**
     - Various sources of historical aerial imagery
     - Aerial photographs (1930s-present)
   * - **Landsat Legacy**
     - Historical Landsat imagery
     - Satellite imagery (1972-present)
   * - **Corona Satellite Imagery**
     - Declassified Cold War satellite imagery
     - Satellite imagery (1960-1972)

Configuration
-------------

Configure historical data sources using the following options:

.. code-block:: python

    from memories.earth.historical import HistoricalData
    
    # Initialize with default sources
    historical_data = HistoricalData()
    
    # Initialize with specific sources and API keys
    historical_data = HistoricalData(
        sources={
            "usgs_topo": {
                "api_key": "your_usgs_api_key",
                "cache_directory": "./data/usgs_topo_cache"
            },
            "rumsey": {
                "api_key": "your_rumsey_api_key",
                "max_results": 10
            },
            "landsat_legacy": {
                "collections": ["landsat-1-mss", "landsat-5-tm"],
                "cache_directory": "./data/landsat_legacy_cache"
            }
        },
        default_source="usgs_topo"
    )

Usage Example
-------------

.. code-block:: python

    from memories.earth.historical import HistoricalData
    
    # Initialize historical data client
    historical_data = HistoricalData()
    
    # Fetch historical maps for a location
    historical_maps = await historical_data.get_historical_maps(
        location="San Francisco, CA",
        time_range=("1900-01-01", "1950-01-01"),
        map_types=["topographic", "city_plan"],
        source="usgs_topo"
    )
    
    # Fetch historical aerial imagery
    historical_imagery = await historical_data.get_historical_imagery(
        location=(37.7749, -122.4194),  # San Francisco
        time_range=("1950-01-01", "2000-01-01"),
        interval="decade",
        source="aerial_photos"
    )
    
    # Georeferencing historical maps
    georeferenced_maps = historical_data.georeference(
        maps=historical_maps,
        reference_system="EPSG:4326",
        method="control_points"
    )
    
    # Visualize results
    historical_data.visualize(
        data=georeferenced_maps,
        output="historical_maps.html"
    )

Socioeconomic Data
==================

Socioeconomic data includes demographics, economic indicators, housing, transportation, and other human activity metrics.

Supported Sources
-----------------

The memories-dev framework supports multiple socioeconomic data sources:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Source
     - Description
     - Data Types
   * - **US Census Bureau**
     - US demographic and economic data
     - Population, housing, income, employment
   * - **World Bank**
     - Global development data
     - Economic indicators, development metrics
   * - **Eurostat**
     - European Union statistics
     - European demographic and economic data
   * - **OECD**
     - Organisation for Economic Co-operation and Development
     - Economic and social statistics
   * - **UN Data**
     - United Nations statistics
     - Global demographic and development data
   * - **OpenDataSoft**
     - Open data platform
     - Various socioeconomic datasets

Configuration
-------------

Configure socioeconomic data sources using the following options:

.. code-block:: python

    from memories.earth.socioeconomic import SocioeconomicData
    
    # Initialize with default sources
    socio_data = SocioeconomicData()
    
    # Initialize with specific sources and API keys
    socio_data = SocioeconomicData(
        sources={
            "census": {
                "api_key": "your_census_api_key",
                "datasets": ["acs5", "decennial"],
                "cache_directory": "./data/census_cache"
            },
            "world_bank": {
                "indicators": ["SP.POP.TOTL", "NY.GDP.PCAP.CD"],
                "cache_directory": "./data/world_bank_cache"
            },
            "eurostat": {
                "datasets": ["demo_pjan", "nama_10_gdp"],
                "cache_directory": "./data/eurostat_cache"
            }
        },
        default_source="census"
    )

Usage Example
-------------

.. code-block:: python

    from memories.earth.socioeconomic import SocioeconomicData
    
    # Initialize socioeconomic data client
    socio_data = SocioeconomicData()
    
    # Fetch demographic data for a location
    demographics = await socio_data.get_demographics(
        location="San Francisco, CA",
        variables=["population", "median_income", "education_level"],
        time_range=("2010-01-01", "2020-01-01"),
        source="census"
    )
    
    # Fetch economic indicators
    economic_data = await socio_data.get_economic_indicators(
        location="United States",
        indicators=["gdp", "unemployment_rate", "inflation"],
        time_range=("2000-01-01", "2023-01-01"),
        source="world_bank"
    )
    
    # Analyze demographic trends
    trends = socio_data.analyze_trends(
        data=demographics,
        variables=["population"],
        trend_type="linear"
    )
    
    # Visualize results
    socio_data.visualize(
        data=demographics,
        variables=["median_income"],
        output="income_trends.html"
    )

Real-time Sensors and IoT
=========================

Real-time sensors and IoT devices provide current conditions from various sources, enabling near-real-time monitoring and analysis.

Supported Sources
-----------------

The memories-dev framework supports multiple real-time data sources:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Source
     - Description
     - Data Types
   * - **Weather Stations**
     - Global network of weather stations
     - Temperature, precipitation, wind, humidity
   * - **Air Quality Sensors**
     - Air quality monitoring networks
     - PM2.5, PM10, ozone, NO2, SO2
   * - **Traffic Sensors**
     - Traffic monitoring systems
     - Traffic volume, speed, congestion
   * - **Water Level Sensors**
     - River and coastal water level monitors
     - Water level, flow rate
   * - **Seismic Sensors**
     - Earthquake monitoring networks
     - Seismic activity
   * - **Custom IoT Devices**
     - User-defined IoT device networks
     - Various sensor data

Configuration
-------------

Configure real-time data sources using the following options:

.. code-block:: python

    from memories.earth.realtime import RealtimeData
    
    # Initialize with default sources
    realtime_data = RealtimeData()
    
    # Initialize with specific sources and API keys
    realtime_data = RealtimeData(
        sources={
            "weather_stations": {
                "api_key": "your_weather_api_key",
                "update_interval": 3600,  # seconds
                "cache_duration": 86400  # seconds
            },
            "air_quality": {
                "api_key": "your_air_quality_api_key",
                "update_interval": 3600,  # seconds
                "pollutants": ["pm25", "ozone", "no2"]
            },
            "custom_iot": {
                "endpoint": "https://your-iot-platform.com/api",
                "api_key": "your_iot_api_key",
                "device_ids": ["device1", "device2", "device3"]
            }
        },
        default_source="weather_stations"
    )

Usage Example
-------------

.. code-block:: python

    from memories.earth.realtime import RealtimeData
    
    # Initialize real-time data client
    realtime_data = RealtimeData()
    
    # Fetch current weather data
    weather = await realtime_data.get_weather(
        location=(37.7749, -122.4194),  # San Francisco
        variables=["temperature", "humidity", "wind_speed", "precipitation"],
        source="weather_stations"
    )
    
    # Fetch current air quality data
    air_quality = await realtime_data.get_air_quality(
        location="San Francisco, CA",
        pollutants=["pm25", "ozone", "no2"],
        source="air_quality"
    )
    
    # Set up real-time monitoring
    async def monitor_callback(data):
        print(f"New data received: {data}")
    
    monitor = await realtime_data.monitor(
        location="San Francisco, CA",
        variables=["temperature", "pm25"],
        update_interval=300,  # seconds
        callback=monitor_callback
    )
    
    # Stop monitoring after some time
    await asyncio.sleep(3600)  # Monitor for 1 hour
    await monitor.stop()

Custom Data Sources
===================

The memories-dev framework supports integration of custom data sources to meet specific needs.

Creating a Custom Data Source
-----------------------------

Create a custom data source by implementing the `DataSource` interface:

.. code-block:: python

    from memories.earth.data_source import DataSource
    
    class CustomDataSource(DataSource):
        def __init__(self, api_key=None, **kwargs):
            super().__init__(name="custom_source", **kwargs)
            self.api_key = api_key
        
        async def get_data(self, location, time_range=None, **kwargs):
            # Implement data retrieval logic
            # ...
            return data
        
        def process_data(self, data, **kwargs):
            # Implement data processing logic
            # ...
            return processed_data
        
        def visualize(self, data, output=None, **kwargs):
            # Implement visualization logic
            # ...
            return visualization

Registering a Custom Data Source
--------------------------------

Register a custom data source with the Earth Memory system:

.. code-block:: python

    from memories.earth import EarthMemory
    
    # Initialize Earth Memory
    earth_memory = EarthMemory()
    
    # Create custom data source
    custom_source = CustomDataSource(
        api_key="your_api_key",
        cache_directory="./data/custom_cache"
    )
    
    # Register custom data source
    earth_memory.register_data_source(custom_source)
    
    # Use custom data source
    data = await earth_memory.get_data(
        location="San Francisco, CA",
        source="custom_source",
        # Additional parameters specific to your custom source
        custom_param1="value1",
        custom_param2="value2"
    )

Data Source Integration
=======================

The memories-dev framework provides tools for integrating and combining data from multiple sources.

Data Fusion
-----------

Combine data from multiple sources for comprehensive analysis:

.. code-block:: python

    from memories.earth.fusion import DataFusion
    
    # Initialize data fusion
    fusion = DataFusion()
    
    # Add data sources
    fusion.add_source(satellite_imagery, weight=0.4)
    fusion.add_source(vector_data, weight=0.3)
    fusion.add_source(environmental_data, weight=0.3)
    
    # Perform data fusion
    fused_data = await fusion.fuse(
        location="San Francisco, CA",
        time_range=("2020-01-01", "2023-01-01"),
        resolution="medium"
    )
    
    # Analyze fused data
    analysis = fusion.analyze(
        data=fused_data,
        analysis_type="comprehensive"
    )
    
    # Visualize results
    fusion.visualize(
        data=analysis,
        output="integrated_analysis.html"
    )

Data Harmonization
------------------

Harmonize data from different sources to ensure consistency:

.. code-block:: python

    from memories.earth.harmonization import DataHarmonizer
    
    # Initialize data harmonizer
    harmonizer = DataHarmonizer()
    
    # Add datasets to harmonize
    harmonizer.add_dataset(satellite_data, name="satellite")
    harmonizer.add_dataset(environmental_data, name="environmental")
    
    # Define harmonization parameters
    harmonizer.set_parameters(
        spatial_resolution=30,  # meters
        temporal_resolution="monthly",
        coordinate_system="EPSG:4326"
    )
    
    # Perform harmonization
    harmonized_data = harmonizer.harmonize()
    
    # Export harmonized data
    harmonizer.export(
        data=harmonized_data,
        format="netcdf",
        output="harmonized_data.nc"
    )

Caching and Performance
=======================

The memories-dev framework includes caching mechanisms to improve performance when working with data sources.

Cache Configuration
-------------------

Configure caching for data sources:

.. code-block:: python

    from memories.earth.cache import CacheManager
    
    # Initialize cache manager
    cache_manager = CacheManager(
        cache_directory="./data/cache",
        max_size_gb=10,
        expiration_days=30
    )
    
    # Configure cache for specific data source
    cache_manager.configure_source(
        source_name="satellite",
        max_size_gb=5,
        expiration_days=60
    )
    
    # Clear cache for specific source
    cache_manager.clear_cache(source_name="satellite")
    
    # Clear all caches
    cache_manager.clear_all_caches()

Performance Optimization
------------------------

Optimize performance when working with data sources:

.. code-block:: python

    from memories.earth.optimization import PerformanceOptimizer
    
    # Initialize performance optimizer
    optimizer = PerformanceOptimizer()
    
    # Configure optimization settings
    optimizer.configure(
        parallel_requests=4,
        chunk_size_mb=100,
        use_compression=True,
        memory_limit_gb=4
    )
    
    # Apply optimization to data source
    optimized_source = optimizer.optimize_source(satellite_imagery)
    
    # Use optimized source
    data = await optimized_source.get_data(
        location="San Francisco, CA",
        time_range=("2020-01-01", "2023-01-01")
    )

Troubleshooting
===============

Common issues and solutions when working with data sources:

API Rate Limiting
-----------------

Many data sources implement rate limiting. To handle this:

1. Implement exponential backoff in your requests
2. Cache results to reduce API calls
3. Consider using bulk data downloads when available

.. code-block:: python

    from memories.utils.rate_limiting import RateLimiter
    
    # Create rate limiter
    rate_limiter = RateLimiter(
        max_requests=100,
        time_period=3600  # seconds
    )
    
    # Use rate limiter with data source
    async with rate_limiter:
        data = await data_source.get_data(location="San Francisco, CA")

Missing or Incomplete Data
--------------------------

Handle missing or incomplete data:

1. Implement data validation checks
2. Use multiple data sources for redundancy
3. Implement interpolation or gap-filling techniques

.. code-block:: python

    from memories.utils.data_validation import validate_data
    from memories.utils.interpolation import interpolate_missing
    
    # Validate data
    validation_result = validate_data(
        data=satellite_data,
        checks=["completeness", "consistency", "range"]
    )
    
    if not validation_result.is_valid:
        # Handle invalid data
        if validation_result.has_missing_values:
            # Interpolate missing values
            fixed_data = interpolate_missing(
                data=satellite_data,
                method="linear"
            )
        else:
            # Use alternative data source
            fixed_data = await alternative_source.get_data(
                location="San Francisco, CA",
                time_range=("2020-01-01", "2023-01-01")
            )

Geospatial Alignment Issues
---------------------------

Handle geospatial alignment issues:

1. Ensure consistent coordinate reference systems
2. Implement reprojection when necessary
3. Validate spatial alignment between datasets

.. code-block:: python

    from memories.utils.geospatial import reproject, validate_alignment
    
    # Reproject data to consistent CRS
    reprojected_data = reproject(
        data=vector_data,
        source_crs="EPSG:3857",
        target_crs="EPSG:4326"
    )
    
    # Validate spatial alignment
    alignment_result = validate_alignment(
        dataset1=satellite_data,
        dataset2=reprojected_data,
        tolerance_meters=10
    )
    
    if not alignment_result.is_aligned:
        # Handle alignment issues
        aligned_data = align_datasets(
            dataset1=satellite_data,
            dataset2=reprojected_data,
            method="warp"
        )

Best Practices
==============

Follow these best practices when working with data sources:

1. **Implement Proper Error Handling**
   
   Always implement robust error handling for API requests and data processing.

2. **Use Asynchronous Processing**
   
   Leverage asynchronous processing for handling multiple data sources efficiently.

3. **Implement Caching**
   
   Cache results to improve performance and reduce API calls.

4. **Validate Data Quality**
   
   Implement data validation checks to ensure quality and consistency.

5. **Document Data Sources**
   
   Maintain documentation about data sources, including limitations and usage notes.

6. **Consider Data Privacy and Licensing**
   
   Respect data privacy regulations and licensing terms for all data sources.

7. **Implement Rate Limiting**
   
   Respect API rate limits and implement appropriate rate limiting in your code.

8. **Use Appropriate Resolution**
   
   Match data resolution to your needs - higher resolution requires more processing resources.

Next Steps
==========

Now that you understand the data sources available in the memories-dev framework, you can:

1. Explore the :doc:`/earth_memory/index` documentation to learn about the Earth Memory system
2. Check out the 'satellite_imagery' documentation for detailed information about satellite imagery
3. Learn about 'environmental_data' for environmental data integration
4. See :doc:`/getting_started/examples` for practical applications of Earth Memory data sources 