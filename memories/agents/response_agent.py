from typing import Dict, Any, List, Optional
import pandas as pd

class AgentResponse:
    def __init__(self, query: str):
        """
        Initialize the response agent.
        
        Args:
            query (str): Original user query
        """
        self.query = query
        self.load_model = None  # Will be initialized when needed
    
    def get_response_prompt(self, data: pd.DataFrame, query: str) -> str:
        """
        Generate a prompt for the LLM to create a response.
        
        Args:
            data (pd.DataFrame): Query results
            query (str): Original user query
            
        Returns:
            str: Formatted prompt
        """
        # Convert DataFrame to string representation
        if data is not None and not data.empty:
            data_str = data.to_string()
            data_summary = (
                f"Found {len(data)} results\n"
                f"Columns: {', '.join(data.columns)}\n"
                f"Data Preview:\n{data.head().to_string()}"
            )
        else:
            data_str = "No results found"
            data_summary = "No matching data available"
            
        return f"""
Given the following user query and data results, generate a natural language response that answers the query.
Be concise but informative. Include relevant numbers and statistics when available.

User Query: {query}

Data Summary:
{data_summary}

Full Data:
{data_str}

Please provide a response that:
1. Directly answers the user's query
2. Includes specific details from the data
3. Mentions distances when available
4. Provides context about the locations
5. Is written in a clear, natural style

Response:"""

    def format_response(self, query: str, data: Optional[pd.DataFrame]) -> Dict[str, Any]:
        """
        Format the final response using the LLM.
        
        Args:
            query (str): Original user query
            data (Optional[pd.DataFrame]): Query results
            
        Returns:
            Dict containing the formatted response
        """
        try:
            from memories.llm.load_model import LoadModel
            
            if self.load_model is None:
                self.load_model = LoadModel()
            
            # Generate prompt
            prompt = self.get_response_prompt(data, query)
            
            # Get response from LLM
            response = self.load_model.get_response(prompt)
            
            return {
                "status": "success",
                "query": query,
                "response": response,
                "data": data.to_dict('records') if data is not None and not data.empty else None
            }
            
        except Exception as e:
            return {
                "status": "error",
                "query": query,
                "error": str(e),
                "data": None
            }

    def process_results(self, query: str, results: List[pd.DataFrame]) -> Dict[str, Any]:
        """
        Process query results and generate a response.
        
        Args:
            query (str): Original user query
            results (List[pd.DataFrame]): List of result DataFrames
            
        Returns:
            Dict containing the formatted response
        """
        try:
            # Combine results if multiple DataFrames
            if results:
                if len(results) > 1:
                    combined_data = pd.concat(results, ignore_index=True)
                else:
                    combined_data = results[0]
                
                # Sort by distance if available
                if 'distance_km' in combined_data.columns:
                    combined_data = combined_data.sort_values('distance_km')
            else:
                combined_data = None
            
            # Format and return response
            return self.format_response(query, combined_data)
            
        except Exception as e:
            return {
                "status": "error",
                "query": query,
                "error": str(e),
                "data": None
            }

# Example usage
if __name__ == "__main__":
    # Example query and data
    query = "Find water tanks near Bangalore"
    data = pd.DataFrame({
        'name': ['Tank 1', 'Tank 2'],
        'latitude': [12.9, 12.8],
        'longitude': [77.6, 77.5],
        'distance_km': [1.2, 2.5]
    })
    
    # Create response agent and get response
    agent = AgentResponse(query)
    response = agent.process_results(query, [data])
    print("\nQuery:", query)
    print("\nResponse:", response['response'])
