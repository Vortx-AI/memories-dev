import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from dotenv import load_dotenv
import os

class BaseModel:
    """Base model class that can be shared across modules"""
    _instance = None
    _initialized = False
    
    # Add model mappings
    MODEL_MAPPINGS = {
        "default": "deepseek-ai/deepseek-coder-1.3b-base",
        "deepseek-coder-small": "deepseek-ai/deepseek-coder-1.3b-base",
        "deepseek-coder-medium": "deepseek-ai/deepseek-coder-6.7b",
        "deepseek-coder-large": "deepseek-ai/deepseek-coder-33b",
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BaseModel, cls).__new__(cls)
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
