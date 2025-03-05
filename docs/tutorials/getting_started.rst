Getting Started
===============

This guide will help you set up JobShopLab and run your first job shop scheduling experiment.

Installation
-------------

To install JobShopLab, clone the repository and install it in editable mode using `pip`. We recommend using a virtual environment.

.. code-block:: bash

    # Create and activate virtual environment (optional but recommended)
    python -m venv jobshoplab-env
    source jobshoplab-env/bin/activate  # On Windows: jobshoplab-env\Scripts\activate
    
    # Clone the repository
    git clone https://github.com/your-username/jobshoplab.git
    
    # Install in editable mode
    cd jobshoplab
    pip install -e .

Basic Example
------------

Let's solve a classic job shop scheduling problem (ft06) using a random policy:

.. code-block:: python

    from jobshoplab import JobShopLabEnv, load_config
    from pathlib import Path
    
    # Load a pre-defined configuration
    config = load_config(config_path=Path("./data/config/getting_started_config.yaml"))
    
    # Create the environment
    env = JobShopLabEnv(config=config)
    
    # Run random actions until the episode is done
    done = False
    while not done:
        action = env.action_space.sample()
        obs, reward, truncated, terminated, info = env.step(action)
        done = truncated or terminated
    
    # Visualize the final schedule
    env.render()

Understanding the Environment
---------------------------

JobShopLab implements the OpenAI Gym interface:

- **reset()**: Initialize the environment with a fresh state
- **step(action)**: Execute an action and advance the simulation
- **render()**: Visualize the current state
- **observation_space**: Defines the structure of observations
- **action_space**: Defines the structure of actions

The environment returns standard Gym outputs:

.. code-block:: python

    obs, reward, truncated, terminated, info = env.step(action)
    
    # obs: Current state observation (depends on observation space)
    # reward: Scalar reward value
    # truncated: Whether episode was truncated (e.g., max steps reached)
    # terminated: Whether episode naturally terminated (all jobs completed)
    # info: Additional information dictionary (makespan, schedule details, etc.)

Configuration
------------

JobShopLab uses YAML configuration files to control environment behavior:

.. code-block:: yaml

    title: "Example Environment"
    default_loglevel: "warning"
    
    env: 
        observation_factory: "BinaryActionObservationFactory"
        reward_factory: "BinaryActionJsspReward"
        interpreter: "BinaryJobActionInterpreter"
        render_backend: "render_in_dashboard"
        middleware: "EventBasedBinaryActionMiddleware"
    
    compiler:
        repo: "SpecRepository"
        spec_repository:
            dir: "data/jssp_instances/ft06"

Key components in the configuration:

- **observation_factory**: Defines the observation space
- **reward_factory**: Determines the reward function
- **interpreter**: Translates actions to scheduling decisions
- **render_backend**: Visualization method
- **middleware**: Connects Gym interface to state machine
- **compiler/repo**: Specifies the problem instance source

Next Steps
---------

Now that you've run your first experiment, you can:

1. Try different problem instances from the data/jssp_instances directory
2. Experiment with different reward functions and observation spaces
3. Implement custom scheduling policies
4. Train reinforcement learning agents using frameworks like Stable Baselines

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