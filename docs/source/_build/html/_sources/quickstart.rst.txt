Quick Start Guide
===============

Basic Usage
----------

Here's a simple example to get you started with memories-dev:

.. code-block:: python

    from memories.models.load_model import LoadModel
    from memories.core.memory import MemoryStore
    from memories.agents.agent import Agent

    # Initialize with advanced models
    load_model = LoadModel(
        use_gpu=True,
        model_provider="deepseek-ai",  # "deepseek" or "openai"
        deployment_type="local",  # "local" or "api"
        model_name="deepseek-r1-zero"  # "deepseek-r1-zero" or "gpt-4o"
    )

    # Create Earth memories
    memory_store = MemoryStore()

    memories = memory_store.create_memories(
        model=load_model,
        location=(37.7749, -122.4194),  # San Francisco coordinates
        time_range=("2024-01-01", "2024-02-01"),
        artifacts={
            "satellite": ["sentinel-2", "landsat8"],
            "landuse": ["osm", "overture"]
        }
    )

    # Generate synthetic data
    synthetic_data = vx.generate_synthetic(
        base_location=(37.7749, -122.4194),
        scenario="urban_development",
        time_steps=10,
        climate_factors=True
    )

    # AGI reasoning with memories
    insights = Agent(
        query="Analyze urban development patterns and environmental impact",
        context_memories=memories,
        synthetic_scenarios=synthetic_data
    )

Key Features
-----------

1. Memory Formation
~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Create memories from various data sources
    memories = memory_store.create_memories(
        location=(37.7749, -122.4194),
        time_range=("2024-01-01", "2024-02-01")
    )

2. Memory Querying
~~~~~~~~~~~~~~~~

.. code-block:: python

    # Query memories based on location and context
    results = memory_store.query_memories(
        query="urban development",
        location_radius_km=10
    )

3. Agent Integration
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Use agents for analysis
    agent = Agent(
        query="Analyze patterns",
        context_memories=memories
    )
    insights = agent.analyze() 