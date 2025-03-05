Getting Started
===============

This guide will help you get up and running with JobShopLab quickly. For detailed installation instructions, see the :doc:`installation` page.

Quick Start
----------

This quick start guide will demonstrate how to solve a simple job shop scheduling problem using JobShopLab.

Installation
^^^^^^^^^^

First, install JobShopLab:

.. code-block:: bash

    # Create and activate a virtual environment (recommended)
    python -m venv jobshoplab-env
    source jobshoplab-env/bin/activate  # On Windows: jobshoplab-env\Scripts\activate
    
    # Install JobShopLab
    pip install -e .

Running Your First Experiment
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Let's solve a classic job shop scheduling problem with a random policy:

.. code-block:: python

    from jobshoplab import JobShopLabEnv, load_config
    from pathlib import Path
    
    # Load configuration
    config = load_config(config_path=Path("./data/config/getting_started_config.yaml"))
    
    # Create environment
    env = JobShopLabEnv(config=config)
    
    # Reset environment
    obs, _ = env.reset()
    
    # Run with random actions until done
    done = False
    total_reward = 0
    
    while not done:
        # Random action
        action = env.action_space.sample()
        
        # Take a step
        obs, reward, truncated, terminated, info = env.step(action)
        
        # Update tracking variables
        total_reward += reward
        done = truncated or terminated
    
    # Print results
    print(f"Experiment completed with makespan: {info['makespan']}")
    print(f"Total reward: {total_reward}")
    
    # Visualize the schedule
    env.render()

Understanding the Components
^^^^^^^^^^^^^^^^^^^^^^^^^^

Let's break down the key components:

1. **Configuration**: Loaded from a YAML file that defines environment behavior
2. **Environment**: The `JobShopLabEnv` class implementing the OpenAI Gym interface
3. **Observation**: State information provided to the agent
4. **Action**: Decision made by the agent (which job to process next)
5. **Reward**: Feedback signal for reinforcement learning
6. **Rendering**: Visualization of the final schedule

Next Steps
---------

Now that you've run your first experiment, here are some next steps to explore:

Try Different Problem Instances
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

JobShopLab includes many standard job shop scheduling benchmark instances:

.. code-block:: python

    # Try a different instance
    from jobshoplab.compiler.repos import SpecRepository
    
    # Load ft10 instance (10 jobs, 10 machines)
    repo = SpecRepository(dir=Path("data/jssp_instances/ft10"), loglevel="warning", config=config)
    
    # Create compiler with this repository
    from jobshoplab.compiler import Compiler
    compiler = Compiler(config=config, loglevel="warning", repo=repo)
    
    # Create environment with this compiler
    env = JobShopLabEnv(config=config, compiler=compiler)

Experiment with Different Policies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Instead of random actions, try simple heuristic policies:

.. code-block:: python

    # Shortest Processing Time (SPT) policy
    def spt_policy(observation, env):
        # Get valid actions
        valid_actions = env.action_mask
        
        # Get processing times for each valid action
        processing_times = []
        for i, is_valid in enumerate(valid_actions):
            if is_valid:
                # Get processing time for this action
                # (Implementation details depend on your observation space)
                processing_time = get_processing_time(observation, i)
                processing_times.append((i, processing_time))
        
        # Choose action with shortest processing time
        if processing_times:
            return min(processing_times, key=lambda x: x[1])[0]
        else:
            return 0  # No valid actions, return dummy action
    
    # Use the policy
    obs, _ = env.reset()
    done = False
    
    while not done:
        action = spt_policy(obs, env)
        obs, reward, truncated, terminated, info = env.step(action)
        done = truncated or terminated

Train a Reinforcement Learning Agent
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use a library like Stable Baselines3 to train a reinforcement learning agent:

.. code-block:: python

    from stable_baselines3 import PPO
    
    # Create environment
    env = JobShopLabEnv(config=config)
    
    # Initialize agent
    model = PPO("MlpPolicy", env, verbose=1)
    
    # Train agent
    model.learn(total_timesteps=10000)
    
    # Evaluate agent
    obs, _ = env.reset()
    done = False
    
    while not done:
        action, _ = model.predict(obs)
        obs, reward, truncated, terminated, info = env.step(action)
        done = truncated or terminated
    
    # Visualize results
    env.render()

Further Reading
--------------

For more detailed information, check out these additional resources:

- :doc:`tutorials/framework_config` - Learn how to configure the framework
- :doc:`tutorials/custom_instances` - Create your own problem instances
- :doc:`tutorials/custom_rewards` - Define custom reward functions
- :doc:`tutorials/custom_observations` - Customize observation spaces
- :doc:`tutorials/visualisation` - Explore visualization options