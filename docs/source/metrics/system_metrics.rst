=================
System Metrics
=================

This section documents the metrics used to evaluate overall system performance.

Performance Metrics
------------------

Query Throughput
~~~~~~~~~~~~~~~

.. math::

   \text{Query Throughput} = \frac{\text{number of queries processed}}{\text{time period in seconds}}

Target values:
- Single node: > 10 queries/second
- Cluster: > 100 queries/second

Query Latency Distribution
~~~~~~~~~~~~~~~~~~~~~~~~

.. math::

   \text{p95 Latency} = \text{95th percentile of query latencies}

.. math::

   \text{p99 Latency} = \text{99th percentile of query latencies}

Target values:
- p95: < 500 ms
- p99: < 1000 ms

Scalability Metrics
------------------

Throughput Scaling Factor
~~~~~~~~~~~~~~~~~~~~~~~~

.. math::

   \text{Scaling Factor} = \frac{\text{throughput with } n \text{ nodes}}{\text{throughput with 1 node}}

Target value: > 0.8 × n (80% efficiency)

Resource Utilization
~~~~~~~~~~~~~~~~~~

.. math::

   \text{CPU Utilization} = \frac{\text{CPU time used}}{\text{total CPU time available}} \times 100\%

.. math::

   \text{Memory Utilization} = \frac{\text{memory used}}{\text{total memory available}} \times 100\%

Target values:
- CPU: 60-80%
- Memory: 60-80%

Reliability Metrics
------------------

System Availability
~~~~~~~~~~~~~~~~~

.. math::

   \text{Availability} = \frac{\text{uptime}}{\text{uptime + downtime}} \times 100\%

Target value: > 99.9% (three nines)

Error Rate
~~~~~~~~~~

.. math::

   \text{Error Rate} = \frac{\text{number of errors}}{\text{total number of requests}} \times 100\%

Target value: < 0.1% 