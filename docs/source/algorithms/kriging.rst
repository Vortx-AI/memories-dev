=======
Kriging
=======

Introduction
------------

Kriging is a sophisticated geostatistical method used in memories-dev for optimal spatial interpolation. It provides the best linear unbiased prediction (BLUP) of intermediate values in spatial data.

Mathematical Foundation
-----------------------

The basic equation for Kriging estimation at an unsampled location $s_0$ is:

.. math::

   \hat{Z}(s_0) = \sum_{i=1}^n \lambda_i Z(s_i)

where:
   - $\hat{Z}(s_0)$ is the predicted value at location $s_0$
   - $\lambda_i$ are the Kriging weights
   - $Z(s_i)$ are the observed values at sampled locations
   
The weights $\lambda_i$ are determined by solving the Kriging system:

.. math::

   \begin{bmatrix} 
   \gamma(h_{11}) & \gamma(h_{12}) & \cdots & \gamma(h_{1n}) & 1 \\ 
   \gamma(h_{21}) & \gamma(h_{22}) & \cdots & \gamma(h_{2n}) & 1 \\ 
   \vdots & \vdots & \ddots & \vdots & \vdots \\ 
   \gamma(h_{n1}) & \gamma(h_{n2}) & \cdots & \gamma(h_{nn}) & 1 \\ 
   1 & 1 & \cdots & 1 & 0 
   \end{bmatrix} 
   \begin{bmatrix} 
   \lambda_1 \\ 
   \lambda_2 \\ 
   \vdots \\ 
   \lambda_n \\ 
   \mu 
   \end{bmatrix} = 
   \begin{bmatrix} 
   \gamma(h_{10}) \\ 
   \gamma(h_{20}) \\ 
   \vdots \\ 
   \gamma(h_{n0}) \\ 
   1 
   \end{bmatrix}

where:
   - $\gamma(h)$ is the semivariogram function
   - $h_{ij}$ is the distance between points i and j
   - $\mu$ is the Lagrange multiplier

Implementation ------------
Here's how to use Kriging in memories-dev:
.. code-block:: python
   
       from memories.spatial import Kriging
       
       # Initialize Kriging with parameters
       kriging = Kriging(
           variogram_model="exponential",
           anisotropy_scaling=1.0,
           anisotropy_angle=0.0
       )
       
       # Fit the model
       kriging.fit(
           coordinates=sample_points,  # Shape: (n_samples, n_dims)
           values=sample_values,      # Shape: (n_samples,)
           variogram_parameters={
               "sill": 1.0,
               "range": 100.0,
               "nugget": 0.1
           }
       )
       
       # Make predictions with uncertainty
       predictions, variances = kriging.predict(
           coordinates=prediction_points,  # Shape: (n_predictions, n_dims)
           return_variance=True
       )

Variogram Models
----------------

memories-dev supports several variogram models:

1. **Exponential Model**

.. math::

   \gamma(h) = c_0 + c_1\left(1 - \exp\left(-\frac{h}{a}\right)\right)

2. **Spherical Model**

.. math::

   \gamma(h) = 
   \begin{cases} 
   c_0 + c_1\left(\frac{3h}{2a} - \frac{h^3}{2a^3}\right) & \text{for } h \leq a \\ 
   c_0 + c_1 & \text{for } h > a 
   \end{cases}

3. **Gaussian Model**

.. math::

   \gamma(h) = c_0 + c_1\left(1 - \exp\left(-\frac{h^2}{a^2}\right)\right)

where:
   - $c_0$ is the nugget effect
   - $c_1$ is the sill
   - $a$ is the range
   - $h$ is the lag distance

Visualization -----------
.. mermaid::

                             A3[Variogram Parameters]
                         end
                         
                         subgraph "Kriging Process"
                             B1[Variogram Fitting]
                             B2[Weight Calculation]
                             B3[Interpolation]
                         end
                         
                         subgraph "Output"
                             C1[Predictions]
                             C2[Prediction Variance]
                             C3[Kriging Maps]
                         end
                         
                         A1 --> B1
                         A2 --> B1
                         A3 --> B1
                         B1 --> B2
                         B2 --> B3
                         B3 --> C1
                         B3 --> C2
                         C1 --> C3
                         C2 --> C3

Performance Considerations
--------------------------

1. **Computational Complexity**

The computational complexity of Kriging is:
- Variogram fitting: O(n²)
- Weight calculation: O(n³)
- Prediction: O(n) per prediction point

where n is the number of sample points.

2. **Memory Requirements**

Memory usage scales with:
- Sample points: O(n²) for the Kriging matrix
- Prediction points: O(m) where m is the number of prediction points

3. **Optimization Strategies**

memories-dev implements several optimization strategies:

.. code-block:: python

    # Use local kriging to reduce computation
    kriging.fit(
        coordinates=sample_points,
        values=sample_values,
        max_points=100  # Use only nearest 100 points
    )
    
    # Enable parallel processing
    kriging.predict(
        coordinates=prediction_points,
        n_jobs=-1  # Use all available cores
    )

Validation Methods
------------------

1. **Cross-Validation**

.. code-block:: python

    # Perform leave-one-out cross-validation
    scores = kriging.cross_validate(
        coordinates=sample_points,
        values=sample_values,
        method="loo"
    )
    
    # Calculate validation metrics
    rmse = scores["rmse"]
    mae = scores["mae"]
    r2 = scores["r2"]

2. **Validation Plots**

.. code-block:: python

    # Generate validation plots
    kriging.plot_validation(
        actual=actual_values,
        predicted=predicted_values,
        variance=prediction_variance
    )

Example Applications
--------------------

1. **Elevation Interpolation**

.. code-block:: python

    # Interpolate elevation data
    elevation_kriging = Kriging(
        variogram_model="spherical",
        coordinates_type="geographic"
    )
    
    elevation_map = elevation_kriging.fit_predict(
        coordinates=elevation_points,
        values=elevation_values,
        grid_size=(100, 100)  # Output resolution
    )

2. **Environmental Monitoring**

.. code-block:: python

    # Monitor air quality
    pollution_kriging = Kriging(
        variogram_model="gaussian",
        anisotropy_scaling=1.5  # Account for wind direction
    )
    
    pollution_map, uncertainty = pollution_kriging.fit_predict(
        coordinates=sensor_locations,
        values=pollution_levels,
        return_variance=True
    )

References
----------

1. Cressie, N. (1990). "The Origins of Kriging". *Mathematical Geology*, 22(3), 239-252.
2. Stein, M. L. (1999). *Interpolation of Spatial Data: Some Theory for Kriging*. Springer.
3. Goovaerts, P. (1997). *Geostatistics for Natural Resources Evaluation*. Oxford University Press. 