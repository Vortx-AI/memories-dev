import duckdb
import time

def test_spatial_query():
    # Initialize connection
    conn = duckdb.connect()
    
    try:
        # Install and load spatial extension with verification
        print("Installing spatial extension...")
        conn.execute("INSTALL spatial;")
        print("Loading spatial extension...")
        conn.execute("LOAD spatial;")
        
        # Verify spatial functions are available by testing a basic spatial function
        print("Verifying spatial functions...")
        test_point = conn.execute("SELECT ST_GeomFromText('POINT(0 0)');").fetchone()[0]
        print("Spatial extension ready!")

        # Create WKT point geometry string
        print("\nCreating target geometry...")
        target_geometry = conn.execute("""
            SELECT ST_GeomFromText('POINT(77.6078977 12.9093124)');
        """).fetchone()[0]

        print(f"Created target geometry: {target_geometry}")

        # Execute query using the 'within_radius_query' function
        query = f"""
            SELECT *
            FROM read_parquet('/home/jaya/memories-dev/data/osm_data/india_points_processed.parquet')
            WHERE communications_dish = 'water tanks'
            AND ST_Distance(
                ST_Transform(geometry, 3857),
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