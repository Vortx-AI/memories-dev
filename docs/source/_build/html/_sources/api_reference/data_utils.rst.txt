Data Utilities
=============

DuckDB Query Utilities
-------------------

.. automodule:: memories.utils.duckdb_utils
   :members:
   :undoc-members:
   :show-inheritance:

query_multiple_parquet Function
---------------------------

.. autofunction:: memories.utils.duckdb_utils.query_multiple_parquet

Example Usage
-----------

.. code-block:: python

    from memories import query_multiple_parquet
    
    # Define parquet files to query
    parquet_files = [
        "data/2025-02-17/*.parquet",
        "data/2025-02-16/*.parquet"
    ]
    
    # Define SQL query
    query = """
        SELECT 
            timestamp,
            location,
            measurements
        FROM parquet_files
        WHERE 
            timestamp >= '2025-02-16T00:00:00' AND
            timestamp < '2025-02-18T00:00:00'
        ORDER BY timestamp DESC
    """
    
    # Execute query across multiple parquet files
    results = query_multiple_parquet(
        parquet_files=parquet_files,
        query=query
    )
    
    # Process results
    for row in results:
        print(f"Timestamp: {row['timestamp']}")
        print(f"Location: {row['location']}")
        print(f"Measurements: {row['measurements']}")
        print("---") 