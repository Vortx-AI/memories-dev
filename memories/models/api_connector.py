"""API connectors for various model providers."""

import os
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging
from pathlib import Path
import requests
from datetime import datetime
import time

from dotenv import load_dotenv

# Azure AI imports


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
    
    @abstractmethod
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a chat completion from messages and optional tools."""
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

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a chat completion using the OpenAI API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            tools: Optional list of tools/functions the model can use
            tool_choice: How to handle tool selection ("auto", "none", or specific)
            **kwargs: Additional parameters for the API call
            
        Returns:
            Dict containing the response message, tool calls, and metadata
        """
        if self.client is None:
            raise RuntimeError("OpenAI client is not initialized")
            
        try:
            logger.info(f"Preparing OpenAI chat completion request")
            logger.debug(f"Messages: {messages}")
            logger.debug(f"Tools: {tools}")
            
            # Get model configuration
            config = self.model_config.get("config", {})
            
            # Prepare parameters
            params = {
                "model": kwargs.pop("model", self.model_config.get("name", "gpt-4-turbo-preview")),
                "messages": messages,
                "temperature": kwargs.pop("temperature", config.get("temperature", 0.7)),
                "max_tokens": kwargs.pop("max_tokens", config.get("max_length", 1000)),
                "top_p": kwargs.pop("top_p", config.get("top_p", 0.95))
            }
            
            # Add tools if provided
            if tools:
                params["tools"] = tools
                params["tool_choice"] = tool_choice
                
            # Add any remaining kwargs
            params.update(kwargs)
            
            logger.info("Sending chat completion request to OpenAI API...")
            start_time = datetime.now()
            
            # Make API call
            response = self.client.chat.completions.create(**params)
            
            end_time = datetime.now()
            generation_time = (end_time - start_time).total_seconds()
            logger.info("Response received from OpenAI API")
            
            # Process response
            message = {
                "role": "assistant",
                "content": response.choices[0].message.content,
            }
            
            # Extract tool calls if any
            tool_calls = []
            if hasattr(response.choices[0].message, "tool_calls") and response.choices[0].message.tool_calls:
                tool_calls = [
                    {
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    }
                    for tool_call in response.choices[0].message.tool_calls
                ]
                message["tool_calls"] = tool_calls
            
            # Prepare metadata
            metadata = {
                "model": response.model,
                "total_tokens": response.usage.total_tokens,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "generation_time": generation_time,
                "finish_reason": response.choices[0].finish_reason
            }
            
            return {
                "message": message,
                "tool_calls": tool_calls,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"OpenAI chat completion error: {str(e)}", exc_info=True)
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

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a chat completion using the Deepseek API.
        Note: Tool usage may not be supported by all Deepseek models.
        """
        if not self.api_key:
            raise RuntimeError("Deepseek API key not found")

        try:
            logger.info("Preparing Deepseek chat completion request")
            config = self.model_config.get("config", {})

            # Prepare headers and data
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": kwargs.pop("model", self.model_config.get("name", "deepseek-chat")),
                "messages": messages,
                "temperature": kwargs.pop("temperature", config.get("temperature", 0.7)),
                "max_tokens": kwargs.pop("max_tokens", config.get("max_length", 1000)),
                "top_p": kwargs.pop("top_p", config.get("top_p", 0.95))
            }

            # Add tools if supported by the model
            if tools:
                data["tools"] = tools
                data["tool_choice"] = tool_choice

            # Add remaining kwargs
            data.update(kwargs)

            logger.info("Sending chat completion request to Deepseek API...")
            start_time = datetime.now()

            # Make API call
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()

            end_time = datetime.now()
            generation_time = (end_time - start_time).total_seconds()
            logger.info("Response received from Deepseek API")

            # Process response
            message = {
                "role": "assistant",
                "content": result["choices"][0]["message"]["content"]
            }

            # Extract tool calls if present
            tool_calls = []
            if "tool_calls" in result["choices"][0]["message"]:
                tool_calls = result["choices"][0]["message"]["tool_calls"]
                message["tool_calls"] = tool_calls

            # Prepare metadata
            metadata = {
                "model": result["model"],
                "total_tokens": result["usage"]["total_tokens"],
                "prompt_tokens": result["usage"]["prompt_tokens"],
                "completion_tokens": result["usage"]["completion_tokens"],
                "generation_time": generation_time,
                "finish_reason": result["choices"][0]["finish_reason"]
            }

            return {
                "message": message,
                "tool_calls": tool_calls,
                "metadata": metadata
            }

        except Exception as e:
            logger.error(f"Deepseek chat completion error: {str(e)}", exc_info=True)
            raise

class AnthropicConnector(APIConnector):
    """Connector for Anthropic API."""
    
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

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a chat completion using the Anthropic API.
        Note: Tool usage may not be supported by all Anthropic models.
        """
        if not self.api_key:
            raise RuntimeError("Anthropic API key not found")

        try:
            logger.info("Preparing Anthropic chat completion request")
            config = self.model_config.get("config", {})

            # Prepare headers and data
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }

            # Convert messages to Anthropic format
            system_message = next((msg["content"] for msg in messages if msg["role"] == "system"), None)
            conversation = [
                {"role": "assistant" if msg["role"] == "assistant" else "user", "content": msg["content"]}
                for msg in messages if msg["role"] != "system"
            ]

            data = {
                "model": kwargs.pop("model", self.model_config.get("name", "claude-3-opus-20240229")),
                "messages": conversation,
                "temperature": kwargs.pop("temperature", config.get("temperature", 0.7)),
                "max_tokens": kwargs.pop("max_tokens", config.get("max_length", 1000)),
                "top_p": kwargs.pop("top_p", config.get("top_p", 0.95))
            }

            # Add system message if present
            if system_message:
                data["system"] = system_message

            # Add tools if supported by the model
            if tools:
                data["tools"] = tools
                data["tool_choice"] = tool_choice

            # Add remaining kwargs
            data.update(kwargs)

            logger.info("Sending chat completion request to Anthropic API...")
            start_time = datetime.now()

            # Make API call
            response = requests.post(
                f"{self.api_base}/messages",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()

            end_time = datetime.now()
            generation_time = (end_time - start_time).total_seconds()
            logger.info("Response received from Anthropic API")

            # Process response
            message = {
                "role": "assistant",
                "content": result["content"][0]["text"]
            }

            # Extract tool calls if present
            tool_calls = []
            if "tool_calls" in result:
                tool_calls = result["tool_calls"]
                message["tool_calls"] = tool_calls

            # Prepare metadata
            metadata = {
                "model": result["model"],
                "total_tokens": result.get("usage", {}).get("total_tokens"),
                "prompt_tokens": result.get("usage", {}).get("prompt_tokens"),
                "completion_tokens": result.get("usage", {}).get("completion_tokens"),
                "generation_time": generation_time,
                "finish_reason": result.get("stop_reason")
            }

            return {
                "message": message,
                "tool_calls": tool_calls,
                "metadata": metadata
            }

        except Exception as e:
            logger.error(f"Anthropic chat completion error: {str(e)}", exc_info=True)
            raise

class AzureAIConnector(APIConnector):
    """Connector for Azure AI API."""
    
    def __init__(self, api_key: str = None, endpoint: str = None):
        try:
            from azure.ai.inference import ChatCompletionsClient
            from azure.core.credentials import AzureKeyCredential
        except ImportError:
            raise ImportError(
                "Azure AI dependencies not found. Please install them with: pip install azure-ai-inference"
            )
            
        super().__init__(api_key)
        # Get Azure credentials from environment or parameters
        self.api_key = api_key or self._get_api_key()
        self.endpoint = endpoint or os.getenv("AZURE_ENDPOINT")
        
        if not self.api_key or not self.endpoint:
            raise ValueError("Azure API key and endpoint are required")
            
        self.credential = AzureKeyCredential(self.api_key)
        self.client = ChatCompletionsClient(self.endpoint, self.credential)

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate chat completion using Azure AI API."""
        try:
            start_time = time.time()
            
            # Prepare the request payload
            payload = {
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", 2048)
            }
            
            # Add tools if provided
            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = tool_choice
            
            # Get chat completion
            response = self.client.complete(payload)
            generation_time = time.time() - start_time
            
            # Extract message content
            message = response.choices[0].message.content
            
            # Extract tool calls if present
            tool_calls = []
            if hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls:
                tool_calls = [
                    {
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    }
                    for tool_call in response.choices[0].message.tool_calls
                ]
            
            # Prepare metadata
            metadata = {
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "total_tokens": response.usage.total_tokens,
                    "completion_tokens": response.usage.completion_tokens
                },
                "generation_time": generation_time
            }
            
            return {
                "message": message,
                "tool_calls": tool_calls,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Azure AI chat completion error: {str(e)}")
            raise

    def generate(self, prompt: str, model: str = None, **kwargs) -> str:
        """Generate text using Azure AI.
        
        Args:
            prompt: Input prompt
            model: Model name (optional)
            **kwargs: Additional arguments
            
        Returns:
            Generated text
        """
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", 2048)
        }
        response = self.client.complete(payload)
        return response.choices[0].message.content

def get_connector(provider: str, api_key: Optional[str] = None, endpoint: Optional[str] = None) -> APIConnector:
    """Get the appropriate API connector based on provider.
    
    Args:
        provider: Name of the API provider (openai, azure-ai, anthropic, deepseek)
        api_key: Optional API key
        endpoint: Optional endpoint URL (for Azure)
        
    Returns:
        APIConnector instance
        
    Raises:
        ValueError: If provider is not supported
    """
    provider = provider.lower()
    
    if provider == "openai":
        return OpenAIConnector(api_key)
    elif provider == "anthropic":
        return AnthropicConnector(api_key)
    elif provider == "deepseek":
        return DeepseekConnector(api_key)
    elif provider == "azure-ai":
        try:
            return AzureAIConnector(api_key, endpoint)
        except ImportError as e:
            logger.warning(f"Azure AI dependencies not available: {str(e)}")
            logger.warning("Falling back to OpenAI connector")
            return OpenAIConnector(api_key)
    else:
        raise ValueError(f"Unsupported provider: {provider}")

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
