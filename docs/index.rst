.. JobShopLab documentation master file

================================
JobShopLab:
================================

.. image:: ../docs/assets/JobShopLabLogo.svg
   :width: 150px
   :align: center
   :alt: JobShopLab Logo

JobShopLab is a flexible and modular framework designed to advance research and development in job shop scheduling using Reinforcement Learning (RL) techniques. It provides an adaptable gym environment, enabling users to test and benchmark different scheduling algorithms under realistic constraints found in industrial settings.

.. code-block:: python

    from jobshoplab import JobShopLabEnv, load_config
    from pathlib import Path
    
    # Load a pre-defined configuration
    config = load_config(config_path=Path("./data/config/getting_started_config.yaml"))
    
    # Create the environment
    env = JobShopLabEnv(config=config)
    
    # Run with random actions until done
    done = False
    while not done:
        action = env.action_space.sample()
        obs, reward, truncated, terminated, info = env.step(action)
        done = truncated or terminated
    
    # Visualize the final schedule
    env.render()

.. raw:: html

   <div class="mermaid">
   graph TD
       Agent[RL Agent] <-->|Actions/Observations| GymEnv[Gym Environment]
       GymEnv <-->|Interface| Middleware
       Middleware <-->|Interface| StateMachine[State Machine]
       StateMachine -->|Updates| State[State]
       GymEnv -->|Renders| Visualization[Visualization]
   </div>

Key Features
------------

- **Modular Gym Environment**: A customizable and extensible framework for testing diverse scheduling strategies and problem specifications.
- **Reinforcement Learning Ready**: Seamless integration with RL algorithms via the standard Gym Interface.
- **Real-World Constraints**: Incorporates transport logistics, buffer management, machine breakdowns, setup times, and stochastic processing conditions.
- **Multi-Objective Optimization**: Supports scheduling based on multiple objectives, such as makespan, energy efficiency, machine utilization, and lead time.
- **Comprehensive Visualization**: Interactive Gantt charts, CLI debugging tools, and 3D rendering capabilities.
- **Extensible Architecture**: Easily customizable reward functions, observation spaces, and action interpreters.


Framework Overview
-----------------

JobShopLab extends the classical Job Shop Scheduling Problem (JSSP) by integrating real-world production constraints and enabling RL-based optimization. It provides a state-machine-based simulation model that includes:

- **Machines**: Modeled with setup times, breakdowns, and stochastic processing.
- **Transport Units**: Handling job movements between machines with delays and constraints.
- **Buffers**: Limited storage capacity impacting scheduling decisions.

Contents
--------

.. toctree::
   :maxdepth: 1
   :caption: Getting Started
   
   installation
   tutorials/getting_started
   

.. toctree::
   :maxdepth: 2
   :caption: Tutorials
   
   tutorials/framework_config
   tutorials/custom_instances
   tutorials/custom_rewards
   custom_observations
   tutorials/visualisation

.. toctree::
   :maxdepth: 2
   :caption: Concepts
   
   concepts/design_choices
   concepts/state_machine
   concepts/the_dsl

.. toctree::
   :maxdepth: 2
   :caption: API Reference
   
   modules
   dsl_reference

.. toctree::
   :maxdepth: 2
   :caption: Additional Resources
   
   contributing
   authors
   testing

Indices and tables
-----------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`