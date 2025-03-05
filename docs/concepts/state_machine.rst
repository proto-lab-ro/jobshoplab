State Machine
============

The state machine is the core of JobShopLab, responsible for simulating the execution of job shop scheduling problems. It follows functional programming principles, operating on immutable data structures to ensure predictability and reproducibility.

State Machine Architecture
-------------------------

The state machine implements a pure functional architecture with these key components:

1. **State**: Immutable data structure representing the complete system state
2. **Handlers**: Pure functions that process transitions and update state
3. **Transitions**: Events that transform the system from one state to another
4. **Validators**: Functions that check transition validity

.. raw:: html

   <div class="mermaid">
   graph TD
       State[Current State] --> Validator[Transition Validator]
       Validator -->|Valid| Handler[Transition Handler]
       Validator -->|Invalid| Reject[Reject Transition]
       Handler --> NewState[New State]
       Transitions[Possible Transitions] --> Validator
   </div>

State Representation
-------------------

The state is represented by an immutable `State` dataclass with these components:

- **Time**: Current simulation time
- **Machines**: Collection of machine states (IDLE, PROCESSING, etc.)
- **Jobs**: Collection of job states with operation completion status
- **Buffers**: Optional buffer capacities and contents
- **Transport**: Optional transport resources and locations

.. code-block:: python
    
    # Example state structure (simplified)
    @dataclass(frozen=True)
    class State:
        time: Time
        machines: Tuple[MachineState, ...]
        jobs: Tuple[JobState, ...]
        buffers: Optional[Tuple[BufferState, ...]] = None
        transport: Optional[Tuple[TransportState, ...]] = None

Transition System
---------------

Transitions represent events that can change the state, such as:

- Starting a job operation on a machine
- Completing an operation
- Moving a job between machines
- Transporting materials

Each transition is validated before being applied to ensure it respects system constraints.

.. raw:: html

   <div class="mermaid">
   graph LR
       StartOp[StartOperation] --> State
       CompleteOp[CompleteOperation] --> State
       MoveJob[MoveJob] --> State
       Transport[Transport] --> State
   </div>

Handler Functions
---------------

Handlers are pure functions that implement transitions:

.. code-block:: python

    def handle_start_operation(
        state: State, 
        job_id: str, 
        machine_id: str,
        operation_id: str
    ) -> State:
        """Handle starting an operation for a job on a machine."""
        # Create new machine states tuple with updated machine
        # Create new job states tuple with updated job
        # Return new state with updated collections
        return State(
            time=state.time,
            machines=new_machines,
            jobs=new_jobs,
            buffers=state.buffers,
            transport=state.transport
        )

Time Management
--------------

The state machine supports different time progression mechanisms:

1. **Event-based**: Time jumps to the next event (operation completion)
2. **Continuous**: Time progresses in fixed increments
3. **Stochastic**: Handles probabilistic completion times

These are implemented as time machines that calculate the next state based on the current one.

.. raw:: html

   <div class="mermaid">
   graph TD
       State[Current State] --> TimeMachine[Time Machine]
       TimeMachine --> |Calculate Next Event| NextEvent[Next Event Time]
       NextEvent --> NewState[New State with Updated Time]
   </div>

Middleware Integration
--------------------

The state machine interacts with the rest of the framework through middleware:

- Middleware translates gym actions into state machine transitions
- State machine executes transitions and returns new states
- Middleware converts state into observations for the agent

This separation of concerns keeps the state machine focused purely on simulating job shop dynamics, while middleware handles RL-specific aspects.