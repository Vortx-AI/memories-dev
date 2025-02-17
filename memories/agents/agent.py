from typing import Dict, Any
from dotenv import load_dotenv
import logging
import os
from memories.agents.agent_query_classification import AgentQueryClassification
from memories.agents.agent_context import AgentContext
from memories.agents.agent_L1 import Agent_L1
from memories.agents.agent_analyst import AgentAnalyst
from memories.core.memory import MemoryStore
from memories.utils.duckdb_queries import DuckDBQueryGenerator
import pandas as pd
from memories.agents.agent_code_executor import AgentCodeExecutor
from memories.utils.run_kb_functions import execute_kb_function, validate_function_inputs

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
                print(context_result)
                print(f"• Data Type: {context_result.get('data_type', '')}")
                
                # Extract location info
                location_info = context_result.get('location_info', {})
                lat_val, lon_val = 0.0, 0.0
                if isinstance(location_info, dict):
                    normalized = location_info.get('normalized', {})
                    coordinates = normalized.get('coordinates', {})
                    if isinstance(coordinates, dict):
                        lat_val = coordinates.get('lat', 0.0)
                        lon_val = coordinates.get('lon', 0.0)
                
                print(f"• Latitude: {lat_val}")
                print(f"• Longitude: {lon_val}")
                
                result.update({
                    'data_type': context_result.get('data_type'),
                    'latitude': lat_val,
                    'longitude': lon_val
                })
            
            # Step 3: L1 Agent (if classification is L1)
            if result.get('classification') == 'L1':
                print("\n[Invoking L1 Agent - Similar Column Search]")
                print("-" * 50)
                
                if self.instance_id and result.get('data_type'):
                    # Use only the data type for column search
                    search_term = result['data_type']
                    l1_agent = Agent_L1(self.instance_id, search_term)
                    l1_result = l1_agent.process()
                    
                    print("L1 Agent Response:")
                    print(f"\n• Searching columns for data type: {search_term}")
                    
                    if l1_result["status"] == "success":
                        similar_columns = l1_result.get("similar_columns", [])
                        result['similar_columns'] = similar_columns
                        
                        if similar_columns:
                            print("\n• Similar columns found:")
                            for col in similar_columns:
                                print(f"\n  Column: {col['column_name']}")
                                print(f"  File: {col['file_name']}")
                                print(f"  File Path: {col['file_path']}")
                                print(f"  Geometry Type: {col['geometry_type']}")
                                print(f"  Data Type: {col['data_type']}")
                                print(f"  Distance: {col['distance']:.4f}")
                            
                            # Only proceed with query generation if we found similar columns
                            best_column = similar_columns[0]  # Get the most similar column
                            parquet_file_path = best_column['file_path']
                            
                            # Generate and execute queries
                            if lat_val and lon_val:
                                print("\n[Generating and Executing Queries]")
                                print("-" * 50)
                                
                                # Create query generator
                                query_generator = DuckDBQueryGenerator(
                                    parquet_file=parquet_file_path,
                                    column_name=best_column['column_name'],
                                    target_lat=lat_val,
                                    target_lon=lon_val
                                )
                                
                                # Get recommended queries
                                recommended_queries = query_generator.get_recommended_queries()
                                result['recommended_queries'] = recommended_queries
                                
                                # Execute queries and combine results
                                combined_results = []
                                
                                for function_name, parameters in recommended_queries.items():
                                    # Convert string coordinates to float if needed
                                    if 'target_lat' in parameters:
                                        parameters['target_lat'] = float(parameters['target_lat'])
                                    if 'target_lon' in parameters:
                                        parameters['target_lon'] = float(parameters['target_lon'])
                                    
                                    print(f"\nExecuting {function_name}:")
                                    print(f"Parameters: {parameters}")
                                    
                                    try:
                                        validation = validate_function_inputs(function_name, parameters)
                                        if validation["is_valid"]:
                                            results = execute_kb_function(function_name, parameters)
                                            if isinstance(results, pd.DataFrame):
                                                results['source_function'] = function_name
                                                combined_results.append(results)
                                                print(f"Found {len(results)} results")
                                            else:
                                                print(f"Unexpected result type: {type(results)}")
                                        else:
                                            print(f"Invalid inputs for {function_name}:")
                                            print(f"Missing parameters: {validation['missing_params']}")
                                            print(f"Extra parameters: {validation['extra_params']}")
                                    except Exception as e:
                                        print(f"Error executing {function_name}: {str(e)}")
                                
                                if combined_results:
                                    final_results = pd.concat(combined_results, ignore_index=True)
                                    result['query_results'] = final_results
                                    print("\nFinal Results:")
                                    print(f"Total records found: {len(final_results)}")
                                else:
                                    result['query_results'] = pd.DataFrame()
                                    print("\nNo results found from any function")
                        else:
                            print(f"\n• {l1_result.get('message', 'No similar columns found')}")
                            result['query_results'] = pd.DataFrame()
                    else:
                        print(f"\n• Error: {l1_result.get('error', 'Unknown error in L1 Agent')}")
                        result['query_results'] = pd.DataFrame()
                
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
    query = "find water tanks near 12.9093124,77.6078977"
    #input("Enter your query: ")
    instance_id = "123937239372432"
    #input("Enter FAISS instance ID (or press Enter to skip): ")
    
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

