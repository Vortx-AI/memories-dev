Agents
======

Agent System
-----------

.. automodule:: memories.agents.agent
   :members:
   :undoc-members:
   :show-inheritance:

Base Agent
----------

.. autoclass:: memories.agents.agent.Agent
   :noindex:
   :members:
   :undoc-members:
   :show-inheritance:

Agent Types
----------

Memory Agent
~~~~~~~~~~~

.. autoclass:: memories.agents.agent.MemoryAgent
   :members:
   :undoc-members:
   :show-inheritance:

Conversation Agent
~~~~~~~~~~~~~~~~

.. autoclass:: memories.agents.agent.ConversationAgent
   :members:
   :undoc-members:
   :show-inheritance:

Task Agent
~~~~~~~~~

.. autoclass:: memories.agents.agent.TaskAgent
   :members:
   :undoc-members:
   :show-inheritance:

Property Agent
------------

.. autoclass:: examples.property_analyzer.PropertyAgent
   :members:
   :undoc-members:
   :show-inheritance:

Location Ambience Agent
--------------------

.. autoclass:: examples.location_ambience.LocationAnalyzer
   :members:
   :undoc-members:
   :show-inheritance:

Traffic Agent
-----------

.. autoclass:: examples.traffic_analyzer.TrafficAnalyzer
   :members:
   :undoc-members:
   :show-inheritance:

Water Body Agent
-------------

.. autoclass:: examples.water_bodies_monitor.WaterBodyAgent
   :members:
   :undoc-members:
   :show-inheritance:

Common Agent Patterns
------------------

All agents in the Memories-Dev framework follow these common patterns:

1. Initialization
   - Takes a MemoryStore instance for data persistence
   - Configures necessary data sources and processors

2. Data Processing
   - Implements the abstract `process` method
   - Handles data acquisition and analysis
   - Generates insights and recommendations

3. Memory Management
   - Stores insights in appropriate memory tiers
   - Implements cleanup and maintenance routines
   - Handles data validation and error cases

Example Usage
-----------

.. code-block:: python

    from memories import MemoryStore, Config
    from examples.property_analyzer import PropertyAgent

    # Initialize memory store
    config = Config(
        storage_path="./data",
        hot_memory_size=50,
        warm_memory_size=200,
        cold_memory_size=1000
    )
    memory_store = MemoryStore(config)

    # Create and use an agent
    agent = PropertyAgent(memory_store)
    insights = await agent.process(data)

For more detailed examples, see the :doc:`../user_guide/examples` section. 