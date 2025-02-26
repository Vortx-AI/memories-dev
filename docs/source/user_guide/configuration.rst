Configuration
=============

This guide explains how to configure the memories-dev framework for your specific needs.

Basic Configuration
-------------------

Environment Setup
~~~~~~~~~~~~~~~~~

Configure the framework using environment variables or a configuration file:

.. code-block:: python

    from memories.core.config import Config
    
    # Load configuration from environment variables
    config = Config.from_env()
    
    # Or load from a YAML file
    config = Config.from_yaml("config.yaml")
    
    # Or set configuration directly
    config = Config(
        data_dir="/path/to/data",
        cache_dir="/path/to/cache",
        log_level="INFO",
        max_memory_gb=64
    )

Memory Configuration
--------------------

Configure different memory tiers:

.. code-block:: python

    # Configure hot memory
    config.hot_memory = {
        "max_size_gb": 32,
        "eviction_policy": "lru",
        "ttl_seconds": 3600,
        "compression": False
    }
    
    # Configure warm memory
    config.warm_memory = {
        "max_size_gb": 128,
        "compression": True,
        "compression_level": 6,
        "chunk_size_mb": 64
    }
    
    # Configure cold memory
    config.cold_memory = {
        "storage_type": "s3",
        "bucket": "memories-cold-storage",
        "region": "us-west-2",
        "lifecycle_days": 90
    }

Storage Configuration
---------------------

Configure storage backends:

.. code-block:: python

    # Configure local storage
    config.storage = {
        "type": "local",
        "root_dir": "/data/memories",
        "max_size_gb": 1000,
        "backup_enabled": True
    }
    
    # Configure cloud storage
    config.storage = {
        "type": "s3",
        "bucket": "memories-data",
        "region": "us-west-2",
        "credentials": {
            "access_key": "${AWS_ACCESS_KEY}",
            "secret_key": "${AWS_SECRET_KEY}"
        }
    }

Network Configuration - --------------------

Configure network settings:

.. code-block:: python

    # Configure network parameters
    config.network = {
        "max_connections": 1000,
        "timeout_seconds": 30,
        "retry_attempts": 3,
        "backoff_factor": 1.5
    }
    
    # Configure API endpoints
    config.endpoints = {
        "main": "https://api.memories.dev",
        "backup": "https://backup.memories.dev",
        "metrics": "https://metrics.memories.dev"
    }

Security Configuration
----------------------

Configure security settings:

.. code-block:: python

    # Configure authentication
    config.auth = {
        "provider": "oauth2",
        "client_id": "${OAUTH_CLIENT_ID}",
        "client_secret": "${OAUTH_CLIENT_SECRET}",
        "scopes": ["read", "write"]
    }
    
    # Configure encryption
    config.encryption = {
        "algorithm": "aes-256-gcm",
        "key_rotation_days": 30,
        "kms_key_id": "${KMS_KEY_ID}"
    }

Monitoring Configuration
------------------------

Configure monitoring and logging:

.. code-block:: python

    # Configure logging
    config.logging = {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "output": ["console", "file"],
        "log_dir": "/var/log/memories"
    }
    
    # Configure metrics
    config.metrics = {
        "provider": "prometheus",
        "endpoint": "http://localhost:9090",
        "push_interval": 10,
        "labels": {
            "environment": "production",
            "region": "us-west"
        }
    }

Performance Configuration
-------------------------

Configure performance settings:

.. code-block:: python

    # Configure caching
    config.cache = {
        "backend": "redis",
        "url": "redis://localhost:6379",
        "max_size_gb": 10,
        "ttl_seconds": 3600
    }
    
    # Configure query optimization
    config.query = {
        "max_results": 1000,
        "timeout_seconds": 30,
        "use_cache": True,
        "spatial_index": "rtree"
    }

Model Configuration
-------------------

Configure AI models:

.. code-block:: python

    # Configure model settings
    config.models = {
        "provider": "openai",
        "api_key": "${OPENAI_API_KEY}",
        "default_model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    # Configure model deployment
    config.model_deployment = {
        "type": "kubernetes",
        "namespace": "memories",
        "min_replicas": 2,
        "max_replicas": 10,
        "gpu_enabled": True
    }

Advanced Configuration
----------------------

Fine-tune advanced settings:

.. code-block:: python

    # Configure advanced features
    config.advanced = {
        "feature_flags": {
            "experimental": False,
            "beta_features": True
        },
        "optimization": {
            "use_gpu": True,
            "batch_size": 64,
            "prefetch_enabled": True
        },
        "debugging": {
            "verbose": True,
            "profile_queries": True,
            "trace_enabled": False
        }
    }

Configuration Validation
------------------------

Validate your configuration:

.. code-block:: python

    # Validate configuration
    try:
        config.validate()
    except ConfigurationError as e:
        print(f"Configuration error: {e}")
        
    # Test configuration
    try:
        config.test_connection()
    except ConnectionError as e:
        print(f"Connection error: {e}")

Configuration Best Practices
----------------------------

1. Security
   - Never hardcode sensitive values
   - Use environment variables for secrets
   - Rotate keys regularly
   - Encrypt sensitive configuration

2. Performance
   - Tune cache sizes based on workload
   - Configure appropriate timeouts
   - Enable compression where needed
   - Monitor and adjust as needed

3. Monitoring
   - Enable comprehensive logging
   - Configure appropriate metrics
   - Set up alerting
   - Regular configuration review

4. Maintenance
   - Document all configuration
   - Version control configuration
   - Regular backup of configuration
   - Automated configuration testing 