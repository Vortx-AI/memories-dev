======================
Memory Storage
======================


Introduction to Memory Storage
--------------------------

Earth Memory requires specialized storage solutions to efficiently manage vast quantities of geospatial and temporal data. This guide covers the storage architecture, available backends, and configuration options for different memory tiers.

Memory Storage Architecture
-----------------------

The Memory Codex uses a tiered storage architecture that balances performance, cost, and capacity:

.. code-block:: text

    ┌───────────────────────────────────────────────────────────┐
    │                  Memory Storage Architecture               │
    └───────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
    ┌───────────────────────┐       ┌───────────────────────┐
    │    Storage Tiers      │       │  Specialized Formats  │
    ├───────────────────────┤       ├───────────────────────┤
    │ ┌─────────────────┐   │       │ ┌─────────────────┐   │
    │ │   Hot Memory    │   │       │ │ Vector Storage  │   │
    │ └─────────────────┘   │       │ └─────────────────┘   │
    │ ┌─────────────────┐   │       │ ┌─────────────────┐   │
    │ │   Warm Memory   │   │       │ │ Raster Storage  │   │
    │ └─────────────────┘   │       │ └─────────────────┘   │
    │ ┌─────────────────┐   │       │ ┌─────────────────┐   │
    │ │   Cold Memory   │   │       │ │ Tensor Storage  │   │
    │ └─────────────────┘   │       │ └─────────────────┘   │
    │ ┌─────────────────┐   │       │ ┌─────────────────┐   │
    │ │ Glacier Memory  │   │       │ │   Time Series   │   │
    │ └─────────────────┘   │       │ └─────────────────┘   │
    └───────────────────────┘       └───────────────────────┘
                │                               │
                └───────────────┬───────────────┘
                                ▼
    ┌───────────────────────────────────────────────────────────┐
    │                    Storage Backends                        │
    ├───────────────────────────────────────────────────────────┤
    │ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────┐   │
    │ │  File Storage   │ │ Object Storage  │ │  Databases  │   │
    │ └─────────────────┘ └─────────────────┘ └─────────────┘   │
    └───────────────────────────────────────────────────────────┘

Storage Tier Configuration
-----------------------

Each memory tier can be configured with appropriate storage backends to optimize performance and cost trade-offs.

Hot Memory Storage
~~~~~~~~~~~~~~

Hot Memory stores actively used, high-resolution data for immediate access:

.. code-block:: python

   from memories.earth import StorageConfig
   from memories.earth.storage import LocalFileStorage, PostgreSQLStorage
   
   # Configure hot memory storage
   hot_storage_config = StorageConfig(
       tier="hot",
       primary_backend=PostgreSQLStorage(
           connection_string="postgresql://user:password@localhost:5432/earth_memory",
           postgis_enabled=True,
           timescaledb_enabled=True,
           max_connections=20
       ),
       vector_backend=PostgreSQLStorage(
           schema="vector_data",
           spatial_index=True
       ),
       raster_backend=LocalFileStorage(
           base_path="/data/hot_memory/rasters",
           format="cloud-optimized-geotiff",
           file_organization="year/month/dataset"
       ),
       cache_settings={
           "max_size": "50GB",
           "eviction_policy": "least-recently-used",
           "prefetching": True
       }
   )

Warm Memory Storage
~~~~~~~~~~~~~~~

Warm Memory balances performance and capacity for medium-term storage:

.. code-block:: python

   from memories.earth.storage import S3Storage, RedisStorage
   
   # Configure warm memory storage
   warm_storage_config = StorageConfig(
       tier="warm",
       primary_backend=S3Storage(
           bucket="earth-memory-warm",
           region="us-west-2",
           prefix="data/",
           credentials={
               "aws_access_key_id": "${AWS_ACCESS_KEY_ID}",
               "aws_secret_access_key": "${AWS_SECRET_ACCESS_KEY}"
           }
       ),
       index_backend=RedisStorage(
           host="redis.example.com",
           port=6379,
           db=0,
           ttl=604800  # 7 days in seconds
       ),
       compression={
           "algorithm": "lz4",
           "level": "medium"
       },
       cache_settings={
           "max_size": "200GB",
           "eviction_policy": "least-frequently-used"
       }
   )

Cold Memory Storage
~~~~~~~~~~~~~~

Cold Memory provides cost-effective storage for archived data:

.. code-block:: python

   from memories.earth.storage import GCSStorage
   
   # Configure cold memory storage
   cold_storage_config = StorageConfig(
       tier="cold",
       primary_backend=GCSStorage(
           bucket="earth-memory-cold",
           project="my-earth-project",
           prefix="archive/",
           credentials_file="/path/to/service-account-key.json"
       ),
       compression={
           "algorithm": "zstd",
           "level": "high"
       },
       access_pattern="batch",
       retrieval_time="hours"
   )

Glacier Memory Storage
~~~~~~~~~~~~~~~~~

Glacier Memory provides long-term archival of important but rarely accessed data:

.. code-block:: python

   from memories.earth.storage import AzureBlobStorage
   
   # Configure glacier memory storage
   glacier_storage_config = StorageConfig(
       tier="glacier",
       primary_backend=AzureBlobStorage(
           account="earthmemoryarchive",
           container="deep-archive",
           connection_string="${AZURE_CONNECTION_STRING}",
           access_tier="archive"
       ),
       compression={
           "algorithm": "zstd",
           "level": "maximum"
       },
       access_pattern="rare",
       retrieval_time="days",
       backup_policy={
           "redundancy": "geo-redundant",
           "versioning": True,
           "immutable": True,
           "retention_period": "10years"
       }
   )

Storage Backend Options
-------------------

The Memory Codex supports various storage backends for different use cases:

File Storage
~~~~~~~~~

Local or network-attached file systems:

.. code-block:: python

   from memories.earth.storage import LocalFileStorage, NetworkFileStorage
   
   # Local file storage
   local_storage = LocalFileStorage(
       base_path="/data/earth_memory",
       format="zarr",
       permissions="rw-r--r--",
       file_organization="hierarchical"
   )
   
   # Network file storage
   network_storage = NetworkFileStorage(
       protocol="nfs",
       mount_point="/mnt/earth_data",
       server="fileserver.example.com",
       remote_path="/exports/earth_data",
       connection_options={
           "rsize": 1048576,
           "wsize": 1048576,
           "actimeo": 600
       }
   )

Object Storage
~~~~~~~~~~

Cloud-based object storage services:

.. code-block:: python

   from memories.earth.storage import S3Storage, GCSStorage, AzureBlobStorage
   
   # Amazon S3
   s3_storage = S3Storage(
       bucket="earth-memory-data",
       region="us-west-2",
       endpoint="https://s3.us-west-2.amazonaws.com",
       prefix="data/",
       storage_class="STANDARD",
       encryption={
           "algorithm": "AES256",
           "kms_key_id": None
       }
   )
   
   # Google Cloud Storage
   gcs_storage = GCSStorage(
       bucket="earth-memory-data",
       project="my-earth-project",
       prefix="raster/",
       storage_class="STANDARD",
       location="us-central1",
       uniform_access_control=True
   )
   
   # Azure Blob Storage
   azure_storage = AzureBlobStorage(
       account="earthmemory",
       container="satellite-data",
       prefix="sentinel/",
       access_tier="hot",
       connection_string="${AZURE_CONNECTION_STRING}"
   )

Database Storage
~~~~~~~~~~~~

Relational, document, and time-series databases:

.. code-block:: python

   from memories.earth.storage import PostgreSQLStorage, MongoDBStorage, InfluxDBStorage
   
   # PostgreSQL/PostGIS
   postgres_storage = PostgreSQLStorage(
       connection_string="postgresql://user:password@localhost:5432/earth_memory",
       schema="public",
       postgis_enabled=True,
       timescaledb_enabled=True,
       pool_size=10,
       max_overflow=20
   )
   
   # MongoDB
   mongodb_storage = MongoDBStorage(
       connection_string="mongodb://user:password@localhost:27017/earth_memory",
       database="earth_memory",
       collection_prefix="memory_",
       write_concern={"w": "majority"},
       read_concern="majority"
   )
   
   # InfluxDB
   influxdb_storage = InfluxDBStorage(
       url="http://localhost:8086",
       token="${INFLUXDB_TOKEN}",
       org="earth-memory-project",
       bucket="time-series-data",
       measurement_prefix="earth_"
   )

Specialized Storage Solutions
-------------------------

For specific data types, specialized storage solutions offer optimized performance:

Vector Data Storage
~~~~~~~~~~~~~~~

For points, lines, polygons, and other vector features:

.. code-block:: python

   from memories.earth.storage.vector import PostGISStorage, GeoJSONStorage
   
   # PostGIS for vector data
   postgis_storage = PostGISStorage(
       connection_string="postgresql://user:password@localhost:5432/earth_memory",
       schema="vector_data",
       spatial_index=True,
       topology=True,
       srid=4326
   )
   
   # GeoJSON files
   geojson_storage = GeoJSONStorage(
       base_path="/data/vector",
       organization="category/subcategory",
       compression="gzip",
       validation=True
   )

Raster Data Storage
~~~~~~~~~~~~~~~

For gridded data like satellite imagery:

.. code-block:: python

   from memories.earth.storage.raster import COGStorage, ZarrStorage
   
   # Cloud-Optimized GeoTIFF
   cog_storage = COGStorage(
       base_path="/data/rasters",
       organization="sensor/year/month",
       overviews=True,
       compression="DEFLATE",
       blocksize=(256, 256),
       predictor=2
   )
   
   # Zarr storage
   zarr_storage = ZarrStorage(
       store_path="/data/zarr",
       chunks=(1, 500, 500),  # (time, y, x)
       compression="zstd",
       compression_level=3,
       dimension_separator="/"
   )

Time Series Storage
~~~~~~~~~~~~~~

For temporal data sequences:

.. code-block:: python

   from memories.earth.storage.timeseries import TimescaleDBStorage, ParquetStorage
   
   # TimescaleDB
   timescaledb_storage = TimescaleDBStorage(
       connection_string="postgresql://user:password@localhost:5432/earth_memory",
       schema="timeseries",
       chunk_time_interval="1 month",
       compression_enabled=True
   )
   
   # Apache Parquet
   parquet_storage = ParquetStorage(
       base_path="/data/timeseries",
       partition_cols=["year", "variable"],
       compression="snappy",
       row_group_size=10000,
       page_size=8192
   )

Storage Configuration for Different Environments
-------------------------------------------

Different deployment environments may require different storage configurations:

Development Environment
~~~~~~~~~~~~~~~~~~

Simplified storage for local development:

.. code-block:: python

   from memories.earth import MemoryCodex, StorageConfig
   from memories.earth.storage import LocalFileStorage, SQLiteStorage
   
   # Development environment storage
   dev_storage = StorageConfig(
       tier_configs={
           "hot": {
               "primary_backend": SQLiteStorage(
                   database_path="./data/hot_memory.db",
                   spatialite_enabled=True
               )
           },
           "warm": {
               "primary_backend": LocalFileStorage(
                   base_path="./data/warm_memory",
                   format="zarr"
               )
           },
           "cold": {
               "primary_backend": LocalFileStorage(
                   base_path="./data/cold_memory",
                   format="zarr",
                   compression=True
               )
           }
       },
       default_vector_format="geojson",
       default_raster_format="tiff",
       default_timeseries_format="csv"
   )
   
   # Initialize Memory Codex with development storage
   codex = MemoryCodex(storage_config=dev_storage)

Production Environment
~~~~~~~~~~~~~~~~~

Robust, scalable storage for production:

.. code-block:: python

   from memories.earth.storage import (
       PostgreSQLStorage, S3Storage, 
       GCSStorage, AzureBlobStorage
   )
   
   # Production environment storage
   prod_storage = StorageConfig(
       tier_configs={
           "hot": {
               "primary_backend": PostgreSQLStorage(
                   connection_string="${DATABASE_URL}",
                   postgis_enabled=True,
                   timescaledb_enabled=True
               ),
               "cache_settings": {
                   "type": "redis",
                   "url": "${REDIS_URL}",
                   "max_size": "10GB"
               }
           },
           "warm": {
               "primary_backend": S3Storage(
                   bucket="${S3_BUCKET_WARM}",
                   region="${AWS_REGION}",
                   credentials={"aws_access_key_id": "${AWS_KEY}",
                               "aws_secret_access_key": "${AWS_SECRET}"}
               )
           },
           "cold": {
               "primary_backend": GCSStorage(
                   bucket="${GCS_BUCKET_COLD}",
                   project="${GCS_PROJECT}",
                   credentials_file="/secrets/gcs-service-account.json"
               )
           },
           "glacier": {
               "primary_backend": AzureBlobStorage(
                   account="${AZURE_ACCOUNT}",
                   container="${AZURE_CONTAINER_GLACIER}",
                   access_tier="archive",
                   connection_string="${AZURE_CONNECTION_STRING}"
               )
           }
       },
       default_vector_format="postgis",
       default_raster_format="cog",
       default_timeseries_format="parquet",
       encryption_enabled=True,
       backup_enabled=True,
       monitoring_enabled=True
   )
   
   # Initialize Memory Codex with production storage
   codex = MemoryCodex(storage_config=prod_storage)

Storage Migration
--------------

As data ages or access patterns change, you may need to migrate data between storage tiers:

.. code-block:: python

   from memories.earth.storage import MigrationJob
   
   # Migrate data between tiers
   migration_job = MigrationJob(
       source_tier="hot",
       destination_tier="warm",
       selection_criteria={
           "last_accessed_before": "30 days ago",
           "memory_types": ["TemperatureMemory", "PrecipitationMemory"],
           "min_size": "100MB"
       },
       validation=True,
       delete_after_migration=True,
       metadata_update=True
   )
   
   # Execute the migration
   codex.execute_migration(migration_job)
   
   # Check migration status
   status = codex.get_migration_status(migration_job.id)
   print(f"Migration status: {status.state}")
   print(f"Progress: {status.progress_percentage}%")
   print(f"Data migrated: {status.bytes_migrated / (1024**3):.2f} GB")

Storage Performance Optimization
-----------------------------

Optimize storage performance for your specific workloads:

.. code-block:: python

   from memories.earth.storage import PerformanceOptimizer
   
   # Create performance optimizer
   optimizer = PerformanceOptimizer(codex)
   
   # Analyze current access patterns
   analysis = optimizer.analyze_access_patterns(
       time_period="7 days",
       detail_level="high"
   )
   
   # Get optimization recommendations
   recommendations = optimizer.get_recommendations()
   for rec in recommendations:
       print(f"Recommendation: {rec.description}")
       print(f"Expected improvement: {rec.expected_improvement}")
       print(f"Implementation complexity: {rec.complexity}")
   
   # Apply specific optimization
   optimizer.apply_optimization(
       optimization_id="chunk-size-adjustment",
       parameters={"new_chunk_size": (1, 1000, 1000)}
   )

Monitoring Storage
--------------

Monitor storage usage and performance:

.. code-block:: python

   from memories.earth.storage import StorageMonitor
   
   # Create storage monitor
   monitor = StorageMonitor(codex)
   
   # Get storage usage statistics
   usage = monitor.get_storage_usage()
   for tier, stats in usage.items():
       print(f"Tier: {tier}")
       print(f"  Used: {stats.used_bytes / (1024**3):.2f} GB")
       print(f"  Available: {stats.available_bytes / (1024**3):.2f} GB")
       print(f"  Utilization: {stats.utilization_percentage}%")
   
   # Get performance metrics
   performance = monitor.get_performance_metrics(
       time_period="24 hours",
       metrics=["read_latency", "write_throughput", "request_rate"]
   )
   
   # Set up alerts
   monitor.set_alert(
       name="hot-storage-nearly-full",
       condition="hot.utilization_percentage > 85",
       notification_channel="email",
       recipients=["admin@example.com"],
       cooldown="6 hours"
   )

Next Steps
---------

After configuring memory storage:

- Learn about memory retrieval and query capabilities in :doc:`../memory_codex/query`
- Set up data processing pipelines in :doc:`../integration/data_processing`
- Explore memory tier transitions in :doc:`../memory_architecture/tiered_memory` 