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
import requests


from memories.agents.agent_query_context import LocationExtractor
from memories.agents.agent_coder import CodeGenerator

load_dotenv()

class LoadModel:
    def __init__(self, 
                 use_gpu: bool = True,
                 model_provider: str = None,
                 deployment_type: str = None,
                 model_name: str = None,
                 api_key: str = None):
        """
        Initialize model loader with configuration.
        
        Args:
            use_gpu (bool): Whether to use GPU if available
            model_provider (str): The model provider (e.g., "openai", "deepseek", "anthropic")
            deployment_type (str): Either "deployment" or "api"
            model_name (str): Name of the model to use
            api_key (str): API key for the model provider (if not in env vars)
        """
        self.logger = logging.getLogger(__name__)
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.model_provider = model_provider
        self.deployment_type = deployment_type
        self.model_name = model_name
        
        # Load API keys from environment or use provided
        self.api_keys = {
            'openai': api_key or os.getenv('OPENAI_API_KEY'),
            'deepseek': api_key or os.getenv('DEEPSEEK_API_KEY'),
            'anthropic': api_key or os.getenv('ANTHROPIC_API_KEY')
        }
        
        # Initialize based on deployment type
        if self.deployment_type == "api":
            self._initialize_api_clients()
        elif self.deployment_type == "deployment":
            self._initialize_local_model()
        else:
            self.client = MockModel()
            
        self.logger.info(f"Model loaded successfully with instance ID: {id(self)}")

    def _initialize_api_clients(self):
        """Initialize API clients based on provider"""
        try:
            if self.model_provider == "openai":
                try:
                    from openai import OpenAI
                    self.client = OpenAI(api_key=self.api_keys['openai'])
                except ImportError:
                    raise ImportError("OpenAI package not installed. Please install it using: pip install openai")
            elif self.model_provider == "deepseek":
                self.client = None  # Will use direct API calls
            elif self.model_provider == "anthropic":
                self.client = None  # Will implement Anthropic client
            else:
                raise ValueError(f"Unsupported API provider: {self.model_provider}")
                
        except Exception as e:
            self.logger.error(f"Error initializing API client: {str(e)}")
            raise

    def _initialize_local_model(self):
        """Initialize local deployment model"""
        try:
            if self.model_provider == "deepseek":
                # Initialize local DeepSeek model
                self.client = MockModel()  # Replace with actual local model initialization
            else:
                raise ValueError(f"Unsupported local deployment for provider: {self.model_provider}")
                
        except Exception as e:
            self.logger.error(f"Error initializing local model: {str(e)}")
            raise

    def get_response(self, prompt: str) -> str:
        """
        Get a response based on deployment type and provider.
        
        Args:
            prompt (str): The input prompt
            
        Returns:
            str: The model's response
        """
        try:
            if self.deployment_type == "api":
                if self.model_provider == "openai":
                    return self._get_openai_response(prompt)
                elif self.model_provider == "deepseek":
                    return self._get_deepseek_api_response(prompt)
                elif self.model_provider == "anthropic":
                    return self._get_anthropic_response(prompt)
                    
            elif self.deployment_type == "deployment":
                if self.model_provider == "deepseek":
                    return self._get_local_deepseek_response(prompt)
                    
            # Default to mock response
            return self.client(prompt)
                
        except Exception as e:
            raise Exception(f"Error generating response: {str(e)}")

    def _get_openai_response(self, prompt: str) -> str:
        """Get response from OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name or "gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

    def _get_deepseek_api_response(self, prompt: str) -> str:
        """Get response from DeepSeek API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_keys['deepseek']}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model_name or "deepseek-coder-1.3b-base",
                "messages": [{"role": "user", "content": prompt}]
            }
            
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=data
            )
            
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content'].strip()
        except Exception as e:
            raise Exception(f"DeepSeek API error: {str(e)}")

    def _get_local_deepseek_response(self, prompt: str) -> str:
        """Get response from local DeepSeek model"""
        try:
            # Use the locally deployed model
            # This should be implemented based on your local deployment setup
            return self.client(prompt)
        except Exception as e:
            raise Exception(f"Local DeepSeek error: {str(e)}")

    def _get_anthropic_response(self, prompt: str) -> str:
        """Get response from Anthropic API"""
        try:
            # Implement Anthropic API call
            raise NotImplementedError("Anthropic API not yet implemented")
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")

# Mock model class for testing
class MockModel:
    def __call__(self, prompt: str) -> str:
        """Mock response generation."""
        if "location" in prompt.lower() or "near" in prompt.lower():
            return "L1_2"
        elif "capital" in prompt.lower() or "country" in prompt.lower():
            return "L0"
        else:
            return "N"

