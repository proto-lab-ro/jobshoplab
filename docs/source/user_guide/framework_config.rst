Framework Configuration
=====================

JobShopLab uses a comprehensive configuration system to control various aspects of the environment. This tutorial explains how to configure the framework effectively.

Configuration Structure
---------------------

Configuration in JobShopLab is managed through YAML files. A typical configuration has the following structure:

.. code-block:: yaml

    title: "Environment Name"
    default_loglevel: "warning"  # Set default logging level
    
    # Core components
    env:
      observation_factory: "BinaryActionObservationFactory"
      reward_factory: "BinaryActionJsspReward"
      action_factory: "BinaryJobActionFactory"
      render_backend: "render_in_dashboard"
      middleware: "EventBasedBinaryActionMiddleware"
      
    # Component-specific settings
    compiler:
      repo: "SpecRepository"
      validator: "SimpleDSLValidator"
      manipulators:
        - "DummyManipulator"
      spec_repository:
        dir: "data/jssp_instances/ft06"
        
    middleware:
      event_based_binary_action_middleware:
        truncation_joker: 5
        truncation_active: False
        
    reward_factory:
      binary_action_jssp_reward:
        sparse_bias: 1
        dense_bias: 0.001
        truncation_bias: -1

Loading Configuration
--------------------

Load configurations using the `load_config` function:

.. code-block:: python

    from jobshoplab import load_config
    from pathlib import Path
    
    config = load_config(config_path=Path("./data/config/my_config.yaml"))
    
    # Config attributes can be accessed with dot notation
    print(f"Dashboard Port: {config.render_backend.render_in_dashboard.port}")

Configuration Objects
-------------------

When loaded, configurations are converted to immutable dataclass objects:

- **Immutability**: Prevents accidental changes during runtime
- **Type safety**: Ensures configuration values have correct types
- **Dot notation**: Enables attribute-style access
- **Autocompletion**: IDE support through stub files

Core Components
--------------

The config file defines several key components:

Observation Factory
^^^^^^^^^^^^^^^^^^

Controls what information is available to the agent:

.. code-block:: yaml

    observation_factory:
      binary_action_observation_factory:
        loglevel: "warning"
        # Factory-specific settings

Reward Factory
^^^^^^^^^^^^^

Defines the reward function:

.. code-block:: yaml

    reward_factory:
      binary_action_jssp_reward:
        sparse_bias: 1       # Reward at episode end
        dense_bias: 0.001    # Reward during episode
        truncation_bias: -1  # Penalty for truncation

Action Factory
^^^^^^^^^^^^^^

Translates agent actions into scheduling decisions:

.. code-block:: yaml

    action_factory:
      binary_job_action_factory:
        loglevel: "warning"
        # Action factory-specific settings

State Machine
^^^^^^^^^^^^^

Controls core state machine behavior:

.. code-block:: yaml

    state_machine:
      loglevel: "warning"
      allow_early_transport: true  # Enable early transport scheduling

**allow_early_transport** (boolean, default: true)
  Controls when transport operations can be scheduled in the job shop system:
  
  - **true** (Early Transport Enabled): AGVs can be scheduled as soon as a job starts processing on a machine, allowing for proactive transport scheduling to minimize waiting times.
  - **false** (No Early Transport): AGVs are only scheduled when jobs are in a valid position in the output buffer, ensuring jobs are completely ready for pickup. This conservative approach prevents potential deadlock situations in AGV traffic management and is typically used in real-world scenarios.
  
  The parameter affects the `get_possible_transport_transition()` function, which filters out "early" transports when disabled. An early transport is defined as a transport request for a job that is not yet ready for pickup from a post-buffer location.

Middleware
^^^^^^^^^^^

Controls state machine interaction and time management:

.. code-block:: yaml

    middleware:
      event_based_binary_action_middleware:
        truncation_joker: 5       # Extra steps allowed after invalid actions
        truncation_active: False  # Whether to truncate after invalid actions

Render Backend
^^^^^^^^^^^^^^^

Configures visualization:

.. code-block:: yaml

    render_backend:
      render_in_dashboard:
        port: 8050
        debug: False
      simulation:
        port: 8051
        bind_all: False
      cli_table:
        loglevel: "warning"

Dependency Injection
-------------------

Instead of using the configuration file, you can override components via dependency injection:

.. code-block:: python

    from jobshoplab import JobShopLabEnv
    from jobshoplab.env.factories.rewards import CustomRewardFactory
    from functools import partial
    
    # Create custom reward factory with specific parameters
    reward_factory = partial(CustomRewardFactory, bias_a=0, bias_b=1)
    
    # Inject into environment
    env = JobShopLabEnv(config=config, reward_factory=reward_factory)

This approach is useful for:

- Hyperparameter optimization
- Quick experiments with custom components
- Testing alternative configurations

Best Practices
-------------

1. **Start with templates**: Use existing config files as starting points
2. **Keep configs versioned**: Store configs with experiments for reproducibility
3. **Validate configs**: Test configurations with small instances before scaling up
4. **Document customizations**: When creating custom components, document their configuration parameters
5. **Use dependency injection sparingly**: For permanent changes, modify the config file rather than relying on injection