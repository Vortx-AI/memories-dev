==========================
Configuration Reference
==========================

.. note::
   This documentation is under development. More detailed content will be added in future releases.

Overview
--------

This reference guide provides comprehensive information on all configuration options available in Memories-Dev. It serves as a definitive resource for fine-tuning the system to meet specific requirements and performance needs.

Configuration File Structure
---------------------------

Memories-Dev uses a hierarchical YAML-based configuration system. The main configuration file is typically named ``config.yml`` and contains sections for different components of the system:

.. code-block:: yaml

   # Memories-Dev Configuration Example
   version: 1.0
   
   system:
     log_level: INFO
     data_dir: /path/to/data
     temp_dir: /path/to/temp
     
   memory:
     tiers:
       hot:
         enabled: true
         capacity: 10GB
         ttl: 24h
       warm:
         enabled: true
         capacity: 100GB
         ttl: 30d
       cold:
         enabled: true
         capacity: 1TB
       glacier:
         enabled: false
         
   vector_store:
     type: "faiss"
     dimensions: 768
     metric: "cosine"
     index_type: "IVF100,PQ16"
     
   graph_db:
     type: "neo4j"
     connection:
       uri: "bolt://localhost:7687"
       user: "neo4j"
       password: "password"
       
   data_sources:
     satellite:
       enabled: true
       update_frequency: "daily"
     sensor_network:
       enabled: true
       update_frequency: "hourly"
     historical:
       enabled: true
       update_frequency: "weekly"

Core Configuration Sections
--------------------------

System Configuration
^^^^^^^^^^^^^^^^^^^

.. list-table::
   :widths: 20 15 50 15
   :header-rows: 1

   * - Parameter
     - Type
     - Description
     - Default
   * - log_level
     - string
     - Logging verbosity level (DEBUG, INFO, WARNING, ERROR)
     - INFO
   * - data_dir
     - string
     - Directory for storing persistent data
     - ./data
   * - temp_dir
     - string
     - Directory for temporary files
     - ./temp
   * - workers
     - integer
     - Number of worker processes
     - 4

Memory Configuration
^^^^^^^^^^^^^^^^^^^

.. list-table::
   :widths: 20 15 50 15
   :header-rows: 1

   * - Parameter
     - Type
     - Description
     - Default
   * - tiers.hot.enabled
     - boolean
     - Enable hot memory tier
     - true
   * - tiers.hot.capacity
     - string
     - Maximum capacity for hot tier
     - 10GB
   * - tiers.hot.ttl
     - string
     - Time-to-live for hot tier data
     - 24h
   * - tiers.warm.enabled
     - boolean
     - Enable warm memory tier
     - true
   * - tiers.warm.capacity
     - string
     - Maximum capacity for warm tier
     - 100GB

Vector Store Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :widths: 20 15 50 15
   :header-rows: 1

   * - Parameter
     - Type
     - Description
     - Default
   * - type
     - string
     - Vector database type (faiss, milvus, etc.)
     - faiss
   * - dimensions
     - integer
     - Vector dimensions
     - 768
   * - metric
     - string
     - Distance metric (cosine, l2, etc.)
     - cosine

Environment Variables
--------------------

Memories-Dev also supports configuration via environment variables, which take precedence over configuration file values:

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Variable
     - Description
   * - MEMORIES_DATA_DIR
     - Override for data directory location
   * - MEMORIES_LOG_LEVEL
     - Override for logging level
   * - MEMORIES_VECTOR_STORE
     - Override for vector store type
   * - MEMORIES_WORKERS
     - Override for number of worker processes

Coming Soon
----------

Future documentation will include:

* Complete reference for all configuration parameters
* Best practices for optimizing configurations
* Performance impact of various settings
* Configuration templates for common use cases
* Validation mechanisms for configuration files

See Also
--------

* :doc:`/getting_started/configuration`
* :doc:`/performance/tuning`
* :doc:`/deployment/index` 