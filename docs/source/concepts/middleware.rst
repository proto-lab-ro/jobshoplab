Middleware
==========

The middleware is a critical component in JobShopLab that bridges the gap between the gym environment interface and the core state machine. It serves as a translator between the reinforcement learning paradigm and the functional state machine simulation.

Middleware Architecture
---------------------

The middleware layer sits between the gym interface and the state machine, performing several essential functions:

.. raw:: html

   <div class="mermaid">
    graph TD
       Agent[RL Agent] -->|Actions| GymEnv[Gym Environment]
       GymEnv -->|Actions| Middleware
       Middleware -->|Transitions| StateMachine[State Machine]
       StateMachine -->|New State| Middleware
       Middleware -->|Observations| GymEnv
       GymEnv -->|Observations| Agent
       Middleware -->|Uses| ObsFactory[Observation Factory]
       Middleware -->|Uses| RewardFactory[Reward Factory]
       Middleware -->|Uses| ActionFactory[Action Factory]
   </div>



Key Responsibilities
------------------

The middleware has several core responsibilities:

Action Translation
^^^^^^^^^^^^^^^^^^^

Middleware translates abstract gym actions into concrete state machine transitions:

.. code-block:: python

    # Agent provides an abstract action (e.g., integer)
    action = 5
    
    # Middleware uses an action interpreter to translate
    transition = action_interpreter.interpret(action, state)
    
    # State machine executes the concrete transition
    new_state = state_machine.execute(transition)

Observation Generation
^^^^^^^^^^^^^^^^^^^^

Middleware converts complex state machine states into observations for the agent:

.. code-block:: python

    # State machine returns detailed state
    state = state_machine.state
    
    # Middleware uses observation factory to create agent-friendly view
    observation = observation_factory.make(state)
    
    # Observation is returned to the agent via gym interface

Time Management
^^^^^^^^^^^^^

Middleware controls how time progresses in the simulation:

1. **Event-based**: Time jumps directly to the next event
2. **Continuous**: Time advances in fixed increments

This is implemented through "time machines" that calculate the next state based on different time progression models.

Reward Calculation
^^^^^^^^^^^^^^^^

Middleware determines rewards based on state transitions and goal achievement:

.. code-block:: python

    # State machine returns a new state
    new_state = state_machine.execute(transition)
    
    # Middleware evaluates the state and calculates reward
    reward = reward_factory.make(state_result, terminated, truncated)

Terminal State Detection
^^^^^^^^^^^^^^^^^^^^^

Middleware determines when an episode ends:

1. **Termination**: Natural completion of all jobs
2. **Truncation**: Episode cut short due to constraints (max steps, invalid actions)

Middleware Types
--------------

JobShopLab provides different middleware implementations for various use cases:

Event-Based Binary Action Middleware
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. info::
    The Event-Based Binary Action Middleware, breaks the complex flow into descrete decisions.
    It has a binary action space, where the agent selects whether to schedule a job/transport or not.
    It utilities event-based time progression and supports truncation behavior.
    The Time is progresses only if all possible actions where considered by the agent.


The most common middleware type, suitable for discrete action spaces:

.. code-block:: yaml

    env:
      middleware: "EventBasedBinaryActionMiddleware"
    
    middleware:
      event_based_binary_action_middleware:
        truncation_joker: 5
        truncation_active: False

Features:
- Supports binary action spaces (job selections)
- Uses event-based time progression
- Configurable truncation behavior


Customizing Middleware
-------------------

Create custom middleware by subclassing the base middleware:

.. code-block:: python

    from jobshoplab.state_machine.middleware import Middleware
    
    class CustomMiddleware(Middleware):
        def __init__(self, loglevel, config, instance, 
                     observation_factory, reward_factory, 
                     action_interpreter, *args, **kwargs):
            super().__init__(loglevel, config, instance,
                             observation_factory, reward_factory,
                             action_interpreter)
        
        def reset(self):
            # Custom reset logic
            pass
        
        def step(self, action):
            # Custom step logic
            pass

Key Middleware Parameters
-------------------------

Configure middleware behavior through these parameters:

.. code-block:: yaml

    middleware:
      event_based_binary_action_middleware:
        truncation_joker: 5       # Actions allowed after invalid action
        truncation_active: False  # Whether to truncate on invalid actions


These parameters control:
- How invalid actions are handled
- When episodes terminate