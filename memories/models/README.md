# Models Directory

This directory contains the model integration components for the Memories project. The models module is designed to be modular and extensible, allowing for easy integration with various model providers.

## What's New in Version 2.0.2 (Scheduled for February 25, 2025)

Since our initial release (v1.0.0 on February 14, 2025), we've made significant improvements to the model integration system:

### New Model Providers
- **DeepSeek AI**: Integration with DeepSeek's powerful coding and general-purpose models
- **Mistral AI**: Support for Mistral's efficient and high-performance models
- **Cohere**: Integration with Cohere's state-of-the-art embedding and generation models

### New Features
- **Multi-model Inference**: Compare results from multiple models in parallel
- **Streaming Responses**: Real-time streaming for all supported model providers
- **Function Calling**: Support for function calling with compatible models
- **Improved Caching**: More efficient caching strategies for repeated operations
- **Model Fallbacks**: Automatic fallback to alternative models when primary is unavailable

## Architecture

The models directory is structured around several core components:

- **base_model.py**: Abstract base class defining the interface for all model implementations
- **load_model.py**: Factory class for loading and initializing models
- **api_connector.py**: Base class for API-based model connections
- **streaming.py**: Utilities for handling streaming responses
- **caching.py**: Caching mechanisms for model responses
- **function_calling.py**: Utilities for function calling capabilities

## Adding a New Model Provider

To add a new model provider, you need to:

1. Create a new JSON configuration file in the `configs` directory:

```json
{
  "provider_name": "new-provider",
  "models": {
    "model-name-1": {
      "context_length": 8192,
      "supports_streaming": true,
      "supports_function_calling": false
    },
    "model-name-2": {
      "context_length": 16384,
      "supports_streaming": true,
      "supports_function_calling": true
    }
  },
  "api_base": "https://api.new-provider.com/v1",
  "requires_api_key": true
}
```

2. Create a new connector class that extends `APIConnector`:

```python
from memories.models.api_connector import APIConnector

class NewProviderConnector(APIConnector):
    def __init__(self, api_key, model_name, **kwargs):
        super().__init__(api_key=api_key, model_name=model_name, **kwargs)
        self.provider = "new-provider"
        
    async def generate(self, prompt, **kwargs):
        # Implementation for the specific API
        pass
        
    async def generate_stream(self, prompt, **kwargs):
        # Implementation for streaming
        pass
        
    async def function_call(self, prompt, functions, **kwargs):
        # Implementation for function calling
        pass
```

3. Register the new connector in `load_model.py`

## Usage Examples

### Local Models

```python
from memories.models.load_model import LoadModel

# Initialize local model
model = LoadModel(
    use_gpu=True,
    model_provider="deepseek-ai",
    deployment_type="local",
    model_name="deepseek-coder-small"
)

# Generate text
response = model.get_response("Write a function to calculate factorial")
print(response["text"])

# Clean up resources
model.cleanup()
```

### API-based Models

```python
from memories.models.load_model import LoadModel

# Initialize API-based model
model = LoadModel(
    model_provider="openai",
    deployment_type="api",
    model_name="gpt-4",
    api_key="your-api-key"
)

# Generate text with parameters
response = model.get_response(
    "Explain the impact of climate change on urban areas",
    temperature=0.7,
    max_tokens=500
)
print(response["text"])

# Clean up resources
model.cleanup()
```

### Streaming Responses

```python
from memories.models.load_model import LoadModel

# Initialize model with streaming support
model = LoadModel(
    model_provider="anthropic",
    deployment_type="api",
    model_name="claude-3-opus",
    api_key="your-api-key"
)

# Get streaming response
for chunk in model.get_streaming_response(
    "Write a short story about a robot that develops consciousness"
):
    print(chunk, end="", flush=True)

# Clean up resources
model.cleanup()
```

### Function Calling

```python
from memories.models.load_model import LoadModel

# Define functions
functions = [
    {
        "name": "get_weather",
        "description": "Get the current weather in a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "The temperature unit to use"
                }
            },
            "required": ["location"]
        }
    }
]

# Initialize model with function calling support
model = LoadModel(
    model_provider="openai",
    deployment_type="api",
    model_name="gpt-4",
    api_key="your-api-key"
)

# Call function
response = model.function_call(
    "What's the weather like in San Francisco?",
    functions=functions
)

print(f"Function: {response['function_name']}")
print(f"Arguments: {response['arguments']}")

# Clean up resources
model.cleanup()
```

### Multi-model Inference

```python
from memories.models.load_model import LoadModel
from memories.models.multi_model import MultiModelInference

# Initialize models
models = {
    "openai": LoadModel(
        model_provider="openai",
        deployment_type="api",
        model_name="gpt-4"
    ),
    "anthropic": LoadModel(
        model_provider="anthropic",
        deployment_type="api",
        model_name="claude-3-opus"
    ),
    "deepseek": LoadModel(
        model_provider="deepseek-ai",
        deployment_type="api",
        model_name="deepseek-chat"
    )
}

# Create multi-model inference
multi_model = MultiModelInference(models=models)

# Get responses from all models
responses = multi_model.get_responses(
    "Explain how satellite imagery can be used for urban planning"
)

# Print responses
for provider, response in responses.items():
    print(f"\n--- {provider.upper()} ---")
    print(response["text"])

# Clean up resources
multi_model.cleanup()
```

## Supported Model Providers

### OpenAI
- **Models**: gpt-4, gpt-4-turbo, gpt-3.5-turbo
- **Features**: Streaming, function calling, JSON mode
- **Deployment**: API only

### Anthropic
- **Models**: claude-3-opus, claude-3-sonnet, claude-3-haiku
- **Features**: Streaming, tool use
- **Deployment**: API only

### DeepSeek AI
- **Models**: deepseek-chat, deepseek-coder
- **Features**: Streaming, function calling
- **Deployment**: API and local

### Mistral AI
- **Models**: mistral-large, mistral-medium, mistral-small
- **Features**: Streaming, tool use
- **Deployment**: API only

### Cohere
- **Models**: command, command-light, command-r
- **Features**: Streaming, tool use
- **Deployment**: API only

### Local Models
- **Models**: Various open-source models
- **Features**: Depends on model capabilities
- **Deployment**: Local only (requires sufficient hardware)

## Coming in Version 2.1.0 (March 2025)

- **Function Calling**: Enhanced support for OpenAI and Anthropic function calling APIs
- **Multi-model Inference**: Compare results from multiple models in parallel with consensus mechanisms
- **Model Quantization**: Support for quantized models to reduce memory footprint
- **Custom Model Training**: Tools for fine-tuning models on custom datasets
- **Model Performance Metrics**: Comprehensive benchmarking and evaluation tools

## Contributing

We welcome contributions to the models module! Please see our [Contributing Guide](https://memories-dev.readthedocs.io/development/contributing.html) for more information.

<p align="center">Built with 💜 by the memories-dev team</p>


