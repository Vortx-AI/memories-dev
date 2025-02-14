import sys
import os
from pathlib import Path
import torch
from typing import Dict, Any, List, Optional, Tuple, Union
from dotenv import load_dotenv
import logging
import tempfile
import gc
from transformers import AutoTokenizer, AutoModelForCausalLM

from memories_dev.models.base_model import BaseModel
from memories_dev.agents.agent_query_context import LocationExtractor
from memories_dev.agents.agent_coder import CodeGenerator

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
        if not all([model_provider, deployment_type, model_name]):
            raise ValueError("model_provider, deployment_type, and model_name are required")
            
        if deployment_type not in ["deployment", "api"]:
            raise ValueError("deployment_type must be either 'deployment' or 'api'")
            
        if deployment_type == "api" and not api_key:
            raise ValueError("api_key is required for API deployment type")
            
        self.logger = logging.getLogger(__name__)
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.deployment_type = deployment_type
        
        if use_gpu and not torch.cuda.is_available():
            self.logger.warning("GPU requested but not available. Falling back to CPU.")
        
        # Get the base model instance
        self.base_model = BaseModel.get_instance()
        
        # Get the full model path from base model mappings
        try:
            self.model_path = BaseModel.get_model_path(model_provider, model_name)
            self.logger.info(f"Resolved model path: {self.model_path}")
        except ValueError as e:
            self.logger.error(f"Error resolving model path: {str(e)}")
            raise
        
        # Initialize the model if using deployment type
        if deployment_type == "deployment":
            success = self.base_model.initialize_model(
                model=self.model_path,
                use_gpu=self.use_gpu
            )
            if not success:
                raise RuntimeError("Failed to initialize model")
            self.logger.info("Model initialized successfully")
        
    def generate_text(self, prompt: str, max_length: int = 1000) -> str:
        """Generate text using the initialized model"""
        if self.deployment_type == "deployment":
            return self.base_model.generate(prompt, max_length)
        else:
            raise NotImplementedError("API-based text generation not implemented")
    
    def cleanup(self):
        """Clean up model resources"""
        if hasattr(self.base_model, 'model'):
            del self.base_model.model
        if hasattr(self.base_model, 'tokenizer'):
            del self.base_model.tokenizer
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        self.logger.info("Model resources cleaned up")

# Example usage
if __name__ == "__main__":
    # For deployment type (local model)
    model = LoadModel(
        use_gpu=True,
        model_provider="deepseek",
        deployment_type="deployment",
        model_name="deepseek-coder-small"
    )
    
    try:
        # Generate text
        result = model.generate_text("Write a Python function to calculate fibonacci numbers")
        print("Generated text:", result)
    finally:
        # Clean up
        model.cleanup()

    