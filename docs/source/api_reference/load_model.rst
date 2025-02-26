LoadModel
=========

Model Loading System
--------------------

.. automodule:: memories.models.load_model
   :members:
   :undoc-members:
   :show-inheritance:

LoadModel Class
---------------

.. autoclass:: memories.models.load_model.LoadModel
   :members:
   :undoc-members:
   :show-inheritance:

Model Types
-----------

Base Model
~~~~~~~~~~

.. autoclass:: memories.models.base_model.BaseModel
   :members:
   :undoc-members:
   :show-inheritance:

API Connectors
~~~~~~~~~~~~~~

.. autoclass:: memories.models.api_connector.APIConnector
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: memories.models.api_connector.OpenAIConnector
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: memories.models.api_connector.AnthropicConnector
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: memories.models.api_connector.DeepseekConnector
   :members:
   :undoc-members:
   :show-inheritance:

Example Usage
-------------

.. code-block:: python

    from memories.models.load_model import LoadModel
    
    # Initialize model with local deployment
    local_model = LoadModel(
        use_gpu=True,
        model_provider="deepseek-ai",
        deployment_type="local",
        model_name="deepseek-coder-small"
    )
    
    # Generate text with the local model
    response = local_model.get_response("Write a function to calculate factorial")
    print(response["text"])
    
    # Initialize model with API deployment
    api_model = LoadModel(
        model_provider="openai",
        deployment_type="api",
        model_name="gpt-4",
        api_key="your-api-key"  # Or set OPENAI_API_KEY environment variable
    )
    
    # Generate text with the API model
    response = api_model.get_response(
        "Explain quantum computing",
        temperature=0.7,
        max_tokens=500
    )
    print(response["text"])
    
    # Clean up resources when done
    local_model.cleanup() 