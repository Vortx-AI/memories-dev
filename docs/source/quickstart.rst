Quick Start Guide
===============

Installation
----------

Install memories-dev using pip:

.. code-block:: bash

    pip install memories-dev

For GPU support:

.. code-block:: bash

    pip install memories-dev[gpu]

Basic Usage
----------

Here's a simple example to get you started with memories-dev:

.. code-block:: python

    from memories.models.load_model import LoadModel
    from memories.data_acquisition.data_manager import DataManager
    import asyncio
    

    # Initialize model
    model = LoadModel(
        use_gpu=True,
        model_provider="deepseek-ai",
        deployment_type="local",
        model_name="deepseek-coder-small"
    )
    
    # Initialize data manager
    data_manager = DataManager(cache_dir="./data_cache")
    
    # Define area of interest (San Francisco)
    bbox = {
        'xmin': -122.4018,
        'ymin': 37.7914,
        'xmax': -122.3928,
        'ymax': 37.7994
    }
    
    # Get satellite data
    async def get_data():
        satellite_data = await data_manager.get_satellite_data(
            bbox_coords=bbox,
            start_date="2023-01-01",
            end_date="2023-02-01"
        )
        return satellite_data
    
    # Run the async function
    satellite_data = asyncio.run(get_data())
    
    # Generate text with the model
    response = model.get_response(
        f"Describe the satellite data for this region: {satellite_data}"
    )
    print(response["text"])
    
    # Clean up resources
    model.cleanup()

Key Components
-----------

1. Model System
~~~~~~~~~~~~~~~~~

The model system provides a unified interface for both local and API-based models:

.. code-block:: python

    # Local model
    local_model = LoadModel(
        model_provider="deepseek-ai",
        deployment_type="local",
        model_name="deepseek-coder-small"
    )
    
    # API-based model
    api_model = LoadModel(
        model_provider="openai",
        deployment_type="api",
        model_name="gpt-4",
        api_key="your-api-key"
    )
    
    # Generate text
    response = local_model.get_response("Write a function to calculate factorial")
    print(response["text"])

2. Data Acquisition
~~~~~~~~~~~~~~~~

The data acquisition system provides access to various data sources:

.. code-block:: python

    from memories.data_acquisition.data_manager import DataManager
    import asyncio
    
    # Initialize data manager
    data_manager = DataManager(cache_dir="./data_cache")
    
    # Define async function to get data
    async def get_data():
        # Get satellite data
        satellite_data = await data_manager.get_satellite_data(
            bbox_coords={
                'xmin': -122.4018, 'ymin': 37.7914,
                'xmax': -122.3928, 'ymax': 37.7994
            },
            start_date="2023-01-01",
            end_date="2023-02-01"
        )
        
        # Get vector data
        vector_data = await data_manager.get_vector_data(
            bbox={
                'xmin': -122.4018, 'ymin': 37.7914,
                'xmax': -122.3928, 'ymax': 37.7994
            },
            layers=["buildings", "roads"]
        )
        
        return satellite_data, vector_data
    
    # Run the async function
    satellite_data, vector_data = asyncio.run(get_data())

3. Deployment Options
~~~~~~~~~~~~~~~~~~

memories-dev supports various deployment configurations:

.. code-block:: python

    from memories.deployments.standalone import StandaloneDeployment
    
    # Configure standalone deployment
    deployment = StandaloneDeployment(
        provider="gcp",
        config={
            "machine_type": "n2-standard-4",
            "region": "us-west1",
            "zone": "us-west1-a"
        }
    )
    
    # Deploy the system
    deployment.deploy()

Next Steps
---------

- Explore the :doc:`user_guide/index` for detailed usage instructions
- Check the :doc:`api_reference/index` for comprehensive API documentation
- See :doc:`user_guide/examples` for more advanced examples

