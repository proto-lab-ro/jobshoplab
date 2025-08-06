Time Dependency Resolution System
=================================

JobShopLab implements a sophisticated time dependency resolution system to handle complex scheduling scenarios where transport operations must wait for optimal conditions. This system prevents deadlocks while respecting buffer ordering constraints (FIFO, LIFO, FLEX) in realistic manufacturing environments.

Overview
--------

The **Time Dependency Resolution System** addresses situations where Automated Guided Vehicles (AGVs) or other transport resources cannot immediately pick up jobs due to buffer positioning constraints. Instead of blocking the simulation, the system creates time dependencies that are resolved when conditions become favorable.

Core Concept
------------

Buffer Ordering Constraints
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Different buffer types enforce specific pickup rules:

- **FIFO (First-In-First-Out)**: Jobs can only be picked up from the front of the queue
- **LIFO (Last-In-First-Out)**: Jobs can only be picked up from the back of the queue  
- **FLEX**: Jobs can be picked up from any position
- **DUMMY**: Jobs can only be picked up from the first position

When a transport wants to pick up a job that's not in the correct position, a time dependency is created instead of blocking the simulation.

.. raw:: html

   <div class="mermaid">
   graph TD
       Transport[Transport Requests Pickup] --> CheckPos{Job at Correct Position?}
       CheckPos -->|Yes| Pickup[Execute Pickup]
       CheckPos -->|No| CreateDep[Create Time Dependency]
       CreateDep --> WaitCondition[Wait for Resolution Conditions]
       WaitCondition --> Resolve{Dependency Resolved?}
       Resolve -->|Yes| Pickup
       Resolve -->|No| ContinueWait[Continue Waiting]
   </div>

Time Dependency Structure
-------------------------

Time dependencies are represented as special state objects that contain:

.. code-block:: python

   @dataclass
   class TimeDependency:
       job_id: str           # The job that's blocking the pickup
       buffer_id: str        # The buffer where the blocking occurs
       transition: ComponentTransition  # The transition to execute when resolved

When a transport encounters a time dependency, it enters a waiting state until the dependency can be resolved.

Dependency Resolution Logic
---------------------------

The resolution system checks two conditions that can resolve a time dependency:

Resolution Condition 1: Job Position Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The desired job has moved to the correct position in the buffer according to the buffer's ordering rules.

.. code-block:: python

   def _time_dependency_is_resolved(transport, state, instance) -> bool:
       # Get the buffer and check if job is now in correct position
       if job_id == get_next_job_from_buffer(buffer_state, buffer_config):
           return True  # Job has moved to pickupable position

**Example Scenario:**
- FIFO buffer contains: [Job-A, Job-B, Job-C] 
- Transport wants Job-B (not at front)
- Creates time dependency on Job-A
- When Job-A is picked up: [Job-B, Job-C]
- Job-B is now at front → dependency resolved

Resolution Condition 2: Blocking Job Handling
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Another transport is already handling the blocking job, clearing the path.

.. code-block:: python

   def _time_dependency_is_resolved(transport, state, instance) -> bool:
       # Check if another transport is handling the blocking job
       for other_transport in state.transports:
           if other_transport.transport_job == blocking_job_id:
               return True  # Blocking job is being handled

**Example Scenario:**
- FIFO buffer contains: [Job-A, Job-B, Job-C]
- Transport-1 wants Job-B, creates dependency on Job-A
- Transport-2 picks up Job-A
- Transport-1's dependency is immediately resolved

Implementation Details
----------------------

Timed Transport Transitions
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The resolution system integrates with the timed transition handler:

.. code-block:: python

   def create_timed_transport_transitions(loglevel, state, instance):
       transitions = []
       
       for transport in state.transports:
           if isinstance(transport.occupied_till, TimeDependency):
               # Check if dependency can be resolved
               if _time_dependency_is_resolved(transport, state, instance):
                   transitions.append(transport.occupied_till.transition)
           elif isinstance(transport.occupied_till, Time):
               # Handle regular time-based transitions
               if transport.occupied_till.time <= state.time.time:
                   transitions.append(create_transport_transition(transport))
       
       return tuple(transitions)

Integration with State Machine
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The dependency resolution is checked during every state machine step:

1. **Transition Creation**: When impossible pickups are requested, time dependencies are created
2. **Resolution Checking**: Each simulation step checks if dependencies can be resolved  
3. **Transition Execution**: Resolved dependencies trigger their associated transitions
4. **State Updates**: Transport states are updated to reflect resolution

.. raw:: html

   <div class="mermaid">
   graph TD
       StateStep[State Machine Step] --> CheckDeps[Check Time Dependencies]
       CheckDeps --> AnyResolved{Any Dependencies Resolved?}
       AnyResolved -->|Yes| ExecuteTrans[Execute Resolved Transitions]
       AnyResolved -->|No| ContinueWait[Dependencies Continue Waiting]
       ExecuteTrans --> UpdateState[Update State]
       UpdateState --> NextStep[Next State Machine Step]
       ContinueWait --> NextStep
   </div>

Buffer Type Behaviors
---------------------

FIFO Buffer Dependency Resolution
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Scenario**: Transport wants Job-3 from FIFO buffer [Job-1, Job-2, Job-3]

.. code-block:: python

   # Dependency created: waiting for Job-1 and Job-2 to be removed
   # Resolution occurs when:
   # 1. Job-3 moves to front position, OR  
   # 2. Another transport handles Job-1 or Job-2

**Resolution Path**: Job-1 picked up → [Job-2, Job-3] → Job-2 picked up → [Job-3] → Job-3 pickupable

LIFO Buffer Dependency Resolution  
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Scenario**: Transport wants Job-1 from LIFO buffer [Job-1, Job-2, Job-3] (Job-3 is at back/pickupable position)

.. code-block:: python

   # Dependency created: waiting for Job-2 and Job-3 to be removed
   # Resolution occurs when Job-1 moves to last position

**Resolution Path**: Job-3 picked up → [Job-1, Job-2] → Job-2 picked up → [Job-1] → Job-1 pickupable

FLEX Buffer Dependency Resolution
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Note**: FLEX buffers typically don't create time dependencies since jobs can be picked up from any position. Dependencies would only occur due to other constraints (capacity, resource conflicts, etc.).

Advanced Scenarios
------------------

Cascading Dependencies
^^^^^^^^^^^^^^^^^^^^^

Multiple transports waiting on the same buffer create cascading resolution:

.. code-block:: python

   # Initial: FIFO buffer [A, B, C, D]
   # Transport-1 wants B → dependency on A
   # Transport-2 wants C → dependency on A and B  
   # Transport-3 wants D → dependency on A, B, and C
   
   # When Transport-X picks up A:
   # → Transport-1's dependency resolves immediately
   # → Transport-2's dependency updates (now only depends on B)
   # → Transport-3's dependency updates (now depends on B and C)

Deadlock Prevention
^^^^^^^^^^^^^^^^^^^

The system prevents deadlocks through multiple mechanisms:

1. **Dependency Chains**: Dependencies reference specific blocking jobs, not positions
2. **Multiple Resolution Paths**: Two different conditions can resolve each dependency
3. **Transport Availability**: Other transports can resolve blocking jobs
4. **Buffer Dynamics**: Jobs naturally flow through buffers over time

Example Usage
-------------

Creating Time Dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^

Time dependencies are created automatically by the transport handlers when pickup conditions aren't met:

.. code-block:: python

   def _get_waiting_time(state, transition, instance):
       # Check if job is at correct position for buffer type
       if not is_job_ready_for_pickup(job_state, buffer_state, buffer_config):
           # Create time dependency instead of blocking
           return TimeDependency(
               job_id=blocking_job_id,
               buffer_id=buffer_id, 
               transition=transition
           )

Monitoring Dependencies
^^^^^^^^^^^^^^^^^^^^^^

You can monitor active time dependencies in the system:

.. code-block:: python

   def count_active_dependencies(state: State) -> int:
       """Count transports waiting on time dependencies."""
       count = 0
       for transport in state.transports:
           if isinstance(transport.occupied_till, TimeDependency):
               count += 1
       return count

   # Usage
   active_deps = count_active_dependencies(current_state)
   print(f"Transports waiting on dependencies: {active_deps}")

Benefits
--------

System Robustness
^^^^^^^^^^^^^^^^^

- **Deadlock Prevention**: Prevents simulation from getting stuck
- **Realistic Behavior**: Models real-world waiting and coordination
- **Buffer Respect**: Maintains buffer ordering constraints
- **Resource Efficiency**: Transports don't waste time on impossible operations

Performance Benefits
^^^^^^^^^^^^^^^^^^^^

- **Non-Blocking**: Simulation continues while dependencies wait
- **Efficient Resolution**: Checks are performed only when conditions might have changed
- **Automatic Recovery**: System automatically recovers when conditions improve
- **Scalable**: Works efficiently with multiple buffers and transports

Configuration
-------------

Buffer Type Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^

Time dependency behavior is determined by buffer type configuration:

.. code-block:: yaml

   machines:
     - id: "machine-1"
       postbuffer:
         type: "fifo"        # Creates dependencies for non-front pickups
         capacity: 5
     - id: "machine-2" 
       postbuffer:
         type: "flex_buffer" # Rarely creates position-based dependencies
         capacity: 10

Transport Configuration
^^^^^^^^^^^^^^^^^^^^^^^

Transport resources that can resolve dependencies:

.. code-block:: yaml

   transports:
     - id: "agv-1"
       type: "agv"
       # AGV can resolve dependencies by handling blocking jobs
     - id: "agv-2"
       type: "agv" 
       # Multiple AGVs increase resolution opportunities

Debugging Time Dependencies
---------------------------

Common Issues and Solutions
^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Issue**: Dependencies never resolve
**Solution**: Ensure sufficient transport resources and check buffer configurations

**Issue**: Performance degradation with many dependencies  
**Solution**: Optimize buffer capacities and transport allocation

**Issue**: Unexpected dependency creation
**Solution**: Verify buffer types match intended pickup behaviors

Monitoring Tools
^^^^^^^^^^^^^^^^

.. code-block:: python

   def analyze_dependencies(state: State) -> dict:
       """Analyze current time dependency status."""
       deps_by_buffer = {}
       for transport in state.transports:
           if isinstance(transport.occupied_till, TimeDependency):
               buffer_id = transport.occupied_till.buffer_id
               if buffer_id not in deps_by_buffer:
                   deps_by_buffer[buffer_id] = []
               deps_by_buffer[buffer_id].append({
                   'transport_id': transport.id,
                   'blocking_job': transport.occupied_till.job_id,
                   'wanted_job': transport.transport_job
               })
       return deps_by_buffer

Future Enhancements
-------------------

Planned improvements to the time dependency system include:

- **Priority-Based Resolution**: Higher priority jobs resolve dependencies faster
- **Timeout Mechanisms**: Dependencies that expire after maximum wait times  
- **Resource Reservation**: Pre-booking transport resources for dependency resolution
- **Predictive Resolution**: Anticipating dependency resolution based on system trends