LoadModel
=========

Model Loading System
-----------------

.. automodule:: memories.models.load_model
   :members:
   :undoc-members:
   :show-inheritance:

LoadModel Class
-------------

.. autoclass:: memories.models.load_model.LoadModel
   :members:
   :undoc-members:
   :show-inheritance:

Model Types
---------

Base Model
~~~~~~~~~

.. autoclass:: memories.models.base.BaseModel
   :members:
   :undoc-members:
   :show-inheritance:

Embedding Model
~~~~~~~~~~~~~

.. autoclass:: memories.models.embedding.EmbeddingModel
   :members:
   :undoc-members:
   :show-inheritance:

Language Model
~~~~~~~~~~~~

.. autoclass:: memories.models.language.LanguageModel
   :members:
   :undoc-members:
   :show-inheritance:

Example Usage
-----------

.. code-block:: python

    from memories import LoadModel
    
    # Initialize model loader
    model_loader = LoadModel()
    
    # Load a language model
    language_model = model_loader.load_language_model(
        model_name="gpt-3.5-turbo",
        model_type="chat",
        api_key="your-api-key"
    )
    
    # Load an embedding model
    embedding_model = model_loader.load_embedding_model(
        model_name="text-embedding-3-small",
        api_key="your-api-key"
    )
    
    # Use the models
    response = language_model.generate("What is the weather like?")
    embeddings = embedding_model.encode("Some text to embed") 