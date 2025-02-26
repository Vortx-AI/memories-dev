Models
======

Model Loading
-------------

.. automodule:: memories.models.load_model
   :members:
   :undoc-members:
   :show-inheritance:

Base Model
----------

.. autoclass:: memories.models.base_model.BaseModel
   :members:
   :undoc-members:
   :show-inheritance:

API Connectors
--------------

.. automodule:: memories.models.api_connector
   :members:
   :undoc-members:
   :show-inheritance:

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

Deployment Types
----------------

The system supports two deployment types:

1. **Local Deployment**: Models are loaded and run locally on your machine
2. **API Deployment**: Models are accessed through provider APIs (OpenAI, Anthropic, Deepseek)

Supported Providers
-------------------

- **deepseek-ai**: Models from Deepseek AI
- **openai**: Models from OpenAI
- **anthropic**: Models from Anthropic
- **meta**: Models from Meta
- **mistral**: Models from Mistral AI 