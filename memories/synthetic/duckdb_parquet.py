
Generate complete, working code based on these requirements.
"""
        
        # Get response from LLM
        response = self.load_model.generate_code(prompt)
        
        # Extract code from response
        code = response.strip()
        
        return code
    
    def execute_generated_code(self, code: str) -> pd.DataFrame:
        """
        Execute the LLM-generated code and return results.
        
        Args:
            code (str): Generated Python code
        """
        try:
            # Create a local namespace for execution
            local_namespace = {}
            
            # Execute the code
            exec(code, globals(), local_namespace)
            
            # Call the fetch_data function
            if 'fetch_data' in local_namespace:
                result = local_namespace['fetch_data']()
                return result
            else:
                print("Error: fetch_data function not found in generated code")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"Error executing generated code: {str(e)}")
            return pd.DataFrame()

def main():
    """Example usage of DuckDBQueryGenerator with LLM"""
    from memories.models.load_model import LoadModel
    
    # Initialize model
    load_model = LoadModel()
    
    # Example inputs
    parquet_file = "/path/to/india_points_processed.parquet"
    query = "find hospitals near bangalore"
    column_info = {
        "column_name": "services",
        "file_name": "india_points_processed.parquet",
        "distance": 0.7762
    }
    location_info = {
        "location": "bangalore",
        "coordinates": [12.9716, 77.5946],
        "radius": 5000
    }
    
    # Initialize generator
    generator = DuckDBQueryGenerator(parquet_file, load_model)
    
    # Generate code
    print("\nGenerating Python Code...")
    code = generator.generate_query_code(query, column_info, location_info)
    print("\nGenerated Code:")
    print(code)
    
    # Execute code
    print("\nExecuting Generated Code:")
    results = generator.execute_generated_code(code)
    print("\nResults:")
    print(results)

if __name__ == "__main__":
    main()