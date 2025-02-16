from typing import Dict, Any
from dotenv import load_dotenv
import logging
import os
from memories.agents.agent_query_classification import AgentQueryClassification
from memories.agents.agent_context import AgentContext
from memories.agents.agent_L1 import Agent_L1
from memories.agents.agent_analyst import AgentAnalyst
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
        Process a query using multiple agents.
        """
        try:
            print("\n" + "="*80)
            print("QUERY PROCESSING PIPELINE")
            print("="*80)
            print(f"Input Query: {query}")
            print("="*80)
            
            # Step 1: Query Classification Agent
            print("\n[Invoking Query Classification Agent]")
            print("-"*50)
            classification_agent = AgentQueryClassification(query, self.load_model)
            classification_result = classification_agent.process_query()
            
            print("Classification Agent Response:")
            print(f"• Classification: {classification_result.get('classification', '')}")
            print(f"• Explanation: {classification_result.get('explanation', '')}")
            if 'processing_hint' in classification_result:
                print(f"• Processing Hint: {classification_result.get('processing_hint', '')}")
            
            result = classification_result
            
            # Step 2: Context Agent (for both L1 and L1_2)
            if result.get('classification') in ['L1', 'L1_2']:
                print("\n[Invoking Context Agent]")
                print("-"*50)
                context_agent = AgentContext(query, self.load_model)
                context_result = context_agent.process_query()
                
                print("Context Agent Response:")
                print(f"• Data Type: {context_result.get('data_type', '')}")
                print(f"• Location Info: {context_result.get('location_info', '')}")
                
                result.update({
                    'data_type': context_result.get('data_type'),
                    'location_details': context_result.get('location_info')
                })
            
            # Step 3: L1 Agent (if classification is L1)
            if result.get('classification') == 'L1':
                print("\n[Invoking L1 Agent - Similar Column Search]")
                print("-"*50)
                
                if self.instance_id and result.get('data_type'):
                    # Use only the data type for column search
                    search_term = result['data_type']
                    l1_agent = Agent_L1(self.instance_id, search_term)
                    l1_result = l1_agent.process()
                    
                    print("L1 Agent Response:")
                    if l1_result["status"] == "success":
                        similar_columns = l1_result["similar_columns"]
                        result['similar_columns'] = similar_columns
                        
                        print(f"\n• Searching columns for data type: {search_term}")
                        print("\n• Similar columns found:")
                        for col in similar_columns:
                            print(f"\n  Column: {col['column_name']}")
                            print(f"  File: {col['file_name']}")
                            print(f"  Distance: {col['distance']:.4f}")
                        
                        # Step 4: Analyst Agent (only for L1 after successful column search)
                        print("\n[Invoking Agent Analyst]")
                        print("-"*50)
                        analyst = AgentAnalyst(self.load_model)
                        
                        # Use the best matching column (first in the list)
                        best_column = similar_columns[0]
                        analyst_result = analyst.analyze_query(
                            query=query,
                            column_info=best_column,
                            location_info=result.get('location_details')
                        )
                        
                        if analyst_result["status"] == "success":
                            result.update({
                                'generated_code': analyst_result['generated_code'],
                                'query_results': analyst_result['results'],
                                'row_count': analyst_result['row_count']
                            })
                            
                            print("\nAnalyst Agent Response:")
                            print(f"• Generated Code:\n{analyst_result['generated_code']}")
                            print(f"\n• Query Results:")
                            print(analyst_result['results'])
                            print(f"\n• Total Rows: {analyst_result['row_count']}")
                        else:
                            print(f"• Error in Analyst: {analyst_result.get('error', 'Unknown error')}")
                    else:
                        print(f"• Error in L1: {l1_result.get('error', 'Unknown error')}")
            
            print("\n" + "="*80)
            print("FINAL PROCESSING RESULT")
            print("="*80)
            print(f"• Query: {result.get('query', '')}")
            print(f"• Classification: {result.get('classification', '')}")
            print(f"• Explanation: {result.get('explanation', '')}")
            
            if 'data_type' in result:
                print(f"\n• Data Type: {result['data_type']}")
                print(f"• Location Details: {result.get('location_details', '')}")
            
            if 'similar_columns' in result:
                print("\n• Similar Columns:")
                for col in result['similar_columns']:
                    print(f"  - {col['column_name']} ({col['file_name']})")
            
            if 'query_results' in result:
                print("\n• Query Results:")
                print(result['query_results'])
                print(f"\n• Total Rows: {result['row_count']}")
            
            print("="*80)
            
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
    
    agent.run()

if __name__ == "__main__":
    main()

