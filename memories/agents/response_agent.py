from typing import Dict, Any, List
import pandas as pd

class AgentResponse:
    def __init__(self, query: str, load_model: Any):
        """
        Initialize the Response Agent.
        
        Args:
            query (str): The original user query
            load_model (Any): The model instance for generating responses
        """
        self.query = query
        self.load_model = load_model

    def process_results(self, query: str, combined_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process the combined results and generate a natural language response.
        
        Args:
            query (str): The original user query
            combined_results (List[Dict]): List of results from different queries
            
        Returns:
            Dict containing the response and status
        """
        try:
            # Extract all results into a list
            all_results = []
            for result_set in combined_results:
                source_function = result_set.get('source_function', '')
                data_type = result_set.get('data_type', '')
                results = result_set.get('results', [])
                
                for item in results:
                    item['source_function'] = source_function
                    item['data_type'] = data_type
                    all_results.append(item)
            
            if not all_results:
                return {
                    "status": "success",
                    "response": "No results found matching your query."
                }
            
            # Convert to DataFrame for easier processing
            results_df = pd.DataFrame(all_results)
            
            # Generate response based on results
            response = self._generate_response(query, results_df)
            
            return {
                "status": "success",
                "response": response
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def _generate_response(self, query: str, results_df: pd.DataFrame) -> str:
        """
        Generate a natural language response from the results.
        
        Args:
            query (str): The original user query
            results_df (pd.DataFrame): DataFrame containing all results
            
        Returns:
            str: Natural language response
        """
        try:
            num_results = len(results_df)
            
            # Basic response template
            response_parts = []
            
            # Add summary of results found
            response_parts.append(f"Found {num_results} result{'s' if num_results != 1 else ''} matching your query.")
            
            # Add details about each result
            for idx, row in results_df.iterrows():
                details = []
                
                # Add name if available
                if 'name' in row and pd.notna(row['name']):
                    details.append(f"name: {row['name']}")
                
                # Add address if available
                if 'address' in row and pd.notna(row['address']):
                    details.append(f"address: {row['address']}")
                
                # Add distance if available
                if 'distance_km' in row and pd.notna(row['distance_km']):
                    distance = round(row['distance_km'], 2)
                    details.append(f"distance: {distance} km")
                
                if details:
                    response_parts.append(f"• {', '.join(details)}")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            return f"Error generating response: {str(e)}"

def main():
    """Example usage of the Response Agent."""
    # Example data
    query = "find water tanks near me"
    combined_results = [
        {
            "source_function": "nearest_query",
            "data_type": "water",
            "results": [
                {
                    "name": "Water Tank 1",
                    "distance_km": 0.5,
                    "address": "123 Main St"
                },
                {
                    "name": "Water Tank 2",
                    "distance_km": 1.2,
                    "address": "456 Oak Ave"
                }
            ]
        }
    ]
    
    # Initialize agent
    agent = AgentResponse(query, None)
    
    # Process results
    response = agent.process_results(query, combined_results)
    print(response)

if __name__ == "__main__":
    main()
