import sys
import os
from pathlib import Path
import torch
from typing import Dict, Any, List, Optional, Tuple, Union
from dotenv import load_dotenv
import logging

from memories_dev.models.base_model import BaseModel
from memories_dev.agents.agent_query_context import LocationExtractor
from memories_dev.agents.agent_coder import CodeGenerator

class MemoriesDev:
    def __init__(self, use_gpu: bool = True, model: str = None):
        self.logger = logging.getLogger(__name__)
        self.use_gpu = use_gpu and torch.cuda.is_available()
        
        if use_gpu and not torch.cuda.is_available():
            self.logger.warning("GPU requested but not available. Falling back to CPU.")
        
        device = "cuda" if self.use_gpu else "cpu"
        self.logger.info(f"Using device: {device}")
        
        # Use default model if no model is provided
        model = model if model else "default"
        
        # Initialize the base model
        self.base_model = BaseModel.get_instance()
        success = self.base_model.initialize_model(
            model=model,
            use_gpu=self.use_gpu
        )
        
        if not success:
            raise RuntimeError("Failed to initialize model")
        
        # Initialize components
        self.location_extractor = LocationExtractor()
        self.code_generator = CodeGenerator()
        
    def generate_text(self, prompt, max_length=1000):
        return self.base_model.generate(prompt, max_length)

    