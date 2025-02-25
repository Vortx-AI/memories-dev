"""API connectors for various model providers."""

import os
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from pathlib import Path
import requests


from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class APIConnector(ABC):
    """Base class for API connectors."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the API connector."""
        self.api_key = api_key or self._get_api_key()
        self.config = self._load_config()
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using the API."""
        pass
    
    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment variables."""
        env_keys = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "google": "GOOGLE_API_KEY"
        }
        for provider, env_var in env_keys.items():
            if self.__class__.__name__.lower().startswith(provider):
                return os.getenv(env_var)
        return None
    
    def _load_config(self) -> Dict[str, Any]:
        """Load model configuration."""
        try:
            config_path = Path(__file__).parent / "config" / "model_config.json"
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            return {}

class OpenAIConnector(APIConnector):
    """Connector for OpenAI API."""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        try:
            logger.info("Attempting to import OpenAI package...")
            from openai import OpenAI
            logger.info("OpenAI package imported successfully")
            
            logger.info("Initializing OpenAI client...")
            if not self.api_key:
                raise ValueError("API key is required for OpenAI")
            self.client = OpenAI(api_key=self.api_key)
            logger.info("OpenAI client initialized successfully")
            
        except ImportError as e:
            logger.error("Failed to import openai package. Please install it with 'pip install openai'")
            self.client = None
            raise
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {str(e)}")
            self.client = None
            raise
            
        self.model_config = next(
            (cfg for cfg in self.config["models"].values() 
             if cfg["provider"] == "openai"),
            {}
        )

    def generate(
        self,
        prompt: str,
        model: str = None,
        **kwargs
    ) -> str:
        if self.client is None:
            raise RuntimeError("OpenAI client is not initialized")
            
        try:
            logger.info(f"Preparing OpenAI request with model: {model or self.model_config.get('name', 'gpt-4-turbo-preview')}")
            
            # Get model configuration
            config = self.model_config.get("config", {})
            
            # Prepare parameters
            params = {
                "model": model or self.model_config.get("name", "gpt-4-turbo-preview"),
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": config.get("max_length", 1000),
                "temperature": config.get("temperature", 0.7),
                "top_p": config.get("top_p", 0.95)
            }
            params.update(kwargs)
            
            logger.info("Sending request to OpenAI API...")
            # Make API call
            response = self.client.chat.completions.create(**params)
            logger.info("Response received from OpenAI API")
            
            content = response.choices[0].message.content
            logger.info(f"Generated response length: {len(content)}")
            return content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}", exc_info=True)
            raise

class DeepseekConnector(APIConnector):
    """Connector for Deepseek API."""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        self.model_config = next(
            (cfg for cfg in self.config["models"].values() 
             if cfg["provider"] == "deepseek-ai" and cfg["type"] == "api"),
            {}
        )
        config = self.model_config.get("config", {})
        self.api_base = config.get("api_base", "https://api.deepseek.com/v1")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def generate(
        self,
        prompt: str,
        model: str = None,
        **kwargs
    ) -> str:
        try:
            # Get model configuration
            config = self.model_config.get("config", {})
            
            # Prepare parameters
            params = {
                "model": model or self.model_config.get("name", "deepseek-coder"),
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": config.get("max_length", 1000),
                "temperature": config.get("temperature", 0.7),
                "top_p": config.get("top_p", 0.95)
            }
            params.update(kwargs)
            
            # Make API call
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=self.headers,
                json=params
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
            
        except Exception as e:
            logger.error(f"Deepseek API error: {str(e)}")
            raise

class AnthropicConnector(APIConnector):
    """Connector for Anthropic API (Claude)."""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            logger.warning("anthropic package not installed. AnthropicConnector will not be available.")
            self.client = None
        self.model_config = next(
            (cfg for cfg in self.config["models"].values() 
             if cfg["provider"] == "anthropic"),
            {}
        )

    def generate(
        self,
        prompt: str,
        model: str = None,
        **kwargs
    ) -> str:
        if self.client is None:
            raise ImportError("anthropic package is required but not installed. Please install it with 'pip install anthropic'")
            
        try:
            # Get model configuration
            config = self.model_config.get("config", {})
            
            # Prepare parameters
            params = {
                "model": model or self.model_config.get("name", "claude-3-opus-20240229"),
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": config.get("max_length", 4096),
                "temperature": config.get("temperature", 0.7),
                "top_p": config.get("top_p", 0.95)
            }
            params.update(kwargs)
            
            # Make API call
            response = self.client.messages.create(**params)
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            raise

def get_connector(provider: str, api_key: Optional[str] = None) -> APIConnector:
    """Get the appropriate API connector for a provider.
    
    Args:
        provider: The provider name (e.g., "openai", "anthropic", "deepseek-ai")
        api_key: Optional API key. If not provided, will try to get from environment
        
    Returns:
        An instance of the appropriate APIConnector
    """
    connectors = {
        "openai": OpenAIConnector,
        "anthropic": AnthropicConnector,
        "deepseek": DeepseekConnector,
        "deepseek-ai": DeepseekConnector,
        "deepseekai": DeepseekConnector
    }
    
    # Normalize provider name
    provider = provider.lower()
    if provider == "deepseek-ai" or provider == "deepseekai":
        provider = "deepseek"
    
    connector_class = connectors.get(provider)
    
    if not connector_class:
        raise ValueError(f"Unsupported provider: {provider}")
    
    return connector_class(api_key)

# Usage example:
"""
# Initialize a connector
connector = get_connector("openai", "your-api-key")

# Generate text
response = connector.generate(
    prompt="Write a hello world program in Python",
    model="gpt-4",
    temperature=0.7
)
"""
