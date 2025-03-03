"""
Memory query implementation for handling different types of queries.
"""

from typing import Dict, Any, Union
import logging
from memories.models.load_model import LoadModel
from memories.utils.text.context_utils import classify_query

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryQuery:
    """Memory query handler for processing different types of queries."""
    
    def __init__(self):
        """Initialize the memory query handler with LoadModel."""
        try:
            self.model = LoadModel()
            logger.info("Successfully initialized LoadModel")
        except Exception as e:
            logger.error(f"Failed to initialize LoadModel: {e}")
            raise

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a query by classifying it and generating appropriate response.
        
        Args:
            query (str): The user's query
            
        Returns:
            Dict containing classification and response
        """
        try:
            # First classify the query
            classification_result = classify_query(query, self.model)
            query_type = classification_result.get("classification", "N")
            
            logger.info(f"Query classified as: {query_type}")
            
            # Handle based on classification
            if query_type in ["N", "L0"]:
                # For N and L0, get direct response from model
                response = self.model.get_response(query)
                return {
                    "classification": query_type,
                    "response": response,
                    "status": "success"
                }
            elif query_type == "L1_2":
                # For L1_2, currently just get response (will be updated later)
                response = self.model.get_response(query)
                return {
                    "classification": "L1_2",
                    "response": response,
                    "status": "success",
                    "note": "Location-based processing will be enhanced later"
                }
            else:
                return {
                    "classification": "unknown",
                    "response": "Unsupported query type",
                    "status": "error"
                }
                
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "classification": "error",
                "response": f"Error processing query: {str(e)}",
                "status": "error"
            }

def main():
    """Main function to demonstrate memory query usage."""
    try:
        # Initialize memory query
        memory_query = MemoryQuery()
        
        # Example queries
        example_queries = [
            "What is the capital of France?",  # L0
            "How do I write a Python function?",  # N
            "Find restaurants near Central Park"  # L1_2
        ]
        
        # Process each query
        for query in example_queries:
            print(f"\nProcessing query: {query}")
            result = memory_query.process_query(query)
            print(f"Classification: {result['classification']}")
            print(f"Response: {result['response']}")
            print(f"Status: {result['status']}")
            if "note" in result:
                print(f"Note: {result['note']}")

    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    main() 