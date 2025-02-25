=================
Metrics Catalog
=================

Welcome to the Metrics Catalog section of the memories-dev documentation. This comprehensive catalog documents the evaluation metrics used throughout the framework to assess performance, accuracy, and efficiency.

.. note::
   The Metrics Catalog is designed for developers and researchers who need to understand how to evaluate the performance of the memories-dev framework and its components. It includes detailed explanations of each metric, its mathematical foundation, and how to interpret results.

Core Metrics
-----------

Memory System Metrics
^^^^^^^^^^^^^^^^^^

.. contents::
   :local:
   :depth: 1

Retrieval Efficiency
~~~~~~~~~~~~~~~~

**Mean Retrieval Time (MRT)**

.. math::

   \text{MRT} = \frac{1}{n} \sum_{i=1}^{n} t_i

Where:
- :math:`t_i` is the time taken to retrieve item i
- :math:`n` is the number of retrievals

Interpretation:
- Lower values indicate faster retrieval
- Target values depend on the memory tier:
  - Hot memory: < 10 ms
  - Warm memory: < 100 ms
  - Cold memory: < 1 s
  - Glacier: < 60 s

**Retrieval Success Rate (RSR)**

.. math::

   \text{RSR} = \frac{\text{successful retrievals}}{\text{total retrieval attempts}} \times 100\%

Interpretation:
- Higher values indicate more reliable memory retrieval
- Target value: > 99.9%

Memory Efficiency
~~~~~~~~~~~~~~

**Memory Tier Distribution (MTD)**

.. math::

   \text{MTD} = \left\{\frac{S_{\text{hot}}}{S_{\text{total}}}, \frac{S_{\text{warm}}}{S_{\text{total}}}, \frac{S_{\text{cold}}}{S_{\text{total}}}, \frac{S_{\text{glacier}}}{S_{\text{total}}}\right\}

Where:
- :math:`S_{\text{hot}}` is the storage used in hot tier
- :math:`S_{\text{warm}}` is the storage used in warm tier
- :math:`S_{\text{cold}}` is the storage used in cold tier
- :math:`S_{\text{glacier}}` is the storage used in glacier tier
- :math:`S_{\text{total}}` is the total storage used

Interpretation:
- Shows the distribution of data across memory tiers
- Optimal distribution depends on access patterns but is typically:
  - Hot: 5-10%
  - Warm: 15-25%
  - Cold: 30-50%
  - Glacier: 25-40%

**Compression Ratio (CR)**

.. math::

   \text{CR} = \frac{\text{original size}}{\text{compressed size}}

Interpretation:
- Higher values indicate better compression
- Target values vary by data type and memory tier:
  - Hot: 1.2-2.0
  - Warm: 2.0-5.0
  - Cold: 5.0-10.0
  - Glacier: 10.0-20.0

Analyzer Metrics
^^^^^^^^^^^^^

Terrain Analysis Accuracy
~~~~~~~~~~~~~~~~~~~~~

**Elevation Accuracy**

.. math::

   \text{RMSE}_{\text{elevation}} = \sqrt{\frac{1}{n} \sum_{i=1}^{n} (z_i - \hat{z}_i)^2}

Where:
- :math:`z_i` is the true elevation at point i
- :math:`\hat{z}_i` is the estimated elevation at point i
- :math:`n` is the number of points

Interpretation:
- Lower values indicate more accurate elevation estimates
- Target value: < 5 m for high-resolution analysis

**Slope and Aspect Accuracy**

.. math::

   \text{MAE}_{\text{slope}} = \frac{1}{n} \sum_{i=1}^{n} |s_i - \hat{s}_i|

.. math::

   \text{MAE}_{\text{aspect}} = \frac{1}{n} \sum_{i=1}^{n} \min(|a_i - \hat{a}_i|, 360 - |a_i - \hat{a}_i|)

Where:
- :math:`s_i` is the true slope at point i
- :math:`\hat{s}_i` is the estimated slope at point i
- :math:`a_i` is the true aspect at point i
- :math:`\hat{a}_i` is the estimated aspect at point i
- :math:`n` is the number of points

Interpretation:
- Lower values indicate more accurate slope and aspect estimates
- Target values:
  - Slope MAE: < 2 degrees
  - Aspect MAE: < 10 degrees

Climate Analysis Accuracy
~~~~~~~~~~~~~~~~~~~~~

**Temperature Prediction Accuracy**

.. math::

   \text{RMSE}_{\text{temperature}} = \sqrt{\frac{1}{n} \sum_{i=1}^{n} (T_i - \hat{T}_i)^2}

Where:
- :math:`T_i` is the true temperature at time i
- :math:`\hat{T}_i` is the predicted temperature at time i
- :math:`n` is the number of time points

Interpretation:
- Lower values indicate more accurate temperature predictions
- Target value: < 1°C for short-term predictions

**Precipitation Prediction Accuracy**

.. math::

   \text{RMSE}_{\text{precipitation}} = \sqrt{\frac{1}{n} \sum_{i=1}^{n} (P_i - \hat{P}_i)^2}

Where:
- :math:`P_i` is the true precipitation at time i
- :math:`\hat{P}_i` is the predicted precipitation at time i
- :math:`n` is the number of time points

Interpretation:
- Lower values indicate more accurate precipitation predictions
- Target value: < 5 mm/day for short-term predictions

Water Resource Analysis Accuracy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Water Body Detection Accuracy**

.. math::

   \text{F1}_{\text{water}} = 2 \times \frac{\text{precision} \times \text{recall}}{\text{precision} + \text{recall}}

Where:
- precision = TP / (TP + FP)
- recall = TP / (TP + FN)
- TP = true positives (correctly identified water pixels)
- FP = false positives (non-water pixels identified as water)
- FN = false negatives (water pixels not identified as water)

Interpretation:
- Higher values indicate more accurate water body detection
- Target value: > 0.9 for high-resolution imagery

AI Integration Metrics
^^^^^^^^^^^^^^^^^^^

Model Performance
~~~~~~~~~~~~~~

**Response Latency**

.. math::

   \text{Response Latency} = t_{\text{response}} - t_{\text{request}}

Where:
- :math:`t_{\text{response}}` is the time when the response is received
- :math:`t_{\text{request}}` is the time when the request is sent

Interpretation:
- Lower values indicate faster model response
- Target values depend on deployment type:
  - Synchronous: < 2 seconds
  - Asynchronous: < 10 seconds for complex analyses

**Token Efficiency**

.. math::

   \text{Token Efficiency} = \frac{\text{useful information bits}}{\text{total tokens used}}

Interpretation:
- Higher values indicate more efficient use of tokens
- Target value: > 0.7 (70% of tokens contain useful information)

Earth Memory Integration
~~~~~~~~~~~~~~~~~~~~~

**Hallucination Reduction Rate (HRR)**

.. math::

   \text{HRR} = \left(1 - \frac{\text{hallucinations with Earth memory}}{\text{hallucinations without Earth memory}}\right) \times 100\%

Interpretation:
- Higher values indicate greater reduction in hallucinations
- Target value: > 80%

**Factual Accuracy Improvement (FAI)**

.. math::

   \text{FAI} = \left(\frac{\text{factual accuracy with Earth memory}}{\text{factual accuracy without Earth memory}} - 1\right) \times 100\%

Interpretation:
- Higher values indicate greater improvement in factual accuracy
- Target value: > 50%

System-Wide Metrics
^^^^^^^^^^^^^^^^^

Performance Metrics
~~~~~~~~~~~~~~~~

**Query Throughput**

.. math::

   \text{Query Throughput} = \frac{\text{number of queries processed}}{\text{time period in seconds}}

Interpretation:
- Higher values indicate better system performance
- Target values depend on deployment type:
  - Single node: > 10 queries/second
  - Cluster: > 100 queries/second

**Query Latency Distribution**

.. math::

   \text{p95 Latency} = \text{95th percentile of query latencies}

.. math::

   \text{p99 Latency} = \text{99th percentile of query latencies}

Interpretation:
- Lower values indicate better system responsiveness
- Target values:
  - p95: < 500 ms
  - p99: < 1000 ms

Scalability Metrics
~~~~~~~~~~~~~~~~

**Throughput Scaling Factor**

.. math::

   \text{Scaling Factor} = \frac{\text{throughput with } n \text{ nodes}}{\text{throughput with 1 node}}

Interpretation:
- Higher values indicate better horizontal scalability
- Target value: > 0.8 × n (80% efficiency)

**Resource Utilization**

.. math::

   \text{CPU Utilization} = \frac{\text{CPU time used}}{\text{total CPU time available}} \times 100\%

.. math::

   \text{Memory Utilization} = \frac{\text{memory used}}{\text{total memory available}} \times 100\%

Interpretation:
- Optimal values are typically 60-80%
- Values consistently above 80% indicate potential resource constraints

Reliability Metrics
~~~~~~~~~~~~~~~~

**System Availability**

.. math::

   \text{Availability} = \frac{\text{uptime}}{\text{uptime + downtime}} \times 100\%

Interpretation:
- Higher values indicate better system availability
- Target value: > 99.9% (three nines)

**Error Rate**

.. math::

   \text{Error Rate} = \frac{\text{number of errors}}{\text{total number of requests}} \times 100\%

Interpretation:
- Lower values indicate better system reliability
- Target value: < 0.1%

Metrics Dashboards
----------------

The memories-dev framework includes built-in support for visualizing metrics through dashboards. The following dashboards are available:

System Performance Dashboard
~~~~~~~~~~~~~~~~~~~~~~~~~

.. figure:: /_static/metrics/system_performance_dashboard.png
   :alt: System Performance Dashboard
   :width: 100%
   
   System Performance Dashboard showing real-time metrics for query throughput, latency, and error rates.

Memory Efficiency Dashboard
~~~~~~~~~~~~~~~~~~~~~~~

.. figure:: /_static/metrics/memory_efficiency_dashboard.png
   :alt: Memory Efficiency Dashboard
   :width: 100%
   
   Memory Efficiency Dashboard showing memory tier distribution, compression ratios, and retrieval times.

Analyzer Accuracy Dashboard
~~~~~~~~~~~~~~~~~~~~~~~~

.. figure:: /_static/metrics/analyzer_accuracy_dashboard.png
   :alt: Analyzer Accuracy Dashboard
   :width: 100%
   
   Analyzer Accuracy Dashboard showing accuracy metrics for different Earth analyzers.

Metrics Collection
----------------

The metrics catalog includes information about how metrics are collected, stored, and analyzed.

Collection Methods
~~~~~~~~~~~~~~

Metrics in memories-dev are collected using the following methods:

1. **Instrumentation**: Code-level instrumentation using decorators and context managers to measure timing and performance.

   .. code-block:: python

      @measure_timing("memory_store.retrieve")
      def retrieve(self, key, include_metadata=False):
          # Method implementation
          pass

      with measure_timing("analyzer.terrain.analyze"):
          results = await terrain_analyzer.analyze(location)

2. **Sampling**: Periodic sampling of system state to track resource utilization.

   .. code-block:: python

      @periodic_sampler(interval_seconds=60)
      def sample_memory_usage():
          return {
              "hot_memory_usage": get_hot_memory_usage(),
              "warm_memory_usage": get_warm_memory_usage(),
              "cold_memory_usage": get_cold_memory_usage(),
              "glacier_memory_usage": get_glacier_memory_usage()
          }

3. **Logging**: Structured logging to capture errors and important events.

   .. code-block:: python

      logger.info("Query processed", 
                 extra={
                     "query_id": query_id,
                     "execution_time_ms": execution_time_ms,
                     "result_count": len(results)
                 })

Storage Backend
~~~~~~~~~~~~

Metrics are stored in a time-series database optimized for fast retrieval and aggregation. Supported backends include:

- **Prometheus**: For real-time monitoring and alerting
- **InfluxDB**: For long-term storage and complex analytics
- **Local SQLite**: For development and testing environments

Analysis Tools
~~~~~~~~~~~

The framework provides tools for analyzing collected metrics:

1. **Aggregation**: Functions for calculating statistics like mean, median, percentiles, etc.

   .. code-block:: python

      from memories.metrics.analysis import calculate_statistics

      stats = calculate_statistics(
          metric_name="memory_store.retrieve.time",
          time_range={"start": "2023-06-01", "end": "2023-06-30"},
          aggregation=["mean", "median", "p95", "p99"]
      )

2. **Visualization**: Tools for generating charts and graphs.

   .. code-block:: python

      from memories.metrics.visualization import generate_time_series_chart

      chart = generate_time_series_chart(
          metric_names=["memory_store.retrieve.time", "memory_store.store.time"],
          time_range={"start": "2023-06-01", "end": "2023-06-30"},
          interval="1h",
          chart_type="line"
      )
      chart.save("retrieval_vs_storage_time.png")

3. **Alerting**: Configurable alerts when metrics exceed thresholds.

   .. code-block:: python

      from memories.metrics.alerting import create_alert_rule

      create_alert_rule(
          metric_name="system.error_rate",
          condition="value > 0.01",  # 1% error rate
          duration="5m",  # Sustained for 5 minutes
          actions=["send_email", "send_slack_notification"],
          severity="high"
      )

Reference Metrics Documentation
-----------------------------

.. toctree::
   :maxdepth: 2
   
   memory_metrics
   analyzer_metrics
   ai_integration_metrics
   system_metrics
   custom_metrics 