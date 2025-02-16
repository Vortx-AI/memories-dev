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