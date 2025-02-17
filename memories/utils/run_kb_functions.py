import json
import duckdb
import os
from typing import Dict, Any, Optional
from memories.utils.earth.geocode import create_spatial_query, compute_spatial_distance, create_point_geometry

def load_kb() -> Dict:
    """
    Load the DuckDB Parquet knowledge base
    
    Returns:
        Dict: The loaded knowledge base
    """
    kb_path = os.path.join(os.path.dirname(__file__), "earth", "duckdb_parquet_kb.json")
    with open(kb_path, 'r') as f:
        return json.load(f)

def list_available_functions() -> None:
    """Print all available functions in the knowledge base with their details"""
    kb = load_kb()
    print("\nAvailable functions in knowledge base:")
    for query in kb['queries']:
        print(f"\nQuery: {query['name']}")
        print(f"Function: {query.get('function', 'No function name')}")
        print(f"Required inputs: {query['inputs_required']}")
        if 'function_call' in query:
            print(f"Function call template: {query['function_call']}")

def execute_kb_function(function_name: str, input_params: dict) -> Optional[Any]:
    """
    Execute a function from the knowledge base using its name and input parameters
    
    Args:
        function_name (str): Name of the function to execute (e.g., 'exact_match_query')
        input_params (dict): Dictionary of input parameters for the function
    
    Returns:
        Optional[Any]: Query results as a pandas DataFrame, or None if execution fails
    
    Raises:
        ValueError: If the function is not found in the knowledge base
        Exception: If there's an error during query execution
    """
    try:
        # Load the knowledge base
        kb = load_kb()
        
        # Find the query definition that matches the function name
        query_def = next((q for q in kb['queries'] if q['function'] == function_name), None)
        if not query_def:
            raise ValueError(f"Function '{function_name}' not found in knowledge base")
        
        # Validate required parameters
        required_params = set(query_def['inputs_required'].keys())
        provided_params = set(input_params.keys())
        missing_params = required_params - provided_params
        if missing_params:
            raise ValueError(f"Missing required parameters: {missing_params}")
        
        # Import required modules (if specified)
        if 'imports_required' in query_def:
            for import_stmt in query_def['imports_required']:
                exec(import_stmt)
        
        # Execute the SQL query
        query = query_def['code_to_execute'].format(**input_params)
        result = duckdb.sql(query)
        return result.df()
    
    except Exception as e:
        print(f"Error executing function {function_name}: {str(e)}")
        raise

def validate_function_inputs(function_name: str, input_params: dict) -> Dict[str, Any]:
    """
    Validate the input parameters for a given function
    
    Args:
        function_name (str): Name of the function to validate inputs for
        input_params (dict): Dictionary of input parameters to validate
    
    Returns:
        Dict[str, Any]: Dictionary containing validation results
        
    Raises:
        ValueError: If the function is not found in the knowledge base
    """
    kb = load_kb()
    query_def = next((q for q in kb['queries'] if q['function'] == function_name), None)
    if not query_def:
        raise ValueError(f"Function '{function_name}' not found in knowledge base")
    
    required_params = set(query_def['inputs_required'].keys())
    provided_params = set(input_params.keys())
    
    return {
        "is_valid": required_params.issubset(provided_params),
        "missing_params": required_params - provided_params,
        "extra_params": provided_params - required_params,
        "required_params": required_params,
        "function_details": query_def
    }

if __name__ == "__main__":
    # Example usage
    try:
        # List all available functions
        list_available_functions()
        
        # Example: Execute an exact match query
        function_name = "exact_match_query"
        params = {
            'parquet_file': '/path/to/data.parquet',
            'column_name': 'city',
            'value': 'New York'
        }
        
        # Validate inputs first
        validation_result = validate_function_inputs(function_name, params)
        if validation_result["is_valid"]:
            results = execute_kb_function(function_name, params)
            print("\nQuery Results:")
            print(results)
        else:
            print("\nInvalid inputs:")
            print(f"Missing parameters: {validation_result['missing_params']}")
            print(f"Extra parameters: {validation_result['extra_params']}")
            
    except Exception as e:
        print(f"Error in example execution: {str(e)}")
