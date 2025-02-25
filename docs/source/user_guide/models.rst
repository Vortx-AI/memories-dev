Models
======

.. image:: /_static/images/model_system_workflow.txt
   :alt: Model System Workflow
   :align: center

Overview
--------

The memories-dev framework provides a flexible and powerful model system that supports both local and API-based models. This allows you to choose the most appropriate deployment option based on your requirements for performance, cost, and privacy.

Supported Model Providers
-----------------------

- **OpenAI**: GPT-4, GPT-3.5-Turbo, and other models via API
- **Anthropic**: Claude models via API
- **DeepSeek AI**: DeepSeek-Coder and other models (local or API)
- **Mistral AI**: Mistral models via API
- **Meta**: Llama 2, Llama 3, and other open models (local)
- **Local Models**: Support for any Hugging Face compatible model

Deployment Types
--------------

1. **Local Deployment**
   - Models run directly on your hardware
   - Full control over inference parameters
   - No data sent to external services
   - Requires appropriate hardware (especially for larger models)

2. **API Deployment**
   - Models accessed through provider APIs
   - No local compute requirements
   - Pay-per-use pricing
   - Internet connection required

Basic Usage
----------

Using the LoadModel Class
~~~~~~~~~~~~~~~~~~~~~~~

The ``LoadModel`` class provides a unified interface for all model types:

.. code-block:: python

    from memories.models.load_model import LoadModel
    
    # Initialize a local model
    local_model = LoadModel(
        use_gpu=True,
        model_provider="deepseek-ai",
        deployment_type="local",
        model_name="deepseek-coder-small"
    )
    
    # Generate text with the local model
    response = local_model.get_response("Write a function to calculate factorial")
    print(response["text"])
    
    # Clean up resources when done
    local_model.cleanup()

Example Output:

.. code-block:: python

    def factorial(n):
        """
        Calculate the factorial of a non-negative integer n.
        
        Args:
            n (int): A non-negative integer
            
        Returns:
            int: The factorial of n
        """
        if n < 0:
            raise ValueError("Factorial is not defined for negative numbers")
        
        if n == 0 or n == 1:
            return 1
        
        result = 1
        for i in range(2, n + 1):
            result *= i
            
        return result

Using API-Based Models
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from memories.models.load_model import LoadModel
    import os
    
    # Set API key in environment variable
    os.environ["OPENAI_API_KEY"] = "your-api-key"
    
    # Initialize an API-based model
    api_model = LoadModel(
        model_provider="openai",
        deployment_type="api",
        model_name="gpt-4"
    )
    
    # Generate text with custom parameters
    response = api_model.get_response(
        "Explain quantum computing in simple terms",
        temperature=0.7,
        max_tokens=500
    )
    
    print(response["text"])
    
    # Clean up resources
    api_model.cleanup()

Advanced Usage
-----------

Model Comparison
~~~~~~~~~~~~~~

Compare results from different models:

.. code-block:: python

    from memories.models.load_model import LoadModel
    import asyncio
    
    async def compare_models(prompt):
        # Initialize models
        models = [
            LoadModel(model_provider="openai", deployment_type="api", model_name="gpt-4"),
            LoadModel(model_provider="anthropic", deployment_type="api", model_name="claude-3-opus"),
            LoadModel(model_provider="deepseek-ai", deployment_type="local", model_name="deepseek-coder-small")
        ]
        
        results = {}
        
        # Generate responses from each model
        for model in models:
            response = model.get_response(prompt)
            results[model.model_name] = response["text"]
            model.cleanup()
        
        return results
    
    # Compare models on a specific task
    prompt = "Write a function to find prime numbers up to n using the Sieve of Eratosthenes"
    comparison = asyncio.run(compare_models(prompt))
    
    # Display results
    for model, response in comparison.items():
        print(f"\n--- {model} ---\n")
        print(response[:300] + "..." if len(response) > 300 else response)

Streaming Responses
~~~~~~~~~~~~~~~~

For models that support streaming:

.. code-block:: python

    from memories.models.load_model import LoadModel
    import time
    
    # Initialize model with streaming support
    model = LoadModel(
        model_provider="openai",
        deployment_type="api",
        model_name="gpt-4"
    )
    
    # Generate streaming response
    prompt = "Write a short story about a robot learning to paint"
    
    for chunk in model.get_streaming_response(prompt):
        print(chunk, end="", flush=True)
        time.sleep(0.05)  # Simulate real-time streaming
    
    print("\n\nGeneration complete!")
    
    # Clean up
    model.cleanup()

Function Calling
~~~~~~~~~~~~~

For models that support function calling:

.. code-block:: python

    from memories.models.load_model import LoadModel
    import json
    
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
    
    # Initialize model
    model = LoadModel(
        model_provider="openai",
        deployment_type="api",
        model_name="gpt-4"
    )
    
    # Generate response with function calling
    response = model.get_response(
        "What's the weather like in San Francisco?",
        functions=functions,
        function_call={"name": "get_weather"}
    )
    
    # Process function call
    if response.get("function_call"):
        function_name = response["function_call"]["name"]
        function_args = json.loads(response["function_call"]["arguments"])
        
        print(f"Function called: {function_name}")
        print(f"Arguments: {function_args}")
        
        # In a real application, you would call the actual function here
        if function_name == "get_weather":
            # Simulate weather API response
            weather_result = {
                "temperature": 68,
                "unit": function_args.get("unit", "fahrenheit"),
                "description": "Partly cloudy",
                "location": function_args["location"]
            }
            
            # Send the result back to the model
            final_response = model.get_response(
                "What's the weather like in San Francisco?",
                functions=functions,
                function_call={"name": "get_weather"},
                function_response=weather_result
            )
            
            print("\nFinal response:")
            print(final_response["text"])
    
    # Clean up
    model.cleanup()

Multi-Model Inference
~~~~~~~~~~~~~~~~~~

Using multiple models in a pipeline:

.. code-block:: python

    from memories.models.load_model import LoadModel
    
    # Initialize models for different tasks
    code_model = LoadModel(
        model_provider="deepseek-ai",
        deployment_type="local",
        model_name="deepseek-coder-small"
    )
    
    explanation_model = LoadModel(
        model_provider="openai",
        deployment_type="api",
        model_name="gpt-4"
    )
    
    # Generate code with the specialized code model
    code_prompt = "Write a Python function to detect edges in an image using the Sobel operator"
    code_response = code_model.get_response(code_prompt)
    generated_code = code_response["text"]
    
    # Generate explanation with a more capable general model
    explanation_prompt = f"Explain the following code in simple terms:\n\n{generated_code}"
    explanation_response = explanation_model.get_response(explanation_prompt)
    explanation = explanation_response["text"]
    
    # Display results
    print("GENERATED CODE:")
    print("==============")
    print(generated_code)
    print("\nEXPLANATION:")
    print("===========")
    print(explanation)
    
    # Clean up
    code_model.cleanup()
    explanation_model.cleanup()

.. image:: /_static/images/model_analysis_result.txt
   :alt: Model Analysis Result
   :align: center

GPU Acceleration
--------------

For models that support GPU acceleration:

.. code-block:: python

    from memories.models.load_model import LoadModel
    from memories.utils.processors.gpu_stat import check_gpu_memory
    import time
    
    # Check available GPU memory
    gpu_stats = check_gpu_memory()
    if gpu_stats:
        print(f"GPU Memory: {gpu_stats['free']/1024**3:.2f}GB free out of {gpu_stats['total']/1024**3:.2f}GB total")
        use_gpu = True
    else:
        print("No GPU available, using CPU")
        use_gpu = False
    
    # Initialize model with GPU if available
    start_time = time.time()
    
    model = LoadModel(
        model_provider="meta",
        deployment_type="local",
        model_name="llama-2-7b",
        use_gpu=use_gpu
    )
    
    load_time = time.time() - start_time
    print(f"Model loaded in {load_time:.2f} seconds")
    
    # Generate text and measure performance
    prompt = "Explain the theory of relativity"
    
    start_time = time.time()
    response = model.get_response(prompt)
    generation_time = time.time() - start_time
    
    print(f"Text generated in {generation_time:.2f} seconds")
    print(f"Generation speed: {len(response['text'])/generation_time:.2f} characters per second")
    
    # Clean up
    model.cleanup()

Best Practices
------------

1. **Model Selection**:
   - Choose the right model for your task (code generation, text generation, etc.)
   - Consider the trade-offs between local and API-based models
   - Start with smaller models and scale up as needed

2. **Resource Management**:
   - Always call `cleanup()` when done with a model
   - Monitor GPU memory usage for local models
   - Use streaming for long responses to improve user experience

3. **Cost Optimization**:
   - Cache results for common queries
   - Use token counting to estimate API costs
   - Consider batching requests when appropriate

4. **Performance Optimization**:
   - Use GPU acceleration when available
   - Implement proper prompt engineering
   - Consider quantized models for faster inference 