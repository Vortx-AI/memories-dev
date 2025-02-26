======================
Data Processing
======================


Introduction to Earth Data Processing
---------------------------------

The Earth Memory framework provides powerful capabilities for processing, transforming, and analyzing Earth observation data. This guide covers the data processing pipeline, available processors, and how to create custom processing workflows for your Earth Memory applications.

Data Processing Pipeline
---------------------

The data processing pipeline in Earth Memory consists of several stages:

1. **Data Acquisition**: Retrieving raw data from various sources
2. **Preprocessing**: Cleaning, normalizing, and preparing data for analysis
3. **Feature Extraction**: Identifying and extracting relevant features from the data
4. **Transformation**: Converting data between different formats and representations
5. **Analysis**: Applying algorithms to extract insights from the data
6. **Memory Formation**: Creating structured memories from processed data
7. **Memory Integration**: Connecting new memories with existing knowledge

Basic Data Processing Workflow
----------------------------

Here's a simple example of a data processing workflow:

.. code-block:: python

   from memories.earth import Observatory
   from memories.earth.processors import (
       CloudMasking,
       NormalizedDifferenceIndex,
       Resampling,
       TemporalAggregation
   )
   from memories.earth.pipelines import ProcessingPipeline
   
   # Create your observatory with data source
   observatory = Observatory(name="vegetation-observatory")
   # ... add your data sources ...
   
   # Create a processing pipeline
   pipeline = ProcessingPipeline(
       name="ndvi-pipeline",
       description="Calculates NDVI from satellite imagery"
   )
   
   # Add processing steps to the pipeline
   pipeline.add_step(
       CloudMasking(
           method="sentinel2_scl",
           mask_values=[3, 8, 9, 10],  # cloud, cloud shadow, etc.
           fill_value=None  # use NaN for masked pixels
       )
   )
   
   pipeline.add_step(
       NormalizedDifferenceIndex(
           name="ndvi",
           band1="B08",  # NIR band
           band2="B04",  # Red band
           description="Normalized Difference Vegetation Index"
       )
   )
   
   pipeline.add_step(
       Resampling(
           target_resolution="30m",
           method="bilinear"
       )
   )
   
   pipeline.add_step(
       TemporalAggregation(
           period="monthly",
           function="mean",
           min_valid_observations=3
       )
   )
   
   # Register the pipeline with the observatory
   observatory.register_pipeline(pipeline)
   
   # Run the pipeline for a specific area and time range
   result = observatory.run_pipeline(
       pipeline_name="ndvi-pipeline",
       area_of_interest={"type": "Polygon", "coordinates": [...]},
       time_range=("2023-01-01", "2023-12-31")
   )
   
   # Access the processed data
   ndvi_timeseries = result.get_data()
   
   # Save the results
   result.save("ndvi_monthly_2023.tif")

Available Processors
-----------------

Earth Memory includes a wide range of built-in processors for common data processing tasks:

Image Processing
~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70
   
   * - Processor
     - Description
   * - ``CloudMasking``
     - Detects and masks clouds in satellite imagery
   * - ``Pansharpening``
     - Increases spatial resolution of multispectral imagery
   * - ``AtmosphericCorrection``
     - Corrects for atmospheric effects in optical imagery
   * - ``BandMath``
     - Performs arithmetic operations on image bands
   * - ``ImageRegistration``
     - Aligns multiple images to a common coordinate system
   * - ``Mosaicking``
     - Combines multiple images into a single seamless image

Indices and Transformations
~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70
   
   * - Processor
     - Description
   * - ``NormalizedDifferenceIndex``
     - Calculates normalized difference indices (NDVI, NDWI, etc.)
   * - ``TasseledCap``
     - Performs Tasseled Cap transformation (brightness, greenness, wetness)
   * - ``PrincipalComponentAnalysis``
     - Reduces dimensionality of multispectral data
   * - ``SpectralUnmixing``
     - Decomposes pixel values into endmember fractions
   * - ``TextureAnalysis``
     - Extracts texture features from imagery
   * - ``TopographicCorrection``
     - Corrects for topographic effects on reflectance

Spatial Analysis
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70
   
   * - Processor
     - Description
   * - ``Resampling``
     - Changes the spatial resolution of data
   * - ``Reprojection``
     - Converts data between different coordinate systems
   * - ``SpatialFilter``
     - Applies spatial filters (e.g., Gaussian, median)
   * - ``ObjectBasedImageAnalysis``
     - Segments imagery into objects for analysis
   * - ``ZonalStatistics``
     - Calculates statistics for regions of interest
   * - ``GeomorphologicFeatures``
     - Extracts landform and terrain features

Temporal Analysis
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70
   
   * - Processor
     - Description
   * - ``TemporalAggregation``
     - Aggregates data over time periods (daily, monthly, etc.)
   * - ``TimeSeriesAnalysis``
     - Analyzes temporal patterns and trends
   * - ``ChangeDetection``
     - Identifies changes between time periods
   * - ``SeasonalDecomposition``
     - Separates seasonal, trend, and residual components
   * - ``GapFilling``
     - Fills missing values in time series
   * - ``TemporalFiltering``
     - Reduces noise in time series data

Machine Learning
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70
   
   * - Processor
     - Description
   * - ``Clustering``
     - Groups similar data points together
   * - ``Regression``
     - Models relationships between variables
   * - ``Classification``
     - Assigns categories to data
   * - ``AnomalyDetection``
     - Identifies unusual patterns in data
   * - ``FeatureExtraction``
     - Extracts meaningful features from raw data
   * - ``DeepLearning``
     - Applies neural networks to Earth observation data

Creating Custom Processors
------------------------

You can create custom processors for specialized tasks:

.. code-block:: python

   from memories.earth.processors import BaseProcessor
   import numpy as np
   
   class BurnAreaIndex(BaseProcessor):
       """Calculate the Burn Area Index (BAI) from satellite imagery."""
       
       def __init__(self, name="bai", description=None):
           super().__init__(name=name, description=description)
           self.requires_bands = ["B04", "B08"]  # RED and NIR bands
           
       def process(self, data):
           """
           Calculate BAI = 1 / ((0.1 - RED)^2 + (0.06 - NIR)^2)
           """
           red = data["B04"]
           nir = data["B08"]
           
           # Calculate BAI
           bai = 1.0 / ((0.1 - red)**2 + (0.06 - nir)**2)
           
           # Add to output
           data[self.name] = bai
           
           return data
   
   # Use the custom processor in a pipeline
   pipeline.add_step(
       BurnAreaIndex(
           name="bai",
           description="Burn Area Index for fire detection"
       )
   )

Processor Configuration
--------------------

Processors can be configured using both Python API and YAML configuration files:

.. code-block:: yaml

   # processors.yml
   
   pipelines:
     - name: ndvi-pipeline
       description: Calculates NDVI from satellite imagery
       steps:
         - type: CloudMasking
           params:
             method: sentinel2_scl
             mask_values: [3, 8, 9, 10]
             fill_value: null
             
         - type: NormalizedDifferenceIndex
           params:
             name: ndvi
             band1: B08
             band2: B04
             description: Normalized Difference Vegetation Index
             
         - type: Resampling
           params:
             target_resolution: 30m
             method: bilinear
             
         - type: TemporalAggregation
           params:
             period: monthly
             function: mean
             min_valid_observations: 3

Load the configuration file in your code:

.. code-block:: python

   # Load processing pipelines from configuration
   observatory.load_pipelines_config("processors.yml")

Distributed Processing
-------------------

For large-scale processing, Earth Memory supports distributed execution:

.. code-block:: python

   from memories.earth.execution import DistributedExecutor
   
   # Create a distributed executor
   executor = DistributedExecutor(
       backend="dask",  # or "ray", "spark", etc.
       n_workers=4,
       memory_per_worker="4GB"
   )
   
   # Run the pipeline with the distributed executor
   result = observatory.run_pipeline(
       pipeline_name="ndvi-pipeline",
       area_of_interest={"type": "Polygon", "coordinates": [...]},
       time_range=("2023-01-01", "2023-12-31"),
       executor=executor
   )

Memory Formation from Processed Data
---------------------------------

After processing, you can create Earth Memories from the results:

.. code-block:: python

   from memories.earth import MemoryCreator
   
   # Create memories from processing results
   memory_creator = MemoryCreator()
   
   # Create a memory from the NDVI data
   vegetation_memory = memory_creator.create_memory(
       name="vegetation-dynamics-2023",
       description="Vegetation dynamics over the year 2023",
       data=result.get_data(),
       type="warm",  # Memory tier
       metadata={
           "resolution": "30m",
           "temporal_coverage": "2023-01-01/2023-12-31",
           "region": "Amazon Basin",
           "processing_pipeline": "ndvi-pipeline"
       },
       tags=["vegetation", "ndvi", "amazon", "2023"]
   )
   
   # Store the memory in the memory codex
   from memories.earth import MemoryCodex
   
   codex = MemoryCodex()
   codex.add_memory(vegetation_memory)

Advanced Processing Patterns
-------------------------

Chain multiple pipelines together for complex workflows:

.. code-block:: python

   # First pipeline: Preprocess satellite imagery
   preprocess_pipeline = ProcessingPipeline(
       name="preprocess-pipeline",
       description="Preprocesses satellite imagery"
   )
   # ... add preprocessing steps ...
   
   # Second pipeline: Calculate indices
   indices_pipeline = ProcessingPipeline(
       name="indices-pipeline",
       description="Calculates various indices"
   )
   # ... add index calculation steps ...
   
   # Third pipeline: Perform change detection
   change_pipeline = ProcessingPipeline(
       name="change-pipeline",
       description="Detects changes over time"
   )
   # ... add change detection steps ...
   
   # Chain the pipelines
   observatory.register_pipeline(preprocess_pipeline)
   observatory.register_pipeline(indices_pipeline, depends_on="preprocess-pipeline")
   observatory.register_pipeline(change_pipeline, depends_on="indices-pipeline")
   
   # Run the complete workflow
   result = observatory.run_workflow(
       starting_pipeline="preprocess-pipeline",
       area_of_interest={"type": "Polygon", "coordinates": [...]},
       time_range=("2022-01-01", "2023-12-31")
   )

Monitoring and Debugging
---------------------

Monitor processing jobs and debug issues:

.. code-block:: python

   # Get status of running jobs
   jobs = observatory.get_jobs()
   for job in jobs:
       print(f"Job ID: {job.id}, Status: {job.status}, Progress: {job.progress}%")
   
   # Get detailed logs from a job
   logs = observatory.get_job_logs(job_id="12345")
   
   # Debug a specific step in a pipeline
   debug_result = observatory.debug_pipeline_step(
       pipeline_name="ndvi-pipeline",
       step_index=1,  # The step to debug (0-based index)
       sample_data=sample_input,  # Sample input data for testing
       verbose=True
   )

Next Steps
---------

After learning about data processing:

- Explore memory types in :doc:`../memory_types/index`
- Learn about integrating AI capabilities in :doc:`../ai_integration/index`
- Set up memory storage options in :doc:`../memory_architecture/storage` 