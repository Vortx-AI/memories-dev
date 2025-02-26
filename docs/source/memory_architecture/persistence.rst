===================
Memory Persistence
===================

Overview
--------

The memories-dev framework provides robust persistence mechanisms to ensure Earth observation data and derived insights are reliably stored and retrievable across system restarts and failures.

Storage Backends
--------------

File System
~~~~~~~~~~

Basic persistent storage using the local file system:

.. code-block:: python

    from memories.persistence import FileSystemStorage
    
    # Initialize storage
    storage = FileSystemStorage(
        root_path="/data/memories",
        max_size="1TB",
        compression=True
    )
    
    # Store data
    await storage.save(
        key="analysis_results",
        data=results,
        metadata={"timestamp": "2024-03-15"}
    )
    
    # Retrieve data
    data = await storage.load("analysis_results")

Database
~~~~~~~

Structured storage using SQL or NoSQL databases:

.. code-block:: python

    from memories.persistence import DatabaseStorage
    
    # Initialize database storage
    db_storage = DatabaseStorage(
        url="postgresql://localhost/memories",
        table_prefix="earth_memory",
        pool_size=10
    )
    
    # Store structured data
    await db_storage.save_structured(
        collection="observations",
        data=observation_data,
        index_fields=["timestamp", "location"]
    )

Cloud Storage
~~~~~~~~~~~

Cloud-based persistent storage:

.. code-block:: python

    from memories.persistence import CloudStorage
    
    # Initialize cloud storage
    cloud_storage = CloudStorage(
        provider="aws",
        bucket="earth-memories",
        region="us-west-2",
        credentials={
            "access_key": "YOUR_ACCESS_KEY",
            "secret_key": "YOUR_SECRET_KEY"
        }
    )
    
    # Store large datasets
    await cloud_storage.save_dataset(
        key="satellite_imagery_2024",
        data=imagery_data,
        metadata={"source": "sentinel-2"}
    )

Persistence Strategies
--------------------

Automatic Persistence
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from memories.persistence import AutoPersistence
    
    # Configure automatic persistence
    auto_persist = AutoPersistence(
        interval="1h",
        storage=storage,
        backup_count=3
    )
    
    # Enable automatic persistence
    auto_persist.start()
    
    # Disable when needed
    auto_persist.stop()

Manual Persistence
~~~~~~~~~~~~~~~

.. code-block:: python

    from memories.persistence import MemoryPersistence
    
    # Initialize persistence manager
    persistence = MemoryPersistence(
        primary_storage=storage,
        backup_storage=cloud_storage
    )
    
    # Manually persist current state
    await persistence.save_checkpoint(
        name="daily_checkpoint",
        include_metadata=True
    )
    
    # Restore from checkpoint
    await persistence.restore_checkpoint("daily_checkpoint")

Recovery Mechanisms
-----------------

Automatic Recovery
~~~~~~~~~~~~~~~

.. code-block:: python

    from memories.persistence import RecoveryManager
    
    # Initialize recovery manager
    recovery = RecoveryManager(
        storage=storage,
        max_attempts=3,
        timeout=30  # seconds
    )
    
    # Attempt recovery
    success = await recovery.recover_latest()
    if success:
        print("Successfully recovered latest state")

Manual Recovery
~~~~~~~~~~~~

.. code-block:: python

    # Manually recover from specific checkpoint
    await recovery.recover_from_checkpoint(
        checkpoint_id="2024-03-15-backup",
        validate=True
    )
    
    # List available recovery points
    checkpoints = await recovery.list_checkpoints()
    for cp in checkpoints:
        print(f"Checkpoint: {cp.id}, Time: {cp.timestamp}")

Monitoring
---------

.. code-block:: python

    from memories.persistence import PersistenceMonitor
    
    # Initialize monitor
    monitor = PersistenceMonitor(storage)
    
    # Get persistence metrics
    metrics = monitor.get_metrics()
    print(f"Storage usage: {metrics.usage_gb}GB")
    print(f"Last backup: {metrics.last_backup_time}")
    print(f"Backup success rate: {metrics.success_rate}%")

Best Practices
------------

1. **Backup Strategy**
   - Regular automated backups
   - Multiple backup locations
   - Versioned backups
   - Backup validation

2. **Performance**
   - Optimize backup timing
   - Use appropriate compression
   - Balance frequency and resource usage
   - Consider incremental backups

3. **Security**
   - Encrypt sensitive data
   - Secure backup locations
   - Access control
   - Audit logging

4. **Recovery Planning**
   - Test recovery procedures
   - Document recovery steps
   - Monitor recovery metrics
   - Maintain recovery points

See Also
--------

* :doc:`/memory_architecture/tiered_memory`
* :doc:`/deployment/backup_restore`
* :doc:`/api_reference/persistence` 