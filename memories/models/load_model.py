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
                 deployment_type: str = None,  # "local" or "api"
                 model_name: str = None,
                 api_key: str = None,
                 device: str = None):
        """
        Initialize model loader with configuration.
        
        Args:
            use_gpu (bool): Whether to use GPU if available
            model_provider (str): The model provider (e.g., "deepseek", "llama", "mistral")
            deployment_type (str): Either "local" or "api"
            model_name (str): Short name of the model from BaseModel.MODEL_MAPPINGS
            api_key (str): API key for the model provider (required for API deployment type)
            device (str): Specific GPU device to use (e.g., "cuda:0", "cuda:1")
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
        
        # Handle device selection
        self.device = device
        if self.use_gpu:
            if device:
                if not device.startswith("cuda:"):
                    raise ValueError("Device must be in format 'cuda:N' where N is the GPU index")
                device_idx = int(device.split(":")[-1])
                if device_idx >= torch.cuda.device_count():
                    raise ValueError(f"Device {device} not available. Maximum device index is {torch.cuda.device_count()-1}")
            else:
                self.device = "cuda:0"  # Default to first GPU
        else:
            self.device = "cpu"
            
        # Initialize appropriate model interface
        if deployment_type == "local":
            self.base_model = BaseModel.get_instance()
            success = self.base_model.initialize_model(
                model_name=model_name,
                use_gpu=use_gpu,
                device=device
            )
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
    
    def get_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate a response using either local model or API.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional generation parameters including:
                max_length: Maximum length of generated response
                temperature: Sampling temperature (0.0 to 1.0)
                top_p: Nucleus sampling parameter
                top_k: Top-k sampling parameter
                num_beams: Number of beams for beam search
                
        Returns:
            Dict[str, Any]: Response dictionary containing:
                text: The generated response text
                metadata: Generation metadata (tokens, time, etc)
                error: Error message if generation failed
        """
        if not prompt or not isinstance(prompt, str):
            return {
                "error": "Invalid prompt - must be non-empty string",
                "text": None,
                "metadata": None
            }
            
        try:
            # Log generation attempt
            self.logger.info(f"Generating response for prompt: {prompt[:100]}...")
            self.logger.debug(f"Full prompt: {prompt}")
            self.logger.info(f"Using deployment type: {self.deployment_type}")
            self.logger.debug(f"Generation parameters: {kwargs}")
            
            # Validate and set default parameters
            max_retries = kwargs.pop('max_retries', 3)
            timeout = kwargs.pop('timeout', 30)
            
            # Initialize response
            response = None
            error = None
            metadata = {
                "attempt": 0,
                "total_tokens": 0,
                "generation_time": 0
            }
            
            # Try generation with retries
            for attempt in range(max_retries):
                metadata["attempt"] = attempt + 1
                
                try:
                    if self.deployment_type == "local":
                        self.logger.info("Using base model for generation")
                        response = self.base_model.generate(
                            prompt,
                            timeout=timeout,
                            **kwargs
                        )
                    else:
                        self.logger.info(f"Using {self.model_provider} API connector")
                        response = self.api_connector.generate(
                            prompt,
                            timeout=timeout,
                            **kwargs
                        )
                        
                    if response:
                        break
                        
                except Exception as e:
                    error = str(e)
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed: {error}",
                        exc_info=True
                    )
                    if attempt < max_retries - 1:
                        continue
            
            # Process results
            if response:
                # Extract metadata if available
                if isinstance(response, dict):
                    metadata.update(response.get('metadata', {}))
                    response = response.get('text', response)
                    
                self.logger.info(
                    f"Response generated successfully. Length: {len(response)}"
                )
                
                return {
                    "text": response,
                    "metadata": metadata,
                    "error": None
                }
            else:
                error_msg = error or "Failed to generate response after retries"
                self.logger.error(error_msg)
                return {
                    "text": None,
                    "metadata": metadata,
                    "error": error_msg
                }
                
        except Exception as e:
            self.logger.error(
                f"Unexpected error in get_response: {str(e)}",
                exc_info=True
            )
            return {
                "text": None,
                "metadata": {"attempt": 1},
                "error": f"Unexpected error: {str(e)}"
            }
    
    def cleanup(self):
        """Clean up model resources."""
        if self.deployment_type == "local" and hasattr(self, 'base_model'):
            self.base_model.cleanup()
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        self.logger.info("Model resources cleaned up")

