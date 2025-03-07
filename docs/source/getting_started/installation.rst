.. _installation:

============
Installation
============

This guide will help you install the ``memories-dev`` framework and set up your environment for working with Earth's collective memory system.

.. admonition:: Requirements
   :class: note

   * Python 3.10 or higher
   * 8GB RAM minimum (16GB+ recommended)
   * CUDA-compatible GPU recommended for computer vision tasks
   * Internet connection for accessing remote data sources

Quick Start
----------

Install memories-dev using pip:

.. code-block:: bash

   pip install memories-dev

For development installation:

.. code-block:: bash

   git clone https://github.com/Vortx-AI/memories-dev.git
   cd memories-dev
   pip install -e ".[docs]"

Optional Dependencies
------------------

For full functionality, install optional dependencies:

.. code-block:: bash

   pip install "memories-dev[docs]"  # Documentation dependencies
   pip install "memories-dev[gpu]"   # GPU support
   pip install "memories-dev[all]"   # All optional dependencies

Building Documentation
-------------------

To build the documentation:

.. code-block:: bash

   cd docs
   pip install -r requirements.txt
   make html     # For HTML documentation

.. note::
   For system-specific dependencies and advanced installation options, 
   please refer to :doc:`../appendix/system_dependencies`

Installation Methods
====================

There are several ways to install the ``memories-dev`` framework, depending on your needs and environment.

Using pip (Recommended)
-----------------------

The simplest way to install the latest stable release is using pip:

.. code-block:: bash

   pip install memories-dev

For installing with specific optional dependencies:

.. code-block:: bash

   # Install with all optional dependencies
   pip install memories-dev[all]

   # Install with GPU support
   pip install memories-dev[gpu]

   # Install with visualization tools
   pip install memories-dev[viz]

   # Install with development tools
   pip install memories-dev[dev]

From Source
-----------

To install the latest development version from source:

.. code-block:: bash

   git clone https://github.com/Vortx-AI/memories-dev.git
   cd memories-dev
   pip install -e .

Using Docker
------------

We provide Docker images with all dependencies pre-installed:

.. code-block:: bash

   # Pull the latest image
   docker pull vortxai/memories-dev:latest

   # Run a container with GPU support
   docker run --gpus all -it vortxai/memories-dev:latest

   # Run a container with mounted local directory
   docker run -v $(pwd):/app -it vortxai/memories-dev:latest

Environment Setup
=================

Setting Up API Keys
-------------------

The ``memories-dev`` framework integrates with various external APIs for data acquisition. You'll need to set up API keys for the services you plan to use:

.. code-block:: python

   import os
   from dotenv import load_dotenv

   # Load API keys from .env file
   load_dotenv()

   # Or set them directly in your environment
   os.environ["SATELLITE_API_KEY"] = "your_satellite_api_key"
   os.environ["GIS_API_KEY"] = "your_gis_api_key"
   os.environ["LLM_API_KEY"] = "your_llm_api_key"

You can also create a ``.env`` file in your project root:

.. code-block:: text

   SATELLITE_API_KEY=your_satellite_api_key
   GIS_API_KEY=your_gis_api_key
   LLM_API_KEY=your_llm_api_key

GPU Configuration
-----------------

For optimal performance with computer vision and machine learning tasks, we recommend using a GPU:

.. tab-set::

   .. tab-item:: PyTorch
      :sync: pytorch

      .. code-block:: python

         import torch

         # Check if CUDA is available
         if torch.cuda.is_available():
             device = torch.device("cuda")
             print(f"Using GPU: {torch.cuda.get_device_name(0)}")
         else:
             device = torch.device("cpu")
             print("GPU not available, using CPU")

         # Configure memories-dev to use the device
         from memories.config import set_default_device
         set_default_device(device)

   .. tab-item:: TensorFlow
      :sync: tensorflow

      .. code-block:: python

         import tensorflow as tf

         # Check if GPU is available
         gpus = tf.config.list_physical_devices('GPU')
         if gpus:
             try:
                 # Currently, memory growth needs to be the same across GPUs
                 for gpu in gpus:
                     tf.config.experimental.set_memory_growth(gpu, True)
                 logical_gpus = tf.config.list_logical_devices('GPU')
                 print(f"Available GPUs: {len(gpus)} physical, {len(logical_gpus)} logical")
             except RuntimeError as e:
                 # Memory growth must be set before GPUs have been initialized
                 print(e)
         else:
             print("GPU not available, using CPU")

         # Configure memories-dev to use TensorFlow
         from memories.config import set_backend
         set_backend('tensorflow')

Data Storage Configuration
--------------------------

Configure where and how ``memories-dev`` stores data:

.. code-block:: python

   from memories.config import configure_storage

   # Configure local storage
   configure_storage(
       storage_type="local",
       base_path="/path/to/data",
       cache_size_gb=10
   )

   # Or configure cloud storage
   configure_storage(
       storage_type="s3",
       bucket_name="memories-data",
       region="us-west-2",
       cache_size_gb=2
   )

Verification
============

To verify that your installation is working correctly:

.. code-block:: python

   import memories

   # Print version information
   print(f"memories-dev version: {memories.__version__}")

   # Run system check
   status = memories.system_check()
   print(f"System status: {'OK' if status.ok else 'Issues detected'}")
   
   if not status.ok:
       for issue in status.issues:
           print(f"- {issue}")

Troubleshooting
===============

Common Issues
-------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Issue
     - Solution
   * - ``ImportError: No module named 'memories'``
     - Ensure you've installed the package correctly. Try ``pip install --force-reinstall memories-dev``.
   * - CUDA/GPU not detected
     - Check that you have compatible NVIDIA drivers installed. Run ``nvidia-smi`` to verify.
   * - Memory errors during processing
     - Reduce batch sizes or image dimensions in your configuration. Consider using a machine with more RAM.
   * - API connection errors
     - Verify your API keys and internet connection. Check if the service has usage limits or is experiencing downtime.
   * - Slow performance
     - Enable caching, use GPU acceleration, or consider distributed processing for large datasets.

Getting Help
------------

If you encounter issues not covered here:

1. Check the `FAQ <../faq.md>`_
2. Search the `GitHub Issues <https://github.com/Vortx-AI/memories-dev/issues>`_
3. Ask a question on the `Discussion Forum <https://github.com/Vortx-AI/memories-dev/discussions>`_
4. Join our `Discord Community <https://discord.gg/memories-dev>`_
5. Email us at `hello@memories.dev <mailto:hello@memories.dev>`_

Next Steps
==========

Now that you have ``memories-dev`` installed, you can:

* Follow the :ref:`quickstart` guide to run your first analysis
* Explore the :ref:`examples` to see real-world applications
* Learn about the 'core_concepts' of the framework
* Configure your 'data_sources' for optimal performance

Installation Guide
==================

This guide will help you install Memories-Dev and its dependencies.

Python Requirements
-----------------

The package requires Python 3.9 or later. We recommend using a virtual environment:

.. code-block:: bash

   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -U pip setuptools wheel

Installing from PyPI
------------------

Install the package using pip:

.. code-block:: bash

   pip install memories-dev

For development installation:

.. code-block:: bash

   git clone https://github.com/Vortx-AI/memories-dev.git
   cd memories-dev
   pip install -e ".[docs]"

System Dependencies
-----------------

For PDF documentation generation with SVG support, you need either ``librsvg`` or ``inkscape``:

macOS
~~~~~

Using Homebrew:

.. code-block:: bash

   brew install librsvg  # For rsvg-convert
   # or
   brew install inkscape  # Alternative

Linux (Ubuntu/Debian)
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   sudo apt-get update
   sudo apt-get install librsvg2-bin  # For rsvg-convert
   # or
   sudo apt-get install inkscape  # Alternative

Windows
~~~~~~~

Using `Chocolatey <https://chocolatey.org/>`_:

.. code-block:: bash

   choco install librsvg  # For rsvg-convert
   # or
   choco install inkscape  # Alternative

Additional Dependencies
--------------------

For full functionality, install optional dependencies:

.. code-block:: bash

   pip install "memories-dev[docs]"  # Documentation dependencies
   pip install "memories-dev[gpu]"   # GPU support
   pip install "memories-dev[all]"   # All optional dependencies

Building Documentation
-------------------

To build the documentation:

.. code-block:: bash

   cd docs
   pip install -r requirements.txt
   make html     # For HTML documentation
   make latexpdf # For PDF documentation (requires LaTeX) 