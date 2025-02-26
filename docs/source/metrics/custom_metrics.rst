=================
Custom Metrics
=================

This section explains how to define and implement custom metrics for the memories-dev framework.

Creating Custom Metrics
--------------------

Basic Structure
~~~~~~~~~~~~~~

Custom metrics should implement the following interface:

.. code-block:: python

   from abc import ABC, abstractmethod
   from typing import Any, Dict

   class CustomMetric(ABC):
       @abstractmethod
       def calculate(self, data: Any) -> float:
           """Calculate the metric value."""
           pass

       @abstractmethod
       def get_target_value(self) -> Dict[str, float]:
           """Return target/threshold values."""
           pass

Example Implementation
~~~~~~~~~~~~~~~~~~~~

Here's an example of a custom metric:

.. code-block:: python

   class DataFreshnessMetric(CustomMetric):
       def __init__(self, max_age_days: float = 30):
           self.max_age_days = max_age_days

       def calculate(self, data_timestamp: float) -> float:
           current_time = time.time()
           age_days = (current_time - data_timestamp) / (24 * 3600)
           freshness = max(0, 1 - (age_days / self.max_age_days))
           return freshness

       def get_target_value(self) -> Dict[str, float]:
           return {
               "min_acceptable": 0.7,
               "target": 0.9
           }

Registration and Usage
-------------------

Registering Custom Metrics
~~~~~~~~~~~~~~~~~~~~~~~~

Register custom metrics using the metrics registry:

.. code-block:: python

   from memories.metrics import register_metric

   # Register the custom metric
   register_metric(
       name="data_freshness",
       metric_class=DataFreshnessMetric,
       description="Measures data freshness based on age"
   )

Using Custom Metrics
~~~~~~~~~~~~~~~~~~

Use custom metrics in your code:

.. code-block:: python

   from memories.metrics import get_metric

   # Get the metric instance
   freshness_metric = get_metric("data_freshness")

   # Calculate the metric
   freshness_value = freshness_metric.calculate(data_timestamp)

   # Check against target values
   targets = freshness_metric.get_target_value()
   if freshness_value < targets["min_acceptable"]:
       logger.warning("Data freshness below acceptable threshold")

Best Practices
-------------

When creating custom metrics:

1. **Documentation**: Provide clear documentation for:
   - What the metric measures
   - How it's calculated
   - Target/threshold values
   - Use cases

2. **Validation**: Include input validation:
   - Check data types
   - Validate value ranges
   - Handle edge cases

3. **Performance**: Ensure efficient calculation:
   - Optimize algorithms
   - Cache results when appropriate
   - Use vectorized operations for large datasets

4. **Testing**: Create comprehensive tests:
   - Unit tests for calculation logic
   - Integration tests with the metrics system
   - Edge case testing 