from typing import Dict, List, Any, Optional
import duckdb
from pathlib import Path
import pandas as pd
from memories.agents.agent_config import get_duckdb_connection

class DuckDBQueryGenerator:
    def __init__(self, parquet_file: str, load_model: Any):
        """
        Initialize DuckDB Query Generator.
        
        Args:
            parquet_file (str): Path to the parquet file
            load_model (Any): LLM model instance
        """
        self.parquet_file = parquet_file
        self.load_model = load_model
        self.table_name = Path(parquet_file).stem
        self.conn = get_duckdb_connection()
        
    def generate_query_code(self, 
                          query: str,
                          column_info: Dict[str, Any],
                          location_info: Optional[Dict[str, Any]] = None) -> str:
        """
        Use LLM to generate Python code for spatial DuckDB query.
        """
        prompt = f"""
Generate Python code that uses an existing DuckDB connection to perform a spatial query. The code should:

Context:
1. User Query: "{query}"
2. Column to Search: {column_info['column_name']}
3. Parquet File: {column_info['file_name']}
4. Location Details: {location_info if location_info else 'Not provided'}

Important Requirements:
1. Use the existing DuckDB connection (passed as 'conn')
2. The parquet file has a 'geom' column with spatial data
3. Use appropriate spatial functions (ST_DWithin, ST_Intersects, etc.)
4. Return results as a pandas DataFrame

Generate complete, working code based on these requirements.
"""
        
        # Get response from LLM
        response = self.load_model.generate_code(prompt)
        
        # Extract code from response
        code = response.strip()
        
        return code
    
    def execute_generated_code(self, code: str) -> pd.DataFrame:
        """
        Execute the LLM-generated code using existing DuckDB connection.
        
        Args:
            code (str): Generated Python code
        """
        try:
            # Create a local namespace with our connection
            local_namespace = {
                'conn': self.conn,
                'pd': pd
            }
            
            # Execute the code
            exec(code, globals(), local_namespace)
            
            # Call the fetch_data function with our connection
            if 'fetch_data' in local_namespace:
                result = local_namespace['fetch_data'](self.conn)
                if isinstance(result, pd.DataFrame):
                    return result
                else:
                    print("Error: fetch_data did not return a DataFrame")
                    return pd.DataFrame()
            else:
                print("Error: fetch_data function not found in generated code")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"Error executing generated code: {str(e)}")
            return pd.DataFrame()
