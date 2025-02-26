======================
Time Series Decomposition
=========================

Overview
--------

The time series decomposition module in memories-dev provides tools for analyzing temporal patterns in Earth observation data. Time series decomposition is essential for understanding underlying trends, seasonal patterns, and anomalies in environmental data. The implementation is based on the actual code in `memories/utils/processors/advanced_processor.py`.

Mathematical Foundation
----------------------

Time series decomposition is based on the principle that a time series $Y(t)$ can be broken down into several components:

$Y(t) = T(t) + S(t) + R(t)$

Where:
- $T(t)$ represents the trend component
- $S(t)$ represents the seasonal component
- $R(t)$ represents the residual (or irregular) component

This additive model is appropriate when the magnitude of seasonal fluctuations does not vary with the level of the time series. For cases where the seasonal pattern varies with the level of the series, a multiplicative model may be more appropriate:

$Y(t) = T(t) \times S(t) \times R(t)$

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
        """
        Analyze time series of images.
        
        Args:
            data: List of image arrays
            dates: List of corresponding dates
            method: Analysis method ("linear", "seasonal")
            
        Returns:
            Dictionary containing analysis results
        """

Analysis Methods
----------------

1. Linear Trend Analysis
^^^^^^^^^^^^^^^^^^^^^^^^

The linear trend analysis calculates pixel-wise trends over time. For each pixel at position $(i,j)$ and band $b$, we fit a linear model:

$Y_{b,i,j}(t) = \alpha_{b,i,j} + \beta_{b,i,j} \cdot t + \epsilon_{b,i,j}(t)$

Where:
- $Y_{b,i,j}(t)$ is the value at time $t$
- $\alpha_{b,i,j}$ is the intercept
- $\beta_{b,i,j}$ is the slope (trend coefficient)
- $\epsilon_{b,i,j}(t)$ is the error term

The implementation calculates these coefficients using least squares fitting:

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

For seasonal patterns, we use the statsmodels implementation of the classical seasonal decomposition method. This algorithm follows these steps:

1. Estimate the trend component $T(t)$ using a moving average
2. De-trend the series by removing the trend: $Y(t) - T(t)$
3. Estimate the seasonal component $S(t)$ by averaging the de-trended values for each time unit across periods
4. Calculate the residual: $R(t) = Y(t) - T(t) - S(t)$

The moving average window for trend estimation is typically the period length. For a series with period $p$, the centered moving average at time $t$ is:

$T(t) = \frac{1}{p} \sum_{i=-\lfloor p/2 \rfloor}^{\lfloor p/2 \rfloor} Y(t+i)$

The implementation:

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

For noise reduction, we implement a smoothing function based on a weighted moving average. For a time series point $Y(t)$, the smoothed value $\hat{Y}(t)$ is:

$\hat{Y}(t) = \frac{\sum_{i=-w}^{w} K(i) \cdot Y(t+i)}{\sum_{i=-w}^{w} K(i)}$

Where:
- $w$ is the window size parameter (half-width)
- $K(i)$ is the kernel function that assigns weights to points

A common kernel is the Gaussian kernel:

$K(i) = e^{-\frac{i^2}{2\sigma^2}}$

Where $\sigma$ controls the width of the kernel.

.. code-block:: python

    def smooth_timeseries(
        data: np.ndarray,
        window_size: int = 5,
        kernel: str = "gaussian"
    ) -> np.ndarray:
        """
        Apply smoothing to time series data.
        
        Args:
            data: Time series data array
            window_size: Size of smoothing window
            kernel: Type of kernel ("gaussian", "uniform")
            
        Returns:
            Smoothed data array
        """

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
        """
        Get time series data from Earth Engine.
        """
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