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

class MemoriesDev:
    def __init__(self, 
                 use_gpu: bool = True,
                 model_provider: str = None,
                 deployment_type: str = None,  # "deployment" or "api"
                 model_name: str = None,
                 api_key: str = None):
        """
        Initialize MemoriesDev with model configuration.
        
        Args:
            use_gpu (bool): Whether to use GPU if available
            model_provider (str): The AI model provider (required)
            deployment_type (str): Either "deployment" or "api"
            model_name (str): Name of the model to use (required)
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
        
        self.device = "cuda" if self.use_gpu else "cpu"
        self.logger.info(f"Using device: {self.device}")
        
        # Create offload directory
        self.offload_folder = os.path.join(tempfile.gettempdir(), 'model_offload')
        os.makedirs(self.offload_folder, exist_ok=True)
        
        # Store model configuration
        self.model_config = {
            "provider": model_provider,
            "deployment_type": deployment_type,
            "model_name": model_name,
            "api_key": api_key,
            "offload_folder": self.offload_folder
        }
        
        # Initialize model if using deployment type
        if deployment_type == "deployment":
            self._initialize_deployment()
        
        # Initialize components with model configuration
        self.location_extractor = LocationExtractor(**self.model_config)
        self.code_generator = CodeGenerator(**self.model_config)
        
    def _initialize_deployment(self):
        """Initialize the model for deployment type"""
        try:
            if torch.cuda.is_available():
                dtype = torch.float16
                device_map = {
                    "": torch.cuda.current_device()
                }
            else:
                dtype = torch.float32
                device_map = "cpu"
                
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_config["model_name"])
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_config["model_name"],
                torch_dtype=dtype,
                device_map=device_map,
                low_cpu_mem_usage=True,
                offload_folder=self.offload_folder
            )
            self.logger.info(f"Model {self.model_config['model_name']} initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize model: {str(e)}")
            raise
            
    def cleanup(self):
        """Clean up model resources and free memory"""
        try:
            if hasattr(self, 'model'):
                # Delete model and tokenizer
                del self.model
                del self.tokenizer
                
                # Clear CUDA cache if available
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.ipc_collect()
                
                # Run garbage collection
                gc.collect()
                
                self.logger.info("Model resources cleaned up successfully")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
            
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()

    def generate_text(self, prompt, max_length=1000):
        """Generate text based on deployment type"""
        if self.deployment_type == "deployment":
            # Use local model
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        else:
            # Use API-based generation
            # Implementation depends on the specific API being used
            raise NotImplementedError("API-based text generation not implemented")

    