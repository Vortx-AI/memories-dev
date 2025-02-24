import sys
import os
from pathlib import Path
import torch
from typing import Dict, Any, List, Optional, Tuple, Union
from dotenv import load_dotenv
import logging
import tempfile
import gc
import uuid
import json

from memories.models.base_model import BaseModel
from memories.models.api_connector import get_connector

# Load environment variables
load_dotenv()

class LoadModel:
    def __init__(self, 
                 use_gpu: bool = True,
                 model_provider: str = None,
                 deployment_type: str = None,  # "deployment" or "api"
                 model_name: str = None,
                 api_key: str = None):
        """
        Initialize model loader with configuration.
        
        Args:
            use_gpu (bool): Whether to use GPU if available
            model_provider (str): The model provider (e.g., "deepseek", "llama", "mistral")
            deployment_type (str): Either "deployment" or "api"
            model_name (str): Short name of the model from BaseModel.MODEL_MAPPINGS
            api_key (str): API key for the model provider (required for API deployment type)
        """
        # Setup logging
        self.instance_id = str(uuid.uuid4())
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config = self._load_config()
        
        # Set default values from config if not provided
        if not all([model_provider, deployment_type, model_name]):
            default_model = self.config["default_model"]
            default_config = self.config["models"][default_model]
            model_provider = model_provider or default_config["provider"]
            deployment_type = deployment_type or default_config["type"]
            model_name = model_name or default_model
        
        # Validate inputs
        if deployment_type not in self.config["deployment_types"]:
            raise ValueError(f"deployment_type must be one of: {self.config['deployment_types']}")
            
        if model_provider not in self.config["supported_providers"]:
            raise ValueError(f"model_provider must be one of: {self.config['supported_providers']}")
            
        if deployment_type == "api" and not api_key:
            raise ValueError("api_key is required for API deployment type")
        
        # Store configuration
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.model_provider = model_provider
        self.deployment_type = deployment_type
        self.model_name = model_name
        self.api_key = api_key
        
        # Initialize appropriate model interface
        if deployment_type == "deployment":
            self.base_model = BaseModel.get_instance()
            success = self.base_model.initialize_model(model_name, use_gpu)
            if not success:
                raise RuntimeError(f"Failed to initialize model: {model_name}")
        else:  # api
            self.api_connector = get_connector(model_provider, api_key)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load model configuration."""
        try:
            config_path = Path(__file__).parent / "config" / "model_config.json"
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading config: {str(e)}")
            return {}
    
    def get_response(self, prompt: str, **kwargs) -> str:
        """
        Generate a response using either local model or API.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional generation parameters
            
        Returns:
            str: The generated response
        """
        try:
            self.logger.info(f"Generating response for prompt: {prompt[:100]}...")
            self.logger.info(f"Using deployment type: {self.deployment_type}")
            self.logger.info(f"Additional parameters: {kwargs}")
            
            if self.deployment_type == "deployment":
                self.logger.info("Using base model for generation")
                response = self.base_model.generate(prompt, **kwargs)
            else:
                self.logger.info(f"Using {self.model_provider} API connector for generation")
                response = self.api_connector.generate(prompt, **kwargs)
            
            self.logger.info(f"Response generated successfully. Length: {len(response)}")
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}", exc_info=True)
            return f"Error: {str(e)}"
    
    def cleanup(self):
        """Clean up model resources."""
        if self.deployment_type == "deployment" and hasattr(self, 'base_model'):
            self.base_model.cleanup()
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        self.logger.info("Model resources cleaned up")

