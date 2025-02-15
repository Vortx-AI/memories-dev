from typing import Dict, Any, List
from dotenv import load_dotenv
import importlib

from memories.agents.agent_query_context import LocationExtractor, QueryContext
from memories.agents.location_filter_agent import LocationFilterAgent
from memories.core.memories_index import FAISSStorage
from memories.agents.agent_coder import CodeGenerator
from memories.agents.agent_code_executor import AgentCodeExecutor
from memories.agents.response_agent import ResponseAgent
from memories.agents.agent_geometry import AgentGeometry

import os
import logging
import torch
import gc

# Load environment variables
load_dotenv()

class Agent:
    def __init__(self, modalities: Dict[str, Dict[str, List[str]]], query: str = None, memories: Dict[str, Any] = None):
        """
        Initialize the Multi-Agent system with all required agents.
        
        Args:
            modalities (Dict[str, Dict[str, List[str]]]): Nested memories structured as {modality: {table: [columns]}}
            query (str, optional): The user's query.
            memories (Dict[str, Any], optional): Memory data.
        """
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        self.modalities = modalities
        self.query = query
        self.memories = memories or {}
        
        # Retrieve PROJECT_ROOT from environment variables
        project_root = os.getenv("PROJECT_ROOT")
        if project_root is None:
            raise ValueError("PROJECT_ROOT environment variable is not set")
        
        # Define the offload_folder path (handled internally in CodeGenerator)
        # Hence, no need to define it here unless other agents require it
        
        # Initialize agents
        self.agents = {
            "context": LocationExtractor(),
            "filter": LocationFilterAgent(),
            "coder": CodeGenerator(),  # No parameters passed
            "executor": AgentCodeExecutor(),
            "response": ResponseAgent(),
            "query_context": QueryContext(),
            "geometry_agent": AgentGeometry()
        }

    def _cleanup_memory(self):
        """Clean up GPU and CPU memory after model execution."""
        try:
            # Clear PyTorch's CUDA cache
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Force garbage collection
            gc.collect()
            
            self.logger.debug("Memory cleanup completed")
        except Exception as e:
            self.logger.warning(f"Memory cleanup warning: {str(e)}")
    
    def process_query(self, query: str, memories: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a query using the agents.
        
        Args:
            query (str): The user's query.
            memories (Dict[str, Any]): Memory data.
        
        Returns:
            Dict[str, Any]: The response containing fields, code, execution result, and final response.
        """
        try:
            print("="*50)
            print(f"Starting query processing: {query}")
            print("="*50)
            
            # Step 1: Extract location using LocationExtractor with up to 5 attempts.
            max_attempts = 5
            attempt = 0
            location = ""
            location_type = ""
            while attempt < max_attempts:
                print(f"\n🔍 INVOKING LOCATION EXTRACTOR, Attempt {attempt+1}")
                location_info = self.agents["context"].process_query(query)
                print(f"Extracted Location Info: {location_info}")
                location, location_type = self._parse_location_info(location_info)
                
                if location:  # Successfully extracted location
                    break
                attempt += 1
            
            if not location:
                print("No location found after 5 attempts.")
                return {
                    "fields": [],
                    "code": "",
                    "execution_result": None,
                    "response": "No location found"
                }
            
            # Step 2: Get geometries using AgentGeometry
            print("\n🌍 INVOKING GEOMETRY AGENT")
            print("---------------------------")
            geometry_info = self.agents["geometry_agent"].process_location(location_info)
            print(f"Found {len(geometry_info.get('features', []))} geometries")
            
            # Step 3: Generate code using CodeGenerator
            print("\n🔍 INVOKING CODE GENERATOR")
            print("---------------------------")
            generated_code = self.agents["coder"].process_query(query, memories)
            print(f"Generated Code:\n{generated_code}")
            
            # Step 4: Execute the generated code
            print("\n🔍 EXECUTING GENERATED CODE")
            print("---------------------------")
            execution_result = self.agents["executor"].execute_code(generated_code)
            print(f"Execution Result: {execution_result}")
            
            # Step 5: Format the final response using ResponseAgent
            print("\n🔍 FORMATTING RESPONSE")
            print("---------------------------")
            final_response = self.agents["response"].format_response(query, execution_result)
            print(f"Final Response: {final_response}")
            
            response = {
                "query": query,
                "location": location_info,
                "geometry": geometry_info,
                "code": generated_code,
                "execution_result": execution_result,
                "response": final_response
            }
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in process_query: {str(e)}")
            return {
                "fields": [],
                "code": "",
                "execution_result": None,
                "response": f"Error: {str(e)}"
            }
    
    def _parse_location_info(self, location_info: Dict[str, Any]) -> (str, str):
        """Parse the location information dictionary."""
        try:
            location = location_info.get('location', '').strip()
            location_type = location_info.get('location_type', '').strip()
            return location, location_type
        except Exception as e:
            self.logger.error(f"Error parsing location info: {str(e)}")
            return "", "unknown"

    def run(self, query: str = None, memories: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run the multi-agent system.
        
        Args:
            query (str, optional): Query string. If None, will prompt for input.
            memories (Dict[str, Any], optional): Dictionary containing memory data from EarthMemoryStore.
        
        Returns:
            Dict[str, Any]: Dictionary containing the final response.
        """
        try:
            if query is None:
                query = input("\nQuery: ")
            if memories is None:
                memories = {}
            
            return self.process_query(query, memories)
        except Exception as e:
            self.logger.error(f"Error in run: {str(e)}")
            return {"fields": [], "code": "", "execution_result": None, "response": ""}

def main():
    """
    Main function to run the agent directly.
    Example usage: python3 agent.py
    """
    # Load environment variables
    load_dotenv()
    
    # Define memories configuration
    memories = {
        'landuse': {
            'india_landuse': ['id', 'landuse', 'geometry']
        }
    }
    
    # Define the query
    query = "Find parks near 12.911935, 77.611699"
    
    # Initialize and run the agent
    agent = Agent(
        modalities=memories,
        query=query,
        memories=memories
    )
    
    insights = agent.process_query(query=query, memories=memories)
    
    # Print insights
    print("\nQuery Results:")
    print("="*50)
    print(f"Fields: {insights.get('fields', [])}")
    print("\nGenerated Code:")
    print("-"*50)
    print(insights.get('code', ''))
    print("\nExecution Result:")
    print("-"*50)
    print(insights.get('execution_result', ''))
    print("\nFinal Response:")
    print("-"*50)
    print(insights.get('response', ''))

if __name__ == "__main__":
    main()

