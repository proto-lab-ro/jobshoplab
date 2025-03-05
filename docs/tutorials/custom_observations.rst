Custom Observations
==================

The observation space defines what information is available to the agent when making scheduling decisions. JobShopLab's flexible observation factory system allows you to create custom observation spaces tailored to specific scheduling problems.

Observation Space Basics
----------------------

In reinforcement learning, the observation (or state) representation significantly impacts learning efficiency and policy quality. JobShopLab provides several built-in observation factories and makes it easy to create custom ones.

Observation spaces in job shop scheduling might include:

- Machine states (idle, processing, setup)
- Job states (waiting, in-progress, completed)
- Operation progress and remaining times
- Buffer occupancy
- Transport resource positions
- Global statistics (makespan, tardiness)

Built-in Observation Factories
----------------------------

JobShopLab includes several observation factories:

1. **BinaryActionObservationFactory**: Standard binary representation of job and machine states
2. **MultiDiscreteObservationFactory**: Multi-dimensional observation for more complex environments
3. **DummyObservationFactory**: Simplified observation for testing

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
            super().__init__(loglevel, config, instance)
            
            # Define observation space dimensions
            self.n_machines = len(instance.machines)
            self.n_jobs = len(instance.jobs)
            
            # Create gym observation space
            self.observation_space = gym.spaces.Box(
                low=0, high=1, 
                shape=(self.n_machines + self.n_jobs * 2,),
                dtype=np.float32
            )
        
        def make(self, state: State):
            """Convert state to observation vector."""
            observation = np.zeros(self.n_machines + self.n_jobs * 2, dtype=np.float32)
            
            # Machine state features (0=idle, 1=busy)
            for i, machine in enumerate(state.machines):
                observation[i] = 1 if machine.state != "IDLE" else 0
            
            # Job progress features (percentage complete)
            for i, job in enumerate(state.jobs):
                total_ops = len(job.operations)
                completed_ops = sum(1 for op in job.operations if op.completed)
                observation[self.n_machines + i] = completed_ops / total_ops
            
            # Job location features (one-hot encoded machine ID)
            for i, job in enumerate(state.jobs):
                current_op_idx = next((idx for idx, op in enumerate(job.operations) 
                                      if not op.completed), None)
                if current_op_idx is not None:
                    current_op = job.operations[current_op_idx]
                    current_machine_idx = next((idx for idx, m in enumerate(self.instance.machines)
                                               if m.id == current_op.machine_id), None)
                    if current_machine_idx is not None:
                        observation[self.n_machines + self.n_jobs + i] = current_machine_idx / self.n_machines
            
            return observation

Registering and Using Your Factory
--------------------------------

To use your custom observation factory:

1. Via dependency injection (for quick experimentation):

.. code-block:: python

    from functools import partial
    
    # Create factory with specific parameters
    observation_factory = partial(CustomObservationFactory, feature_dim=64)
    
    # Use in environment
    env = JobShopLabEnv(config=config, observation_factory=observation_factory)

2. Via configuration (for reproducible experiments):

First, register your factory:

.. code-block:: python

    from jobshoplab.env.factories import register_observation_factory
    
    # Register custom factory
    register_observation_factory("CustomObservationFactory", CustomObservationFactory)

Then configure it in your config file:

.. code-block:: yaml

    env:
      observation_factory: "CustomObservationFactory"
    
    observation_factory:
      custom_observation_factory:
        feature_dim: 64

Observation Design Guidelines
---------------------------

When designing custom observations, consider these best practices:

Normalization
^^^^^^^^^^^

Normalize all observation features to similar ranges (typically 0-1) to improve learning stability:

.. code-block:: python

    # Normalize processing time (divide by max possible time)
    max_process_time = max(op.duration.duration for job in instance.jobs 
                           for op in job.operations)
    normalized_time = current_time / max_process_time

Feature Selection
^^^^^^^^^^^^^^^

Include only relevant information:

- **Include**: Features that help distinguish good from bad decisions
- **Exclude**: Redundant or constant information
- **Consider**: Domain knowledge about what matters for scheduling

Locality
^^^^^^^

For complex problems, focus on locally relevant information:

.. code-block:: python

    # For each machine, include only:
    # 1. Machine's own state
    # 2. State of jobs that can be processed on this machine
    # 3. State of directly connected machines (e.g., upstream/downstream)
    
    def make_local_observation(self, state, machine_id):
        # Get machine's own state
        machine_state = next(m for m in state.machines if m.id == machine_id)
        
        # Get jobs that can be processed on this machine
        relevant_jobs = [j for j in state.jobs if any(op.machine_id == machine_id 
                                                    for op in j.operations)]
        
        # Build localized observation
        # ...

Temporal Information
^^^^^^^^^^^^^^^^^^

Include information about time and progress:

.. code-block:: python

    # Add time-related features
    def make(self, state):
        observation = np.zeros(self.observation_dim)
        
        # Current normalized time
        observation[0] = state.time.time / self.max_time
        
        # Average job completion percentage
        total_ops = sum(len(job.operations) for job in state.jobs)
        completed_ops = sum(sum(1 for op in job.operations if op.completed) 
                            for job in state.jobs)
        observation[1] = completed_ops / total_ops
        
        # ...

Testing Your Observation Factory
------------------------------

To validate your custom observation factory:

1. **Observation shape**: Ensure dimensions match your specification
2. **Range check**: Verify values stay within expected ranges
3. **Information content**: Test if essential scheduling information is captured
4. **Learning performance**: Compare agent performance with different observation spaces

.. code-block:: python

    # Quick validation test
    env = JobShopLabEnv(config=config, observation_factory=CustomObservationFactory)
    obs, _ = env.reset()
    
    # Check shape
    expected_shape = env.observation_space.shape
    assert obs.shape == expected_shape
    
    # Check range
    assert np.all(obs >= 0) and np.all(obs <= 1)
    
    # Run a simple episode to check values change reasonably
    for _ in range(10):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        print(f"Observation: {obs}, Reward: {reward}")