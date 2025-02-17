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
                "L1": "This query requires geographic data that can be extracted using SQL queries.",
                "L2": "This query requires geographic data and advanced spatial analytics, complex processing, or satellite imagery analysis."
            }
            
            # Further classify L1_2 into L1 or L2
            if classification == "L1_2":
                # Keywords suggesting SQL-queryable data (L1)
                l1_keywords = [
                    'count', 'find', 'list', 'show', 'where', 'how many',
                    'nearest', 'closest', 'within', 'distance', 'nearby',
                    'in', 'at', 'located', 'between'
                ]
                
                # Keywords suggesting advanced analytics or satellite imagery (L2)
                l2_keywords = [
                    # Spatial analytics keywords
                    'analyze', 'pattern', 'cluster', 'density', 'distribution',
                    'trend', 'correlation', 'compare', 'relationship', 'impact',
                    'optimize', 'route', 'path', 'coverage', 'heatmap',
                    'concentration', 'spread', 'movement', 'flow', 'network','calculate'
                    
                    # Satellite imagery keywords
                    'satellite', 'aerial', 'image', 'imagery', 'photo',
                    'rooftop', 'solar', 'area', 'measure', 'calculate',
                    'vegetation', 'ndvi', 'land use', 'land cover',
                    'building footprint', 'elevation', 'terrain',
                    'surface', 'height', '3d', 'three dimensional',
                    'shadow', 'roof', 'building'
                ]
                
                # Check query complexity
                query_lower = self.query.lower()
                
                # Count matches for each category
                l1_matches = sum(1 for keyword in l1_keywords if keyword in query_lower)
                l2_matches = sum(1 for keyword in l2_keywords if keyword in query_lower)
                
                # Determine final classification
                if l2_matches > 0:
                    classification = "L2"  # If any L2 keywords are present, classify as L2
                else:
                    classification = "L1"  # Default to L1 if no L2 keywords are found
                
                # Add detailed explanation
                if classification == "L1":
                    explanations["L1"] = "This query requires geographic data that can be retrieved using SQL queries. " \
                                       "The data can be accessed directly from the database without complex processing."
                else:
                    if any(keyword in query_lower for keyword in ['satellite', 'aerial', 'image', 'imagery', 'photo']):
                        explanations["L2"] = "This query requires satellite imagery analysis and advanced processing. " \
                                           "It involves downloading and analyzing satellite/aerial imagery data."
                    else:
                        explanations["L2"] = "This query requires advanced spatial analytics or complex processing. " \
                                           "It may involve patterns, trends, or spatial relationships that need specialized algorithms."
            
            response = {
                "query": self.query,
                "classification": classification,
                "explanation": explanations.get(classification, "Unknown classification type")
            }
            
            # For N and L0 classifications, get direct response from model
            if classification in ["N", "L0"]:
                model_response = self.load_model.get_response(self.query)
                response['response'] = model_response
            elif classification in ["L1", "L2"]:
                # Extract location information
                location_info = result.get('location_info', 'Location information not available')
                response['location_info'] = location_info
                
                # Add processing hints based on classification
                if classification == "L1":
                    response['processing_hint'] = "Use SQL queries to extract data"
                else:  # L2
                    if any(keyword in query_lower for keyword in ['satellite', 'aerial', 'image', 'imagery', 'photo']):
                        response['processing_hint'] = "Requires satellite imagery download and analysis"
                    else:
                        response['processing_hint'] = "Requires spatial analytics or complex processing"
                
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
    from memories.models.load_model import LoadModel
    
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
        "What cafes are within 2km of my current location?",
        "Analyze the distribution of hospitals in Mumbai",
        "Show me the nearest gas station",
        "Calculate the optimal delivery route through Delhi",
        "List all schools in Bangalore",
        "Generate a heatmap of traffic patterns in Chennai",
        "Calculate solar rooftop area for my house",
        "Measure the building height using satellite imagery",
        "Analyze vegetation cover from aerial photos",
        "Calculate the shadow cast by buildings in my neighborhood"
    ]
    
    # Process each query
    for query in test_queries:
        agent = AgentQueryClassification(query, load_model)
        result = agent.process_query()
        print("\n" + "="*50)
        print(f"Query: {result['query']}")
        print(f"Classification: {result['classification']}")
        print(f"Explanation: {result['explanation']}")
        if 'processing_hint' in result:
            print(f"Processing Hint: {result['processing_hint']}")

if __name__ == "__main__":
    main()
