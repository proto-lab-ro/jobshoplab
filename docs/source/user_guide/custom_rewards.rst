Custom Rewards
=============

One of JobShopLab's strengths is its flexibility in defining reward functions. This tutorial shows how to create and use custom reward functions to optimize different scheduling objectives.

Reward Functions in Job Shop Scheduling
-------------------------------------

Different applications have different optimization goals:

- **Makespan**: Minimize total completion time (most common)
- **Tardiness**: Minimize lateness against due dates
- **Throughput**: Maximize number of completed jobs
- **Resource utilization**: Maximize machine usage
- **Energy consumption**: Minimize energy usage
- **Multiple objectives**: Weighted combinations of the above

JobShopLab's reward factory system makes it easy to define custom reward functions for any of these objectives.

Understanding the Reward Factory
-----------------------------

Reward factories in JobShopLab:

1. Receive the current state and transition information
2. Calculate a reward value based on the state
3. Return a scalar reward to the agent

The `RewardFactory` abstract base class defines the interface:

.. code-block:: python

    class RewardFactory(ABC):
        def __init__(self, loglevel, config, instance, *args, **kwargs):
            # Initialize with config and instance information
            
        @abstractmethod
        def make(self, state_result: StateMachineResult, 
                 terminated: bool, truncated: bool) -> float:
            """Calculate and return the reward value."""
            pass

Creating a Custom Reward Factory
------------------------------

To create a custom reward function, subclass `RewardFactory`:

.. code-block:: python

    from jobshoplab.env.factories.rewards import RewardFactory
    from jobshoplab.types import StateMachineResult
    
    class CustomRewardFactory(RewardFactory):
        def __init__(self, loglevel, config, instance, bias_a, bias_b, *args, **kwargs):
            super().__init__(loglevel, config, instance)
            self.bias_a = bias_a
            self.bias_b = bias_b
        
        def make(self, state_result: StateMachineResult, terminated: bool, truncated: bool) -> float:
            # During episode (not done)
            if not (terminated or truncated):
                return self.bias_a
            
            # Episode completed
            else:
                # Return reward inversely proportional to makespan
                return self.bias_b * state_result.state.time.time

Using a Custom Reward Factory
---------------------------

There are two ways to use your custom reward factory:

1. Via dependency injection (for quick experiments):

.. code-block:: python

    from functools import partial
    
    # Create factory with specific parameters
    reward_factory = partial(CustomRewardFactory, bias_a=0, bias_b=1)
    
    # Use in environment
    env = JobShopLabEnv(config=config, reward_factory=reward_factory)

2. Via configuration (for reproducible experiments):

.. code-block:: python

    # First, register your factory with JobShopLab (in your module)
    from jobshoplab.env.factories import register_reward_factory
    
    register_reward_factory("CustomRewardFactory", CustomRewardFactory)
    
    # Then in your config file:
    """
    env:
      reward_factory: "CustomRewardFactory"
    
    reward_factory:
      custom_reward_factory:
        bias_a: 0
        bias_b: 1
    """

Reward Design Considerations
--------------------------

When designing custom rewards, consider:

Sparse vs. Dense Rewards
^^^^^^^^^^^^^^^^^^^^^^^

- **Sparse rewards**: Only given at episode end (e.g., final makespan)
  - Pros: Clear global objective
  - Cons: Delayed feedback makes learning difficult
  
- **Dense rewards**: Given at each step
  - Pros: Immediate feedback helps learning
  - Cons: May lead to suboptimal policies if not aligned with global objective

A common approach is to combine both:

.. code-block:: python

    def make(self, state_result, terminated, truncated):
        # Dense reward component based on current progress
        current_progress = self._calculate_progress(state_result)
        dense_reward = self.dense_weight * current_progress
        
        # If episode is done, add sparse reward component
        if terminated or truncated:
            makespan = state_result.state.time.time
            sparse_reward = self.sparse_weight * (1000 / makespan)
            return dense_reward + sparse_reward
        
        return dense_reward

Reward Scaling
^^^^^^^^^^^^

Rewards should typically be in a reasonable range (e.g., -1 to 1) for most RL algorithms. Consider normalizing rewards:

.. code-block:: python

    def make(self, state_result, terminated, truncated):
        if terminated:
            # Get makespan
            makespan = state_result.state.time.time
            
            # Get lower bound estimate for the instance
            lower_bound = self._calculate_lower_bound()
            
            # Normalized reward (1.0 for perfect solution)
            return lower_bound / makespan
        
        return 0

Multi-objective Rewards
^^^^^^^^^^^^^^^^^^^^^

For multiple objectives, use weighted combinations:

.. code-block:: python

    def make(self, state_result, terminated, truncated):
        if terminated:
            # Makespan component
            makespan = state_result.state.time.time
            makespan_reward = self.makespan_weight * (1000 / makespan)
            
            # Tardiness component
            tardiness = self._calculate_tardiness(state_result)
            tardiness_reward = self.tardiness_weight * (1 / (1 + tardiness))
            
            # Energy component
            energy = self._calculate_energy(state_result)
            energy_reward = self.energy_weight * (1 / energy)
            
            return makespan_reward + tardiness_reward + energy_reward
        
        return 0