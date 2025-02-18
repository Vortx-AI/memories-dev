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
        geometry: str,
        geometry_type: str,
        data_type: str,
        parquet_file: str,
        relevant_column: str,
        geometry_column: str = None,
        extra_params: Dict = None
    ) -> Dict[str, Any]:
        """
        Analyze the query and recommend appropriate functions with parameters.

        Args:
            query: The natural language query
            geometry: WKT geometry string for spatial filtering
            geometry_type: Type of geometry (POINT, LINESTRING, POLYGON)
            data_type: Type of data being queried
            parquet_file: Path to the parquet file
            relevant_column: Column name relevant to the query
            geometry_column: Name of the geometry column in the parquet file
            extra_params: Additional parameters for query customization
        """
        try:
            prompt = f"""
Given a spatial query and data details, recommend appropriate query functions with parameters.

Query: {query}
Data Type: {data_type}
Geometry: {geometry}
Geometry Type: {geometry_type}
Parquet File: {parquet_file}
Relevant Column: {relevant_column}
Geometry Column: {geometry_column if geometry_column else 'geometry'}

Available functions:
1. nearest_query - Find nearest records (default limit: 5)
2. within_area_query - Find records within the specified geometry
3. count_within_area_query - Count records within the specified geometry
4. exact_match_query - Find exact matches with spatial filtering

Return recommendations in this JSON format:
{{
    "status": "success",
    "recommendations": [
        {{
            "function_name": "function_name",
            "parameters": {{
                "parquet_file": "file_path",
                "column_name": "column_name",
                "value": "true/false",
                "geometry": "WKT_string",
                "geometry_type": "POINT/LINESTRING/POLYGON",
                "limit": number         // for nearest query
            }},
            "reason": "explanation"
        }}
    ]
}}

Note: All filter columns are boolean type, so value should be 'true' or 'false'.
"""
            # Get response from model
            response = self.load_model.get_response(prompt)
            
            # Parse the response
            try:
                if isinstance(response, str):
                    if "```json" in response:
                        response = response.split("```json")[1].split("```")[0]
                    elif "```" in response:
                        response = response.split("```")[1].split("```")[0]
                    
                    result = json.loads(response.strip())
                    
                    # Set default values for limit if it's a string
                    for rec in result.get('recommendations', []):
                        params = rec.get('parameters', {})
                        if 'limit' in params and not isinstance(params['limit'], (int, float)):
                            params['limit'] = 5   # Default 5 results
                        # Ensure value is boolean string
                        if 'value' in params:
                            params['value'] = 'true'  # Default to true for boolean columns
                        # Ensure geometry and geometry_type are set
                        if 'geometry' not in params:
                            params['geometry'] = geometry
                        if 'geometry_type' not in params:
                            params['geometry_type'] = geometry_type
                    
                    return result
                    
            except json.JSONDecodeError as e:
                return {
                    'status': 'error',
                    'error': f'Failed to parse response: {str(e)}',
                    'response': response
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

def main():
    """
    Example usage of the updated Agent Analyst.
    """
    # For demonstration purposes, we don't need the load_model to provide query selection.
    load_model = None  
    analyst = AgentAnalyst(load_model)

    # Example inputs
    query = "find restaurants near"
    geometry = "POLYGON((77.5946 12.9716, 77.5947 12.9716, 77.5947 12.9717, 77.5946 12.9717, 77.5946 12.9716))"
    geometry_type = "POLYGON"
    data_type = "amenity"
    parquet_file = os.path.join(os.getenv("PROJECT_ROOT", ""), "data", "example.parquet")
    relevant_column = "amenity"
    geometry_column = "geometry"
    extra_params = {
        "value": "restaurant",    # used by exact_match_query if needed
        "pattern": "%restaurant%"  # used by like_query if needed
    }

    result = analyst.analyze_query(
        query, geometry, geometry_type, data_type, parquet_file, 
        relevant_column, geometry_column, extra_params
    )
    
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
