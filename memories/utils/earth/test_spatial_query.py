import duckdb

def test_spatial_query():
    # Initialize connection
    conn = duckdb.connect()
    
    try:
        # Load spatial extension first
        conn.execute("INSTALL spatial;")
        conn.execute("LOAD spatial;")

        # Create WKT point geometry string
        target_geometry = conn.execute("""
            SELECT ST_SetSRID(ST_Point(77.6078977, 12.9093124), 4326);
        """).fetchone()[0]

        print(f"Created target geometry: {target_geometry}")

        # Execute query using the 'within_radius_query' function
        query = f"""
            SELECT *
            FROM read_parquet('/home/jaya/memories-dev/data/osm_data/india_points_processed.parquet')
            WHERE communications_dish = 'water tanks'
            AND ST_Distance(
                ST_Transform(ST_SetSRID(geometry, 4326), 3857),
                ST_Transform('{target_geometry}', 3857)
            ) <= 1000;
        """
        
        print("\nExecuting query:")
        print(query)
        
        results = conn.execute(query).fetchdf()
        print(f"\nFound {len(results)} results")
        print("\nResults:")
        print(results)
        
        return results

    except Exception as e:
        print(f"Error: {str(e)}")
        raise e
    
    finally:
        conn.close()

if __name__ == "__main__":
    test_spatial_query() 