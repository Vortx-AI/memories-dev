.. _quickstart:

==========
Quickstart
==========

This guide will help you get started with the ``memories-dev`` framework quickly. We'll walk through a basic example of retrieving historical satellite imagery, analyzing changes over time, and visualizing the results.

.. admonition:: Prerequisites
   :class: important

   Before starting, make sure you have:

   * Installed ``memories-dev`` (see :ref:`installation`)
   * Set up your API keys for data sources
   * Basic familiarity with Python and geospatial concepts

Basic Setup
===========

First, let's import the necessary modules and set up our environment:

.. code-block:: python

   import asyncio
   import memories
   from memories.earth import SatelliteImagery
   from memories.analysis import TemporalAnalyzer
   from memories.visualization import MapVisualizer

   # Print the version to verify installation
   print(f"memories-dev version: {memories.__version__}")

   # Configure API keys (if not using .env file)
   import os
   os.environ["SATELLITE_API_KEY"] = "your_satellite_api_key"

Retrieving Historical Imagery
=============================

Now, let's retrieve historical satellite imagery for a specific location. We'll use San Francisco as an example:

.. code-block:: python

   # Define the location and time range
   location = (37.7749, -122.4194)  # San Francisco coordinates (latitude, longitude)
   time_range = ("2000-01-01", "2025-03-11")
   
   # Initialize the satellite imagery client
   imagery = SatelliteImagery(api_key=os.environ.get("SATELLITE_API_KEY"))
   
   # Define an async function to fetch the imagery
   async def fetch_imagery():
       # Fetch historical imagery with yearly interval
       images = await imagery.get_historical_imagery(
           location=location,
           time_range=time_range,
           interval="yearly",
           resolution="medium",  # Options: low, medium, high
           cloud_cover_max=20    # Maximum cloud cover percentage
       )
       return images
   
   # Run the async function
   images = asyncio.run(fetch_imagery())
   
   # Print summary of retrieved images
   print(f"Retrieved {len(images)} images spanning {images.time_span} years")
   print(f"Resolution: {images.resolution} meters/pixel")
   print(f"Bands available: {images.bands}")

Analyzing Changes Over Time
===========================

With our historical imagery in hand, let's analyze how the area has changed over time:

.. code-block:: python

   # Initialize the temporal analyzer
   analyzer = TemporalAnalyzer()
   
   # Detect changes between images
   changes = analyzer.detect_changes(
       images=images,
       method="difference",  # Options: difference, ndvi, urban, water
       threshold=0.15        # Sensitivity threshold (0-1)
   )
   
   # Get statistics about the changes
   stats = changes.get_statistics()
   
   print(f"Change detection complete")
   print(f"Total area changed: {stats['area_changed']} square km")
   print(f"Rate of change: {stats['change_rate']} square km per year")
   print(f"Most significant change period: {stats['peak_change_period']}")

   # Identify specific types of changes
   urban_expansion = analyzer.classify_changes(
       changes=changes,
       classification="urban_expansion"
   )
   
   print(f"Urban expansion detected: {urban_expansion.total_area} square km")
   print(f"Major expansion periods: {urban_expansion.significant_periods}")

Visualizing the Results
=======================

Finally, let's visualize our results to better understand the changes:

.. code-block:: python

   # Initialize the map visualizer
   visualizer = MapVisualizer()
   
   # Create an interactive map showing changes over time
   change_map = visualizer.create_change_map(
       changes=changes,
       base_map="satellite",  # Options: satellite, streets, terrain
       title="San Francisco Urban Changes (2000-2025)"
   )
   
   # Add a time slider to the map
   change_map.add_time_slider()
   
   # Add additional layers
   change_map.add_layer(urban_expansion, name="Urban Expansion", color="red")
   
   # Save the map to an HTML file
   change_map.save("san_francisco_changes.html")
   
   print("Map saved to san_francisco_changes.html")
   
   # Open the map in a web browser
   import webbrowser
   webbrowser.open("san_francisco_changes.html")

Complete Example
================

Here's the complete code for the quickstart example:

.. code-block:: python

   import asyncio
   import os
   import webbrowser
   import memories
   from memories.earth import SatelliteImagery
   from memories.analysis import TemporalAnalyzer
   from memories.visualization import MapVisualizer
   
   # Print version and configure API keys
   print(f"memories-dev version: {memories.__version__}")
   os.environ["SATELLITE_API_KEY"] = "your_satellite_api_key"
   
   # Define location and time range
   location = (37.7749, -122.4194)  # San Francisco
   time_range = ("2000-01-01", "2025-03-11")
   
   # Initialize components
   imagery = SatelliteImagery(api_key=os.environ.get("SATELLITE_API_KEY"))
   analyzer = TemporalAnalyzer()
   visualizer = MapVisualizer()
   
   async def analyze_location():
       # Fetch historical imagery
       print("Fetching historical imagery...")
       images = await imagery.get_historical_imagery(
           location=location,
           time_range=time_range,
           interval="yearly",
           resolution="medium",
           cloud_cover_max=20
       )
       
       print(f"Retrieved {len(images)} images spanning {images.time_span} years")
       
       # Detect changes
       print("Analyzing changes...")
       changes = analyzer.detect_changes(
           images=images,
           method="difference",
           threshold=0.15
       )
       
       # Get statistics
       stats = changes.get_statistics()
       print(f"Total area changed: {stats['area_changed']} square km")
       
       # Classify changes
       urban_expansion = analyzer.classify_changes(
           changes=changes,
           classification="urban_expansion"
       )
       
       # Create visualization
       print("Creating visualization...")
       change_map = visualizer.create_change_map(
           changes=changes,
           base_map="satellite",
           title="San Francisco Urban Changes (2000-2025)"
       )
       
       change_map.add_time_slider()
       change_map.add_layer(urban_expansion, name="Urban Expansion", color="red")
       change_map.save("san_francisco_changes.html")
       
       print("Analysis complete! Opening map...")
       webbrowser.open("san_francisco_changes.html")
   
   # Run the analysis
   if __name__ == "__main__":
       asyncio.run(analyze_location())

Advanced Features
=================

The ``memories-dev`` framework offers many more advanced features:

Multi-Location Analysis
-----------------------

Analyze multiple locations simultaneously:

.. code-block:: python

   locations = [
       {"name": "San Francisco", "coords": (37.7749, -122.4194)},
       {"name": "New York", "coords": (40.7128, -74.0060)},
       {"name": "Miami", "coords": (25.7617, -80.1918)}
   ]
   
   async def analyze_multiple_locations():
       tasks = []
       for loc in locations:
           task = imagery.get_historical_imagery(
               location=loc["coords"],
               time_range=time_range,
               interval="yearly"
           )
           tasks.append(task)
       
       # Fetch all imagery concurrently
       all_images = await asyncio.gather(*tasks)
       
       # Process each location's imagery
       for i, images in enumerate(all_images):
           location_name = locations[i]["name"]
           print(f"Analyzing {location_name}...")
           
           # Analyze and visualize as before
           # ...

Custom Analysis Pipelines
-------------------------

Create custom analysis pipelines for specific use cases:

.. code-block:: python

   from memories.pipeline import Pipeline
   from memories.processors import (
       CloudRemoval,
       NDVICalculator,
       UrbanDetector,
       ChangeClassifier
   )
   
   # Create a custom pipeline
   pipeline = Pipeline([
       CloudRemoval(method="deep_learning"),
       NDVICalculator(),
       UrbanDetector(sensitivity=0.8),
       ChangeClassifier(classes=["urban", "vegetation", "water"])
   ])
   
   # Process images through the pipeline
   results = pipeline.process(images)

Next Steps
==========

Now that you've completed the quickstart guide, you can:

* Explore more detailed :ref:`examples` for specific use cases
* Learn about the 'core_concepts' of the framework
* Dive into the 'api_reference' for comprehensive documentation
* Configure advanced 'data_sources' for your specific needs
* Explore 'applications' built on the framework 