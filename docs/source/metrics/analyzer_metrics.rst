===================
Analyzer Metrics
===================

This section documents the metrics used to evaluate analyzer performance.

Terrain Analysis
---------------

Elevation Accuracy
~~~~~~~~~~~~~~~~

.. math::

   RMSE_{elevation} = \sqrt{\frac{1}{n} \sum_{i=1}^{n} (z_i - \hat{z}_i)^2}

Where:
- :math:`z_i` is the true elevation at point i
- :math:`\hat{z}_i` is the estimated elevation at point i
- :math:`n` is the number of points

Target value: < 5 m for high-resolution analysis

Slope and Aspect Accuracy
~~~~~~~~~~~~~~~~~~~~~~~~

.. math::

   MAE_{slope} = \frac{1}{n} \sum_{i=1}^{n} |s_i - \hat{s}_i|

.. math::

   MAE_{aspect} = \frac{1}{n} \sum_{i=1}^{n} \min(|a_i - \hat{a}_i|, 360 - |a_i - \hat{a}_i|)

Where:
- :math:`s_i` is the true slope at point i
- :math:`\hat{s}_i` is the estimated slope at point i
- :math:`a_i` is the true aspect at point i
- :math:`\hat{a}_i` is the estimated aspect at point i

Target values:
- Slope MAE: < 2 degrees
- Aspect MAE: < 10 degrees

Climate Analysis
--------------

Temperature Prediction
~~~~~~~~~~~~~~~~~~~~

.. math::

   RMSE_{temperature} = \sqrt{\frac{1}{n} \sum_{i=1}^{n} (T_i - \hat{T}_i)^2}

Where:
- :math:`T_i` is the true temperature at time i
- :math:`\hat{T}_i` is the predicted temperature at time i

Target value: < 1°C for short-term predictions

Precipitation Prediction
~~~~~~~~~~~~~~~~~~~~~~

.. math::

   RMSE_{precipitation} = \sqrt{\frac{1}{n} \sum_{i=1}^{n} (P_i - \hat{P}_i)^2}

Where:
- :math:`P_i` is the true precipitation at time i
- :math:`\hat{P}_i` is the predicted precipitation at time i

Target value: < 5 mm/day for short-term predictions

Water Resource Analysis
---------------------

Water Body Detection
~~~~~~~~~~~~~~~~~~

.. math::

   F1_{water} = 2 \times \frac{precision \times recall}{precision + recall}

Where:
- precision = TP / (TP + FP)
- recall = TP / (TP + FN)
- TP = true positives (correctly identified water pixels)
- FP = false positives (non-water pixels identified as water)
- FN = false negatives (water pixels not identified as water)

Target value: > 0.9 for high-resolution imagery 