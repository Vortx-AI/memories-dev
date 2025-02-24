"""
Multi-agent system coordinator for the memories system.
"""

from typing import Dict, Any, List, Optional, Callable, Set
from dotenv import load_dotenv
import importlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
import os
import logging
import torch
import gc

from memories.models.load_model import LoadModel
from memories.agents.query_understanding_agent import LocationExtractor, QueryContext
from memories.agents.location_processing_agent import LocationProcessingAgent
from memories.agents.code_generation_agent import CodeGenerationAgent
from memories.agents.code_execution_agent import CodeExecutionAgent
from memories.agents.response_generation_agent import ResponseGenerationAgent
from memories.agents.spatial_analysis_agent import SpatialAnalysisAgent

# Load environment variables
load_dotenv()

class Agent:
    def __init__(self, modalities: Dict[str, Dict[str, List[str]]], load_model=None, query: str = None, memories: Dict[str, Any] = None):
        """
        Initialize the Multi-Agent system with all required agents.
        
        Args:
            modalities (Dict[str, Dict[str, List[str]]]): Nested memories structured as {modality: {table: [columns]}}
            load_model: Instance of LoadModel for model operations
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
        
        # Store the provided model instance
        self.load_model = load_model
        if self.load_model is None:
            raise ValueError("load_model instance must be provided")
        
        # Initialize agents
        self.agents = {
            "context": LocationExtractor(),
            "filter": LocationProcessingAgent(),
            "coder": CodeGenerationAgent(),
            "executor": CodeExecutionAgent(),
            "response": ResponseGenerationAgent(),
            "query_context": QueryContext(),
            "spatial": SpatialAnalysisAgent()
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
            
            # Step 1: Classify the query using QueryContext
            print("\n🔍 CLASSIFYING QUERY")
            print("---------------------------")
            context_agent = self.agents["query_context"]
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
                location_extractor = self.agents["context"]
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