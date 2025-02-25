# Models

This directory contains the model management and API connector implementations for the Memories project. The system is designed to be modular and extensible, making it easy to add support for new models and providers.

## What's New in Version 2.0.2

### New Model Providers
- **DeepSeek AI**: Added support for DeepSeek's code and language models
- **Mistral AI**: Integrated Mistral's efficient language models
- **Cohere**: Added support for Cohere's embedding and generation models
- **Local Models**: Enhanced support for running models locally with optimized inference

### Improvements
- **Multi-model Inference**: Compare results from multiple models in parallel
- **Streaming Responses**: Added streaming capability for all supported providers
- **Function Calling**: Support for OpenAI and Anthropic function calling APIs
- **Improved Caching**: Intelligent response caching to reduce API costs
- **Model Fallbacks**: Automatic fallback to alternative models when primary is unavailable

## Architecture

The models system consists of several key components:

### Core Components

- `base_model.py`: Base implementation for local model management
- `load_model.py`: High-level model loader that handles both local and API-based models
- `api_connector.py`: API connectors for various model providers
- `config/model_config.json`: Central configuration for all models and providers
- `streaming.py`: Streaming response handlers (New in 2.0.2)
- `caching.py`: Model response caching system (New in 2.0.2)
- `function_calling.py`: Function calling utilities (New in 2.0.2)

### Directory Structure

```
models/
├── README.md
├── __init__.py
├── base_model.py
├── load_model.py
├── api_connector.py
├── streaming.py
├── caching.py
├── function_calling.py
└── config/
    └── model_config.json
```

## Adding a New Model Provider

To add support for a new model provider:

1. Add the provider configuration to `config/model_config.json`:
```json
{
    "models": {
        "your-model-name": {
            "name": "provider/model-name",
            "provider": "your-provider",
            "type": "local",  # or "api"
            "config": {
                "max_length": 2048,
                "temperature": 0.7,
                "top_p": 0.95,
                "supports_streaming": true,
                "supports_function_calling": false
            }
        }
    }
}
```

2. Create a new connector class in `api_connector.py`:
```python
class YourProviderConnector(APIConnector):
    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        # Initialize your provider's client
        
    def generate(self, prompt: str, **kwargs) -> str:
        # Implement generation logic
        pass
        
    def generate_streaming(self, prompt: str, **kwargs) -> Iterator[str]:
        # Implement streaming logic
        pass
        
    def generate_with_functions(self, prompt: str, functions: List[Dict], **kwargs) -> Dict:
        # Implement function calling logic
        pass
```

3. Register the connector in the `get_connector` function:
```python
connectors = {
    "your-provider": YourProviderConnector,
    # ... existing connectors ...
}
```

## Using Models

### Local Models

```python
from memories.models.load_model import LoadModel

model = LoadModel(
    model_provider="your-provider",
    deployment_type="local",
    model_name="your-model-name"
)
response = model.get_response("Your prompt here")
```

### API-based Models

```python
from memories.models.load_model import LoadModel

model = LoadModel(
    model_provider="your-provider",
    deployment_type="api",
    model_name="your-model-name",
    api_key="your-api-key"
)
response = model.get_response("Your prompt here")
```

### Streaming Responses (New in 2.0.2)

```python
from memories.models.load_model import LoadModel

model = LoadModel(
    model_provider="openai",
    deployment_type="api",
    model_name="gpt-4",
    api_key="your-api-key"
)

# Get streaming response
for chunk in model.get_streaming_response("Your prompt here"):
    print(chunk, end="", flush=True)
```

### Function Calling (New in 2.0.2)

```python
from memories.models.load_model import LoadModel

model = LoadModel(
    model_provider="openai",
    deployment_type="api",
    model_name="gpt-4",
    api_key="your-api-key"
)

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
                }
            },
            "required": ["location"]
        }
    }
]

response = model.get_response_with_functions("What's the weather in New York?", functions=functions)
print(response)
```

### Multi-model Inference (New in 2.0.2)

```python
from memories.models.load_model import LoadModel
from memories.models.multi_model import MultiModelInference

# Initialize models
openai_model = LoadModel(
    model_provider="openai",
    deployment_type="api",
    model_name="gpt-4"
)

anthropic_model = LoadModel(
    model_provider="anthropic",
    deployment_type="api",
    model_name="claude-3-opus"
)

deepseek_model = LoadModel(
    model_provider="deepseek",
    deployment_type="api",
    model_name="deepseek-chat"
)

# Create multi-model inference
multi_model = MultiModelInference(
    models=[openai_model, anthropic_model, deepseek_model],
    aggregation_method="consensus"  # Options: "consensus", "voting", "best_confidence"
)

# Get responses from all models
results = multi_model.get_responses("Analyze this satellite image for urban development")

# Print results
for provider, response in results.items():
    print(f"{provider}: {response['text']}")

# Get aggregated response
consensus = multi_model.get_aggregated_response()
print(f"Consensus: {consensus}")
```

## Model Providers (Updated for 2.0.2)

### OpenAI
- Models: GPT-3.5-Turbo, GPT-4, GPT-4-Turbo
- Features: Streaming, Function Calling, Vision

### Anthropic
- Models: Claude 3 Opus, Claude 3 Sonnet, Claude 3 Haiku
- Features: Streaming, Tool Use, Vision

### DeepSeek AI (New in 2.0.2)
- Models: DeepSeek-Chat, DeepSeek-Coder
- Features: Streaming, Code Generation

### Mistral AI (New in 2.0.2)
- Models: Mistral-7B, Mixtral-8x7B, Mistral-Large
- Features: Streaming, Tool Use

### Cohere (New in 2.0.2)
- Models: Command, Command-R
- Features: Streaming, RAG Optimization

### Local Models
- Models: Llama 3, Phi-3, Gemma
- Features: Optimized Inference, Quantization

## Contributing

### Guidelines

1. **Code Style**
   - Follow PEP 8 guidelines
   - Use type hints
   - Include docstrings for all classes and methods
   - Add logging for important operations

2. **Error Handling**
   - Use appropriate exception types
   - Include meaningful error messages
   - Log errors with sufficient context
   - Handle cleanup properly

3. **Testing**
   - Add unit tests for new functionality
   - Include integration tests for API connectors
   - Test both success and error cases
   - Use mock objects for API calls in tests

### Adding a New Feature

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests
5. Update documentation
6. Submit a pull request

### Testing Your Changes

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Run tests:
```bash
python -m pytest tests/models/
```

3. Test with example script:
```bash
python examples/test_model.py
```

## Configuration

### Environment Variables

Required environment variables for different providers:

```bash
# OpenAI
export OPENAI_API_KEY="your-key-here"

# Anthropic
export ANTHROPIC_API_KEY="your-key-here"

# DeepSeek (New in 2.0.2)
export DEEPSEEK_API_KEY="your-key-here"

# Mistral AI (New in 2.0.2)
export MISTRAL_API_KEY="your-key-here"

# Cohere (New in 2.0.2)
export COHERE_API_KEY="your-key-here"
```

### Model Configuration

The `model_config.json` file contains all model-specific configurations:

- Model parameters (temperature, max length, etc.)
- Provider groupings
- Deployment types
- Global settings
- Streaming and function calling capabilities (New in 2.0.2)
- Fallback configurations (New in 2.0.2)

## Troubleshooting

Common issues and solutions:

1. **ImportError**: Make sure all required packages are installed
2. **API Errors**: Verify API key and model name
3. **Memory Issues**: Check GPU memory usage and cleanup
4. **Missing Configuration**: Ensure model_config.json is properly set up
5. **Streaming Errors**: Verify model supports streaming (New in 2.0.2)
6. **Function Calling Errors**: Check function schema format (New in 2.0.2)

## Support

- Create an issue for bugs or feature requests
- Join our discord channel for discussions

<p align="center">Built with 💜 by the memories-dev team</p>


