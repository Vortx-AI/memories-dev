======================
Time Series Decomposition
=========================

Overview
--------

The time series decomposition module in memories-dev provides tools for analyzing temporal patterns in Earth observation data. The implementation is based on the actual code in `memories/utils/processors/advanced_processor.py`.

Core Implementation
-------------------

The main time series analysis functionality is implemented in the `analyze_time_series` method:

.. code-block:: python

    def analyze_time_series(
        self,
        data: List[np.ndarray],
        dates: List[datetime],
        method: str = "linear"
    ) -> Dict:
""""""""""
        Analyze time series of images.
        
        Args:
            data: List of image arrays
            dates: List of corresponding dates
            method: Analysis method ("linear", "seasonal")
            
        Returns:
            Dictionary containing analysis results
""""""""""""""""""""""""""""""""""""""

Analysis Methods
----------------

1. Linear Trend Analysis
^^^^^^^^^^^^^^^^^^^^^^^^

The linear trend analysis calculates pixel-wise trends over time:

.. code-block:: python

    # Linear trend analysis
    time_index = np.arange(len(dates))
    
    # Calculate trend for each pixel
    coefficients = np.zeros((data[0].shape[0], data[0].shape[1], data[0].shape[2]))
    for band in range(data[0].shape[0]):
        for i in range(data[0].shape[1]):
            for j in range(data[0].shape[2]):
                values = da.sel(band=band)[:, i, j]
                coefficients[band, i, j] = np.polyfit(time_index, values, 1)[0]

2. Seasonal Decomposition
^^^^^^^^^^^^^^^^^^^^^^^^^

For seasonal patterns, we use the statsmodels implementation:

.. code-block:: python

    # Seasonal decomposition
    from statsmodels.tsa.seasonal import seasonal_decompose
    
    decomposition = {}
    for band in range(data[0].shape[0]):
        band_data = da.sel(band=band)
        
        # Reshape for decomposition
        values = band_data.values.reshape(-1, band_data.shape[1] * band_data.shape[2])
        
        # Decompose each pixel time series
        trend = np.zeros_like(values)
        seasonal = np.zeros_like(values)
        residual = np.zeros_like(values)
        
        for pixel in range(values.shape[1]):
            decomp = seasonal_decompose(
                values[:, pixel],
                period=12,  # Monthly data
                extrapolate_trend=True
            )
            trend[:, pixel] = decomp.trend
            seasonal[:, pixel] = decomp.seasonal
            residual[:, pixel] = decomp.resid

Data Smoothing
--------------

For noise reduction, we implement a smoothing function:

.. code-block:: python

    def smooth_timeseries(
        data: np.ndarray,
        window_size: int = 5
    ) -> np.ndarray:
""""""""""""""""
        Apply smoothing to time series data.
        
        Args:
            data: Input time series
            window_size: Smoothing window size
            
        Returns:
            Smoothed time series
""""""""""""""""""""
        kernel = np.ones(window_size) / window_size
        smoothed = ndimage.convolve1d(data, kernel, mode='reflect')
        return smoothed

Configuration
-------------

Analysis parameters are defined in `analysis_config.py`:

.. code-block:: python

    CHANGE_CONFIG = {
        'change_threshold': 0.2,
        'min_area': 1000,  # square meters
        'temporal_window': 365,  # days
        'confidence_threshold': 0.8,
        'noise_removal_kernel': 3
    }

Usage Example
-------------

Here's how to use the time series analysis in your code:

.. code-block:: python

    from memories.utils.processors.advanced_processor import AdvancedProcessor
    
    # Initialize processor
    processor = AdvancedProcessor()
    
    # Analyze time series
    results = processor.analyze_time_series(
        data=image_series,
        dates=date_list,
        method="seasonal"
    )
    
    # Access decomposition results
    trend = results["decomposition"]["band_0"]["trend"]
    seasonal = results["decomposition"]["band_0"]["seasonal"]
    residual = results["decomposition"]["band_0"]["residual"]

Integration with Earth Engine
-----------------------------

The time series analysis can be used with Earth Engine data:

.. code-block:: python

    def get_time_series(
        self,
        bbox: Union[Tuple[float, float, float, float], Polygon],
        start_date: str,
        end_date: str,
        collection: str,
        band: str,
        temporal_resolution: str = "month"
    ) -> Dict:
""""""""""
        Get time series data from Earth Engine.
"""""""""""""""""""""""""""""""""""""""
        # Implementation from memories/data_acquisition/sources/earth_engine_api.py

Performance Considerations
--------------------------

1. Memory Usage
   - For large datasets, data is processed in tiles
   - Configurable batch size in PROCESSING_CONFIG

2. Computational Efficiency
   - Parallel processing for pixel-wise operations
   - GPU acceleration where available

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

Planned enhancements to the time series analysis module:
1. Implementation of more advanced decomposition methods
2. Enhanced GPU acceleration for large-scale processing
3. Integration with additional data sources
4. Improved handling of missing data and outliers 