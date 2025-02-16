from typing import Dict, Any
from dotenv import load_dotenv
import logging
import os
from memories.agents.agent_query_classification import AgentQueryClassification
from memories.agents.agent_context import AgentContext
from memories.agents.agent_L1 import Agent_L1
from memories.core.memory import MemoryStore

# Load environment variables
load_dotenv()

class Agent:
    def __init__(self, query: str, load_model: Any, memory_store: MemoryStore, instance_id: str = None):
        """
        Initialize the Agent system.
        
        Args:
            query (str): The user's query.
            load_model (Any): The initialized model instance.
            memory_store (MemoryStore): The memory store instance.
            instance_id (str, optional): The instance ID for FAISS search.
        """
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        self.query = query
        self.load_model = load_model
        self.memory_store = memory_store
        self.instance_id = instance_id
        
        # Retrieve PROJECT_ROOT from environment variables
        project_root = os.getenv("PROJECT_ROOT")
        if project_root is None:
            raise ValueError("PROJECT_ROOT environment variable is not set")

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a query using the query classification agent and search FAISS if needed.
        
        Args:
            query (str): The user's query.
        
        Returns:
            Dict[str, Any]: The response containing the classification and result.
        """
        try:
            print("\n" + "="*50)
            print("QUERY PROCESSING PIPELINE")
            print("="*50)
            print(f"Input Query: {query}")
            print("="*50)
            
            # Step 1: Query Classification Agent
            print("\n1. Query Classification Agent")
            print("-"*30)
            classification_agent = AgentQueryClassification(query, self.load_model)
            classification_result = classification_agent.process_query()
            
            print(f"Classification: {classification_result.get('classification', '')}")
            print(f"Explanation: {classification_result.get('explanation', '')}")
            
            result = classification_result
            
            # Step 2: Process based on classification
            if result.get('classification') == 'L1':
                print("\n2. L1 Processing - Similar Column Search")
                print("-"*30)
                
                if self.instance_id:
                    # Use Agent_L1 to find similar columns
                    l1_agent = Agent_L1(self.instance_id, query)
                    l1_result = l1_agent.process()
                    
                    if l1_result["status"] == "success":
                        similar_columns = l1_result["similar_columns"]
                        result['similar_columns'] = similar_columns
                        
                        print("\nSimilar columns found:")
                        for col in similar_columns:
                            print(f"\nColumn: {col['column_name']}")
                            print(f"File: {col['file_name']}")
                            print(f"Distance: {col['distance']:.4f}")
                    else:
                        print(f"Error in L1 processing: {l1_result.get('error', 'Unknown error')}")
            
            # Step 3: Context Agent (if needed)
            if result.get('classification') == 'L1_2':
                print("\n3. Context Agent")
                print("-"*30)
                context_agent = AgentContext(query, self.load_model)
                context_result = context_agent.process_query()
                
                print(f"Context Data Type: {context_result.get('data_type', '')}")
                print(f"Location Info: {context_result.get('location_info', '')}")
                
                result.update({
                    'data_type': context_result.get('data_type'),
                    'location_details': context_result.get('location_info')
                })
            
            print("\n" + "="*50)
            print("PROCESSING COMPLETE")
            print("="*50)
            
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
    from memories.models.load_model import LoadModel
    from memories.core.memory import MemoryStore
    from memories.agents.agent_config import get_model_config
    
    # Get input from user
    query = input("Enter your query: ")
    instance_id = input("Enter FAISS instance ID (or press Enter to skip): ")
    
    # Initialize model with get_model_config
    load_model, _ = get_model_config(
        use_gpu=True,
        model_provider="deepseek-ai",
        deployment_type="deployment",
        model_name="deepseek-coder-1.3b-base"
    )
    
    print(f"[Agent] Model initialized")
    
    # Initialize memory store
    memory_store = MemoryStore()
    
    # Initialize and run agent
    agent = Agent(
        query=query, 
        load_model=load_model,
        memory_store=memory_store,
        instance_id=instance_id if instance_id else None
    )
    
    result = agent.run()
    
    # Print results
    print("\nResults:")
    if result.get('similar_columns'):
        print("\nSimilar columns found:")
        for col in result['similar_columns']:
            print(f"\nColumn: {col['column_name']}")
            print(f"File: {col['file_name']}")
            print(f"Distance: {col['distance']:.4f}")
    
    print(f"\nClassification: {result.get('classification', '')}")
    print(f"Explanation: {result.get('explanation', '')}")

if __name__ == "__main__":
    main()

