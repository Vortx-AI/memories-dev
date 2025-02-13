import duckdb
import os
from dotenv import load_dotenv

def query_multiple_parquet():
    """
    Queries all Parquet files in the directory specified by GEO_MEMORIES in the .env file.

    Returns:
        pandas.DataFrame: The combined data from all Parquet files.
    """
    # Load environment variables from the .env file
    load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

    # Retrieve the GEO_MEMORIES path from environment variables
    geo_memories_path = os.getenv('GEO_MEMORIES')

    if not geo_memories_path:
        raise ValueError("GEO_MEMORIES path is not set in the .env file.")

    # Establish a connection to DuckDB (in-memory by default)
    conn = duckdb.connect()

    try:
        # Define the query with a wildcard to match all Parquet files in the GEO_MEMORIES directory
        query = f"SELECT * FROM '{geo_memories_path}/*.parquet'"

        # Execute the query and fetch the results
        result = conn.execute(query).fetchdf()
    finally:
        # Ensure the connection is closed even if an error occurs
        conn.close()

    return result

# Usage example
if __name__ == "__main__":
    try:
        data = query_multiple_parquet()
        print(data)
    except Exception as e:
        print(f"An error occurred: {e}")
