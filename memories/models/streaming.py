"""Streaming utilities for model responses."""

import asyncio
import logging
from typing import AsyncIterator, Dict, Any, Optional, Callable
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class StreamingResponse:
    """Handles streaming responses from model providers."""

    def __init__(self, provider: str, model_name: str):
        """Initialize streaming response handler.

        Args:
            provider: Model provider name
            model_name: Name of the model
        """
        self.provider = provider
        self.model_name = model_name
        self.chunks = []
        self.start_time = None
        self.end_time = None
        self.total_tokens = 0

    async def stream_response(
        self,
        stream_iterator: AsyncIterator[str],
        callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """Process streaming response.

        Args:
            stream_iterator: Async iterator yielding response chunks
            callback: Optional callback function called for each chunk

        Returns:
            Dict containing full response and metadata
        """
        self.start_time = datetime.now()
        full_response = ""
        chunk_count = 0

        try:
            async for chunk in stream_iterator:
                chunk_count += 1
                full_response += chunk
                self.chunks.append(chunk)

                # Call callback if provided
                if callback:
                    callback(chunk)

                logger.debug(f"Received chunk {chunk_count}: {len(chunk)} chars")

            self.end_time = datetime.now()
            generation_time = (self.end_time - self.start_time).total_seconds()

            return {
                "text": full_response,
                "chunks": self.chunks,
                "metadata": {
                    "provider": self.provider,
                    "model": self.model_name,
                    "chunk_count": chunk_count,
                    "generation_time": generation_time,
                    "start_time": self.start_time.isoformat(),
                    "end_time": self.end_time.isoformat(),
                    "total_chars": len(full_response)
                }
            }

        except Exception as e:
            logger.error(f"Error during streaming: {str(e)}", exc_info=True)
            raise


class OpenAIStreaming:
    """Handle OpenAI streaming responses."""

    def __init__(self, client, model_name: str):
        """Initialize OpenAI streaming handler.

        Args:
            client: OpenAI client instance
            model_name: Name of the OpenAI model
        """
        self.client = client
        self.model_name = model_name

    async def stream_chat_completion(
        self,
        messages: list,
        callback: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Stream chat completion from OpenAI.

        Args:
            messages: List of message dictionaries
            callback: Optional callback for each chunk
            **kwargs: Additional parameters

        Returns:
            Dict with full response and metadata
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=True,
                **kwargs
            )

            streaming_response = StreamingResponse("openai", self.model_name)

            async def chunk_iterator():
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content

            return await streaming_response.stream_response(
                chunk_iterator(),
                callback
            )

        except Exception as e:
            logger.error(f"OpenAI streaming error: {str(e)}", exc_info=True)
            raise


class AnthropicStreaming:
    """Handle Anthropic streaming responses."""

    def __init__(self, client, model_name: str):
        """Initialize Anthropic streaming handler.

        Args:
            client: Anthropic client instance
            model_name: Name of the Anthropic model
        """
        self.client = client
        self.model_name = model_name

    async def stream_completion(
        self,
        messages: list,
        callback: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Stream completion from Anthropic.

        Args:
            messages: List of message dictionaries
            callback: Optional callback for each chunk
            **kwargs: Additional parameters

        Returns:
            Dict with full response and metadata
        """
        try:
            # Convert messages to Anthropic format
            system_message = next(
                (msg["content"] for msg in messages if msg["role"] == "system"),
                None
            )
            conversation = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in messages if msg["role"] != "system"
            ]

            stream = self.client.messages.stream(
                model=self.model_name,
                messages=conversation,
                system=system_message if system_message else None,
                **kwargs
            )

            streaming_response = StreamingResponse("anthropic", self.model_name)

            async def chunk_iterator():
                with stream as s:
                    for text in s.text_stream:
                        yield text

            return await streaming_response.stream_response(
                chunk_iterator(),
                callback
            )

        except Exception as e:
            logger.error(f"Anthropic streaming error: {str(e)}", exc_info=True)
            raise


class DeepseekStreaming:
    """Handle DeepSeek streaming responses."""

    def __init__(self, api_base: str, api_key: str, model_name: str):
        """Initialize DeepSeek streaming handler.

        Args:
            api_base: DeepSeek API base URL
            api_key: DeepSeek API key
            model_name: Name of the DeepSeek model
        """
        self.api_base = api_base
        self.api_key = api_key
        self.model_name = model_name
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    async def stream_completion(
        self,
        messages: list,
        callback: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Stream completion from DeepSeek.

        Args:
            messages: List of message dictionaries
            callback: Optional callback for each chunk
            **kwargs: Additional parameters

        Returns:
            Dict with full response and metadata
        """
        import aiohttp

        try:
            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": True,
                **kwargs
            }

            streaming_response = StreamingResponse("deepseek", self.model_name)

            async def chunk_iterator():
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.api_base}/chat/completions",
                        headers=self.headers,
                        json=payload
                    ) as response:
                        async for line in response.content:
                            if line:
                                line_str = line.decode('utf-8').strip()
                                if line_str.startswith("data: "):
                                    data_str = line_str[6:]
                                    if data_str != "[DONE]":
                                        try:
                                            data = json.loads(data_str)
                                            if "choices" in data and len(data["choices"]) > 0:
                                                delta = data["choices"][0].get("delta", {})
                                                content = delta.get("content", "")
                                                if content:
                                                    yield content
                                        except json.JSONDecodeError:
                                            continue

            return await streaming_response.stream_response(
                chunk_iterator(),
                callback
            )

        except Exception as e:
            logger.error(f"DeepSeek streaming error: {str(e)}", exc_info=True)
            raise


async def stream_from_provider(
    provider: str,
    client: Any,
    messages: list,
    model_name: str,
    callback: Optional[Callable[[str], None]] = None,
    **kwargs
) -> Dict[str, Any]:
    """Stream response from any supported provider.

    Args:
        provider: Provider name (openai, anthropic, deepseek)
        client: Provider client instance
        messages: List of message dictionaries
        model_name: Name of the model
        callback: Optional callback for each chunk
        **kwargs: Additional parameters

    Returns:
        Dict with full response and metadata

    Raises:
        ValueError: If provider is not supported
    """
    provider = provider.lower()

    if provider == "openai":
        streaming = OpenAIStreaming(client, model_name)
        return await streaming.stream_chat_completion(messages, callback, **kwargs)
    elif provider == "anthropic":
        streaming = AnthropicStreaming(client, model_name)
        return await streaming.stream_completion(messages, callback, **kwargs)
    elif provider == "deepseek":
        api_base = kwargs.pop("api_base", "https://api.deepseek.com/v1")
        api_key = kwargs.pop("api_key")
        streaming = DeepseekStreaming(api_base, api_key, model_name)
        return await streaming.stream_completion(messages, callback, **kwargs)
    else:
        raise ValueError(f"Unsupported provider for streaming: {provider}")
