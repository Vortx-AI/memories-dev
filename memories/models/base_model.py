import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from dotenv import load_dotenv
import os
import logging
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
    
    # Comprehensive model mappings (only HuggingFace compatible models)
    MODEL_MAPPINGS = {
        # DeepSeek Models (HF compatible)
        "deepseek-coder-small": "deepseek-ai/deepseek-coder-1.3b-base",
        "deepseek-coder-medium": "deepseek-ai/deepseek-coder-6.7b",
        "deepseek-coder-large": "deepseek-ai/deepseek-coder-33b",
        "deepseek-math": "deepseek-ai/deepseek-math-7b-base",
        "deepseek-llm-small": "deepseek-ai/deepseek-llm-7b-base",
        "deepseek-llm-large": "deepseek-ai/deepseek-llm-67b-base",

        # Meta/Llama Models (HF compatible)
        "llama-2-7b": "meta-llama/Llama-2-7b",
        "llama-2-13b": "meta-llama/Llama-2-13b",
        "llama-2-70b": "meta-llama/Llama-2-70b",
        "llama-2-7b-chat": "meta-llama/Llama-2-7b-chat",
        "llama-2-13b-chat": "meta-llama/Llama-2-13b-chat",
        "llama-2-70b-chat": "meta-llama/Llama-2-70b-chat",
        "code-llama-7b": "codellama/CodeLlama-7b-hf",
        "code-llama-13b": "codellama/CodeLlama-13b-hf",
        "code-llama-34b": "codellama/CodeLlama-34b-hf",

        # Mistral Models (HF compatible)
        "mistral-7b": "mistralai/Mistral-7B-v0.1",
        "mistral-8x7b": "mistralai/Mixtral-8x7B-v0.1",

        # HuggingFace Open Models
        "falcon-7b": "tiiuae/falcon-7b",
        "falcon-40b": "tiiuae/falcon-40b",
        "falcon-180b": "tiiuae/falcon-180B",
        "mpt-7b": "mosaicml/mpt-7b",
        "mpt-30b": "mosaicml/mpt-30b",
        "stable-diffusion-2": "stabilityai/stable-diffusion-2",
        "stable-diffusion-xl": "stabilityai/stable-diffusion-xl-base-1.0",
        
        # Default fallback
        "default": "deepseek-ai/deepseek-coder-1.3b-base"
    }
    
    # Add provider-specific mappings for easy lookup
    PROVIDER_GROUPS = {
        "deepseek": ["deepseek-coder-small", "deepseek-coder-medium", "deepseek-coder-large", 
                    "deepseek-math", "deepseek-llm-small", "deepseek-llm-large"],
        "llama": ["llama-2-7b", "llama-2-13b", "llama-2-70b", "llama-2-7b-chat",
                 "llama-2-13b-chat", "llama-2-70b-chat", "code-llama-7b",
                 "code-llama-13b", "code-llama-34b"],
        "mistral": ["mistral-7b", "mistral-8x7b"],
        "huggingface": ["falcon-7b", "falcon-40b", "falcon-180b", "mpt-7b", 
                       "mpt-30b", "stable-diffusion-2", "stable-diffusion-xl"]
    }

    @classmethod
    def get_model_path(cls, provider: str, model_key: str) -> str:
        """Get the full model path/identifier for a given provider and model key"""
        if model_key not in cls.MODEL_MAPPINGS:
            raise ValueError(f"Unknown model key: {model_key}")
        if provider not in cls.PROVIDER_GROUPS:
            raise ValueError(f"Unknown provider: {provider}")
        if model_key not in cls.PROVIDER_GROUPS[provider]:
            raise ValueError(f"Model {model_key} not available for provider {provider}")
        return cls.MODEL_MAPPINGS[model_key]

    @classmethod
    def list_providers(cls) -> list:
        """List all available providers"""
        return list(cls.PROVIDER_GROUPS.keys())

    @classmethod
    def list_models(cls, provider: str = None) -> list:
        """List all available models, optionally filtered by provider"""
        if provider:
            if provider not in cls.PROVIDER_GROUPS:
                raise ValueError(f"Unknown provider: {provider}")
            return cls.PROVIDER_GROUPS[provider]
        return list(cls.MODEL_MAPPINGS.keys())

    @classmethod
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.model = None
            self.tokenizer = None
            self._initialized = True
            # Load environment variables
            load_dotenv()
            self.hf_token = os.getenv('HF_TOKEN')
            if not self.hf_token:
                print("Warning: HF_TOKEN not found in environment variables")
    
    @classmethod
    def get_instance(cls):
        return cls() if cls._instance is None else cls._instance
    
    def initialize_model(self, model: str, use_gpu: bool = True):
        """Initialize the model and tokenizer
        
        Args:
            model (str): Key name of the model to load from MODEL_MAPPINGS
            use_gpu (bool): Whether to use GPU if available
        """
        try:
            # Determine device
            device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
            
            # Resolve model name from mappings if it's a key
            model_identifier = self.MODEL_MAPPINGS.get(model, model)
            print(f"Resolved model identifier: {model_identifier}")
            
            # Load tokenizer with auth token
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_identifier,
                use_auth_token=self.hf_token,
                trust_remote_code=True
            )
            
            # Load model with auth token
            self.model = AutoModelForCausalLM.from_pretrained(
                model_identifier,
                use_auth_token=self.hf_token,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                device_map="auto" if device == "cuda" else None,
                trust_remote_code=True
            )
            
            if device == "cpu":
                self.model = self.model.to(device)
                
            print(f"Model initialized on {device}")
            return True
            
        except Exception as e:
            print(f"Error initializing model: {str(e)}")
            return False
    
    def generate(self, prompt, max_length=1000):
        """Generate text using the model"""
        if self.model is None or self.tokenizer is None:
            raise ValueError("Model not initialized. Call initialize_model first.")
            
        inputs = self.tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        
        outputs = self.model.generate(
            **inputs,
            max_length=max_length,
            num_return_sequences=1,
            pad_token_id=self.tokenizer.eos_token_id
        )
        
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True) 
    
    def load_stable_diffusion_model():
        """
        Preloads the Stable Diffusion model into the global `pipe` variable.
        """
        global pipe

        if pipe is not None:
            logger.info("Stable Diffusion model already loaded; skipping.")
            return

        hf_cache_dir = os.getenv("CACHE_DIR", ".cache/huggingface")
        stable_diffusion_model = os.getenv("STABLE_DIFFUSION_MODEL", "CompVis/stable-diffusion-v1-4")
        device = "cuda" if torch.cuda.is_available() else "cpu"

        logger.info(f"Loading Stable Diffusion model '{stable_diffusion_model}' on device: {device}")
        try:
            pipe = StableDiffusionPipeline.from_pretrained(
                stable_diffusion_model,
                variant="fp16",  # Updated from revision="fp16"
                torch_dtype=torch.float16,
                use_auth_token=True,
                cache_dir=hf_cache_dir,
            )
            pipe = pipe.to(device)
            logger.info("Stable Diffusion model loaded successfully.")
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
