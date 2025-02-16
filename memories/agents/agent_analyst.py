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

    def analyze_query(self, 
                      query: str, 
                      lat: float, 
                      lon: float, 
                      data_type: str, 
                      parquet_file: str, 
                      extra_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze the given query by determining the appropriate DuckDB query template from
        a knowledge base, substituting required parameters, and executing the resulting SQL code.

        Args:
            query (str): The user query describing what to search for.
            lat (float): Target latitude coordinate.
            lon (float): Target longitude coordinate.
            data_type (str): Data type or column to be used (for example, 'amenity').
            parquet_file (str): Full file path to the Parquet file.
            extra_params (Optional[Dict[str, Any]]): Additional parameters (e.g., radius, value, pattern).

        Returns:
            Dict[str, Any]: The execution status, generated SQL query, results, and
                            the selected function name.
        """
        try:
            # Load DuckDB knowledge base from JSON.
            kb_path = os.path.join(self.project_root, "memories", "utils", "earth", "duckdb_parquet_kb.json")
            with open(kb_path, "r") as f:
                kb = json.load(f)

            # Use the internal function to select the correct query template.
            chosen_function = self.select_query_function(query, lat, lon, data_type)

            # Find the corresponding template entry in the knowledge base.
            func_details = next((item for item in kb["queries"] if item["function"] == chosen_function), None)
            if func_details is None:
                return {
                    "status": "error",
                    "error": f"Function '{chosen_function}' not found in the knowledge base."
                }

            # Prepare a parameters dictionary for substitution into the SQL template.
            extra = extra_params if extra_params is not None else {}
            params = {
                "parquet_file": parquet_file,
                "lat_col": extra.get("lat_col", "latitude"),
                "lon_col": extra.get("lon_col", "longitude"),
                "target_lat": lat,
                "target_lon": lon,
                "column_name": data_type,
                "value": extra.get("value", ""),
                "pattern": extra.get("pattern", ""),
                "radius": extra.get("radius", 1000)  # default radius if not provided
            }

            # Generate the SQL query by filling in the template.
            query_to_run = func_details["code_to_execute"].format(**params)

            # Execute the generated query using DuckDB.
            conn = duckdb.connect(':memory:')
            results = conn.execute(query_to_run).fetchdf()

            return {
                "status": "success",
                "generated_code": query_to_run,
                "results": results,
                "chosen_function": chosen_function
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
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
