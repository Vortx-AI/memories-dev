import duckdb
import os
from dotenv import load_dotenv
from typing import List

def query_multiple_parquet(output_query="SELECT * FROM combined_data"):
    """
    Executes a SQL query on all Parquet files in the directory specified by GEO_MEMORIES.
    Handles schema mismatches by aligning columns by name.

    Args:
        output_query (str): The SQL query to execute on the combined data.

    Returns:
        list: The result of the executed query.
    """
    # Load environment variables from the .env file
    load_dotenv()

    # Retrieve the GEO_MEMORIES path from environment variables
    geo_memories_path = os.getenv('GEO_MEMORIES')

    if not geo_memories_path:
        raise ValueError("GEO_MEMORIES path is not set in the .env file.")

    # Establish a connection to DuckDB
    conn = duckdb.connect(database=':memory:', read_only=False)

    try:
        # Register all Parquet files in the directory as a single table
        # Use union_by_name to handle schema differences
        conn.execute(f"""
            CREATE OR REPLACE VIEW combined_data AS
            SELECT *
            FROM read_parquet('{geo_memories_path}/*.parquet', union_by_name=true, filename=true)
        """)

        # Execute the user's query
        result = conn.execute(output_query).fetchall()
        return result

    finally:
        # Ensure the connection is closed even if an error occurs
        conn.close()

def list_parquet_files(directory: str) -> List[str]:
    """List all Parquet files in a directory.
    
    Args:
        directory: Path to directory to search for Parquet files
        
    Returns:
        List of paths to Parquet files
    """
    parquet_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.parquet'):
                parquet_files.append(os.path.join(root, file))
    return parquet_files

# Usage example
if __name__ == "__main__":
    try:
        # Define your SQL query here
        sql_query = "SELECT * FROM combined_data LIMIT 10;"  # Example: Fetch first 10 rows
        data = query_multiple_parquet(sql_query)
        for row in data:
            print(row)
    except Exception as e:
        print(f"An error occurred: {e}") 