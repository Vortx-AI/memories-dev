=============
Point Pattern
=============

Overview
--------

The point pattern analysis module in memories-dev provides tools for analyzing spatial point patterns in Earth observation data. The implementation is based on the actual code in `memories/utils/processors/vector_processor.py`.

Core Implementation
-------------------

The main point pattern analysis functionality is implemented in the `VectorProcessor` class:

.. code-block:: python

    class VectorProcessor:
        """Processor for vector data."""
        
        def calculate_density(
            self,
            gdf: gpd.GeoDataFrame,
            resolution: float,
            bbox: Union[Tuple[float, float, float, float], Polygon],
            kernel_size: int = 5
        ) -> np.ndarray:
""""""""""""""""
            Calculate feature density.
            
            Args:
                gdf: GeoDataFrame to analyze
                resolution: Output resolution in meters
                bbox: Bounding box or Polygon
                kernel_size: Size of the smoothing kernel
                
            Returns:
                Density array
"""""""""""""

Density Analysis
----------------

The density calculation uses a Gaussian smoothing approach:

.. code-block:: python

    # Rasterize first
    raster = self.rasterize_layer(gdf, resolution, bbox)
    
    # Apply Gaussian smoothing
    kernel = np.ones((kernel_size, kernel_size)) / (kernel_size * kernel_size)
    density = cv2.filter2D(raster.astype(np.float32), -1, kernel)

Spatial Analysis Tools
----------------------

Area-based statistics calculation:

.. code-block:: python

    def calculate_area_statistics(
        gdf: gpd.GeoDataFrame,
        value_column: str = None
    ) -> Dict[str, float]:
""""""""""""""""""""""
        Calculate area-based statistics for vector features.
        
        Args:
            gdf: Input GeoDataFrame
            value_column: Optional column for weighted statistics
            
        Returns:
            Dictionary of statistics
""""""""""""""""""""""""
        stats = {
            'total_area': gdf.geometry.area.sum(),
            'mean_area': gdf.geometry.area.mean(),
            'count': len(gdf)
        }
        
        if value_column and value_column in gdf.columns:
            stats.update({
                'weighted_mean': np.average(
                    gdf.geometry.area,
                    weights=gdf[value_column]
                )
            })
        
        return stats

Configuration
-------------

Analysis parameters are defined in `analysis_config.py`:

.. code-block:: python

    URBAN_CONFIG = {
        'building_density_threshold': 0.4,
        'road_density_threshold': 0.2,
        'min_building_size': 50,  # square meters
        'buffer_distance': 100,  # meters
        'cluster_distance': 50  # meters
    }

Usage Example
-------------

Here's how to use the point pattern analysis in your code:

.. code-block:: python

    from memories.utils.processors.vector_processor import VectorProcessor
    
    # Initialize processor
    processor = VectorProcessor()
    
    # Calculate density
    density = processor.calculate_density(
        gdf=vector_data,
        resolution=10.0,  # 10 meter resolution
        bbox=area_bounds,
        kernel_size=5
    )
    
    # Calculate statistics
    stats = calculate_area_statistics(
        gdf=vector_data,
        value_column='importance'
    )

Integration with Property Analysis
----------------------------------

The point pattern analysis is used in property analysis:

.. code-block:: python

    async def analyze_urban_patterns(
        self,
        bounds: Bounds,
        layers: List[str] = ['buildings', 'roads']
    ) -> Dict[str, Any]:
""""""""""""""""""""
        Analyze urban development patterns.
"""""""""""""""""""""""""""""""""""
        # Initialize vector processor if needed
        if self.vector_processor is None:
            self.vector_processor = VectorTileProcessor(bounds=bounds, layers=layers)
        
        # Get vector data
        vector_data = self.vector_processor.process_tile(bounds)
        
        # Calculate urban metrics
        building_density = len(vector_data) / (
            (bounds.east - bounds.west) * (bounds.north - bounds.south)
        )
        
        return {
            'building_density': building_density,
            'building_count': len(vector_data),
            'bounds': bounds
        }

Performance Considerations
--------------------------

1. Memory Usage
   - Vector data is processed in tiles
   - Efficient spatial indexing for large datasets

2. Computational Efficiency
   - Uses OpenCV for fast density calculations
   - Parallel processing for large areas

3. Optimization Settings
   .. code-block:: python

       PROCESSING_CONFIG = {
           'tile_size': 256,
           'overlap': 32,
           'batch_size': 8,
           'num_workers': 4,
           'use_gpu': True
       }

Future Developments
-------------------

Planned enhancements to the point pattern analysis module:
1. Implementation of advanced spatial statistics
2. Enhanced clustering algorithms
3. Integration with machine learning for pattern recognition
4. Support for temporal point pattern analysis 