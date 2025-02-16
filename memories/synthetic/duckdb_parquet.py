from typing import Dict, List, Any, Optional
import duckdb
from pathlib import Path
import pandas as pd
from memories.agents.agent_config import get_duckdb_connection

def fetch_data(conn):
    """
    Example DuckDB spatial query template.
    Shows how to:
    1. Use existing DuckDB connection
    2. Query parquet files with geometry data
    3. Use spatial functions
    4. Return results as DataFrame
    """
    try:
        query = """
            SELECT 
                amenity,
                name,
                ST_X(geom) as longitude,
                ST_Y(geom) as latitude,
                ST_Distance(geom, ST_Point(77.5946, 12.9716)) as distance_meters
            FROM parquet_scan('india_points_processed.parquet')
            WHERE 
                amenity = 'hospital'
                AND ST_DWithin(
                    geom,
                    ST_Point(77.5946, 12.9716),
                    5000  -- 5km radius
                )
            ORDER BY distance_meters
            LIMIT 100
        """
        return conn.execute(query).fetchdf()
    except Exception as e:
        print(f"Error executing query: {str(e)}")
        return pd.DataFrame()

if __name__ == "__main__":
    # Get DuckDB connection
    conn = get_duckdb_connection()
    
    # Execute query
    results = fetch_data(conn)
    
    # Display results
    print("\nQuery Results:")
    print(results)
    print(f"\nTotal rows: {len(results)}")