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
import uuid
import duckdb


from memories.agents.agent_query_context import LocationExtractor
from memories.agents.agent_coder import CodeGenerator
from memories.models.base_model import BaseModel

class LoadModel(BaseModel):
    def __init__(self, 
                 use_gpu: bool = True,
                 model_provider: str = "deepseek-ai",
                 deployment_type: str = "deployment",
                 model_name: str = "deepseek-coder-1.3b-base"):
        """
        Initialize the model loader.
        
        Args:
            use_gpu (bool): Whether to use GPU if available
            model_provider (str): The model provider (e.g., "deepseek-ai")
            deployment_type (str): Type of deployment
            model_name (str): Name of the model to load
        """
        super().__init__()
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.model_provider = model_provider
        self.deployment_type = deployment_type
        self.model_name = model_name
        
        # Initialize the model and tokenizer
        self.initialize_model()

    def initialize_model(self):
        """Initialize the model and tokenizer"""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
            
            if self.use_gpu:
                self.model = self.model.cuda()
                
            self.model.eval()  # Set to evaluation mode
            
        except Exception as e:
            raise Exception(f"Error initializing model: {str(e)}")

    def get_response(self, prompt: str) -> str:
        """
        Get a response from the model for a given prompt.
        
        Args:
            prompt (str): The input prompt
            
        Returns:
            str: The model's response
        """
        try:
            # Tokenize the input
            inputs = self.tokenizer(prompt, return_tensors="pt")
            if self.use_gpu:
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=512,
                    num_return_sequences=1,
                    temperature=0.7,
                    top_p=0.95,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode and return the response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Remove the original prompt from the response
            if response.startswith(prompt):
                response = response[len(prompt):].strip()
                
            return response
            
        except Exception as e:
            raise Exception(f"Error generating response: {str(e)}")

    def cleanup(self):
        """Clean up model resources"""
        if hasattr(self.model, 'model'):
            del self.model
            self.model = None
        if hasattr(self.tokenizer, 'tokenizer'):
            del self.tokenizer
            self.tokenizer = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        gc.collect()
        self.logger.info("Model resources cleaned up")
    
    def __del__(self):
        """Destructor to ensure connection is closed"""
        if hasattr(self, 'conn'):
            self.conn.close()

