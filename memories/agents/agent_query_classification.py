from typing import Dict, Any
from memories.utils.earth.query_classification import classify_query

class AgentQueryClassification:
    def __init__(self, query: str, load_model: Any):
        """
        Initialize the Query Classification Agent.
        
        Args:
            query (str): The user's query
            load_model (Any): The initialized model instance
        """
        self.query = query
        self.load_model = load_model

    def process_query(self) -> Dict[str, Any]:
        """
        Process the query and classify it into appropriate category.
        
        Returns:
            Dict[str, Any]: Dictionary containing the query, classification and explanation
        """
        try:
            # Get the classification
            result = classify_query(self.query, self.load_model)
            
            # Extract classification from result
            classification = result.get('classification', 'N')  # Default to 'N' if not found
            
            # Prepare explanation based on classification
            explanations = {
                "N": "This query has no location component and can be answered by a general AI model.",
                "L0": "This query has location references but can be answered without additional geographic data.",
                "L1_2": "This query has location components and requires additional geographic data to provide an accurate response."
            }
            
            response = {
                "query": self.query,
                "classification": classification,
                "explanation": explanations.get(classification, "Unknown classification type")
            }
            
            # Add response or location_info based on what's in the result
            if 'response' in result:
                response['response'] = result['response']
            elif 'location_info' in result:
                response['location_info'] = result['location_info']
                
            return response
            
        except Exception as e:
            return {
                "query": self.query,
                "classification": "ERROR",
                "explanation": f"Error during classification: {str(e)}"
            }

def main():
    """
    Example usage of the Query Classification Agent
    """
    from memories_dev.models.load_model import LoadModel
    
    # Initialize the model
    load_model = LoadModel(
        use_gpu=True,
        model_provider="deepseek-ai",
        deployment_type="deployment",
        model_name="deepseek-coder-1.3b-base"
    )
    
    # Test queries
    test_queries = [
        "What is the weather like?",
        "What is the capital of France?",
        "Find restaurants near Central Park",
        "How do I write a Python function?",
        "What cafes are within 2km of my current location?"
    ]
    
    # Process each query
    for query in test_queries:
        agent = AgentQueryClassification(query, load_model)
        result = agent.process_query()
        print("\n" + "="*50)
        print(f"Query: {result['query']}")
        print(f"Classification: {result['classification']}")
        print(f"Explanation: {result['explanation']}")

if __name__ == "__main__":
    main()
