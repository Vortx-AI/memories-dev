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
        
        Args:
            code (str): The raw generated code
            
        Returns:
            str: Clean, executable Python code
        """
        # Remove markdown code blocks if present
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        elif "```" in code:
            code = code.split("```")[1].split("```")[0]
        
        # Remove any leading/trailing whitespace
        code = code.strip()
        
        # Remove any installation instructions or other text before import statements
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
        geometry: Optional[str] = None,
        geometry_type: Optional[str] = None,
        extra_params: dict = {}
    ) -> dict:
        """
        Uses an LLM with the duckdb_parquet_kb.json knowledgebase to generate Python code that queries
        the provided Parquet file.
        """
        try:
            # Load the knowledge base
            kb_path = os.path.join(self.project_root, "knowledge_base", "duckdb_parquet_kb.json")
            with open(kb_path, 'r') as f:
                knowledge_base = json.load(f)

            prompt = f"""
Generate only executable Python code for DuckDB query. No explanations or markdown formatting.
The code must:
1. Import duckdb
2. Connect to DuckDB
3. Query the Parquet file at '{parquet_file}'
4. Find records matching:
   - latitude: {lat}
   - longitude: {lon}
5. Store results in a variable named 'results'

Use this exact structure:
import duckdb
conn = duckdb.connect()
conn.execute("LOAD spatial;")
results = conn.execute("YOUR QUERY HERE").fetchall()

Knowledge Base:
{json.dumps(knowledge_base, indent=2)}
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
