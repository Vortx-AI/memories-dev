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
                
                # Extract latitude and longitude from the 'location_info' output.
                # Expected format:
                # {'location': '12.9093124,77.6078977', 'location_type': 'coordinates', 
                #  'normalized': {'original': '12.9093124,77.6078977', 'type': 'coordinates', 
                #                 'coordinates': {'lat': 12.9093124, 'lon': 77.6078977}}}
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
                    'latitude': lat_val,    # extracted from nested "location_info"
                    'longitude': lon_val    # extracted from nested "location_info"
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
                    if l1_result["status"] == "success":
                        similar_columns = l1_result["similar_columns"]
                        result['similar_columns'] = similar_columns
                        
                        print(f"\n• Searching columns for data type: {search_term}")
                        print("\n• Similar columns found:")
                        for col in similar_columns:
                            print(f"\n  Column: {col['column_name']}")
                            print(f"  File: {col['file_name']}")
                            print(f"  File Path: {col['file_path']}")
                            print(f"  Geometry Type: {col['geometry_type']}")
                            print(f"  Data Type: {col['data_type']}")
                            print(f"  Distance: {col['distance']:.4f}")
                        
                        # Use the extracted latitude and longitude from the Context Agent.
                        lat_val = result.get('latitude', 0.0)
                        lon_val = result.get('longitude', 0.0)
    
                        # Use the previously retrieved data_type.
                        data_type = result.get('data_type', '')
    
                        # Get the Parquet file information from the best matching column.
                        best_column = similar_columns[0]
                        raw_file_path = best_column.get('file_path', '')
    
                        # Construct the full Parquet file path if the provided file_path is not absolute.
                        if not os.path.isabs(raw_file_path):
                            project_root = os.getenv("PROJECT_ROOT", "")
                            parquet_file_path = os.path.join(project_root, "data", "parquet", raw_file_path)
                        else:
                            parquet_file_path = raw_file_path
    
                        print("\n[Invoking Agent Analyst]")
                        print("-" * 50)
                        analyst = AgentAnalyst(self.load_model)
                        relevant_column = best_column.get('column_name', '')
                        analyst_result = analyst.analyze_query(
                            query=query,
                            lat=lat_val,
                            lon=lon_val,
                            data_type=data_type,
                            parquet_file=parquet_file_path,
                            relevant_column=relevant_column,
                            geometry_column='geometry',
                            geometry_type='POINT',
                            extra_params={}
                        )

                        print(analyst_result)
                        
                        # Execute recommended functions
                        if analyst_result.get('status') == 'success':
                            print("\n[Executing Recommended Functions]")
                            print("-" * 50)
                            
                            combined_results = []
                            for recommendation in analyst_result.get('recommendations', []):
                                function_name = recommendation.get('function_name')
                                parameters = recommendation.get('parameters', {})
                                
                                # Set a default radius if not specified
                                if 'radius' in parameters and parameters['radius'] == 'specify_radius':
                                    parameters['radius'] = 1000  # Default 1km radius
                                
                                # Convert lat/lon to float if they're strings
                                if 'target_lat' in parameters:
                                    parameters['target_lat'] = float(parameters['target_lat'])
                                if 'target_lon' in parameters:
                                    parameters['target_lon'] = float(parameters['target_lon'])
                                
                                print(f"\nExecuting {function_name}:")
                                print(f"Parameters: {parameters}")
                                
                                try:
                                    # Validate inputs first
                                    validation = validate_function_inputs(function_name, parameters)
                                    if validation["is_valid"]:
                                        # Execute the function
                                        results = execute_kb_function(function_name, parameters)
                                        if isinstance(results, pd.DataFrame):
                                            # Add a column to indicate which function produced these results
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
                            
                            # Combine all results into a single DataFrame
                            if combined_results:
                                final_results = pd.concat(combined_results, ignore_index=True)
                                result['query_results'] = final_results
                                print("\nFinal Results:")
                                print(f"Total records found: {len(final_results)}")
                            else:
                                result['query_results'] = pd.DataFrame()
                                print("\nNo results found from any function")
            
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

