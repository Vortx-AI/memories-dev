import os
import json
import duckdb
from typing import Dict, Any, Optional

class AgentAnalyst:
    def __init__(self, load_model: Any):
        """
        Initialize Agent Analyst.

        Args:
            load_model: An LLM instance or similar component used for generating code.
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

    def analyze_query(
        self,
        query: str,
        lat: float,
        lon: float,
        data_type: str,
        parquet_file: str,
        geometry: Optional[str] = None,
        geometry_type: Optional[str] = None,
        extra_params: dict = {}
    ) -> dict:
        """
        Uses an LLM with the duckdb_parquet_kb.json knowledgebase to generate Python code that queries
        the provided Parquet file. The generated code will filter records based on the provided
        latitude and longitude. If columns named 'latitude'/'longitude' or 'lat'/'lon' exist, they should be used.
        Otherwise, if a geometry column is provided (with its type), generate code that uses spatial functions
        (like ST_Y and ST_X) on the geometry column.

        Returns:
            A dictionary with the status and the generated Python code.
        """
        try:
            # Load the knowledge base
            kb_path = os.path.join(self.project_root, "knowledge_base", "duckdb_parquet_kb.json")
            with open(kb_path, 'r') as f:
                knowledge_base = json.load(f)

            prompt = f"""
Generate a Python code snippet that queries a Parquet file using DuckDB.
The Parquet file is located at '{parquet_file}'.
The target coordinates to filter are:
    latitude: {lat}
    longitude: {lon}
The code should follow this logic:
1. If the file contains columns named 'latitude' and 'longitude', filter using these.
2. If not, but it contains 'lat' and 'lon', filter using those columns.
3. Otherwise, if a geometry column is present, use the provided geometry column name:
      geometry column: {geometry if geometry else "N/A"}
   and its type: {geometry_type if geometry_type else "N/A"}.
   In that case, generate code that applies spatial functions (for example, ST_Y and ST_X)
   to extract the latitude and longitude from the geometry column.

Knowledge Base Context:
{json.dumps(knowledge_base, indent=2)}

Return only the Python code snippet.
            """
            generated_code = self.load_model.get_response(prompt)
            return {
                "status": "success",
                "generated_code": generated_code,
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
    print(result)
    print("\nAnalysis Results:")
    print("=" * 50)
    if result["status"] == "success":
        print(f"\nChosen Function: {result['chosen_function']}")
        print(f"\nGenerated Code:\n{result['generated_code']}")
    else:
        print(f"Error: {result['error']}")

if __name__ == "__main__":
    main()
