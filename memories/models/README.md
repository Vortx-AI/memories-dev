# Models

This directory contains the model management and API connector implementations for the Memories project. The system is designed to be modular and extensible, making it easy to add support for new models and providers.

## Architecture

The models system consists of several key components:

### Core Components

- `base_model.py`: Base implementation for local model management
- `load_model.py`: High-level model loader that handles both local and API-based models
- `api_connector.py`: API connectors for various model providers
- `config/model_config.json`: Central configuration for all models and providers

### Directory Structure

```
models/
├── README.md
├── __init__.py
├── base_model.py
├── load_model.py
├── api_connector.py
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
            "type": "local",  // or "api"
            "config": {
                "max_length": 2048,
                "temperature": 0.7,
                "top_p": 0.95
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

# Deepseek
export DEEPSEEK_API_KEY="your-key-here"
```

### Model Configuration

The `model_config.json` file contains all model-specific configurations:

- Model parameters (temperature, max length, etc.)
- Provider groupings
- Deployment types
- Global settings

## Troubleshooting

Common issues and solutions:

1. **ImportError**: Make sure all required packages are installed
2. **API Errors**: Verify API key and model name
3. **Memory Issues**: Check GPU memory usage and cleanup
4. **Missing Configuration**: Ensure model_config.json is properly set up

## Support

- Create an issue for bugs or feature requests
- Join our discord channel for discussions


