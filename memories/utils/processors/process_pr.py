import logging
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import json
import signal
import torch
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)  # Detailed logs
logger = logging.getLogger(__name__)

# Global variable for the LLaMA pipeline to avoid reinitializing
llama_pipeline = None

class TimeoutException(Exception):
    """Custom exception for timeout handling."""
    pass

def timeout_handler(signum, frame):
    """Handles timeout events."""
    raise TimeoutException("Inference timed out.")

def load_llama_model(model_name: str = 'meta-llama/Llama-2-7b-chat-hf', hf_token: str = None):
    """
    Loads the LLaMA model pipeline if not already initialized.

    Args:
        model_name (str): Name of the LLaMA model to use.
        hf_token (str): Hugging Face token for gated models.
    """
    global llama_pipeline
    if llama_pipeline is not None:
        logger.info("LLaMA model already loaded.")
        return

    try:
        # Use the provided hf_token or fetch it from environment variables
        hf_token = hf_token or os.getenv('HF_TOKEN')

        logger.info(f"Loading LLaMA model '{model_name}'...")
        tokenizer = AutoTokenizer.from_pretrained(model_name, use_auth_token=hf_token)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype="auto",  # Automatic precision
            device_map="auto",   # Automatically allocate layers to GPU/CPU
            max_memory={0: "10GiB"}  # Adjust based on GPU memory
        )

        llama_pipeline = pipeline('text-generation', model=model, tokenizer=tokenizer)
        logger.info("LLaMA model loaded successfully.")

        if not os.getenv('HF_TOKEN'):
            logger.error("HF_TOKEN is not set in the environment variables.")
            raise EnvironmentError("HF_TOKEN is required but not set.")
    except Exception as e:
        logger.error(f"Error loading LLaMA model: {e}")
        raise RuntimeError("Failed to load LLaMA model.") from e

def unload_llama_model():

    """
    Unloads the LLaMA model and clears GPU memory.
    """

    global llama_pipeline
    if llama_pipeline:
        logger.info("Unloading LLaMA model...")
        del llama_pipeline
        llama_pipeline = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("LLaMA model unloaded and GPU cache cleared.")
    else:
        logger.info("No LLaMA model to unload.")

def generate_prompt_from_caption(prompt: str, model_name: str = 'meta-llama/Llama-2-7b-chat-hf', hf_token: str = None) -> list:
   
    
        # Load the LLaMA model
    load_llama_model(model_name=model_name, hf_token=hf_token)

        # Generate the response
    logger.info("Generating response from LLaMA...")
    result = llama_pipeline(
            prompt,
            max_new_tokens=200,  # Limit token generation for speed
            num_return_sequences=1,
            temperature=0.2,  # Lower randomness for deterministic results
            top_p=0.9,
            do_sample=False  # Disable sampling for faster output
    )

        # Debug: Print raw model output
    logger.info(f"Raw Model Output: {result}")
    generated_text = result[0]['generated_text'] if result else None
    return generated_text

    