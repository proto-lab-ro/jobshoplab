Contributing
============

Thank you for your interest in contributing to JobShopLab! This document provides guidelines and instructions for contributing to the project.

Development Setup
---------------

1. Fork the repository on GitHub
2. Clone your forked repository
3. Create a virtual environment and install development dependencies:

.. code-block:: bash

    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -e ".[dev]"

4. Set up pre-commit hooks:

.. code-block:: bash

    pre-commit install

Code Style
---------

JobShopLab follows these coding conventions:

- **Python**: Python 3.12+
- **Formatting**: Black with line-length=100
- **Imports**: Standard lib ’ Third-party ’ Local (alphabetically sorted within each)
- **Naming**:
  - snake_case for functions/variables
  - PascalCase for classes
  - ALL_CAPS for constants
- **Error Handling**: Use custom exceptions from `jobshoplab/utils/exceptions.py`
- **Type Annotations**: Required for all function parameters and return values
- **Docstrings**: Google-style docstrings

Example of a well-formatted function with docstring:

.. code-block:: python

    def multiply(a: int, b: int) -> int:
        """
        Multiplies two numbers and returns the result.

        Args:
            a (int): The first number.
            b (int): The second number.

        Returns:
            int: The product of a and b.
        """
        return a * b

Running Tests
-----------

Before submitting a pull request, ensure all tests pass:

.. code-block:: bash

    # Run all tests
    pytest
    
    # Run specific test categories
    pytest tests/unit_tests/
    pytest tests/integration_tests/
    pytest tests/end_to_end_tests/
    
    # Run a specific test
    pytest tests/path/to/test_file.py::test_function_name
    
    # Get test coverage
    scripts/get_test_coverage.sh

Pull Request Process
-----------------

1. Create a new branch for your feature or bugfix:

.. code-block:: bash

    git checkout -b feature/your-feature-name
    # or
    git checkout -b fix/issue-you-are-fixing

2. Make your changes, following the code style guidelines

3. Add tests for your changes

4. Run the test suite to ensure all tests pass

5. Commit your changes with clear, descriptive commits:

.. code-block:: bash

    git commit -m "Add feature X that does Y"

6. Push your changes to your fork:

.. code-block:: bash

    git push origin feature/your-feature-name

7. Open a pull request to the main repository's `dev` branch

8. Describe your changes in the pull request, linking any related issues

9. Wait for code review and address any feedback

Documentation
-----------

When adding new features, please update the documentation:

1. Add docstrings to all new classes and functions
2. Update or create new RST files in the `docs/` directory if needed
3. If applicable, add examples to show how to use the new feature

Building Documentation
^^^^^^^^^^^^^^^^^^^

To build and preview the documentation locally:

.. code-block:: bash

    # Navigate to the docs directory
    cd docs
    
    # Build the documentation
    make html
    
    # Open in browser
    # On Linux/macOS
    open _build/html/index.html
    # On Windows
    start _build/html/index.html

Adding New Components
------------------

When adding new component types:

Factory Components
^^^^^^^^^^^^^^^

For new observation factories, reward factories, or action interpreters:

1. Create a new class extending the appropriate base class
2. Implement all required methods
3. Register the factory using the registration function
4. Add tests for the new factory
5. Document the factory and its parameters

Example for registering a new observation factory:

.. code-block:: python

    from jobshoplab.env.factories import register_observation_factory
    
    # Register the factory
    register_observation_factory("CustomObservationFactory", CustomObservationFactory)

State Machine Extensions
^^^^^^^^^^^^^^^^^^^^^

For extending the state machine:

1. Add new state types to the appropriate files in `jobshoplab/types/`
2. Create handlers for the new state components
3. Update validators as needed
4. Add tests covering the new functionality

Bug Reports
---------

When reporting bugs:

1. Check if the bug has already been reported
2. Use the bug report template
3. Include a clear description of the bug
4. Provide steps to reproduce the issue
5. Include expected and actual behavior
6. Add information about your environment (Python version, OS, etc.)

Feature Requests
--------------

When suggesting new features:

1. Check if the feature has already been suggested
2. Use the feature request template
3. Clearly describe the feature and its benefits
4. Provide examples of how the feature would be used

Code of Conduct
-------------

Please note that JobShopLab has a Code of Conduct. By participating in this project, you agree to abide by its terms.