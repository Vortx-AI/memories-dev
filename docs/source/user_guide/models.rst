Models
======

.. code-block:: text
   
Overview
--------

The memories-dev framework provides a flexible and powerful model system that supports both local and API-based models. This allows you to choose the most appropriate deployment option based on your requirements for performance, cost, and privacy.

Supported Model Providers
-------------------------

- **OpenAI**: GPT-4, GPT-3.5-Turbo, and other models via API
- **Anthropic**: Claude models via API
- **DeepSeek AI**: DeepSeek-Coder and other models (local or API)
- **Mistral AI**: Mistral models via API
- **Meta**: Llama 2, Llama 3, and other open models (local)
- **Local Models**: Support for any Hugging Face compatible model

Deployment Types
----------------

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
-----------

Using the LoadModel Class
~~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~~

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
--------------

Model Comparison
~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~

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

.. code-block:: text
   
=====================
   
   Query: "Analyze urban development in this region over the past year"
   Model: DeepSeek-Coder-Small
   Deployment: Local (GPU)

Analysis Results
---------------

Findings
--------
- Significant vegetation changes in urban areas
- Clear development patterns along transport corridors
- Strong correlation with climate impacts

Environmental Impact
------------------
- Heat island mitigation through green spaces
- Improved air quality in vegetated areas
- Enhanced ecosystem resilience

Recommendations
-------------
- Expand green infrastructure initiatives
- Optimize urban density planning
- Implement climate adaptation measures

GPU Acceleration
----------------

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
--------------

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

.. mermaid::

    flowchart TD
        A1[Satellite Imagery APIs]
        A2[Historical Maps]
        A3[GIS Data Sources]
        A4[Environmental Data]
        A5[Socioeconomic Data]

        subgraph MemoryManagement["Memory Management Layer"]
            B1[Temporal Memory Manager]
            B2[Spatial Memory Manager]
            B3[Context Memory Manager]
            B4[Relationship Memory Manager]
        end

        subgraph ModelIntegration["Model Integration Layer"]
            C1[Computer Vision Models]
            C2[NLP Models]
            C3[Time Series Models]
            C4[Geospatial Models]
            C5[Multi-Modal Models]
        end

        subgraph ApplicationLayer["Application Layer"]
            D1[Real Estate Analysis]
            D2[Urban Planning]
            D3[Environmental Monitoring]
            D4[Historical Research]
            D5[Disaster Response]
        end

        A1 & A2 & A3 & A4 & A5 --> B1 & B2 & B3 & B4
        B1 & B2 & B3 & B4 --> C1 & C2 & C3 & C4 & C5
        C1 & C2 & C3 & C4 & C5 --> D1 & D2 & D3 & D4 & D5

        classDef acquisition fill:#3b82f6,color:#fff,stroke:#2563eb
        classDef memory fill:#10b981,color:#fff,stroke:#059669
        classDef model fill:#8b5cf6,color:#fff,stroke:#7c3aed
        classDef application fill:#f59e0b,color:#fff,stroke:#d97706

        class A1,A2,A3,A4,A5 acquisition
        class B1,B2,B3,B4 memory
        class C1,C2,C3,C4,C5 model
        class D1,D2,D3,D4,D5 application

.. mermaid::

    flowchart TD
        A[Data Sources]
        B[Preprocessing]
        C[Memory System]
        D[Memory Layer]
        E[Analysis Layer]
        F[Model Integration Layer]
        G[Application Layer]

        A --> B
        B --> C
        C --> D
        D --> E
        E --> F
        F --> G

        B -.-> D
        D -.-> C
        E -.-> D
        F -.-> D

        style A fill:#1e40af,color:white
        style B fill:#1d4ed8,color:white
        style C fill:#b91c1c,color:white
        style D fill:#047857,color:white
        style E fill:#7c3aed,color:white
        style F fill:#6d28d9,color:white
        style G fill:#9a3412,color:white

.. mermaid::

    flowchart TD
        A[Raw Data]
        B[Data Preprocessing]
        C1[Data Cleaning]
        C2[Feature Extraction]
        C3[Temporal Alignment]
        C4[Spatial Registration]
        D[Processed Data]

        A --> B
        B --> C1
        B --> C2
        B --> C3
        B --> C4

        C1 & C2 & C3 & C4 --> D

        style A fill:#1d4ed8,color:white
        style B fill:#b91c1c,color:white
        style C1 fill:#b91c1c,color:white
        style C2 fill:#b91c1c,color:white
        style C3 fill:#b91c1c,color:white
        style C4 fill:#b91c1c,color:white
        style D fill:#b91c1c,color:white 