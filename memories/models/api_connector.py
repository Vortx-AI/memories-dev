"""API connectors for various model providers."""

import os
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging
from pathlib import Path
import requests
from datetime import datetime

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
        max_tokens: int = 30000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get chat completion from OpenAI API.
        
        Args:
            messages: List of message dictionaries
            tools: Optional list of tool definitions
            tool_choice: Optional tool choice ("auto" or "none")
            max_tokens: Maximum tokens allowed for the request
            **kwargs: Additional parameters for the API call
            
        Returns:
            API response as dictionary
        """
        try:
            # Estimate input tokens
            input_tokens = self.estimate_tokens(messages)
            
            if input_tokens > max_tokens:
                # Try to reduce message content
                messages = self.truncate_messages(messages, max_tokens)
                input_tokens = self.estimate_tokens(messages)
                
                if input_tokens > max_tokens:
                    return {
                        "error": f"Input too large ({input_tokens} tokens) even after truncation. Maximum is {max_tokens} tokens."
                    }
            
            params = {
                "messages": messages,
                "model": self.model_config.get("name", "gpt-4-turbo-preview"),
                "max_tokens": min(4096, max_tokens - input_tokens),  # Leave room for response
                **kwargs
            }
            
            if tools:
                params["tools"] = tools
            if tool_choice:
                params["tool_choice"] = tool_choice
                
            response = self.client.chat.completions.create(**params)
            return self._process_response(response)
            
        except Exception as e:
            logger.error(f"OpenAI chat completion error: {str(e)}")
            return {"error": str(e)}
            
    def estimate_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Estimate the number of tokens in the messages."""
        # Rough estimation: 1 token ≈ 4 characters for English text
        total_chars = sum(len(str(msg.get("content", ""))) for msg in messages)
        return total_chars // 4
        
    def truncate_messages(self, messages: List[Dict[str, str]], max_tokens: int) -> List[Dict[str, str]]:
        """Truncate messages to fit within token limit."""
        # Keep system message and last few user/assistant exchanges
        truncated = []
        total_chars = 0
        
        # Always keep system message if present
        if messages and messages[0]["role"] == "system":
            truncated.append(messages[0])
            total_chars += len(str(messages[0].get("content", "")))
            messages = messages[1:]
        
        # Keep most recent messages that fit within limit
        for msg in reversed(messages):
            msg_chars = len(str(msg.get("content", "")))
            if (total_chars + msg_chars) * 4 > max_tokens:
                break
            truncated.insert(1, msg)  # Insert after system message
            total_chars += msg_chars
            
        return truncated

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
