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
        
        # Initialize load_model
        from memories.models.load_model import LoadModel
        self.load_model = LoadModel(
            use_gpu=True,
            model_provider="deepseek-ai",
            deployment_type="deployment",
            model_name="deepseek-coder-1.3b-base"
        )
        
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
            
            # Step 1: Classify the query using AgentContext
            print("\n🔍 CLASSIFYING QUERY")
            print("---------------------------")
            from memories.agents.agent_context import AgentContext, LocationExtractor
            context_agent = AgentContext()
            classification_result = context_agent.classify_query(query)
            print(f"Query Classification: {classification_result}")

            print("Classification Agent Response:")
            print(f"• Classification: {classification_result.get('classification', '')}")
            print(f"• Explanation: {classification_result.get('explanation', '')}")
            if 'processing_hint' in classification_result:
                print(f"• Processing Hint: {classification_result.get('processing_hint', '')}")

            # If classification is L1_2, extract detailed location info
            if classification_result.get('classification') in ['L1', 'L1_2','L2']:
                print("\n🔍 EXTRACTING LOCATION DETAILS")
                print("---------------------------")
                location_extractor = LocationExtractor(self.load_model)
                location_details = location_extractor.extract_query_info(query)
                print("Location Details:")
                print(f"• Data Type: {location_details.get('data_type', '')}")
                if location_details.get('location_info'):
                    loc_info = location_details['location_info']
                    print(f"• Location: {loc_info.get('location', '')}")
                    print(f"• Location Type: {loc_info.get('location_type', '')}")
                    
                    # Normalize the location
                    normalized = location_extractor.normalize_location(
                        loc_info.get('location', ''),
                        loc_info.get('location_type', '')
                    )
                    print("\nNormalized Location:")
                    print(normalized)
                    
                    # Add location details to classification result
                    classification_result['location_details'] = location_details
                    classification_result['normalized_location'] = normalized
            
            return classification_result
            
        except Exception as e:
            self.logger.error(f"Error in process_query: {str(e)}")
            return {
                "error": str(e),
                "classification": None,
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

