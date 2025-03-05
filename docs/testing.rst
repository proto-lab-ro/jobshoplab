=======
Testing
=======

This guide covers how to run and write tests for JobShopLab, ensuring the framework's reliability and stability.

Running Tests
------------

JobShopLab uses pytest for testing. All tests are located in the ``tests/`` directory and are organized by test type.

To run the full test suite:

.. code-block:: bash

    pytest

To run specific test categories:

.. code-block:: bash

    # Run only unit tests
    pytest tests/unit_tests/

    # Run only integration tests
    pytest tests/integration_tests/

    # Run only end-to-end tests
    pytest tests/end_to_end_tests/

    # Run a specific test file
    pytest tests/unit_tests/test_state_machine.py

    # Run a specific test function
    pytest tests/unit_tests/test_state_machine.py::test_function_name

Check Test Coverage
------------------

To generate a test coverage report:

.. code-block:: bash

    ./scripts/get_test_coverage.sh

This will run tests with coverage analysis and generate an HTML report in the ``htmlcov/`` directory.

Test Structure
-------------

Tests in JobShopLab follow these organizational principles:

1. **Unit Tests** (``tests/unit_tests/``)
   
   Test individual components in isolation. Each module typically has its own test file.

2. **Integration Tests** (``tests/integration_tests/``)
   
   Test interactions between components. These tests verify that modules work correctly together.

3. **End-to-End Tests** (``tests/end_to_end_tests/``)
   
   Test complete workflows from environment creation to step execution and rendering.

4. **Fuzzy Tests** (``tests/fuzzy_testing/``)
   
   Explore edge cases through randomized inputs.

Writing Tests
------------

When writing tests for JobShopLab, follow these guidelines:

1. **Name tests descriptively**

   Test names should describe what they're testing and the expected outcome.

   .. code-block:: python

       def test_machine_processes_job_correctly():
           # Test implementation

2. **Use fixtures for setup**

   JobShopLab has several fixtures defined in ``conftest.py`` files to help with test setup.

   .. code-block:: python

       def test_with_standard_config(standard_config):
           # Test using the standard_config fixture
           assert standard_config["machines"] > 0

3. **Test both success and failure cases**

   Ensure both valid and invalid inputs are tested.

   .. code-block:: python

       def test_invalid_transition_raises_exception():
           # Setup
           state_machine = create_test_state_machine()
           
           # Test that invalid transition raises the correct exception
           with pytest.raises(InvalidTransitionError):
               state_machine.transition(invalid_action)

4. **Use parameterized tests for multiple scenarios**

   .. code-block:: python

       @pytest.mark.parametrize("num_machines,num_jobs", [(2, 2), (3, 3), (5, 10)])
       def test_various_problem_sizes(num_machines, num_jobs):
           config = create_config(num_machines, num_jobs)
           # Test implementation

Test Data
---------

Test data is stored in ``tests/data/`` and includes:

- Sample configuration files
- Test problem instances
- Invalid configurations for testing error handling

When adding new features, ensure that appropriate test data is included.

CI/CD Integration
----------------

When contributing to JobShopLab, ensure all tests pass before submitting pull requests. The CI pipeline will run the test suite automatically on each commit.

Troubleshooting Tests
--------------------

If tests are failing:

1. Check if you've installed all dependencies
2. Ensure your code follows the established patterns
3. Run failing tests with the ``-v`` flag for more details:

   .. code-block:: bash

       pytest tests/failing_test.py -v

4. Use the ``--pdb`` flag to drop into a debugger when a test fails:

   .. code-block:: bash

       pytest tests/failing_test.py --pdb