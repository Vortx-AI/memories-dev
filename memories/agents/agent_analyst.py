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
        relevant_column: str = None,
        geometry: Optional[str] = None,
        geometry_type: Optional[str] = None,
        extra_params: dict = {}
    ) -> dict:
        """
        Uses an LLM with the duckdb_parquet_kb.json knowledgebase to generate Python code that queries
        the provided Parquet file using the appropriate query function based on the data type and context.
        """
        try:
            # Load the knowledge base from the correct path
            kb_path = os.path.join(self.project_root, "memories", "utils", "earth", "duckdb_parquet_kb.json")
            with open(kb_path, 'r') as f:
                knowledge_base = json.load(f)

            prompt = f"""
Generate executable Python code that uses the query functions defined in the knowledge base to fetch data from a Parquet file.

Context:
- User Query: "{query}"
- Data Type: "{data_type}"
- Relevant Column: "{relevant_column}"
- Coordinates: ({lat}, {lon})
- Parquet File: "{parquet_file}"

Requirements:
1. Use ONLY the query functions defined in the knowledge base
2. Choose the most appropriate function based on the query context
3. The code must store results in a variable named 'results'
4. Use the relevant column for filtering data
5. Consider the data type when constructing the query
6. Include spatial functions if needed (geometry column: {geometry}, type: {geometry_type})
7. Use proper string escaping for file paths in SQL queries

Example structure:
import duckdb

def within_radius_query(conn, parquet_file, target_lat, target_lon, radius_meters):
    query = f'''
        SELECT *
        FROM read_parquet({{parquet_file}})
        WHERE ST_DWithin(
            ST_Point(longitude, latitude),
            ST_Point({target_lon}, {target_lat}),
            {radius_meters}
        )
    '''
    return conn.execute(query).fetchall()

conn = duckdb.connect()
conn.execute("LOAD spatial;")
results = within_radius_query(conn, '{parquet_file}', {lat}, {lon}, 5000)

Knowledge Base (contains available functions and their usage):
{json.dumps(knowledge_base, indent=2)}

Return only the executable Python code without any explanations or markdown.
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
