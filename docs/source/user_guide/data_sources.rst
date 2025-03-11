Data Sources
============

.. code-block:: text
   
Overview
--------

memories-dev provides a comprehensive data acquisition system that supports multiple data sources for creating and enriching memories, including satellite imagery, vector data, and environmental metrics.

Supported Data Sources
----------------------

Satellite Data
~~~~~~~~~~~~~~
- **Sentinel-2**: High-resolution multispectral imagery via Planetary Computer
- **Landsat**: Medium-resolution multispectral imagery
- **Earth Engine**: Access to Google Earth Engine datasets
- **COG/STAC**: Cloud-optimized GeoTIFF and SpatioTemporal Asset Catalog

Vector Data
~~~~~~~~~~~
- **OpenStreetMap**: Comprehensive global mapping data
- **Overture Maps**: Detailed vector mapping data
- **WFS Services**: Web Feature Service endpoints

Data Manager
------------

The ``DataManager`` class provides a unified interface for accessing all data sources:

.. code-block:: python

    from memories.data_acquisition.data_manager import DataManager
    import asyncio
    from datetime import datetime, timedelta
    
    # Initialize data manager with cache directory
    data_manager = DataManager(cache_dir="./data_cache")
    
    # Define area of interest (San Francisco)
    bbox = {
        'xmin': -122.4018,
        'ymin': 37.7914,
        'xmax': -122.3928,
        'ymax': 37.7994
    }
    
    # Define time range (last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    async def get_comprehensive_data():
        # Get satellite data
        satellite_data = await data_manager.get_satellite_data(
            bbox_coords=bbox,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )
        
        # Get vector data
        vector_data = await data_manager.get_vector_data(
            bbox=bbox,
            layers=["buildings", "roads", "landuse"]
        )
        
        # Prepare comprehensive training data
        training_data = await data_manager.prepare_training_data(
            bbox=bbox,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            satellite_collections=["sentinel-2-l2a"],
            vector_layers=["buildings", "roads"],
            cloud_cover=20.0
        )
        
        return {
            "satellite": satellite_data,
            "vector": vector_data,
            "training": training_data
        }
    
    # Run the async function
    results = asyncio.run(get_comprehensive_data())
    
    # Process results
    print(f"Satellite data: {len(results['satellite']['scenes'])} scenes")
    print(f"Vector data: {len(results['vector']['features'])} features")
    print(f"Training data: {results['training']['status']}")

Example Output:

.. code-block:: text

    Satellite data: 3 scenes
    Vector data: 1245 features
    Training data: success

Advanced Usage: Multi-Source Data Fusion
----------------------------------------

Combining multiple data sources for comprehensive analysis:

.. code-block:: python

    from memories.data_acquisition.data_manager import DataManager
    from memories.data_acquisition.processors import DataFusion
    import asyncio
    
    data_manager = DataManager(cache_dir="./data_cache")
    fusion_processor = DataFusion()
    
    async def perform_data_fusion():
        # Get data from multiple sources
        satellite_data = await data_manager.get_satellite_data(
            bbox_coords=bbox,
            start_date="2024-01-01",
            end_date="2024-02-01"
        )
        
        vector_data = await data_manager.get_vector_data(
            bbox=bbox,
            layers=["buildings", "roads"]
        )
        
        # Perform data fusion
        fused_data = fusion_processor.fuse(
            primary=satellite_data,
            secondary=vector_data,
            method="overlay",
            resolution=10  # meters per pixel
        )
        
        # Extract insights
        insights = fusion_processor.analyze(
            fused_data,
            metrics=["urban_density", "vegetation_health"]
        )
        
        return insights
    
    # Run the fusion process
    insights = asyncio.run(perform_data_fusion())
    
    # Display insights
    for metric, value in insights.items():
        print(f"{metric}: {value}")

Example Output:

.. code-block:: text

    urban_density: 78.3%
    vegetation_health: Good (NDVI: 0.68)

Sentinel API
------------

The ``SentinelAPI`` class provides direct access to Sentinel-2 data:

.. code-block:: python

    from memories.data_acquisition.sources.sentinel_api import SentinelAPI
    from datetime import datetime, timedelta
    import asyncio
    import matplotlib.pyplot as plt
    import numpy as np
    
    # Initialize Sentinel API
    api = SentinelAPI(data_dir="./sentinel_data")
    
    async def download_and_visualize():
        # Initialize the client
        await api.initialize()
        
        # Define area of interest
        bbox = {
            'xmin': -122.4018,
            'ymin': 37.7914,
            'xmax': -122.3928,
            'ymax': 37.7994
        }
        
        # Define date range
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        # Download specific bands with cloud cover filter
        result = await api.download_data(
            bbox=bbox,
            start_date=start_date,
            end_date=end_date,
            bands=["B04", "B08"],  # Red and NIR bands
            cloud_cover=10.0
        )
        
        if result["status"] == "success":
            # Calculate NDVI (if both red and NIR bands are available)
            if "B04" in result["bands"] and "B08" in result["bands"]:
                red_band = np.load(f"./sentinel_data/{result['scene_id']}_B04.npy")
                nir_band = np.load(f"./sentinel_data/{result['scene_id']}_B08.npy")
                
                # Calculate NDVI
                ndvi = (nir_band - red_band) / (nir_band + red_band)
                
                # Plot NDVI
                plt.figure(figsize=(10, 8))
                plt.imshow(ndvi, cmap='RdYlGn', vmin=-1, vmax=1)
                plt.colorbar(label='NDVI')
                plt.title(f"NDVI - {result['metadata']['acquisition_date']}")
                plt.savefig("./sentinel_data/ndvi_visualization.png")
                
                return {
                    "status": "success",
                    "ndvi_mean": float(np.mean(ndvi)),
                    "ndvi_max": float(np.max(ndvi)),
                    "visualization": "./sentinel_data/ndvi_visualization.png"
                }
            
            return result
        else:
            return result
    
    # Run the download and visualization
    result = asyncio.run(download_and_visualize())
    
    # Display results
    if result["status"] == "success":
        print(f"Downloaded bands: {result.get('bands', [])}")
        print(f"Scene ID: {result.get('scene_id', '')}")
        print(f"Cloud cover: {result.get('cloud_cover', 0)}%")
        if "ndvi_mean" in result:
            print(f"Mean NDVI: {result['ndvi_mean']:.2f}")
            print(f"Max NDVI: {result['ndvi_max']:.2f}")
            print(f"Visualization saved to: {result['visualization']}")
    else:
        print(f"Error: {result.get('message', 'Unknown error')}")

Example Output:

.. code-block:: text

    Downloaded bands: ['B04', 'B08']
    Scene ID: S2A_MSIL2A_20240215T184721_N0509_R113_T10SEG_20240215T221514
    Cloud cover: 5.2%
    Mean NDVI: 0.42
    Max NDVI: 0.89
    Visualization saved to: ./sentinel_data/ndvi_visualization.png

.. code-block:: text
   
   ENVIRONMENTAL METRICS:
   -----------------
   - Vegetation Index (NDVI): 0.68 (Healthy)
   - Urban Density: 78% (High)
   - Water Bodies: 22% of area
   - Cloud Cover: 5%
   
   DETECTED FEATURES:
   ------------------
   - Buildings: 1,245 structures
   - Roads: 87 km total length
   - Water: San Francisco Bay
   - Parks: Golden Gate Park, other green spaces
   
Change Detection Results
------------------------
   - Vegetation: +2.3% increase
   - Urban Area: +0.8% increase

Key Insights
-------------
   - Healthy vegetation in park areas
   - Moderate urban development in northern sectors

Environmental Impact
--------------------
   - Reduced heat island effect
   - Improved air quality
   - Enhanced ecosystem resilience

Recommendations
---------------
   - Expand green infrastructure
   - Optimize urban density
   - Implement climate adaptation measures

Error Handling
--------------

The data acquisition components include robust error handling:

.. code-block:: python

    from memories.data_acquisition.data_manager import DataManager
    import asyncio
    
    data_manager = DataManager(cache_dir="./data_cache")
    
    async def handle_data_errors():
        try:
            # Try with invalid bbox
            invalid_bbox = {
                'xmin': 200,  # Invalid longitude
                'ymin': 37.7914,
                'xmax': -122.3928,
                'ymax': 37.7994
            }
            
            result = await data_manager.get_satellite_data(
                bbox_coords=invalid_bbox,
                start_date="2024-01-01",
                end_date="2024-02-01"
            )
            
        except ValueError as e:
            print(f"Validation error: {e}")
            
        except ConnectionError as e:
            print(f"Connection error: {e}")
            
        except Exception as e:
            print(f"Unexpected error: {e}")
            
        finally:
            print("Error handling complete")
    
    # Run the error handling example
    asyncio.run(handle_data_errors())

Best Practices
--------------

1. **Efficient Data Acquisition**:
   - Use the smallest possible bounding box for your area of interest
   - Request only the bands you need
   - Set appropriate cloud cover thresholds (10-20% recommended)
   - Use the cache system to avoid redundant downloads

2. **Asynchronous Operations**:
   - All data acquisition methods are asynchronous
   - Use `asyncio.gather()` for concurrent downloads
   - Handle exceptions properly in asynchronous code

3. **Resource Management**:
   - Clean up temporary files when no longer needed
   - Monitor disk usage when downloading large datasets
   - Consider using cloud storage for large-scale operations
