Installation
============

Basic Installation
----------------

.. code-block:: bash

    pip install memories-dev

Python Version Compatibility
-------------------------

The package supports Python versions 3.9 through 3.13. Dependencies are automatically adjusted based on your Python version to ensure compatibility.

Installation Options
------------------

1. CPU-only Installation (Default)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    pip install memories-dev

2. GPU Support Installation
~~~~~~~~~~~~~~~~~~~~~~~~~

For CUDA 11.8:

.. code-block:: bash

    pip install memories-dev[gpu]

For different CUDA versions, install PyTorch manually first:

.. code-block:: bash

    # For CUDA 12.1
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    
    # Then install the package
    pip install memories-dev[gpu]

3. Development Installation
~~~~~~~~~~~~~~~~~~~~~~~~

For contributing to the project:

.. code-block:: bash

    pip install memories-dev[dev]

4. Documentation Tools
~~~~~~~~~~~~~~~~~~~

For building documentation:

.. code-block:: bash

    pip install memories-dev[docs]

Detailed Installation Steps
-------------------------

1. Create and Activate Virtual Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It's recommended to install memories-dev in a virtual environment:

.. code-block:: bash

    # Create virtual environment
    python -m venv venv_test
    
    # Activate virtual environment
    source venv_test/bin/activate  # Linux/Mac
    # or
    .\venv_test\Scripts\activate   # Windows

2. Install Core Package
~~~~~~~~~~~~~~~~~~~~~

Install the package in editable mode with development dependencies:

.. code-block:: bash

    pip install -e .[dev]

3. Install Documentation Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you're working with documentation:

.. code-block:: bash

    pip install -r docs/requirements.txt

4. Verify Installation
~~~~~~~~~~~~~~~~~~~

Run the test suite to verify the installation:

.. code-block:: bash

    pytest

Expected output:
- Some tests may be skipped (particularly GPU-related tests if GPU is not available)
- You should see "passed" tests with potential skips
- Any warnings can typically be ignored unless they cause functionality issues

Troubleshooting
-------------

Common Issues and Solutions
~~~~~~~~~~~~~~~~~~~~~~~~

1. Import Issues
   - If you encounter import errors, ensure you're in the correct virtual environment
   - Verify that all dependencies are installed: ``pip list``
   - Try reinstalling the package: ``pip install -e .``

2. GPU Support
   - For GPU support, ensure CUDA toolkit is installed
   - Verify GPU availability: ``nvidia-smi``
   - Install GPU dependencies: ``pip install -r gpu-requirements.txt``

3. Documentation Build
   - Install Sphinx and related packages: ``pip install -r docs/requirements.txt``
   - Build documentation locally: ``cd docs && make html``

4. Test Failures
   - Update all dependencies: ``pip install --upgrade -r requirements.txt``
   - Clear pytest cache: ``pytest --cache-clear``
   - Run specific test file: ``pytest path/to/test_file.py -v``

Version-specific Dependencies
--------------------------

The package automatically handles version-specific dependencies based on your Python version:

- Python 3.9: Compatible with older versions of key packages
- Python 3.10-3.11: Standard modern package versions
- Python 3.12-3.13: Latest package versions with improved performance

Working Examples
--------------

Basic Usage Example
~~~~~~~~~~~~~~~~

After installation, you can verify the setup with these examples:

.. code-block:: python

    from memories.models.load_model import LoadModel
    from memories.core.memory import MemoryStore
    from memories.agents.agent import Agent

    # Basic initialization
    def test_basic_setup():
        # Initialize model loader
        model = LoadModel(
            use_gpu=False,  # Set to True if GPU is available
            model_provider="deepseek-ai",
            deployment_type="local"
        )
        
        # Create memory store
        memory_store = MemoryStore()
        
        # Test memory creation
        memories = memory_store.create_memories(
            location=(37.7749, -122.4194),  # San Francisco
            time_range=("2024-01-01", "2024-02-01")
        )
        
        return "Setup successful!"

GPU Support Example
~~~~~~~~~~~~~~~~

If you've installed GPU support:

.. code-block:: python

    import torch
    from memories.utils.processors import gpu_stat

    def verify_gpu_setup():
        # Check CUDA availability
        cuda_available = torch.cuda.is_available()
        
        if cuda_available:
            device_count = torch.cuda.device_count()
            device_name = torch.cuda.get_device_name(0)
            
            # Get GPU memory stats
            memory_stats = gpu_stat()
            
            return {
                "cuda_available": True,
                "device_count": device_count,
                "device_name": device_name,
                "memory_stats": memory_stats
            }
        else:
            return {"cuda_available": False}

Documentation Build Example
~~~~~~~~~~~~~~~~~~~~~~~

To build and verify documentation:

.. code-block:: bash

    # Navigate to docs directory
    cd docs

    # Build documentation
    make html

    # Check build output
    ls build/html/

    # Open in browser (macOS)
    open build/html/index.html
    # or on Linux
    xdg-open build/html/index.html
    # or on Windows
    start build/html/index.html

Testing Example
~~~~~~~~~~~~

Run specific test categories:

.. code-block:: bash

    # Run all tests
    pytest

    # Run specific test file
    pytest tests/test_installation.py

    # Run tests with coverage report
    pytest --cov=memories tests/

    # Run tests in parallel
    pytest -n auto

For more detailed examples and usage patterns, please refer to our :doc:`quickstart` guide.

For more detailed information about dependencies and compatibility, please refer to our :doc:`user_guide/index`. 