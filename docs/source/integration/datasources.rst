======================
Earth Data Sources
======================


Introduction to Earth Data Sources
-------------------------------

The Memory Codex framework integrates with a wide variety of Earth observation data sources, from satellite imagery to climate data, sensor networks to geospatial databases. This guide covers the data sources available and how to integrate them into your Earth Memory system.

Supported Data Source Categories
-----------------------------

.. list-table::
   :header-rows: 1
   :widths: 25 75
   
   * - Category
     - Description
   * - **Satellite Imagery**
     - Optical, radar, and multispectral imagery from various satellite platforms
   * - **Climate Data**
     - Historical and forecast climate data, including temperature, precipitation, and atmospheric conditions
   * - **Environmental Sensors**
     - Ground-based sensor networks and IoT devices measuring environmental parameters
   * - **Geospatial Databases**
     - Vector and raster databases containing geographic features and attributes
   * - **Digital Elevation Models**
     - Topographic data representing Earth's surface terrain
   * - **Ocean Data**
     - Sea surface temperature, ocean currents, salinity, and other marine parameters
   * - **Historical Archives**
     - Digitized historical records, maps, and observations

Satellite Data Integration
-------------------------

Satellite data provides high-resolution, regular observations of Earth's surface. The Memory Codex supports multiple satellite platforms:

.. code-block:: python

   from memories.earth import Observatory
   from memories.earth.sources import SatelliteSource
   
   # Create your observatory
   observatory = Observatory(name="satellite-observatory")
   
   # Add Sentinel-2 optical imagery
   observatory.add_data_source(
       SatelliteSource(
           name="sentinel-2",
           collection="sentinel-2-l2a",
           bands=["B02", "B03", "B04", "B08"],  # RGB + NIR
           resolution="10m",
           revisit_days=5,
           cloud_cover_max=20
       )
   )
   
   # Add Sentinel-1 SAR imagery
   observatory.add_data_source(
       SatelliteSource(
           name="sentinel-1",
           collection="sentinel-1-grd",
           polarizations=["VV", "VH"],
           resolution="10m",
           revisit_days=6
       )
   )
   
   # Add Landsat imagery
   observatory.add_data_source(
       SatelliteSource(
           name="landsat",
           collection="landsat-8-c2-l2",
           bands=["B2", "B3", "B4", "B5", "B6", "B7"],
           resolution="30m",
           revisit_days=16
       )
   )

Climate Data Integration
----------------------

Climate data provides essential context about Earth's atmospheric conditions:

.. code-block:: python

   from memories.earth.sources import ClimateSource
   
   # Add ERA5 reanalysis data
   observatory.add_data_source(
       ClimateSource(
           name="era5",
           provider="ecmwf",
           variables=["temperature", "precipitation", "wind_u", "wind_v"],
           temporal_resolution="hourly",
           spatial_resolution="0.25deg"
       )
   )
   
   # Add CMIP6 climate model data
   observatory.add_data_source(
       ClimateSource(
           name="cmip6",
           provider="cmip",
           model="EC-Earth3",
           scenario="ssp245",
           variables=["tas", "pr"],
           temporal_resolution="monthly",
           spatial_resolution="1deg"
       )
   )

Environmental Sensor Networks
---------------------------

Ground-based sensors provide precise, localized measurements:

.. code-block:: python

   from memories.earth.sources import SensorNetworkSource
   
   # Add weather station network
   observatory.add_data_source(
       SensorNetworkSource(
           name="weather-stations",
           provider="noaa",
           network="ghcn",
           variables=["TMIN", "TMAX", "PRCP"],
           update_frequency="daily"
       )
   )
   
   # Add air quality monitoring network
   observatory.add_data_source(
       SensorNetworkSource(
           name="air-quality",
           provider="epa",
           network="airnow",
           variables=["PM2.5", "PM10", "O3", "NO2"],
           update_frequency="hourly"
       )
   )

Custom Data Source Integration
----------------------------

You can integrate custom or local data sources:

.. code-block:: python

   from memories.earth.sources import CustomSource
   
   # Add a local GeoTIFF collection
   observatory.add_data_source(
       CustomSource(
           name="local-elevation",
           source_type="raster",
           data_path="/path/to/elevation/data/*.tif",
           spatial_reference="EPSG:4326",
           metadata={
               "description": "Local high-resolution DEM",
               "resolution": "1m",
               "acquisition_date": "2023-05-10"
           }
       )
   )
   
   # Add a database connection
   observatory.add_data_source(
       CustomSource(
           name="local-database",
           source_type="vector",
           connection_string="postgresql://user:password@localhost:5432/gisdb",
           tables=["land_cover", "urban_boundaries", "water_bodies"],
           spatial_column="geom",
           spatial_reference="EPSG:4326"
       )
   )

Data Source Authentication
------------------------

Most remote data sources require authentication:

.. code-block:: python

   # Add authentication for Copernicus data (Sentinel satellites)
   observatory.add_authentication(
       provider="copernicus",
       username="your-username",
       password="your-password"
   )
   
   # Add API key authentication
   observatory.add_authentication(
       provider="planet",
       api_key="your-api-key-here"
   )
   
   # Add OAuth authentication
   observatory.add_authentication(
       provider="google-earth-engine",
       oauth_credentials="/path/to/credentials.json"
   )

Data Source Configuration File
---------------------------

For production use, it's recommended to configure data sources using a YAML file:

.. code-block:: yaml

   # data_sources.yml
   
   sources:
     - name: sentinel-2
       type: satellite
       provider: copernicus
       collection: sentinel-2-l2a
       bands: [B02, B03, B04, B08]
       resolution: 10m
       cloud_cover_max: 20
       
     - name: era5
       type: climate
       provider: ecmwf
       variables: [temperature, precipitation, wind_u, wind_v]
       temporal_resolution: hourly
       spatial_resolution: 0.25deg
       
     - name: weather-stations
       type: sensor_network
       provider: noaa
       network: ghcn
       variables: [TMIN, TMAX, PRCP]
       update_frequency: daily
   
   authentication:
     - provider: copernicus
       username: ${COPERNICUS_USERNAME}
       password: ${COPERNICUS_PASSWORD}
       
     - provider: ecmwf
       api_key: ${ECMWF_API_KEY}

Load this configuration file in your code:

.. code-block:: python

   # Load data sources from configuration
   observatory.load_data_sources_config("data_sources.yml")

Testing Data Source Connectivity
-----------------------------

Always test data source connectivity before using them in production:

.. code-block:: python

   # Test all data source connections
   test_results = observatory.test_all_connections()
   
   for source_name, result in test_results.items():
       if result.success:
           print(f"✅ {source_name}: Connection successful")
       else:
           print(f"❌ {source_name}: Connection failed - {result.error}")
   
   # Test a specific data source with sample query
   sentinel_test = observatory.test_data_source(
       name="sentinel-2",
       bbox=[13.1, 52.3, 13.6, 52.7],  # Berlin area
       time_range=("2023-01-01", "2023-01-31"),
       max_cloud_cover=10
   )
   
   if sentinel_test.success:
       print(f"Found {sentinel_test.scenes_count} scenes")
       print(f"Sample scene: {sentinel_test.sample_scene}")
   else:
       print(f"Error: {sentinel_test.error}")

Next Steps
---------

After configuring your data sources:

- Learn how to process and transform Earth observation data in :doc:`data_processing`
- Set up memory storage for your Earth observations in :doc:`../memory_architecture/storage`
- Create specialized memory types based on your data sources in :doc:`../memory_types/index` 