import os
from typing import Dict, List, Optional, Union
import openai
from openai import OpenAI
import anthropic
import requests
import json

class APIConnector:
    """Base class for API connections to different LLM providers."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided either directly or through environment variables")

class OpenAIConnector(APIConnector):
    """Connector for OpenAI API."""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        self.client = OpenAI(api_key=self.api_key)

    def generate(
        self,
        prompt: str,
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

class DeepseekConnector(APIConnector):
    """Connector for Deepseek API."""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        self.api_base = "https://api.deepseek.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def generate(
        self,
        prompt: str,
        model: str = "deepseek-coder",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        try:
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
                **kwargs
            }
            
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            raise Exception(f"Deepseek API error: {str(e)}")

class AnthropicConnector(APIConnector):
    """Connector for Anthropic API (Claude)."""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def generate(
        self,
        prompt: str,
        model: str = "claude-3-opus-20240229",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        try:
            response = self.client.messages.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")

def get_connector(provider: str, api_key: str) -> APIConnector:
    """Factory function to get the appropriate connector based on provider."""
    connectors = {
        "openai": OpenAIConnector,
        "deepseek": DeepseekConnector,
        "anthropic": AnthropicConnector
    }
    
    if provider not in connectors:
        raise ValueError(f"Unsupported provider: {provider}. Supported providers are: {list(connectors.keys())}")
    
    return connectors[provider](api_key)

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
