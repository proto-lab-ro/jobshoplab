Installation
============

This guide will help you install JobShopLab and set up your development environment.

Prerequisites
------------

Before installing JobShopLab, ensure you have the following prerequisites:

- Python 3.12 or higher
- pip (Python package installer)
- Git (for cloning the repository)

We strongly recommend using a virtual environment to avoid package conflicts.

Installation Steps
-----------------

Install from Source
^^^^^^^^^^^^^^^^^^

The recommended way to install JobShopLab is from source in development mode:

.. code-block:: bash

    # Create and activate a virtual environment (recommended)
    python -m venv jobshoplab-env
    
    # On Linux/macOS
    source jobshoplab-env/bin/activate
    
    # On Windows
    jobshoplab-env\\Scripts\\activate
    
    # Clone the repository
    git clone https://github.com/your-username/jobshoplab.git
    cd jobshoplab
    
    # Install in development mode
    pip install -e .

This installs JobShopLab in "editable" mode, allowing you to modify the code and have changes immediately available.

Verify Installation
^^^^^^^^^^^^^^^^^

To verify that JobShopLab is installed correctly, run:

.. code-block:: bash

    # Activate your virtual environment if not already active
    
    # Check import works
    python -c "from jobshoplab import JobShopLabEnv; print('Installation successful!')"

Development Dependencies
----------------------

If you plan to contribute to JobShopLab development, install additional development dependencies:

.. code-block:: bash

    # Install development dependencies
    pip install -e ".[dev]"

This will install testing libraries, documentation tools, and other development utilities.

Optional Dependencies
-------------------

Visualization Tools
^^^^^^^^^^^^^^^^^^

For using all visualization features:

.. code-block:: bash

    # Install visualization dependencies
    pip install plotly dash

Reinforcement Learning Libraries
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To use JobShopLab with common reinforcement learning frameworks:

.. code-block:: bash

    # Stable Baselines 3
    pip install stable-baselines3
    
    # or RLlib
    pip install ray[rllib]

Troubleshooting
--------------

Common installation issues and their solutions:

Package Conflicts
^^^^^^^^^^^^^^^^

If you encounter package conflicts, try installing in a fresh virtual environment:

.. code-block:: bash

    python -m venv fresh-env
    source fresh-env/bin/activate  # On Windows: fresh-env\Scripts\activate
    pip install -e .

Import Errors
^^^^^^^^^^^^

If you encounter import errors like `ModuleNotFoundError`, ensure:

1. Your virtual environment is activated
2. You've installed JobShopLab with `pip install -e .`
3. You're running Python from the correct environment

Visualization Issues
^^^^^^^^^^^^^^^^^^

If you encounter problems with the visualization tools:

1. Ensure you have the latest versions of plotly and dash
2. Check browser console for JavaScript errors
3. Try different rendering backends (e.g., `env.render(mode="debug")`)

Platform-Specific Notes
---------------------

Windows
^^^^^^^

On Windows, you might need to install additional build tools:

.. code-block:: bash

    # Install Microsoft C++ Build Tools
    pip install --upgrade setuptools wheel

macOS
^^^^^

On macOS, you might need to install developer tools:

.. code-block:: bash

    # Install command-line tools
    xcode-select --install