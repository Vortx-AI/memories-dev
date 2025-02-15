from typing import Dict, Any
from dotenv import load_dotenv
<<<<<<< HEAD:memories_dev/agents/agent.py
=======
import importlib

from memories.agents.agent_query_context import LocationExtractor, QueryContext
from memories.agents.location_filter_agent import LocationFilterAgent
from memories.memories.memories_index import FAISSStorage
from memories.agents.agent_coder import CodeGenerator
from memories.agents.agent_code_executor import AgentCodeExecutor
from memories.agents.response_agent import ResponseAgent
from memories.agents.agent_geometry import AgentGeometry

import os
>>>>>>> de15d751916e940ce5b6cf90cca5baae5ad24350:memories/agents/agent.py
import logging
import os
from memories_dev.agents.agent_query_classification import AgentQueryClassification

# Load environment variables
load_dotenv()

class Agent:
    def __init__(self, query: str, load_model: Any):
        """
        Initialize the Agent system.
        
        Args:
            query (str): The user's query.
            load_model (Any): The initialized model instance.
        """
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        self.query = query
        self.load_model = load_model
        
        # Retrieve PROJECT_ROOT from environment variables
        project_root = os.getenv("PROJECT_ROOT")
        if project_root is None:
            raise ValueError("PROJECT_ROOT environment variable is not set")

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a query using the query classification agent.
        
        Args:
            query (str): The user's query.
        
        Returns:
            Dict[str, Any]: The response containing the classification and result.
        """
        try:
            print("="*50)
            print(f"Starting query processing: {query}")
            print("="*50)
            
            # Initialize and use the query classification agent
            classification_agent = AgentQueryClassification(query, self.load_model)
            result = classification_agent.process_query()
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in process_query: {str(e)}")
            return {
                "query": query,
                "classification": "ERROR",
                "explanation": f"Error: {str(e)}"
            }

    def run(self, query: str = None) -> Dict[str, Any]:
        """
        Run the agent system.
        
        Args:
            query (str, optional): Query string. If None, will use the query from initialization.
        
        Returns:
            Dict[str, Any]: Dictionary containing the response.
        """
        try:
            if query is None:
                query = self.query
            
            return self.process_query(query)
        except Exception as e:
            self.logger.error(f"Error in run: {str(e)}")
            return {
                "query": query, 
                "classification": "ERROR",
                "explanation": f"Error: {str(e)}"
            }

def main():
    """
    Main function to run the agent directly.
    Example usage: python3 agent.py
    """
    from memories_dev.models.load_model import LoadModel
    
    # Load environment variables
    load_dotenv()
    
    # Initialize the model
    load_model = LoadModel(
        use_gpu=True,
        model_provider="deepseek-ai",
        deployment_type="deployment",
        model_name="deepseek-coder-1.3b-base"
    )
    
    # Test different types of queries
    test_queries = [
        "How do I write a Python function?",
        "What is the capital of France?",
        "Find restaurants near Central Park",
        "What cafes are within 2km of my current location?"
    ]
    
    # Initialize and run the agent for each query
    for query in test_queries:
        print("\n" + "="*50)
        print(f"Testing query: {query}")
        
        agent = Agent(query=query, load_model=load_model)
        result = agent.process_query(query)
        
        print("\nResults:")
        print(f"Classification: {result.get('classification', '')}")
        if 'response' in result:
            print(f"Response: {result['response']}")
        elif 'location_info' in result:
            print(f"Location Info: {result['location_info']}")
        print(f"Explanation: {result.get('explanation', '')}")

if __name__ == "__main__":
    main()

