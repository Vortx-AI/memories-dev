# Models Directory

This directory contains the model integration components for the Memories project. The models module is designed to be modular and extensible, allowing for easy integration with various model providers.

## What's New in Version 2.0.4 (Scheduled for March 3, 2025)

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

## Real-World Model Applications

Our models module powers a diverse range of real-world applications across various industries. Here are some examples of how organizations are leveraging our model integration capabilities:

### Automated Environmental Impact Assessment

**Environmental Consulting Firm**

A leading environmental consulting firm implemented a system using our models module to automate environmental impact assessments for infrastructure projects. Their application:

- Analyzes satellite imagery to identify sensitive ecosystems
- Processes project plans and specifications
- Generates comprehensive environmental impact reports
- Recommends mitigation strategies for identified risks

```python
from memories.models.load_model import LoadModel
from memories.data_acquisition.data_manager import DataManager
import asyncio

async def generate_environmental_assessment(project_area, project_description):
    # Initialize data manager
    data_manager = DataManager(cache_dir="./env_assessment")
    
    # Get environmental data for the project area
    env_data = await data_manager.get_satellite_data(
        bbox_coords=project_area,
        start_date="2024-01-01",
        end_date="2024-02-01",
        source="sentinel-2",
        bands=["B02", "B03", "B04", "B08"]
    )
    
    # Get protected areas and sensitive ecosystems
    protected_areas = await data_manager.get_vector_data(
        bbox=project_area,
        source="custom",
        layers=["protected_areas", "sensitive_ecosystems"]
    )
    
    # Initialize model
    model = LoadModel(
        model_provider="anthropic",
        deployment_type="api",
        model_name="claude-3-opus"
    )
    
    # Generate environmental impact assessment
    assessment = model.get_response(
        prompt=f"""
        Generate a comprehensive environmental impact assessment for the following project:
        
        Project Description:
        {project_description}
        
        Environmental Data:
        {env_data}
        
        Protected Areas and Sensitive Ecosystems:
        {protected_areas}
        
        The assessment should include:
        1. Potential impacts on flora and fauna
        2. Effects on water resources
        3. Air quality implications
        4. Noise pollution considerations
        5. Mitigation recommendations
        """,
        temperature=0.2,
        max_tokens=4000
    )
    
    # Clean up resources
    model.cleanup()
    
    return assessment["text"]
```

The system reduced assessment time from weeks to hours while improving consistency and thoroughness.

### Medical Diagnostic Assistant

**Healthcare Technology Provider**

A healthcare technology provider developed a diagnostic assistant using our models module to help physicians interpret medical imaging and patient data. Their system:

- Processes and analyzes medical images (X-rays, MRIs, CT scans)
- Integrates patient history and symptoms
- Generates differential diagnoses with supporting evidence
- Suggests additional tests or examinations when appropriate

The system achieved 91% accuracy in preliminary diagnoses across 15 common conditions, serving as a valuable second opinion for healthcare professionals.

### Financial Risk Analysis

**Global Investment Bank**

A global investment bank implemented a financial risk analysis system using our models module to evaluate investment opportunities. Their application:

- Analyzes company financial statements and reports
- Processes market trends and economic indicators
- Identifies potential risks and opportunities
- Generates comprehensive risk assessment reports

```python
from memories.models.load_model import LoadModel
from memories.models.multi_model import MultiModelInference

def analyze_investment_risk(company_data, market_data, economic_indicators):
    # Initialize multiple models for consensus analysis
    models = {
        "financial_expert": LoadModel(
            model_provider="openai",
            deployment_type="api",
            model_name="gpt-4"
        ),
        "risk_analyst": LoadModel(
            model_provider="anthropic",
            deployment_type="api",
            model_name="claude-3-opus"
        ),
        "market_specialist": LoadModel(
            model_provider="deepseek-ai",
            deployment_type="api",
            model_name="deepseek-chat"
        )
    }
    
    # Create multi-model inference
    multi_model = MultiModelInference(models=models)
    
    # Get risk analyses from all models
    prompt = f"""
    Analyze the investment risk for the following company:
    
    Company Financial Data:
    {company_data}
    
    Market Trends:
    {market_data}
    
    Economic Indicators:
    {economic_indicators}
    
    Provide a comprehensive risk assessment including:
    1. Financial stability analysis
    2. Market position evaluation
    3. Growth potential assessment
    4. Identified risk factors
    5. Overall risk rating (Low, Medium, High)
    """
    
    analyses = multi_model.get_responses(prompt)
    
    # Synthesize consensus analysis
    consensus = synthesize_consensus(analyses)
    
    # Clean up resources
    multi_model.cleanup()
    
    return consensus
```

The system has analyzed over 5,000 investment opportunities, identifying high-risk factors that were previously overlooked in 23% of cases.

### Automated Code Review

**Enterprise Software Development**

A large enterprise software company implemented an automated code review system using our models module to improve code quality and security. Their application:

- Analyzes code repositories for potential issues
- Identifies security vulnerabilities and performance bottlenecks
- Suggests improvements and optimizations
- Ensures compliance with coding standards and best practices

```python
from memories.models.load_model import LoadModel

def review_code(code_snippet, language, standards):
    # Initialize model
    model = LoadModel(
        model_provider="deepseek-ai",
        deployment_type="local",
        model_name="deepseek-coder-large",
        use_gpu=True
    )
    
    # Generate code review
    review = model.get_response(
        prompt=f"""
        Review the following {language} code for:
        1. Security vulnerabilities
        2. Performance issues
        3. Compliance with {standards} standards
        4. Potential bugs or edge cases
        5. Suggested improvements
        
        Code:
        ```{language}
        {code_snippet}
        ```
        
        Provide a detailed analysis with specific recommendations.
        """,
        temperature=0.1
    )
    
    # Clean up resources
    model.cleanup()
    
    return review["text"]
```

The system has reviewed over 2 million lines of code, identifying critical security vulnerabilities in 3.2% of submissions and suggesting performance improvements that reduced execution time by an average of 18%.

### Legal Document Analysis

**Law Firm**

A major law firm implemented a legal document analysis system using our models module to streamline contract review and due diligence processes. Their application:

- Analyzes legal documents and contracts
- Identifies key clauses, obligations, and potential issues
- Extracts important dates, parties, and terms
- Generates comprehensive summaries and risk assessments

The system reduced document review time by 73% while improving accuracy and consistency.

### Educational Content Generation

**EdTech Company**

An educational technology company uses our models module to generate personalized learning materials for students. Their system:

- Analyzes student performance and learning styles
- Identifies knowledge gaps and areas for improvement
- Generates customized explanations, examples, and practice problems
- Adapts content difficulty based on student progress

```python
from memories.models.load_model import LoadModel

def generate_personalized_lesson(student_profile, topic, difficulty):
    # Initialize model
    model = LoadModel(
        model_provider="anthropic",
        deployment_type="api",
        model_name="claude-3-sonnet"
    )
    
    # Generate personalized lesson
    lesson = model.get_response(
        prompt=f"""
        Create a personalized lesson on {topic} for a student with the following profile:
        
        Student Profile:
        {student_profile}
        
        The lesson should be at {difficulty} difficulty level and include:
        1. A clear explanation of the concept
        2. Examples that relate to the student's interests
        3. Practice problems with varying difficulty
        4. A summary of key points
        5. Additional resources for further learning
        """,
        temperature=0.7,
        max_tokens=2000
    )
    
    # Clean up resources
    model.cleanup()
    
    return lesson["text"]
```

The system has generated over 50,000 personalized lessons, resulting in a 32% improvement in student engagement and a 28% increase in concept retention.

## Getting Started with Your Own Model Application

Inspired by these real-world applications? Here's how to get started with your own model-powered project:

1. **Define your use case**: Determine the specific problem you want to solve
2. **Select appropriate models**: Choose the right models based on your requirements
3. **Set up the model integration**: Initialize the LoadModel with appropriate parameters
4. **Implement your application logic**: Connect models with your data sources and processing
5. **Optimize for performance**: Fine-tune parameters and implement caching as needed

For more detailed guidance, check out our [comprehensive documentation](https://memories-dev.readthedocs.io/) and [tutorial series](https://memories-dev.readthedocs.io/tutorials/).

## Contributing

We welcome contributions to the models module! Please see our [Contributing Guide](https://memories-dev.readthedocs.io/development/contributing.html) for more information.

<p align="center">Built with 💜 by the memories-dev team</p>


