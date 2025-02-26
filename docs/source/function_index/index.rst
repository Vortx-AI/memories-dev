===================
Function Catalog
===================

Welcome to the Function Catalog section of the memories-dev documentation. This comprehensive catalog provides a detailed index of all functions available in the framework, organized by module and purpose.

.. note::
   The Function Catalog is an essential reference for developers working with the memories-dev API. It provides detailed information about each function, including parameters, return values, and usage examples.

How to Use This Catalog
-----------------------

Functions in this catalog are organized by module and purpose. You can:

1. Navigate through the module structure to find functions by location
2. Use the search functionality to find specific functions by name
3. Browse the categorized function listings to discover capabilities

Each function entry includes:

- Full function signature with type annotations
- Detailed description of the function's purpose
- Parameter descriptions with types and default values
- Return value description with type information
- Usage examples
- Links to related functions and classes

Core Functions
--------------

Memory Management
^^^^^^^^^^^^^^^^^

.. py:function:: memories.MemoryStore.store(key, data, metadata=None, tier=None)
   :noindex:

   Store data in the memory system with associated metadata.

   :param str key: The unique identifier for the data
   :param dict data: The data to store
   :param dict metadata: Optional metadata associated with the data
   :param str tier: Optional memory tier to store in (hot, warm, cold, glacier)
   :return: Boolean indicating success
   :rtype: bool

   **Example:**

   .. code-block:: python

       from memories import MemoryStore, Config

       memory_store = MemoryStore(Config())
       memory_store.store(
           key="location_123",
           data={"satellite_image": image_data},
           metadata={"location": {"lat": 37.7749, "lon": -122.4194}}
       )

.. py:function:: memories.MemoryStore.retrieve(key, include_metadata=False)
   :noindex:

   Retrieve data from the memory system.

   :param str key: The unique identifier for the data
   :param bool include_metadata: Whether to include metadata in the result
   :return: The retrieved data or (data, metadata) if include_metadata is True
   :rtype: dict or tuple

   **Example:**

   .. code-block:: python

       from memories import MemoryStore, Config

       memory_store = MemoryStore(Config())
       data, metadata = memory_store.retrieve(
           key="location_123",
           include_metadata=True
       )

.. py:function:: memories.MemoryStore.query(query, limit=10, include_metadata=False)
   :noindex:

   Query the memory system for data matching the query.

   :param dict query: The query to match against the data
   :param int limit: Maximum number of results to return
   :param bool include_metadata: Whether to include metadata in the results
   :return: List of matching data items or (data, metadata) pairs
   :rtype: list

   **Example:**

   .. code-block:: python

       from memories import MemoryStore, Config

       memory_store = MemoryStore(Config())
       results = memory_store.query(
           query={
               "location": {
                   "lat": {"$gte": 37.7, "$lte": 37.8},
                   "lon": {"$gte": - 122.5, "$lte": -122.4}
               }
           },
           limit=5,
           include_metadata=True
       )

Earth Analyzers
^^^^^^^^^^^^^^^

.. py:function:: memories.core.analyzers.TerrainAnalyzer.analyze(location, resolution='medium')
   :noindex:

   Analyze the terrain features of a location.

   :param dict location: Location coordinates with lat/lon
   :param str resolution: Resolution of analysis ('low', 'medium', 'high')
   :return: Terrain analysis results
   :rtype: dict

   **Example:**

   .. code-block:: python

       from memories.core.analyzers import TerrainAnalyzer

       analyzer = TerrainAnalyzer()
       results = await analyzer.analyze(
           location={"lat": 37.7749, "lon": -122.4194},
           resolution="high"
       )

.. py:function:: memories.core.analyzers.ClimateAnalyzer.analyze(location, time_range=None)
   :noindex:

   Analyze climate data for a location over a time range.

   :param dict location: Location coordinates with lat/lon
   :param dict time_range: Time range to analyze with start and end dates
   :return: Climate analysis results
   :rtype: dict

   **Example:**

   .. code-block:: python

       from memories.core.analyzers import ClimateAnalyzer

       analyzer = ClimateAnalyzer()
       results = await analyzer.analyze(
           location={"lat": 37.7749, "lon": -122.4194},
           time_range={
               "start": "2020-01-01",
               "end": "2023-01-01"
           }
       )

Model Integration
^^^^^^^^^^^^^^^^^

.. py:function:: memories.models.load_model.LoadModel.__init__(model_provider, model_name, **kwargs)
   :noindex:

   Initialize a model with the specified provider and name.

   :param str model_provider: Model provider name
   :param str model_name: Model name
   :param kwargs: Additional provider-specific parameters
   :return: Model instance
   :rtype: LoadModel

   **Example:**

   .. code-block:: python

       from memories.models.load_model import LoadModel

       model = LoadModel(
           model_provider="openai",
           model_name="gpt-4",
           api_key=os.environ.get("OPENAI_API_KEY")
       )

.. py:function:: memories.models.load_model.LoadModel.generate(prompt, **kwargs)
   :noindex:

   Generate a response using the model.

   :param str prompt: The prompt to send to the model
   :param kwargs: Additional generation parameters
   :return: Generated response
   :rtype: str

   **Example:**

   .. code-block:: python

       from memories.models.load_model import LoadModel

       model = LoadModel(
           model_provider="anthropic",
           model_name="claude-3-opus"
       )

       response = await model.generate(
           prompt="Analyze the climate risks for San Francisco",
           max_tokens=1000,
           temperature=0.7
       )

Data Acquisition
^^^^^^^^^^^^^^^^

.. py:function:: memories.data_acquisition.SatelliteClient.get_imagery(location, date, resolution='medium')
   :noindex:

   Retrieve satellite imagery for a location and date.

   :param dict location: Location coordinates with lat/lon
   :param str date: Date to retrieve imagery for (YYYY-MM-DD)
   :param str resolution: Image resolution ('low', 'medium', 'high')
   :return: Satellite imagery data
   :rtype: dict

   **Example:**

   .. code-block:: python

       from memories.data_acquisition import SatelliteClient

       client = SatelliteClient()
       imagery = await client.get_imagery(
           location={"lat": 37.7749, "lon": -122.4194},
           date="2023-06-15",
           resolution="high"
       )

Utility Functions
^^^^^^^^^^^^^^^^^

.. py:function:: memories.utils.geo_utils.calculate_distance(point1, point2)
   :noindex:

   Calculate the distance between two geographic points.

   :param dict point1: First point with lat/lon coordinates
   :param dict point2: Second point with lat/lon coordinates
   :return: Distance in meters
   :rtype: float

   **Example:**

   .. code-block:: python

       from memories.utils.geo_utils import calculate_distance

       distance = calculate_distance(
           point1={"lat": 37.7749, "lon": -122.4194},
           point2={"lat": 37.3382, "lon": -121.8863}
       )
       print(f"Distance: {distance} meters")

.. py:function:: memories.utils.geo_utils.is_point_in_polygon(point, polygon)
   :noindex:

   Check if a point is within a polygon.

   :param dict point: Point with lat/lon coordinates
   :param list polygon: List of polygon vertices with lat/lon coordinates
   :return: True if point is in polygon, False otherwise
   :rtype: bool

   **Example:**

   .. code-block:: python

       from memories.utils.geo_utils import is_point_in_polygon

       is_inside = is_point_in_polygon(
           point={"lat": 37.7749, "lon": -122.4194},
           polygon=[
               {"lat": 37.7, "lon": -122.5},
               {"lat": 37.8, "lon": -122.5},
               {"lat": 37.8, "lon": -122.4},
               {"lat": 37.7, "lon": -122.4}
           ]
       )
       print(f"Point is inside polygon: {is_inside}")

Function Categories
-------------------

.. toctree::
   :maxdepth: 2
   
   memory_functions
   analyzer_functions
   model_functions
   data_acquisition_functions
   utility_functions

Alphabetical Index
------------------

This section provides an alphabetical listing of all functions in the framework:

.. list-table::
   :widths: 40 60
   :header-rows: 1
   
   * - Function Name
     - Module
   * - calculate_distance
     - memories.utils.geo_utils
   * - ClimateAnalyzer.analyze
     - memories.core.analyzers
   * - generate
     - memories.models.load_model
   * - get_imagery
     - memories.data_acquisition
   * - is_point_in_polygon
     - memories.utils.geo_utils
   * - LoadModel.__init__
     - memories.models.load_model
   * - MemoryStore.query
     - memories
   * - MemoryStore.retrieve
     - memories
   * - MemoryStore.store
     - memories
   * - TerrainAnalyzer.analyze
     - memories.core.analyzers

Function Search
---------------

Use the search box at the top of this page to find specific functions. You can search by function name, module name, or functionality.

For a comprehensive API reference, see the 'index>' section. 