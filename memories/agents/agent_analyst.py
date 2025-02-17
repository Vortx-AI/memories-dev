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

    def clean_generated_code(self, code: str) -> str:
        """
        Clean up the generated code by removing markdown formatting and comments.
        """
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        elif "```" in code:
            code = code.split("```")[1].split("```")[0]
        
        code = code.strip()
        
        if "import" in code:
            code_lines = code.split('\n')
            for i, line in enumerate(code_lines):
                if 'import' in line:
                    code = '\n'.join(code_lines[i:])
                    break
        
        return code

    def analyze_query(
        self,
        query: str,
        lat: float,
        lon: float,
        data_type: str,
        parquet_file: str,
        relevant_column: str,
        geometry_column: str,
        geometry_type: str,
        extra_params: dict = {}
    ) -> dict:
        """
        Generate DuckDB query code based on the input parameters.
        """
        try:
            # Load the knowledge base
            kb_path = os.path.join(self.project_root, "memories", "utils", "earth", "duckdb_parquet_kb.json")
            with open(kb_path, 'r') as f:
                knowledge_base = json.load(f)

            # Find the appropriate query function based on the query type
            query_type = "within_radius_query"  # Default to within_radius_query
            if "exact" in query.lower() or "match" in query.lower():
                query_type = "exact_match_query"
            elif "like" in query.lower() or "similar" in query.lower():
                query_type = "like_query"
            elif "nearest" in query.lower() or "closest" in query.lower():
                query_type = "nearest_query"
            elif "count" in query.lower():
                query_type = "count_within_radius_query"

            # Generate code using the selected query type
            code = f"""from memories.utils.earth.duckdb_parquet_queries import {query_type}, execute_duckdb_spatial_query

query = {query_type}(
    parquet_file='{parquet_file}',
    geometry_column='{geometry_column}',
    geometry_type='{geometry_type}',
    column_name='{relevant_column}',
    value='{data_type}',
    target_lat={lat},
    target_lon={lon},
    radius=1000
)

results = execute_duckdb_spatial_query(query)
return results"""
            
            return {
                "status": "success",
                "generated_code": code,
                "chosen_function": query_type
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Analysis Error: {str(e)}",
                "traceback": str(e.__traceback__)
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
    relevant_column = "amenity"
    geometry_column = "geometry"
    geometry_type = "POINT"
    extra_params = {
        "radius": 5000,           # used by spatial queries like within_radius_query
        "value": "restaurant",    # used by exact_match_query if needed
        "pattern": "%restaurant%"  # used by like_query if needed
    }

    result = analyst.analyze_query(query, lat, lon, data_type, parquet_file, relevant_column, geometry_column, geometry_type, extra_params)
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
