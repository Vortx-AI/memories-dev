=================
Memory Metrics
=================

This section documents the metrics used to evaluate memory system performance.

Retrieval Metrics
----------------

Mean Retrieval Time (MRT)
~~~~~~~~~~~~~~~~~~~~~~~~~

.. math::

   MRT = \frac{1}{n} \sum_{i=1}^{n} t_i

Where:
- :math:`t_i` is the time taken to retrieve item i
- :math:`n` is the number of retrievals

Target values:
- Hot memory: < 10 ms
- Warm memory: < 100 ms
- Cold memory: < 1 s
- Glacier: < 60 s

Retrieval Success Rate (RSR)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. math::

   RSR = \frac{\text{successful retrievals}}{\text{total retrieval attempts}} \times 100\%

Target value: > 99.9%

Storage Metrics
--------------

Memory Tier Distribution (MTD)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. math::

   MTD = \left\{\frac{S_{hot}}{S_{total}}, \frac{S_{warm}}{S_{total}}, \frac{S_{cold}}{S_{total}}, \frac{S_{glacier}}{S_{total}}\right\}

Where:
- :math:`S_{hot}` is storage used in hot tier
- :math:`S_{warm}` is storage used in warm tier
- :math:`S_{cold}` is storage used in cold tier
- :math:`S_{glacier}` is storage used in glacier tier
- :math:`S_{total}` is total storage used

Optimal distribution:
- Hot: 5-10%
- Warm: 15-25%
- Cold: 30-50%
- Glacier: 25-40%

Compression Ratio (CR)
~~~~~~~~~~~~~~~~~~~~~

.. math::

   CR = \frac{\text{original size}}{\text{compressed size}}

Target values by tier:
- Hot: 1.2-2.0
- Warm: 2.0-5.0
- Cold: 5.0-10.0
- Glacier: 10.0-20.0 