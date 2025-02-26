======================
Memory Types
======================


Introduction to Earth Memory Types
-------------------------------

The Earth Memory framework organizes environmental data into specialized memory types, each designed to capture different aspects of Earth's systems. This guide introduces the various memory types available and explains how to work with them.

Core Memory Concepts
-------------------

In the Earth Memory framework, **memories** are structured representations of environmental data that:

1. Capture specific phenomena or patterns observed in Earth systems
2. Include rich metadata about spatial and temporal context
3. Maintain information about data provenance and quality
4. Support various resolutions and levels of detail
5. Can be combined, compared, and analyzed together

Memory Type Hierarchy
--------------------

Memory types are organized in a hierarchical structure:

.. code-block:: text

   BaseMemory
   ├── ClimaticMemory
   │   ├── TemperatureMemory
   │   ├── PrecipitationMemory
   │   ├── WindMemory
   │   └── AtmosphericCompositionMemory
   ├── HydrologicMemory
   │   ├── SurfaceWaterMemory
   │   ├── GroundwaterMemory
   │   ├── SoilMoistureMemory
   │   └── SnowIceMemory
   ├── BiologicMemory
   │   ├── VegetationMemory
   │   ├── BiodiversityMemory
   │   ├── EcosystemMemory
   │   └── PhenologyMemory
   ├── GeologicMemory
   │   ├── LandformMemory
   │   ├── SoilMemory
   │   ├── TectonicMemory
   │   └── GeochemicalMemory
   ├── AnthropogenicMemory
   │   ├── LandUseMemory
   │   ├── InfrastructureMemory
   │   ├── PollutionMemory
   │   └── ResourceExtractionMemory
   └── IntegratedMemory
       ├── LandscapeMemory
       ├── EventMemory
       ├── CarbonCycleMemory
       └── WaterCycleMemory

Working with Memory Types
------------------------

Creating Memory Instances
~~~~~~~~~~~~~~~~~~~~~~~

Here's how to create instances of different memory types:

.. code-block:: python

   from memories.earth import MemoryCreator
   from memories.earth.types import VegetationMemory, TemperatureMemory
   
   # Create a memory creator
   creator = MemoryCreator()
   
   # Create a vegetation memory from NDVI data
   vegetation_memory = creator.create_memory(
       memory_type=VegetationMemory,
       name="amazon-vegetation-2023",
       data=ndvi_data,  # NumPy array or xarray.Dataset
       spatial_reference="EPSG:4326",
       time_range=("2023-01-01", "2023-12-31"),
       resolution="30m",
       metadata={
           "sensor": "Sentinel-2",
           "index": "NDVI",
           "processing_level": "L2A",
           "cloud_cover_max": 20
       }
   )
   
   # Create a temperature memory
   temperature_memory = creator.create_memory(
       memory_type=TemperatureMemory,
       name="global-temperature-2020-2023",
       data=temperature_data,
       spatial_reference="EPSG:4326",
       time_range=("2020-01-01", "2023-12-31"),
       resolution="0.25deg",
       units="celsius",
       metadata={
           "source": "ERA5",
           "variable": "2m_temperature",
           "aggregation": "monthly_mean"
       }
   )

Memory Tier Assignment
~~~~~~~~~~~~~~~~~~~~

Memory instances can be assigned to different tiers based on their access patterns and temporal relevance:

.. code-block:: python

   # Assign to hot memory tier for active use
   vegetation_memory.assign_to_tier("hot")
   
   # Assign to warm memory tier for medium-term storage
   older_vegetation_memory.assign_to_tier("warm")
   
   # Assign to cold memory tier for long-term archival
   historical_vegetation_memory.assign_to_tier("cold")
   
   # Assign to glacier memory tier for indefinite preservation
   ancient_pollen_record.assign_to_tier("glacier")

Memory Operations
~~~~~~~~~~~~~~~

Memories support various operations for analysis and transformation:

.. code-block:: python

   # Extract a subset of a memory
   amazon_subset = vegetation_memory.subset(
       bbox=[-73.5, -9.0, -60.0, 0.0],  # Western Amazon
       time_range=("2023-06-01", "2023-08-31")  # Dry season
   )
   
   # Combine two memories
   combined_memory = vegetation_memory.combine(temperature_memory)
   
   # Transform a memory
   monthly_aggregated = vegetation_memory.transform(
       operation="temporal_aggregation",
       params={"frequency": "1M", "method": "mean"}
   )
   
   # Extract statistics
   stats = vegetation_memory.statistics()
   print(f"Mean NDVI: {stats['mean']}")
   print(f"Standard deviation: {stats['std']}")
   print(f"Minimum: {stats['min']}, Maximum: {stats['max']}")
   
   # Analyze trends
   trend_analysis = vegetation_memory.analyze_trend(
       method="linear_regression",
       significance_level=0.05
   )

Memory Type Descriptions
-----------------------

Climatic Memories
~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 25 75
   
   * - Memory Type
     - Description
   * - **TemperatureMemory**
     - Records air, land, and sea temperature patterns over time
   * - **PrecipitationMemory**
     - Captures rainfall, snowfall, and other forms of precipitation
   * - **WindMemory**
     - Represents wind speed, direction, and patterns
   * - **AtmosphericCompositionMemory**
     - Tracks greenhouse gases, aerosols, and other atmospheric constituents

Hydrologic Memories
~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 25 75
   
   * - Memory Type
     - Description
   * - **SurfaceWaterMemory**
     - Represents lakes, rivers, reservoirs, and surface water dynamics
   * - **GroundwaterMemory**
     - Captures aquifer levels, recharge rates, and groundwater quality
   * - **SoilMoistureMemory**
     - Tracks water content in soil at different depths
   * - **SnowIceMemory**
     - Records snow cover, ice extent, glaciers, and polar ice

Biologic Memories
~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 25 75
   
   * - Memory Type
     - Description
   * - **VegetationMemory**
     - Represents plant cover, health, productivity, and structure
   * - **BiodiversityMemory**
     - Captures species distributions, richness, and ecosystem diversity
   * - **EcosystemMemory**
     - Tracks ecosystem function, services, and resilience
   * - **PhenologyMemory**
     - Represents seasonal biological events and cycles

Geologic Memories
~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 25 75
   
   * - Memory Type
     - Description
   * - **LandformMemory**
     - Represents terrain, topography, and geomorphology
   * - **SoilMemory**
     - Captures soil composition, structure, and properties
   * - **TectonicMemory**
     - Tracks plate movements, earthquakes, and volcanic activity
   * - **GeochemicalMemory**
     - Represents chemical composition of rocks, soils, and sediments

Anthropogenic Memories
~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 25 75
   
   * - Memory Type
     - Description
   * - **LandUseMemory**
     - Represents human land use patterns and changes
   * - **InfrastructureMemory**
     - Captures built environment and human infrastructure
   * - **PollutionMemory**
     - Tracks pollutants in air, water, soil, and their impacts
   * - **ResourceExtractionMemory**
     - Represents mining, drilling, harvesting, and extraction activities

Integrated Memories
~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 25 75
   
   * - Memory Type
     - Description
   * - **LandscapeMemory**
     - Holistic representation of landscapes integrating multiple aspects
   * - **EventMemory**
     - Captures discrete environmental events like floods, fires, or storms
   * - **CarbonCycleMemory**
     - Integrates carbon fluxes and stocks across Earth systems
   * - **WaterCycleMemory**
     - Represents the complete hydrological cycle in a region

Creating Custom Memory Types
--------------------------

You can create custom memory types to represent specialized environmental data:

.. code-block:: python

   from memories.earth.types import BiologicMemory
   
   class CoralReefMemory(BiologicMemory):
       """Memory type specialized for coral reef ecosystems."""
       
       def __init__(self, name, data, **kwargs):
           super().__init__(name, data, **kwargs)
           self.ecosystem_type = "coral_reef"
           self.required_attributes = [
               "coral_cover", "species_diversity", "health_index"
           ]
       
       def calc_bleaching_risk(self, temperature_memory):
           """Calculate coral bleaching risk based on temperature anomalies."""
           # Implementation details...
           return bleaching_risk_index
       
       def identify_resilient_areas(self):
           """Identify areas of the reef showing resilience."""
           # Implementation details...
           return resilient_zones

Using Memory Types in Analysis
----------------------------

Different memory types can be used together in analysis pipelines:

.. code-block:: python

   from memories.earth.analysis import CorrelationAnalysis, RegimeShiftDetection
   
   # Analyze relationship between temperature and vegetation
   correlation = CorrelationAnalysis.run(
       memories=[temperature_memory, vegetation_memory],
       method="pearson",
       lag_range=(-3, 3),  # Months
       significance_level=0.05
   )
   
   # Detect regime shifts in ecosystem
   shifts = RegimeShiftDetection.run(
       memory=ecosystem_memory,
       method="sequential_t_test",
       parameters={
           "cut_off_length": 10,
           "significance_level": 0.01,
           "huber_weight": 1
       }
   )

Advanced Memory Features
-----------------------

Memory Ensemble
~~~~~~~~~~~~~

Create and work with ensembles of memories:

.. code-block:: python

   from memories.earth.ensemble import MemoryEnsemble
   
   # Create an ensemble from multiple vegetation memories
   vegetation_ensemble = MemoryEnsemble(
       memories=[vegetation_memory_1, vegetation_memory_2, vegetation_memory_3],
       name="vegetation-ensemble-2023",
       weights=[0.5, 0.3, 0.2]  # Optional weights for each memory
   )
   
   # Calculate ensemble statistics
   ensemble_mean = vegetation_ensemble.mean()
   ensemble_uncertainty = vegetation_ensemble.uncertainty()
   
   # Find optimal subset of memories
   optimal_subset = vegetation_ensemble.optimize(
       target_variable="primary_productivity",
       optimization_metric="rmse",
       reference_data=ground_truth_data
   )

Memory Fusion
~~~~~~~~~~~~

Fuse different memory types to create integrated understanding:

.. code-block:: python

   from memories.earth.fusion import MemoryFusion
   
   # Create a fusion of vegetation, temperature, and precipitation memories
   drought_memory = MemoryFusion.create(
       memories=[vegetation_memory, temperature_memory, precipitation_memory],
       fusion_type="drought_index",
       parameters={
           "veg_weight": 0.4,
           "temp_weight": 0.3,
           "precip_weight": 0.3,
           "method": "weighted_integration"
       }
   )
   
   # Use the fused memory for analysis
   drought_severity = drought_memory.extract_index("severity")
   drought_duration = drought_memory.extract_index("duration")
   drought_impact = drought_memory.analyze_impact(
       target="vegetation_productivity"
   )

Next Steps
---------

After learning about memory types:

- Explore memory architecture in :doc:`../memory_architecture/index`
- Learn about memory retrieval and query in :doc:`../memory_codex/query`
- Discover AI integration capabilities in :doc:`../ai_integration/index` 