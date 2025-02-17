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

            prompt = f"""Based on the following query and parameters, generate executable Python code using ONLY the functions from the provided knowledge base. The code should return results from the parquet file.

User Query: {query}

Parameters:
- Parquet file: {parquet_file}
- Target coordinates: lat={lat}, lon={lon}
- Data type: {data_type}
- Column to filter: {relevant_column}
- Geometry column: {geometry_column}
- Geometry type: {geometry_type}

Choose the most appropriate function from these options:
1. within_radius_query - for finding items within a radius
2. exact_match_query - for exact matches
3. like_query - for pattern matching
4. nearest_query - for finding closest items
5. count_within_radius_query - for counting items within radius

Generate ONLY the code to execute, following this structure:
from memories.utils.earth.duckdb_parquet_queries import [chosen_function], execute_duckdb_spatial_query

query = [chosen_function](
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
return results

Do not include any explanations or markdown formatting. Return only the executable Python code.
"""
            # Get the response and clean it
            generated_code = self.load_model.get_response(prompt)
            clean_code = self.clean_generated_code(generated_code)
            
            return {
                "status": "success",
                "generated_code": clean_code,
                "chosen_function": "analyze_query"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Analysis Error: {str(e)}"
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
