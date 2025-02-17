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
        Analyze query to identify suitable DuckDB query functions from knowledge base.
        
        Args:
            query (str): User's natural language query
            lat (float): Target latitude
            lon (float): Target longitude
            data_type (str): Type of data being queried
            parquet_file (str): Path to Parquet file
            relevant_column (str): Column name for filtering
            geometry_column (str): Name of the geometry column
            geometry_type (str): Type of geometry (e.g., 'POINT')
            extra_params (dict): Additional parameters
        """
        try:
            # Load the knowledge base
            kb_path = os.path.join(self.project_root, "memories", "utils", "earth", "duckdb_parquet_kb.json")
            with open(kb_path, 'r') as f:
                knowledge_base = json.load(f)

            prompt = f"""
Given the following query and data requirements, identify which function(s) from the knowledge base would be most appropriate to use.
Provide the function name(s) and their required parameters.

Query: "{query}"
Data Requirements:
- Data field/type: {data_type}
- Column to query: {relevant_column}
- Spatial components: Uses lat={lat}, lon={lon}
- File: {parquet_file}

Knowledge Base Functions:
{json.dumps(knowledge_base, indent=2)}

Return a list of suitable functions with their parameter requirements in this JSON format:
{{
    "recommended_functions": [
        {{
            "function_name": "name_of_function",
            "parameters": {{
                "param1": "value1",
                "param2": "value2"
            }},
            "reason": "Brief explanation of why this function is suitable"
        }}
    ]
}}
"""
            # Get the response from the LLM
            response = self.load_model.get_response(prompt)
            
            # Parse the response to get the JSON
            try:
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0]
                elif "```" in response:
                    response = response.split("```")[1].split("```")[0]
                
                function_recommendations = json.loads(response.strip())
                
                return {
                    "status": "success",
                    "recommendations": function_recommendations["recommended_functions"]
                }
            except json.JSONDecodeError as e:
                return {
                    "status": "error",
                    "error": f"Failed to parse LLM response: {str(e)}"
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
        print(f"\nRecommended Functions:")
        for function in result["recommendations"]:
            print(f"Function: {function['function_name']}")
            print(f"Parameters: {function['parameters']}")
            print(f"Reason: {function['reason']}")
    else:
        print(f"Error: {result['error']}")

if __name__ == "__main__":
    main()
