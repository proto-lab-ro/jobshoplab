Custom Observations
==================

The observation space defines what information is available to the agent when making scheduling decisions. JobShopLab's flexible observation factory system allows you to create custom observation spaces tailored to specific scheduling problems.

Observation Space Basics
----------------------

In reinforcement learning, the observation (or state) representation significantly impacts learning efficiency and policy quality. JobShopLab provides several built-in observation factories and makes it easy to create custom ones.


Built-in Observation Factories
----------------------------

JobShopLab includes several observation factories:

1. **SimpleJsspObservationFactory**: Observation containing selected freatrues of the current state
2. **BinaryActionObservationFactory**: Observation containing selected freatrues of the current state a job of transport id 
3. **MultiDiscreteObservationFactory**: Multi-dimensional observation for more complex environments
4. **OperationArrayObservation**: array of operation locations and progress
5. **BinaryOperationArrayObservation**: array of operation locations and progress and a job of transport id 

Creating Custom Observation Factories
-----------------------------------

To create a custom observation factory, extend the `ObservationFactory` base class:

.. code-block:: python

    from jobshoplab.env.factories.observations import ObservationFactory
    from jobshoplab.types import State
    import numpy as np
    import gym

    class CustomObservationFactory(ObservationFactory):
        def __init__(self, loglevel, config, instance, *args, **kwargs):
            super().__init__(loglevel, config, instance) # required standard arguments
            
            # Define observation space dimensions
            # self.observation_space = gym.spaces.Box()
        
        def make(self, state: State):
            """Convert state to observation vector."""
            observation = "your observation logic here"
            return observation

Registering and Using Your Factory
--------------------------------

To use your custom observation factory:

1. Via dependency injection (for quick experimentation):

.. code-block:: python

    from functools import partial
    
    # Create factory with specific parameters
    observation_factory = partial(CustomObservationFactory, some_additional_parameter=42)
    
    # Use in environment
    env = JobShopLabEnv(config=config, observation_factory=observation_factory)

2. Via configuration (for reproducible experiments):

Then configure it in your config file:

.. code-block:: yaml

    env:
      observation_factory: "CustomObservationFactory"
    
    observation_factory:
      custom_observation_factory:
        some_additional_parameter: 42


Testing Your Observation Factory
------------------------------

To validate your custom observation factory:

1. **Observation shape**: Ensure dimensions match your specification
2. **Range check**: Verify values stay within expected ranges
3. **Information content**: Test if essential scheduling information is captured
4. **Learning performance**: Compare agent performance with different observation spaces

.. hint::
    Its highly suggested to write tests for your custom observation factory.
    For more information on testing, see the `Testing` section in the `Contributing` guide.