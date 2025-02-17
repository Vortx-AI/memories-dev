import duckdb
import pandas as pd
from typing import Dict, Any, List, Optional
from memories.utils.earth.duckdb_parquet_queries import (
    nearest_query,
    within_radius_query,
    count_within_radius_query
)

def execute_kb_function(function_name: str, parameters: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """
    Execute a knowledge base function with the given parameters.
    
    Args:
        function_name (str): Name of the function to execute
        parameters (Dict[str, Any]): Parameters for the function
        
    Returns:
        Optional[pd.DataFrame]: Results as a DataFrame, or None if error
    """
    try:
        # Initialize DuckDB connection
        conn = duckdb.connect(database=':memory:')
        
        # Load spatial extension
        conn.execute("INSTALL spatial;")
        conn.execute("LOAD spatial;")
        
        # Get the query based on function name
        query = None
        if function_name == 'nearest_query':
            query = nearest_query(
                parquet_file=parameters['parquet_file'],
                column_name=parameters['column_name'],
                value=parameters['value'],
                target_lat=parameters['target_lat'],
                target_lon=parameters['target_lon'],
                limit=parameters.get('limit', 5)
            )
        elif function_name == 'within_radius_query':
            query = within_radius_query(
                parquet_file=parameters['parquet_file'],
                column_name=parameters['column_name'],
                value=parameters['value'],
                target_lat=parameters['target_lat'],
                target_lon=parameters['target_lon'],
                radius=parameters.get('radius', 5)
            )
        elif function_name == 'count_within_radius_query':
            query = count_within_radius_query(
                parquet_file=parameters['parquet_file'],
                column_name=parameters['column_name'],
                value=parameters['value'],
                target_lat=parameters['target_lat'],
                target_lon=parameters['target_lon'],
                radius=parameters.get('radius', 5)
            )
        else:
            raise ValueError(f"Unknown function: {function_name}")
        
        if query:
            print(f"\nExecuting query:\n{query}")
            # Execute query and return results as DataFrame
            result = conn.execute(query).fetchdf()
            return result
            
    except Exception as e:
        print(f"Error executing {function_name}: {str(e)}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()

def validate_function_inputs(function_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate the input parameters for a function.
    
    Args:
        function_name (str): Name of the function
        parameters (Dict[str, Any]): Parameters to validate
        
    Returns:
        Dict containing validation results
    """
    required_params = {
        'nearest_query': ['parquet_file', 'column_name', 'value', 'target_lat', 'target_lon'],
        'within_radius_query': ['parquet_file', 'column_name', 'value', 'target_lat', 'target_lon', 'radius'],
        'count_within_radius_query': ['parquet_file', 'column_name', 'value', 'target_lat', 'target_lon', 'radius']
    }
    
    if function_name not in required_params:
        return {
            'is_valid': False,
            'error': f"Unknown function: {function_name}"
        }
    
    # Check for missing parameters
    missing_params = [param for param in required_params[function_name] 
                     if param not in parameters]
    
    # Check for extra parameters
    extra_params = [param for param in parameters 
                   if param not in required_params[function_name]]
    
    return {
        'is_valid': len(missing_params) == 0,
        'missing_params': missing_params,
        'extra_params': extra_params
    }

def run_recommended_queries(recommendations: List[Dict[str, Any]]) -> List[pd.DataFrame]:
    """
    Run a list of recommended queries and return their results.
    
    Args:
        recommendations (List[Dict[str, Any]]): List of function recommendations
        
    Returns:
        List[pd.DataFrame]: List of result DataFrames
    """
    results = []
    
    for rec in recommendations:
        function_name = rec['function_name']
        parameters = rec['parameters']
        
        # Validate parameters
        validation = validate_function_inputs(function_name, parameters)
        if validation['is_valid']:
            result = execute_kb_function(function_name, parameters)
            if result is not None:
                results.append(result)
        else:
            print(f"\nInvalid parameters for {function_name}:")
            if validation.get('missing_params'):
                print(f"Missing parameters: {validation['missing_params']}")
            if validation.get('extra_params'):
                print(f"Extra parameters: {validation['extra_params']}")
    
    return results

# Example usage:
if __name__ == "__main__":
    # Example recommendations
    recommendations = [
        {
            'function_name': 'nearest_query',
            'parameters': {
                'parquet_file': '/path/to/file.parquet',
                'column_name': 'communications_dish',
                'value': 'true',
                'target_lat': 12.9093124,
                'target_lon': 77.6078977,
                'limit': 5
            }
        }
    ]
    
    results = run_recommended_queries(recommendations)
    for i, df in enumerate(results, 1):
        print(f"\nResults from query {i}:")
        print(df) 