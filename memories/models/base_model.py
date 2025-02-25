import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from dotenv import load_dotenv
import os
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import gc
from diffusers import StableDiffusionPipeline

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Global pipe variable for Stable Diffusion
pipe = None

class BaseModel:
    """Base model class that can be shared across modules"""
    _instance = None
    _initialized = False
    
    def __init__(self):
        """Initialize the base model."""
        if not BaseModel._initialized:
            self.model = None
            self.tokenizer = None
            self.config = self._load_config()
            self.hf_token = os.getenv("HF_TOKEN")
            BaseModel._initialized = True
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance of BaseModel."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _load_config(self) -> Dict[str, Any]:
        """Load model configuration from JSON file."""
        try:
            config_path = Path(__file__).parent / "config" / "model_config.json"
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading model config: {str(e)}")
            return {}
    
    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        """Get configuration for a specific model."""
        return self.config.get("models", {}).get(model_name, {})
    
    def initialize_model(self, model: str, use_gpu: bool = True, device: str = None) -> bool:
        """Initialize a model with the specified configuration.
        
        Args:
            model: Model identifier from config
            use_gpu: Whether to use GPU if available
            device: Specific GPU device to use (e.g., "cuda:0", "cuda:1")
            
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Clean up any existing model
            self.cleanup()
            
            # Get model configuration
            model_config = self.get_model_config(model)
            if not model_config:
                logger.error(f"No configuration found for model: {model}")
                return False
            
            # Determine device
            if use_gpu and torch.cuda.is_available():
                if device:
                    if not device.startswith("cuda:"):
                        logger.error("Device must be in format 'cuda:N' where N is the GPU index")
                        return False
                    device_idx = int(device.split(":")[-1])
                    if device_idx >= torch.cuda.device_count():
                        logger.error(f"Device {device} not available. Maximum device index is {torch.cuda.device_count()-1}")
                        return False
                else:
                    device = "cuda:0"  # Default to first GPU
            else:
                device = "cpu"
                if not self.config["global_config"]["fallback_to_cpu"]:
                    logger.error("GPU requested but not available and fallback_to_cpu is False")
                    return False
            
            # Get model parameters
            config = model_config["config"]
            model_name = model_config["name"]
            
            # Set up model parameters
            model_kwargs = {
                "use_auth_token": self.hf_token if self.config["global_config"]["use_auth_token"] else None,
                "torch_dtype": getattr(torch, config.get("torch_dtype", "float32")),
                "device_map": "auto" if device.startswith("cuda") else None,
                "trust_remote_code": config.get("trust_remote_code", True)
            }
            
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                use_auth_token=model_kwargs["use_auth_token"],
                trust_remote_code=model_kwargs["trust_remote_code"]
            )
            
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                **model_kwargs
            )
            
            # Move model to specified device
            if device == "cpu" or device.startswith("cuda:"):
                self.model = self.model.to(device)
            
            logger.info(f"Model {model_name} initialized successfully on {device}")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing model: {str(e)}")
            self.cleanup()
            return False
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using the model with configured parameters.
        
        Args:
            prompt: Input prompt
            **kwargs: Override default generation parameters
            
        Returns:
            str: Generated text
        """
        if self.model is None or self.tokenizer is None:
            raise ValueError("Model not initialized. Call initialize_model first.")
        
        try:
            # Get current model's config
            current_model = next(
                (name for name, cfg in self.config["models"].items() 
                 if cfg["name"] == self.model.config._name_or_path),
                self.config["default_model"]
            )
            model_config = self.get_model_config(current_model)["config"]
            
            # Prepare generation config
            gen_config = {
                "max_length": model_config.get("max_length", 1000),
                "temperature": model_config.get("temperature", 0.7),
                "top_p": model_config.get("top_p", 0.95),
                "top_k": model_config.get("top_k", 50),
                "repetition_penalty": model_config.get("repetition_penalty", 1.1),
                "pad_token_id": self.tokenizer.eos_token_id,
                "do_sample": True
            }
            
            # Override with any provided kwargs
            gen_config.update(kwargs)
            
            # Generate
            inputs = self.tokenizer(prompt, return_tensors="pt")
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model.generate(**inputs, **gen_config)
            
            return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
        except Exception as e:
            logger.error(f"Error during generation: {str(e)}")
            raise
    
    def cleanup(self):
        """Clean up model resources."""
        if hasattr(self, 'model') and self.model is not None:
            del self.model
            self.model = None
        if hasattr(self, 'tokenizer') and self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        gc.collect()
        logger.info("Model resources cleaned up")
    
    @classmethod
    def get_model_path(cls, provider: str, model_key: str) -> str:
        """Get the full model path/identifier for a given provider and model key"""
        instance = cls.get_instance()
        if model_key not in instance.config["models"]:
            raise ValueError(f"Unknown model key: {model_key}")
            
        model_config = instance.config["models"][model_key]
        if model_config["provider"] != provider:
            raise ValueError(f"Model {model_key} not available for provider {provider}")
            
        return model_config["name"]

    @classmethod
    def list_providers(cls) -> List[str]:
        """List all available providers"""
        instance = cls.get_instance()
        return instance.config["supported_providers"]

    @classmethod
    def list_models(cls, provider: str = None) -> List[str]:
        """List all available models, optionally filtered by provider"""
        instance = cls.get_instance()
        if provider:
            if provider not in instance.config["supported_providers"]:
                raise ValueError(f"Unknown provider: {provider}")
            return [
                name for name, cfg in instance.config["models"].items()
                if cfg["provider"] == provider
            ]
        return list(instance.config["models"].keys())

def load_stable_diffusion_model(device: str = None):
    """
    Preloads the Stable Diffusion model into the global `pipe` variable.
    
    Args:
        device: Specific GPU device to use (e.g., "cuda:0", "cuda:1")
    """
    global pipe

    if pipe is not None:
        logger.info("Stable Diffusion model already loaded; skipping.")
        return

    try:
        instance = BaseModel.get_instance()
        model_config = instance.get_model_config("stable-diffusion-2")
        
        if not model_config:
            raise ValueError("No configuration found for Stable Diffusion model")
        
        config = model_config["config"]
        model_name = model_config["name"]
        
        pipe = StableDiffusionPipeline.from_pretrained(
            model_name,
            **config
        )
        
        # Determine device
        if torch.cuda.is_available():
            if device:
                if not device.startswith("cuda:"):
                    raise ValueError("Device must be in format 'cuda:N' where N is the GPU index")
                device_idx = int(device.split(":")[-1])
                if device_idx >= torch.cuda.device_count():
                    raise ValueError(f"Device {device} not available. Maximum device index is {torch.cuda.device_count()-1}")
            else:
                device = "cuda:0"  # Default to first GPU
            pipe = pipe.to(device)
        else:
            logger.warning("CUDA not available, using CPU. This will be slow!")
            pipe = pipe.to("cpu")
            
        logger.info(f"Stable Diffusion model loaded successfully on {device if device else 'cuda:0'}")
        
    except Exception as e:
        logger.error(f"Failed to load Stable Diffusion model: {e}")
        pipe = None
        raise RuntimeError("Failed to load Stable Diffusion model. Ensure proper environment setup and access.") from e

def unload_stable_diffusion_model():
    """
    Unloads the Stable Diffusion model from memory and clears the GPU cache.
    """
    global pipe
    if pipe:
        del pipe
        pipe = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("Stable Diffusion model unloaded and GPU cache cleared.")
