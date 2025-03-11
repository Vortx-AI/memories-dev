.. _examples:

========
Examples
========

This page provides practical examples of using the ``memories-dev`` framework for various real-world applications. Each example includes complete code that you can adapt for your own projects.

Basic Examples
==============

Historical Imagery Analysis
---------------------------

This example demonstrates how to retrieve and analyze historical satellite imagery for a specific location:

.. code-block:: python

   import asyncio
   import memories
   from memories.earth import SatelliteImagery
   from memories.analysis import TemporalAnalyzer
   from memories.visualization import MapVisualizer
   
   async def analyze_historical_imagery():
       # Initialize components
       imagery = SatelliteImagery()
       analyzer = TemporalAnalyzer()
       visualizer = MapVisualizer()
       
       # Define location and time range
       location = (37.7749, -122.4194)  # San Francisco
       time_range = ("2000-01-01", "2025-03-11")
       
       # Fetch historical imagery
       images = await imagery.get_historical_imagery(
           location=location,
           time_range=time_range,
           interval="yearly",
           resolution="medium"
       )
       
       # Detect changes over time
       changes = analyzer.detect_changes(
           images=images,
           method="difference",
           threshold=0.15
       )
       
       # Get statistics about the changes
       stats = changes.get_statistics()
       print(f"Total area changed: {stats['area_changed']} square km")
       print(f"Rate of change: {stats['change_rate']} square km per year")
       
       # Visualize the changes
       change_map = visualizer.create_change_map(
           changes=changes,
           base_map="satellite"
       )
       
       # Save the visualization
       change_map.save("historical_changes.html")
       print("Analysis complete! Map saved to historical_changes.html")
   
   # Run the analysis
   if __name__ == "__main__":
       asyncio.run(analyze_historical_imagery())

Environmental Monitoring
------------------------

This example shows how to monitor environmental changes such as deforestation:

.. code-block:: python

   import asyncio
   import memories
   from memories.earth import SatelliteImagery
   from memories.analysis import EnvironmentalAnalyzer
   from memories.visualization import MapVisualizer
   
   async def monitor_deforestation():
       # Initialize components
       imagery = SatelliteImagery()
       analyzer = EnvironmentalAnalyzer()
       visualizer = MapVisualizer()
       
       # Define region and time range
       region = {
           "name": "Amazon Rainforest",
           "bbox": (-73.9872, -9.7889, -50.7929, 2.2869)  # (min_lon, min_lat, max_lon, max_lat)
       }
       time_range = ("2010-01-01", "2025-03-11")
       
       # Fetch imagery for the region
       images = await imagery.get_regional_imagery(
           bbox=region["bbox"],
           time_range=time_range,
           interval="yearly",
           resolution="medium"
       )
       
       # Analyze deforestation
       deforestation = analyzer.detect_deforestation(
           images=images,
           method="ndvi_threshold",
           threshold=0.3
       )
       
       # Calculate statistics
       stats = deforestation.get_statistics()
       print(f"Region: {region['name']}")
       print(f"Total deforested area: {stats['total_area']} square km")
       print(f"Deforestation rate: {stats['annual_rate']} square km per year")
       print(f"Hotspots detected: {len(stats['hotspots'])}")
       
       # Visualize deforestation
       deforestation_map = visualizer.create_environmental_map(
           data=deforestation,
           base_map="satellite",
           title=f"Deforestation in {region['name']} (2010-2025)"
       )
       
       # Add time slider and legend
       deforestation_map.add_time_slider()
       deforestation_map.add_legend(
           title="Deforestation Intensity",
           colors=["#FFEDA0", "#FEB24C", "#FC4E2A", "#BD0026"]
       )
       
       # Save the visualization
       deforestation_map.save("deforestation_analysis.html")
       print("Analysis complete! Map saved to deforestation_analysis.html")
   
   # Run the analysis
   if __name__ == "__main__":
       asyncio.run(monitor_deforestation())

Intermediate Examples
=====================

Real Estate Analysis
--------------------

This example demonstrates how to analyze a property and its surroundings over time:

.. code-block:: python

   import asyncio
   import memories
   from memories.applications import RealEstateAgent
   from memories.visualization import PropertyVisualizer
   
   async def analyze_property():
       # Initialize the real estate agent
       agent = RealEstateAgent()
       
       # Define the property to analyze
       property_address = "123 Main St, San Francisco, CA"
       
       # Analyze the property
       analysis = await agent.analyze_property(
           address=property_address,
           time_range=("1990-01-01", "2025-03-11"),
           include_environmental=True,
           include_neighborhood=True,
           include_projections=True
       )
       
       # Print property insights
       print(f"Property: {property_address}")
       print(f"Property Timeline:")
       for event in analysis.timeline:
           print(f"  - {event['date']}: {event['description']}")
       
       print("\nEnvironmental Factors:")
       for factor, value in analysis.environmental_factors.items():
           print(f"  - {factor}: {value}")
       
       print("\nNeighborhood Changes:")
       for period, changes in analysis.neighborhood_changes.items():
           print(f"  - {period}:")
           for change in changes:
               print(f"    - {change}")
       
       print("\nFuture Projections:")
       for year, projection in analysis.future_projections.items():
           print(f"  - {year}: {projection}")
       
       # Visualize the property analysis
       visualizer = PropertyVisualizer()
       
       # Create property visualization
       property_viz = visualizer.create_property_visualization(
           analysis=analysis,
           include_timeline=True,
           include_3d=True,
           include_neighborhood=True
       )
       
       # Save the visualization
       property_viz.save("property_analysis.html")
       print("Analysis complete! Visualization saved to property_analysis.html")
   
   # Run the analysis
   if __name__ == "__main__":
       asyncio.run(analyze_property())

Urban Development Analysis
--------------------------

This example shows how to analyze urban development patterns over time:

.. code-block:: python

   import asyncio
   import memories
   from memories.applications import UrbanPlanner
   from memories.visualization import UrbanVisualizer
   
   async def analyze_urban_development():
       # Initialize the urban planner
       planner = UrbanPlanner()
       
       # Define the city to analyze
       city = "Boston, MA"
       time_range = ("1950-01-01", "2025-03-11")
       
       # Analyze urban development
       development = await planner.analyze_development(
           city=city,
           time_range=time_range,
           factors=["buildings", "roads", "green_space", "water_bodies"],
           resolution="high"
       )
       
       # Print development insights
       print(f"Urban Development Analysis: {city}")
       print(f"Analysis period: {time_range[0]} to {time_range[1]}")
       
       print("\nDevelopment Statistics:")
       for factor, stats in development.statistics.items():
           print(f"  - {factor}:")
           for stat, value in stats.items():
               print(f"    - {stat}: {value}")
       
       # Generate recommendations
       recommendations = planner.generate_recommendations(
           development=development,
           focus_areas=["sustainability", "public_transport", "housing", "green_space"]
       )
       
       print("\nUrban Planning Recommendations:")
       for area, recs in recommendations.items():
           print(f"  - {area}:")
           for rec in recs:
               print(f"    - {rec}")
       
       # Visualize urban development
       visualizer = UrbanVisualizer()
       
       # Create urban development visualization
       urban_viz = visualizer.create_urban_visualization(
           development=development,
           recommendations=recommendations,
           include_3d=True,
           include_timeline=True
       )
       
       # Save the visualization
       urban_viz.save("urban_development.html")
       print("Analysis complete! Visualization saved to urban_development.html")
   
   # Run the analysis
   if __name__ == "__main__":
       asyncio.run(analyze_urban_development())

Advanced Examples
=================

Multi-Location Comparative Analysis
-----------------------------------

This example demonstrates how to compare multiple locations over time:

.. code-block:: python

   import asyncio
   import memories
   from memories.earth import SatelliteImagery
   from memories.analysis import ComparativeAnalyzer
   from memories.visualization import ComparativeVisualizer
   
   async def compare_locations():
       # Initialize components
       imagery = SatelliteImagery()
       analyzer = ComparativeAnalyzer()
       visualizer = ComparativeVisualizer()
       
       # Define locations to compare
       locations = [
           {"name": "San Francisco", "coords": (37.7749, -122.4194)},
           {"name": "New York", "coords": (40.7128, -74.0060)},
           {"name": "Miami", "coords": (25.7617, -80.1918)},
           {"name": "Seattle", "coords": (47.6062, -122.3321)}
       ]
       
       time_range = ("2000-01-01", "2025-03-11")
       
       # Fetch imagery for all locations concurrently
       fetch_tasks = []
       for location in locations:
           task = imagery.get_historical_imagery(
               location=location["coords"],
               time_range=time_range,
               interval="yearly",
               resolution="medium"
           )
           fetch_tasks.append(task)
       
       all_images = await asyncio.gather(*fetch_tasks)
       
       # Create a dictionary mapping location names to their imagery
       location_images = {
           locations[i]["name"]: images for i, images in enumerate(all_images)
       }
       
       # Perform comparative analysis
       comparison = analyzer.compare_locations(
           location_images=location_images,
           metrics=["urban_growth", "vegetation_change", "water_change"],
           normalization="area"
       )
       
       # Print comparison results
       print("Multi-Location Comparative Analysis")
       print(f"Analysis period: {time_range[0]} to {time_range[1]}")
       
       print("\nComparison Results:")
       for metric, results in comparison.metrics.items():
           print(f"\n{metric.replace('_', ' ').title()}:")
           for location, value in results.items():
               print(f"  - {location}: {value}")
       
       print("\nRankings:")
       for metric, rankings in comparison.rankings.items():
           print(f"\n{metric.replace('_', ' ').title()} Ranking:")
           for i, (location, score) in enumerate(rankings):
               print(f"  {i+1}. {location}: {score}")
       
       # Create visualization
       comparison_viz = visualizer.create_comparison_visualization(
           comparison=comparison,
           include_charts=True,
           include_maps=True,
           include_rankings=True
       )
       
       # Save the visualization
       comparison_viz.save("location_comparison.html")
       print("Analysis complete! Visualization saved to location_comparison.html")
   
   # Run the analysis
   if __name__ == "__main__":
       asyncio.run(compare_locations())

Custom Analysis Pipeline
------------------------

This example shows how to create a custom analysis pipeline for specific needs:

.. code-block:: python

   import asyncio
   import memories
   from memories.earth import SatelliteImagery
   from memories.pipeline import Pipeline
   from memories.processors import (
       CloudRemoval,
       NDVICalculator,
       UrbanDetector,
       ChangeClassifier,
       StatisticsCalculator
   )
   from memories.visualization import MapVisualizer
   
   async def custom_pipeline_analysis():
       # Initialize satellite imagery client
       imagery = SatelliteImagery()
       
       # Define location and time range
       location = (34.0522, -118.2437)  # Los Angeles
       time_range = ("2000-01-01", "2025-03-11")
       
       # Fetch historical imagery
       images = await imagery.get_historical_imagery(
           location=location,
           time_range=time_range,
           interval="yearly",
           resolution="medium"
       )
       
       # Create a custom processing pipeline
       pipeline = Pipeline([
           # Step 1: Remove clouds from images
           CloudRemoval(
               method="deep_learning",
               fallback="interpolation"
           ),
           
           # Step 2: Calculate NDVI (Normalized Difference Vegetation Index)
           NDVICalculator(
               red_band="B04",
               nir_band="B08",
               output_name="ndvi"
           ),
           
           # Step 3: Detect urban areas
           UrbanDetector(
               method="spectral_index",
               threshold=0.4,
               output_name="urban_areas"
           ),
           
           # Step 4: Classify changes between time periods
           ChangeClassifier(
               reference_year="2000",
               classes=["urban", "vegetation", "water", "barren"],
               min_area=10000,  # square meters
               output_name="classified_changes"
           ),
           
           # Step 5: Calculate statistics
           StatisticsCalculator(
               metrics=["area", "rate", "percentage"],
               per_class=True,
               output_name="statistics"
           )
       ])
       
       # Process the images through the pipeline
       results = pipeline.process(images)
       
       # Print the results
       print("Custom Pipeline Analysis Results")
       print(f"Location: Los Angeles")
       print(f"Analysis period: {time_range[0]} to {time_range[1]}")
       
       print("\nStatistics:")
       for class_name, stats in results["statistics"].items():
           print(f"\n{class_name.replace('_', ' ').title()}:")
           for metric, value in stats.items():
               print(f"  - {metric}: {value}")
       
       # Visualize the results
       visualizer = MapVisualizer()
       
       # Create visualization
       pipeline_viz = visualizer.create_pipeline_visualization(
           results=results,
           base_map="satellite",
           title="Los Angeles Urban and Vegetation Changes (2000-2025)"
       )
       
       # Add components to visualization
       pipeline_viz.add_time_slider()
       pipeline_viz.add_layer_controls()
       pipeline_viz.add_statistics_panel()
       
       # Save the visualization
       pipeline_viz.save("custom_pipeline_analysis.html")
       print("Analysis complete! Visualization saved to custom_pipeline_analysis.html")
   
   # Run the analysis
   if __name__ == "__main__":
       asyncio.run(custom_pipeline_analysis())

Integration with External Data
------------------------------

This example demonstrates how to integrate external data sources with the framework:

.. code-block:: python

   import asyncio
   import pandas as pd
   import geopandas as gpd
   import memories
   from memories.earth import SatelliteImagery, GISProvider
   from memories.analysis import IntegratedAnalyzer
   from memories.visualization import IntegratedVisualizer
   
   async def integrated_analysis():
       # Initialize components
       imagery = SatelliteImagery()
       gis = GISProvider(provider="osm")
       analyzer = IntegratedAnalyzer()
       visualizer = IntegratedVisualizer()
       
       # Define study area
       city = "Chicago, IL"
       time_range = ("2010-01-01", "2025-03-11")
       
       # Get city boundary
       boundary = await gis.get_boundary(city)
       
       # Fetch satellite imagery for the city
       images = await imagery.get_area_imagery(
           boundary=boundary,
           time_range=time_range,
           interval="yearly",
           resolution="medium"
       )
       
       # Load external census data
       census_data = pd.read_csv("chicago_census_data.csv")
       
       # Load external climate data
       climate_data = pd.read_csv("chicago_climate_data.csv")
       
       # Load external property value data as GeoDataFrame
       property_values = gpd.read_file("chicago_property_values.geojson")
       
       # Integrate all data sources
       integrated_data = analyzer.integrate_data(
           imagery=images,
           boundary=boundary,
           external_data={
               "census": census_data,
               "climate": climate_data,
               "property_values": property_values
           },
           spatial_join_method="intersects",
           temporal_alignment="yearly"
       )
       
       # Analyze relationships between data sources
       relationships = analyzer.analyze_relationships(
           integrated_data=integrated_data,
           dependent_variable="property_values",
           independent_variables=[
               "urban_density", 
               "green_space",
               "temperature",
               "precipitation",
               "income",
               "population"
           ],
           method="regression"
       )
       
       # Print relationship findings
       print("Integrated Data Analysis Results")
       print(f"City: {city}")
       print(f"Analysis period: {time_range[0]} to {time_range[1]}")
       
       print("\nRelationships with Property Values:")
       for variable, stats in relationships.items():
           print(f"\n{variable.replace('_', ' ').title()}:")
           print(f"  - Correlation: {stats['correlation']:.3f}")
           print(f"  - Significance: {stats['p_value']:.3f}")
           print(f"  - Direction: {stats['direction']}")
           print(f"  - Strength: {stats['strength']}")
       
       # Create visualization
       integrated_viz = visualizer.create_integrated_visualization(
           integrated_data=integrated_data,
           relationships=relationships,
           base_map="light",
           title=f"{city} Integrated Analysis ({time_range[0]} to {time_range[1]})"
       )
       
       # Add components to visualization
       integrated_viz.add_time_slider()
       integrated_viz.add_layer_controls()
       integrated_viz.add_relationship_charts()
       integrated_viz.add_data_explorer()
       
       # Save the visualization
       integrated_viz.save("integrated_analysis.html")
       print("Analysis complete! Visualization saved to integrated_analysis.html")
   
   # Run the analysis
   if __name__ == "__main__":
       asyncio.run(integrated_analysis())

Real-World Applications
=======================

Disaster Impact Assessment
--------------------------

This example shows how to assess the impact of natural disasters:

.. code-block:: python

   import asyncio
   import memories
   from memories.applications import DisasterAnalyzer
   from memories.visualization import DisasterVisualizer
   from datetime import datetime, timedelta
   
   async def analyze_disaster_impact():
       # Initialize the disaster analyzer
       analyzer = DisasterAnalyzer()
       
       # Define disaster parameters
       disaster_info = {
           "type": "hurricane",
           "name": "Hurricane Ian",
           "location": "Florida, USA",
           "date": "2022-09-28",
           "bbox": (-87.6348, 23.8063, -79.9742, 31.0035)  # Florida bounding box
       }
       
       # Calculate time range (before and after disaster)
       disaster_date = datetime.strptime(disaster_info["date"], "%Y-%m-%d")
       before_date = (disaster_date - timedelta(days=30)).strftime("%Y-%m-%d")
       after_date = (disaster_date + timedelta(days=90)).strftime("%Y-%m-%d")
       
       # Analyze disaster impact
       impact = await analyzer.analyze_disaster(
           disaster_type=disaster_info["type"],
           location=disaster_info["location"],
           bbox=disaster_info["bbox"],
           before_date=before_date,
           disaster_date=disaster_info["date"],
           after_date=after_date,
           include_infrastructure=True,
           include_environmental=True,
           include_economic=True
       )
       
       # Print impact assessment
       print(f"Disaster Impact Assessment: {disaster_info['name']}")
       print(f"Location: {disaster_info['location']}")
       print(f"Date: {disaster_info['date']}")
       
       print("\nImpact Summary:")
       print(f"  - Affected Area: {impact.affected_area} square km")
       print(f"  - Severity Level: {impact.severity_level}")
       
       print("\nInfrastructure Impact:")
       for category, details in impact.infrastructure.items():
           print(f"  - {category}:")
           for item, value in details.items():
               print(f"    - {item}: {value}")
       
       print("\nEnvironmental Impact:")
       for category, value in impact.environmental.items():
           print(f"  - {category}: {value}")
       
       print("\nEconomic Impact:")
       for category, value in impact.economic.items():
           print(f"  - {category}: ${value:,.2f}")
       
       print("\nRecovery Timeline:")
       for phase, details in impact.recovery_timeline.items():
           print(f"  - {phase}: {details['duration']} ({details['status']})")
       
       # Visualize the disaster impact
       visualizer = DisasterVisualizer()
       
       # Create disaster impact visualization
       disaster_viz = visualizer.create_disaster_visualization(
           impact=impact,
           disaster_info=disaster_info,
           include_before_after=True,
           include_recovery=True,
           include_statistics=True
       )
       
       # Save the visualization
       disaster_viz.save("disaster_impact.html")
       print("Analysis complete! Visualization saved to disaster_impact.html")
   
   # Run the analysis
   if __name__ == "__main__":
       asyncio.run(analyze_disaster_impact())

Historical Site Reconstruction
------------------------------

This example demonstrates how to reconstruct historical sites using multiple data sources:

.. code-block:: python

   import asyncio
   import memories
   from memories.applications import HistoricalReconstructor
   from memories.visualization import HistoricalVisualizer
   
   async def reconstruct_historical_site():
       # Initialize the historical reconstructor
       reconstructor = HistoricalReconstructor()
       
       # Define historical site parameters
       site_info = {
           "name": "Ancient Rome",
           "location": "Rome, Italy",
           "coordinates": (41.9028, 12.4964),
           "time_period": "100 CE",
           "radius_km": 5
       }
       
       # Reconstruct the historical site
       reconstruction = await reconstructor.reconstruct_site(
           site_name=site_info["name"],
           location=site_info["coordinates"],
           time_period=site_info["time_period"],
           radius_km=site_info["radius_km"],
           data_sources=["historical_maps", "archaeological_data", "textual_descriptions", "artwork"],
           reconstruction_detail="high",
           include_uncertainty=True
       )
       
       # Print reconstruction details
       print(f"Historical Site Reconstruction: {site_info['name']}")
       print(f"Time Period: {site_info['time_period']}")
       print(f"Location: {site_info['location']}")
       
       print("\nReconstruction Summary:")
       print(f"  - Confidence Level: {reconstruction.confidence_level}")
       print(f"  - Data Sources Used: {len(reconstruction.data_sources)}")
       print(f"  - Structures Reconstructed: {len(reconstruction.structures)}")
       
       print("\nKey Structures:")
       for structure in reconstruction.key_structures:
           print(f"  - {structure.name}:")
           print(f"    - Type: {structure.type}")
           print(f"    - Confidence: {structure.confidence}")
           print(f"    - Data Sources: {', '.join(structure.sources)}")
       
       print("\nLandscape Features:")
       for feature in reconstruction.landscape_features:
           print(f"  - {feature.name}: {feature.description}")
       
       # Visualize the historical reconstruction
       visualizer = HistoricalVisualizer()
       
       # Create historical site visualization
       historical_viz = visualizer.create_historical_visualization(
           reconstruction=reconstruction,
           site_info=site_info,
           include_3d=True,
           include_uncertainty=True,
           include_modern_comparison=True,
           include_timeline=True
       )
       
       # Save the visualization
       historical_viz.save("historical_reconstruction.html")
       print("Reconstruction complete! Visualization saved to historical_reconstruction.html")
   
   # Run the reconstruction
   if __name__ == "__main__":
       asyncio.run(reconstruct_historical_site())

Next Steps
==========

After exploring these examples, you might want to:

* Adapt them to your specific use cases
* Combine multiple examples to create more complex applications
* Explore the 'api_reference' for detailed information about each component
* Learn about 'advanced_features' for more sophisticated analyses
* Check out the 'tutorials' for step-by-step guides on specific tasks 