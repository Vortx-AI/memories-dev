======================
Tiered Memory
======================


Introduction to Tiered Memory
----------------------------

The Earth Memory framework implements a tiered memory architecture inspired by both human memory systems and modern computing storage hierarchies. This approach optimizes the balance between data accessibility, processing efficiency, and long-term preservation of Earth observations.

Memory Tier Overview
------------------

The framework defines four primary memory tiers, each with distinct characteristics and purposes:

.. code-block:: text

    ┌─────────────────────────────────────────────────────────────┐
    │                    Earth Memory Tiers                        │
    └─────────────────────────────────────────────────────────────┘
                               │
               ┌───────────────┼───────────────┐
               │               │               │
    ┌──────────▼───────┐ ┌────▼─────┐ ┌───────▼────────┐
    │   Hot Memory     │ │   Warm   │ │  Cold Memory   │
    │ (Real-time state)│ │  Memory  │ │(Historical data)│
    └──────────────────┘ └────┬─────┘ └───────┬────────┘
                              │               │
                         ┌────▼─────────────┐ │
                         │ Glacier Memory   │◄┘
                         │ (Deep archive)   │
                         └──────────────────┘

Hot Memory Tier
--------------

The Hot Memory tier stores current, high-resolution data for immediate access and real-time processing.

**Key characteristics:**

* **Purpose**: Real-time Earth state representation and active processing
* **Access pattern**: Random access, high throughput, low latency
* **Temporal scope**: Current to very recent (hours to days)
* **Resolution**: Highest available, full fidelity
* **Update frequency**: Continuous or near real-time
* **Typical size**: Smaller (gigabytes to terabytes)
* **Implementation**: In-memory databases, high-performance storage

Example usage:

.. code-block:: python

   from memories.earth import MemoryCodex, HotMemory
   
   # Initialize the Memory Codex
   codex = MemoryCodex()
   
   # Create a Hot Memory instance for current weather data
   current_weather = HotMemory(
       name="global-weather-current",
       resolution="0.1deg",
       update_frequency="hourly",
       variables=["temperature", "precipitation", "wind", "pressure"],
       caching_strategy="aggressive"
   )
   
   # Add to the codex
   codex.add_memory(current_weather)
   
   # Retrieve real-time data
   temperature_now = current_weather.get_variable(
       "temperature",
       region=(40.7, -74.0, 41.0, -73.7),  # NYC area bounding box
       timestamp="latest"
   )
   
   # Process the data
   anomaly = temperature_now - current_weather.get_variable(
       "temperature",
       region=(40.7, -74.0, 41.0, -73.7),
       timestamp="24h_ago"
   )
   
   print(f"Temperature change in the last 24 hours: {anomaly.mean():.2f}°C")

Hot Memory provides AI systems with immediate access to the current state of Earth systems for real-time analysis and response.

Warm Memory Tier
---------------

The Warm Memory tier stores medium-term, intermediate-resolution data for efficient analysis of patterns and trends.

**Key characteristics:**

* **Purpose**: Seasonal and annual patterns, medium-term analysis
* **Access pattern**: Mixed random/sequential, moderate throughput
* **Temporal scope**: Recent past (days to months to a few years)
* **Resolution**: Medium to high, potentially aggregated
* **Update frequency**: Daily to weekly
* **Typical size**: Medium to large (terabytes)
* **Implementation**: SSD storage, columnar databases, optimized formats

Example usage:

.. code-block:: python

   from memories.earth import WarmMemory
   
   # Create a Warm Memory instance for seasonal vegetation data
   vegetation_memory = WarmMemory(
       name="global-vegetation-seasonal",
       resolution="30m",
       temporal_aggregation="10-day",
       variables=["ndvi", "evi", "lai"],
       retention_period="2-years"
   )
   
   # Add to the codex
   codex.add_memory(vegetation_memory)
   
   # Analyze seasonal patterns
   seasonal_ndvi = vegetation_memory.get_time_series(
       variable="ndvi",
       region="amazon-basin",
       time_range=("2022-01-01", "2023-12-31"),
       aggregation="spatial_mean"
   )
   
   # Detect anomalies
   anomalies = vegetation_memory.detect_anomalies(
       variable="ndvi",
       region="amazon-basin",
       baseline_period=("2018-01-01", "2021-12-31"),
       current_period=("2022-01-01", "2023-12-31"),
       method="z-score",
       threshold=2.0
   )
   
   print(f"Detected {len(anomalies)} significant vegetation anomalies")

Warm Memory enables medium-term trend analysis and pattern recognition across seasons and years.

Cold Memory Tier
--------------

The Cold Memory tier stores long-term, lower-resolution historical data for analyzing long-term trends and changes.

**Key characteristics:**

* **Purpose**: Historical records, long-term trends, baseline data
* **Access pattern**: Primarily sequential, batch processing
* **Temporal scope**: Longer past (years to decades)
* **Resolution**: Lower, often aggregated or summarized
* **Update frequency**: Monthly to yearly
* **Typical size**: Large (tens to hundreds of terabytes)
* **Implementation**: Object storage, archive formats, compression

Example usage:

.. code-block:: python

   from memories.earth import ColdMemory
   
   # Create a Cold Memory instance for climate data
   climate_memory = ColdMemory(
       name="global-climate-historical",
       resolution="0.5deg",
       temporal_aggregation="monthly",
       variables=["temperature", "precipitation"],
       time_range=("1950-01-01", "2020-12-31"),
       compression_level="high"
   )
   
   # Add to the codex
   codex.add_memory(climate_memory)
   
   # Analyze long-term climate trends
   temperature_trend = climate_memory.analyze_trend(
       variable="temperature",
       region="global",
       time_range=("1950-01-01", "2020-12-31"),
       method="linear_regression",
       temporal_aggregation="annual"
   )
   
   print(f"Global temperature trend: {temperature_trend.slope * 10:.2f}°C per decade")
   print(f"Statistical significance: p={temperature_trend.p_value:.5f}")

Cold Memory provides essential historical context for understanding long-term Earth system changes and establishing baselines.

Glacier Memory Tier
-----------------

The Glacier Memory tier preserves rare, extremely valuable, or very old data for permanent archival and occasional reference.

**Key characteristics:**

* **Purpose**: Permanent archive, rare but valuable data
* **Access pattern**: Infrequent, retrieval-focused
* **Temporal scope**: Distant past (decades to centuries)
* **Resolution**: Variable, often preserving original fidelity
* **Update frequency**: Rarely or never
* **Typical size**: Potentially very large (petabytes)
* **Implementation**: Archive storage, deep preservation formats

Example usage:

.. code-block:: python

   from memories.earth import GlacierMemory
   
   # Create a Glacier Memory instance for paleoclimate records
   paleo_memory = GlacierMemory(
       name="global-paleoclimate-records",
       data_types=["ice-cores", "sediment-cores", "tree-rings"],
       time_range=("10000 BCE", "1900 CE"),
       preservation_level="maximum",
       metadata_richness="comprehensive"
   )
   
   # Add to the codex
   codex.add_memory(paleo_memory)
   
   # Retrieve ancient climate data (this operation may take time)
   holocene_optimum = paleo_memory.retrieve_data(
       proxy_type="ice-cores",
       region="greenland",
       time_range=("8000 BCE", "6000 BCE"),
       variables=["isotope_ratios", "dust", "greenhouse_gases"]
   )
   
   # Compare with recent climate
   modern_comparison = paleo_memory.compare_with_memory(
       source_memory=holocene_optimum,
       target_memory=climate_memory,
       target_period=("1950-01-01", "2000-12-31"),
       comparison_method="normalized_difference"
   )

Glacier Memory preserves Earth's deepest histories, providing access to rare but invaluable datasets that reveal Earth's past states.

Memory Flow Between Tiers
------------------------

Data naturally flows between memory tiers based on access patterns, age, and importance:

.. code-block:: text

            ┌──────────────┐
            │  Hot Memory  │
            └──────┬───────┘
                   │
                   │ Age-out, Aggregation
                   ▼
            ┌──────────────┐
            │ Warm Memory  │
            └──────┬───────┘
                   │
                   │ Archive, Compression
                   ▼
            ┌──────────────┐
            │ Cold Memory  │
            └──────┬───────┘
                   │
                   │ Distillation, Preservation
                   ▼
            ┌──────────────┐
            │Glacier Memory│
            └──────────────┘

Data Movement Policies
--------------------

The Memory Codex manages data movement between tiers using configurable policies:

.. code-block:: python

   from memories.earth import TierTransitionPolicy
   
   # Configure automatic transitions between tiers
   codex.set_transition_policy(
       TierTransitionPolicy(
           # Hot to Warm transition
           hot_to_warm={
               "age_threshold": "30 days",
               "access_frequency_threshold": "less than once per day",
               "aggregation_method": "temporal_mean",
               "aggregation_period": "daily",
               "retain_extremes": True
           },
           
           # Warm to Cold transition
           warm_to_cold={
               "age_threshold": "2 years",
               "access_frequency_threshold": "less than once per month",
               "compression_level": "high",
               "summarization_method": "statistical_moments",
               "retain_original_resolution": False
           },
           
           # Cold to Glacier transition
           cold_to_glacier={
               "age_threshold": "10 years",
               "scientific_value_threshold": "high",
               "preservation_priority": "metadata_enrichment",
               "access_pattern": "research_only"
           }
       )
   )

Automatic Data Aging
------------------

The system can automatically migrate data based on configured policies:

.. code-block:: python

   # Configure automatic data aging
   codex.configure_data_aging(
       enabled=True,
       schedule="daily at 02:00 UTC",
       dry_run_first=True,
       notification_email="data-admin@example.org",
       exceptions=[
           # Critical data that should never be moved from hot tier
           {"memory_name": "global-weather-current", "fixed_tier": "hot"},
           # Data that should move directly from hot to cold
           {"memory_name": "rare-event-captures", "skip_tiers": ["warm"]}
       ]
   )
   
   # Manually trigger aging process
   aging_job = codex.trigger_data_aging()
   
   # Check status of aging job
   status = codex.get_job_status(aging_job.id)
   print(f"Aging job status: {status.state}")
   print(f"Bytes moved: {status.bytes_processed / (1024**3):.2f} GB")

Memory Tier Selection
-------------------

When working with the Memory Codex, you can specify which tier to query or let the system automatically select the appropriate tier:

.. code-block:: python

   # Query specific tier
   hot_data = codex.query(
       variable="temperature",
       region="europe",
       time="latest",
       tier="hot"
   )
   
   # Let system determine appropriate tier based on query
   historical_data = codex.query(
       variable="temperature",
       region="europe",
       time_range=("1980-01-01", "2020-12-31"),
       temporal_resolution="monthly"
       # No tier specified - system will choose cold tier
   )
   
   # Query across tiers with automatic resolution
   complete_record = codex.query(
       variable="temperature",
       region="europe",
       time_range=("1900-01-01", "now"),
       cross_tier=True,
       harmonize_resolution=True
   )

Tier-Specific Processing
-----------------------

Different processing strategies apply to different memory tiers:

.. code-block:: python

   # Hot Memory: Real-time processing
   hot_memory = codex.get_memory("global-weather-current")
   hot_memory.set_processing_strategy(
       streaming=True,
       update_frequency="5min",
       alert_on_threshold=True,
       threshold_values={"temperature": 35.0}  # Alert on extreme heat
   )
   
   # Warm Memory: Batch analysis
   warm_memory = codex.get_memory("global-vegetation-seasonal")
   warm_memory.set_processing_strategy(
       batch_window="overnight",
       compute_derived_indices=True,
       derived_indices=["vci", "tci", "vhi"],  # Vegetation health indices
       persist_derivatives=True
   )
   
   # Cold Memory: Distributed computing
   cold_memory = codex.get_memory("global-climate-historical")
   cold_memory.set_processing_strategy(
       distributed=True,
       cluster_config="dask-cluster-large",
       chunk_size="1-year",
       optimize_for="throughput"
   )

Implementing Custom Tiering Strategies
------------------------------------

You can create custom tiering strategies for specific use cases:

.. code-block:: python

   from memories.earth import CustomTieringStrategy
   
   # Define a custom tiering strategy for disaster response
   disaster_strategy = CustomTieringStrategy(
       name="disaster-response",
       
       # Define tier selection logic
       tier_selection=lambda query: (
           "hot" if query.time_range.end > (now - timedelta(days=7)) 
           else "warm" if query.time_range.end > (now - timedelta(days=90))
           else "cold"
       ),
       
       # Define special data movement patterns
       tier_transitions={
           "disaster_declaration": {
               "trigger": "external_event",
               "action": "promote_to_hot",
               "region_selection": "disaster_zone_plus_buffer",
               "buffer_distance": "100km",
               "duration": "disaster_duration + 30 days"
           }
       },
       
       # Define special access patterns
       access_patterns={
           "emergency_responders": {
               "tier_access": ["hot", "warm", "cold"],
               "priority": "highest",
               "prefetching": True
           }
       }
   )
   
   # Register the custom strategy
   codex.register_tiering_strategy(disaster_strategy)
   
   # Activate the strategy during an event
   codex.activate_tiering_strategy(
       strategy_name="disaster-response",
       parameters={
           "disaster_type": "hurricane",
           "disaster_zone": hurricane_path_geojson,
           "expected_duration": "7 days"
       }
   )

Performance Considerations
------------------------

Different memory tiers offer different performance characteristics:

.. list-table::
   :header-rows: 1
   :widths: 20 20 20 20 20
   
   * - Performance Metric
     - Hot Memory
     - Warm Memory
     - Cold Memory
     - Glacier Memory
   * - **Read Latency**
     - Milliseconds
     - Milliseconds to seconds
     - Seconds to minutes
     - Minutes to hours
   * - **Write Throughput**
     - Very high
     - High
     - Moderate
     - Low
   * - **Query Complexity**
     - Complex, real-time
     - Moderate to complex
     - Simple to moderate
     - Simple, retrieval-focused
   * - **Concurrent Access**
     - Very high
     - High
     - Moderate
     - Low
   * - **Cost per GB**
     - Highest
     - Moderate
     - Low
     - Lowest

Storage Requirements
------------------

Memory tiers have different storage requirements based on their purpose:

.. code-block:: python

   from memories.earth.storage import StorageRequirements
   
   # Define storage requirements for different tiers
   storage_requirements = {
       "hot": StorageRequirements(
           latency_max="50ms",
           throughput_min="1GB/s",
           availability="99.99%",
           durability="99.99%",
           backup_frequency="daily",
           replication="synchronous",
           encryption="at-rest and in-transit"
       ),
       "warm": StorageRequirements(
           latency_max="500ms",
           throughput_min="200MB/s",
           availability="99.9%",
           durability="99.999%",
           backup_frequency="weekly",
           replication="asynchronous",
           encryption="at-rest"
       ),
       "cold": StorageRequirements(
           latency_max="30s",
           throughput_min="50MB/s",
           availability="99%",
           durability="99.9999%",
           backup_frequency="monthly",
           replication="geo-redundant",
           encryption="at-rest"
       ),
       "glacier": StorageRequirements(
           latency_max="hours",
           throughput_min="10MB/s",
           availability="90%",
           durability="99.99999%",
           backup_frequency="yearly",
           replication="multi-region",
           encryption="at-rest with key rotation"
       )
   }
   
   # Check if current storage meets requirements
   storage_compliance = codex.check_storage_compliance(storage_requirements)
   for tier, compliance in storage_compliance.items():
       print(f"Tier: {tier}, Compliant: {compliance.is_compliant}")
       if not compliance.is_compliant:
           print(f"  Issues: {compliance.issues}")

Monitoring and Optimization
-------------------------

The Memory Codex provides tools for monitoring and optimizing tiered memory performance:

.. code-block:: python

   # Get tier usage statistics
   tier_stats = codex.get_tier_statistics()
   for tier, stats in tier_stats.items():
       print(f"Tier: {tier}")
       print(f"  Storage used: {stats.storage_used / (1024**3):.2f} GB")
       print(f"  Memory count: {stats.memory_count}")
       print(f"  Access frequency: {stats.access_per_day} queries/day")
       print(f"  Average latency: {stats.average_latency_ms} ms")
   
   # Identify optimization opportunities
   optimizations = codex.identify_tier_optimizations()
   for opt in optimizations:
       print(f"Recommended: {opt.description}")
       print(f"  Expected impact: {opt.impact}")
       print(f"  Effort: {opt.effort}")
   
   # Apply specific optimization
   codex.apply_optimization(
       optimization_id="hot-tier-cache-tuning",
       parameters={"cache_size": "20GB", "eviction_policy": "LFU"}
   )

Next Steps
---------

After learning about tiered memory architecture:

- Configure storage backends for each tier in :doc:`storage`
- Explore data processing patterns across tiers in :doc:`../integration/data_processing`
- Learn about memory types that work with this architecture in :doc:`../memory_types/index`

Overview
--------

The memories-dev framework implements a tiered memory architecture that optimizes data storage and access based on frequency of use, importance, and performance requirements.

Memory Hierarchy
--------------

.. mermaid::

    flowchart TD
        A[Memory Manager] --> B[Hot Memory]
        A --> C[Warm Memory]
        A --> D[Cold Memory]
        A --> E[Glacier Memory]
        
        B --> F[In-Memory Cache]
        C --> G[SSD Storage]
        D --> H[HDD Storage]
        E --> I[Cloud Archive]

        style A fill:#4B5563,color:white
        style B fill:#EF4444,color:white
        style C fill:#F59E0B,color:white
        style D fill:#10B981,color:white
        style E fill:#3B82F6,color:white

Hot Memory
---------

Characteristics:
- Highest performance tier
- In-memory storage
- Limited capacity
- Most frequently accessed data
- Automatic eviction based on LRU

Implementation:

.. code-block:: python

    from memories.storage import HotMemoryManager
    
    # Configure hot memory
    hot_memory = HotMemoryManager(
        capacity="32GB",
        eviction_policy="lru",
        compression=True
    )
    
    # Store frequently accessed data
    await hot_memory.store(
        key="recent_analysis",
        data=analysis_results,
        priority="high"
    )

Warm Memory
----------

Characteristics:
- Medium performance tier
- SSD-based storage
- Moderate capacity
- Recently accessed data
- Balanced cost-performance ratio

Implementation:

.. code-block:: python

    from memories.storage import WarmMemoryManager
    
    # Configure warm memory
    warm_memory = WarmMemoryManager(
        path="/data/warm",
        capacity="1TB",
        cleanup_interval="1d"
    )
    
    # Move data to warm storage
    await warm_memory.store(
        key="monthly_summary",
        data=summary_data,
        retention="30d"
    )

Cold Memory
----------

Characteristics:
- Lower performance tier
- HDD-based storage
- Large capacity
- Infrequently accessed data
- Cost-effective long-term storage

Implementation:

.. code-block:: python

    from memories.storage import ColdMemoryManager
    
    # Configure cold memory
    cold_memory = ColdMemoryManager(
        path="/data/cold",
        capacity="10TB",
        compression_level="high"
    )
    
    # Archive older data
    await cold_memory.store(
        key="historical_data_2023",
        data=historical_data,
        compress=True
    )

Glacier Memory
------------

Characteristics:
- Lowest performance tier
- Cloud-based archival storage
- Unlimited capacity
- Rarely accessed data
- Lowest storage cost

Implementation:

.. code-block:: python

    from memories.storage import GlacierMemoryManager
    
    # Configure glacier memory
    glacier_memory = GlacierMemoryManager(
        provider="aws",
        bucket="earth-memories-archive",
        region="us-west-2"
    )
    
    # Archive data for long-term storage
    await glacier_memory.store(
        key="historical_archive_2020",
        data=archive_data,
        retention="7y"
    )

Memory Movement
-------------

Data automatically moves between tiers based on access patterns:

.. code-block:: python

    from memories.storage import MemoryManager
    
    # Initialize memory manager
    manager = MemoryManager(
        hot_memory=hot_memory,
        warm_memory=warm_memory,
        cold_memory=cold_memory,
        glacier_memory=glacier_memory
    )
    
    # Data automatically moves between tiers
    data = await manager.get("analysis_2023")  # Promotes to hot if frequently accessed
    
    # Manually move data between tiers
    await manager.promote("monthly_data", to_tier="warm")
    await manager.demote("old_data", to_tier="cold")

Monitoring and Metrics
--------------------

Track memory tier performance and usage:

.. code-block:: python

    # Get memory metrics
    metrics = manager.get_metrics()
    
    print(f"Hot memory usage: {metrics['hot']['usage_percent']}%")
    print(f"Warm memory usage: {metrics['warm']['usage_percent']}%")
    print(f"Cold memory usage: {metrics['cold']['usage_percent']}%")
    print(f"Glacier memory usage: {metrics['glacier']['usage_percent']}%")
    
    # Get access patterns
    patterns = manager.get_access_patterns(
        timeframe="7d",
        granularity="1h"
    )

Best Practices
------------

1. **Data Classification**
   - Classify data based on access patterns
   - Consider data importance and retention requirements
   - Define clear promotion/demotion policies

2. **Capacity Planning**
   - Monitor tier utilization
   - Set appropriate tier capacities
   - Plan for data growth

3. **Performance Optimization**
   - Use appropriate compression levels
   - Configure eviction policies
   - Optimize access patterns

4. **Cost Management**
   - Balance performance and cost
   - Monitor storage costs
   - Implement lifecycle policies

See Also
--------

* :doc:`/memory_architecture/memory_system`
* :doc:`/memory_architecture/retention`
* :doc:`/deployment/scaling` 