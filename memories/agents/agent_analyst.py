import os
import json
import duckdb
from typing import Dict, Any, Optional

class AgentAnalyst:
    def __init__(self, load_model: Any):
        """
        Initialize Agent Analyst.

        Args:
            load_model: Model or other component (not used for query selection anymore)
        """
        self.load_model = load_model
        self.project_root = os.getenv("PROJECT_ROOT", "")

    def select_query_function(self, query: str, lat: float, lon: float, data_type: str) -> str:
        """
        Selects the appropriate query function based on the input query and other parameters.

        Args:
            query (str): The user query describing what to search for.
            lat (float): Target latitude coordinate.
            lon (float): Target longitude coordinate.
            data_type (str): Data type or column name to be used (for example, 'amenity').

        Returns:
            str: The chosen function name from the available set, e.g., "nearest_query",
                 "within_radius_query", "at_coordinates_query", or "exact_match_query".
        """
        query_lower = query.lower()
        if "nearest" in query_lower:
            return "nearest_query"
        elif "within" in query_lower:
            return "within_radius_query"
        elif "at" in query_lower:
            return "at_coordinates_query"
        else:
            return "exact_match_query"

    def analyze_query(self, query: str, lat: float, lon: float, data_type: str, parquet_file: str, extra_params: dict) -> dict:
        """
        Analyze the query using the provided parameters.

        This function inspects the schema of the given Parquet file. It will:
          - Use traditional latitude/longitude columns if available.
          - Otherwise, check for a 'geometry' column. If found, it retrieves the column type and then
            constructs a query using spatial functions (ST_Y and ST_X) assuming the geometry column is a POINT.
        
        Note: Ensure the necessary spatial extension (e.g., for DuckDB) is enabled if needed.

        Args:
            query (str): The original query.
            lat (float): The latitude value.
            lon (float): The longitude value.
            data_type (str): The data type extracted from context.
            parquet_file (str): The full Parquet file path.
            extra_params (dict): Any additional parameters (such as a search radius).

        Returns:
            dict: A dictionary containing the query result, generated SQL, and additional metadata.
        """
        import duckdb
        try:
            # Connect to DuckDB
            con = duckdb.connect()
            # Retrieve the schema for the Parquet file by describing a scan of it.
            schema_df = con.execute(f"DESCRIBE parquet_scan('{parquet_file}')").fetchdf()
            # Ensure column names are lower-cased for uniformity.
            columns = [str(c).lower() for c in schema_df['column_name'].to_list()]

            # Build SQL query based on available spatial columns
            if 'latitude' in columns and 'longitude' in columns:
                # Use these columns directly
                sql_query = f"""
                    SELECT *
                    FROM '{parquet_file}'
                    WHERE latitude = {lat} AND longitude = {lon};
                """
            elif 'lat' in columns and 'lon' in columns:
                sql_query = f"""
                    SELECT *
                    FROM '{parquet_file}'
                    WHERE lat = {lat} AND lon = {lon};
                """
            elif 'geometry' in columns:
                # Retrieve the type of the geometry column for debugging/logging purposes.
                geom_type_row = schema_df[schema_df['column_name'].str.lower() == 'geometry']
                geom_type = geom_type_row['type'].iloc[0] if not geom_type_row.empty else "unknown"
                # Assuming the geometry column stores spatial data that can be processed
                # with ST_X (returning longitude) and ST_Y (returning latitude). Note that in many
                # spatial databases, a POINT type stores coordinates as (x, y) = (lon, lat).
                sql_query = f"""
                    SELECT *
                    FROM '{parquet_file}'
                    WHERE ST_Y(geometry) = {lat} AND ST_X(geometry) = {lon};
                """
                # You might want to add a tolerance/tolerance_distance here if exact equality is too strict.
            else:
                raise ValueError("No recognizable spatial columns found in the Parquet file.")

            # Debug: Log the generated SQL query (optional)
            print("[Agent Analyst] Generated SQL Query:")
            print(sql_query)
            
            # Execute the query and fetch the results.
            results = con.execute(sql_query).fetchall()
            con.close()
            return {
                "status": "success",
                "results": results,
                "generated_code": sql_query,  # For debugging purposes.
                "chosen_function": "analyze_query"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Binder Error: {str(e)}"
            }

def main():
    """
    Example usage of the updated Agent Analyst.
    """
    # For demonstration purposes, we don't need the load_model to provide query selection.
    load_model = None  
    analyst = AgentAnalyst(load_model)

    # Example inputs.
    query = "find restaurants near"
    lat = 12.9716
    lon = 77.5946
    data_type = "amenity"
    parquet_file = os.path.join(os.getenv("PROJECT_ROOT", ""), "data", "example.parquet")
    extra_params = {
        "radius": 5000,           # used by spatial queries like within_radius_query
        "value": "restaurant",    # used by exact_match_query if needed
        "pattern": "%restaurant%"  # used by like_query if needed
    }

    result = analyst.analyze_query(query, lat, lon, data_type, parquet_file, extra_params)
    print("\nAnalysis Results:")
    print("=" * 50)
    if result["status"] == "success":
        print(f"\nChosen Function: {result['chosen_function']}")
        print(f"\nGenerated Code:\n{result['generated_code']}")
        print(f"\nResults DataFrame:\n{result['results']}")
    else:
        print(f"Error: {result['error']}")

if __name__ == "__main__":
    main()
