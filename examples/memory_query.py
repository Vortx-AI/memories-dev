"""
Memory query implementation for handling different types of queries.
"""

from typing import Dict, Any, Union, Optional
import logging
import os
from memories.models.load_model import LoadModel
from memories.utils.text.context_utils import classify_query

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryQuery:
    """Memory query handler for processing different types of queries."""
    
    def __init__(
        self,
        model_provider: str = "openai",
        deployment_type: str = "api",
        model_name: str = "gpt-4",
        api_key: Optional[str] = None
    ):
        """
        Initialize the memory query handler with LoadModel.
        
        Args:
            model_provider (str): The model provider (e.g., "openai")
            deployment_type (str): Type of deployment (e.g., "api")
            model_name (str): Name of the model to use
            api_key (Optional[str]): API key for the model provider
        """
        try:
            self.model = LoadModel(
                model_provider=model_provider,
                deployment_type=deployment_type,
                model_name=model_name,
                api_key=api_key
            )
            logger.info(f"Successfully initialized LoadModel with {model_name}")
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
        # Get API key from environment variable or user input
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            api_key = input("Please enter your OpenAI API key: ")
        
        # Initialize memory query with specific model parameters
        memory_query = MemoryQuery(
            model_provider="openai",
            deployment_type="api",
            model_name="gpt-4",
            api_key=api_key
        )
        
        print("\nMemory Query System initialized successfully!")
        print("Type 'exit' to quit the program")
        print("\nExample query types:")
        print("1. Normal (N): 'How do I write a Python function?'")
        print("2. Location without data (L0): 'What is the capital of France?'")
        print("3. Location with data (L1_2): 'Find restaurants near Central Park'")
        
        while True:
            # Get query from user
            query = input("\nEnter your query: ").strip()
            
            # Check if user wants to exit
            if query.lower() == 'exit':
                print("Exiting Memory Query System...")
                break
            
            # Process the query
            if query:
                result = memory_query.process_query(query)
                print(f"\nClassification: {result['classification']}")
                print(f"Response: {result['response']}")
                print(f"Status: {result['status']}")
                if "note" in result:
                    print(f"Note: {result['note']}")
            else:
                print("Please enter a valid query.")

    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    main() 