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
            
        self.instance_id = str(uuid.uuid4())
        self.logger = logging.getLogger(__name__)
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.model_provider = model_provider
        self.deployment_type = deployment_type
        self.model_name = model_name
        self.api_key = api_key
        
        # Initialize DuckDB connection
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'memories.db')
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = duckdb.connect(self.db_path)
        
        # Create models table if it doesn't exist
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS models (
                instance_id VARCHAR PRIMARY KEY,
                model_provider VARCHAR,
                model_name VARCHAR,
                deployment_type VARCHAR,
                use_gpu BOOLEAN,
                api_key VARCHAR,
                model_path VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        if use_gpu and not torch.cuda.is_available():
            self.logger.warning("GPU requested but not available. Falling back to CPU.")
        
        # Initialize base_model
        from memories.models.base_model import BaseModel
        self.base_model = BaseModel.get_instance()
        
        # Clean up any existing model resources first
        if hasattr(self, 'base_model'):
            self.cleanup()
        
        try:
            self.model_path = model_name
            if deployment_type == "deployment":
                self.model_path = f"{model_provider}/{model_name}"
            self.logger.info(f"Resolved model path: {self.model_path}")
            
            # Store model details in DuckDB
            self.conn.execute("""
                INSERT INTO models (
                    instance_id,
                    model_provider,
                    model_name,
                    deployment_type,
                    use_gpu,
                    api_key,
                    model_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                self.instance_id,
                model_provider,
                model_name,
                deployment_type,
                use_gpu,
                api_key,
                self.model_path
            ))
            
        except Exception as e:
            self.logger.error(f"Error initializing model: {str(e)}")
            raise
        
        # Initialize the model if using deployment type
        if deployment_type == "deployment":
            success = self.base_model.initialize_model(
                model=self.model_path,
                use_gpu=self.use_gpu
            )
            if not success:
                raise RuntimeError("Failed to initialize model")
                
        self.logger.info(f"Model loaded successfully with instance ID: {self.instance_id}")
    
    def cleanup(self):
        """Clean up model resources"""
        if hasattr(self.base_model, 'model'):
            del self.base_model.model
            self.base_model.model = None
        if hasattr(self.base_model, 'tokenizer'):
            del self.base_model.tokenizer
            self.base_model.tokenizer = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        gc.collect()
        self.logger.info("Model resources cleaned up")
    
    def __del__(self):
        """Destructor to ensure connection is closed"""
        if hasattr(self, 'conn'):
            self.conn.close()

