System Dependencies
=================

This appendix provides detailed information about system-specific dependencies required for certain features of memories-dev.

PDF Documentation Generation
--------------------------

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

LaTeX Dependencies
----------------

For building PDF documentation using LaTeX:

macOS
~~~~~

.. code-block:: bash

   brew install --cask mactex

Linux (Ubuntu/Debian)
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   sudo apt-get update
   sudo apt-get install texlive-full

Windows
~~~~~~~

Install MiKTeX from https://miktex.org/download 