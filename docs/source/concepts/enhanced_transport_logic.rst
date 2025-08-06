Enhanced Transport Logic
=======================

JobShopLab's transport system has been significantly enhanced to provide intelligent routing decisions, better integration with the output buffer completion model, and improved support for complex manufacturing workflows. The enhanced transport logic ensures efficient material flow from input through processing to final output delivery.

Overview
--------

The **Enhanced Transport Logic** represents a comprehensive overhaul of how Automated Guided Vehicles (AGVs) and other transport resources make routing and pickup decisions. The system now intelligently determines destinations based on job completion status, handles output buffer deliveries, and provides robust decision-making for complex scenarios.

Key Improvements
----------------

Intelligent Destination Selection
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The transport system now makes context-aware routing decisions:

.. raw:: html

   <div class="mermaid">
   graph TD
       JobRequest[Transport Job Request] --> CheckOps{All Operations Complete?}
       CheckOps -->|Yes| OutputBuffer[Route to Output Buffer]
       CheckOps -->|No| NextOp[Route to Next Operation Machine]
       OutputBuffer --> FinalDelivery[Complete Job Workflow]
       NextOp --> ContinueProcess[Continue Processing]
   </div>

**Decision Logic:**

.. code-block:: python

   # Determine destination based on job's operation completion status
   match job_type_utils.no_operation_idle(job_state):
       case True:  # All operations complete - transport to output buffer
           destination = next(iter(get_output_buffers(instance))).id
       case False:  # Operations remain - transport to next operation's machine  
           destination = get_next_idle_operation(job_state).machine_id

Enhanced Job Transportability Assessment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The system now uses a comprehensive 4-case decision tree for determining transport needs:

1. **Fully Complete Jobs**: No transport needed (already at output buffer)
2. **Processing Complete**: Transport to output buffer required
3. **At Correct Machine**: No transport needed (ready for next operation)
4. **Wrong Location**: Transport to next operation machine required

.. code-block:: python

   def is_transportable(job_state: JobState, state: State, 
                       instance: InstanceConfig) -> bool:
       """Comprehensive transport need assessment."""
       
       # Case 1: Job is fully complete
       if job_type_utils.is_done(job_state, instance):
           return False  # No transport needed
           
       # Case 2: All operations done but not at output buffer
       if job_type_utils.all_operations_done(job_state):
           return True   # Transport to output buffer needed
           
       # Case 3: Job has remaining operations
       next_op = job_type_utils.get_next_idle_operation(job_state)
       if next_op is None:
           raise InvalidValue(job_state, "Inconsistent job state")
           
       # Case 4: Check if already at correct machine
       if is_job_at_machine(job_state, get_machine_by_id(next_op.machine_id)):
           return False  # No transport needed
           
       return True  # Transport to next machine needed

Transport Handler Enhancements
------------------------------

Unified Destination Logic
^^^^^^^^^^^^^^^^^^^^^^^^^

All transport handlers now use consistent destination selection logic:

**Pickup to Transit Handler:**

.. code-block:: python

   def handle_agv_transport_pickup_to_transit_transition(state, instance, transition, transport):
       # Get job and determine routing
       job_state = get_job_state_by_id(state.jobs, transition.job_id)
       
       # Determine transport destination based on job's operation state
       match job_type_utils.no_operation_idle(job_state):
           case True:  # All operations complete - transport to output buffer
               transport_destination = next(iter(get_output_buffers(instance))).id
           case False:  # Operations remain - transport to next operation's machine
               transport_destination = get_next_not_done_operation(job_state).machine_id

**Idle to Working Handler:**

.. code-block:: python

   def handle_agv_transport_idle_to_working_transition(state, instance, transition, transport):
       job_state = get_job_state_by_id(state.jobs, transition.job_id)
       
       # Determine target location based on job's operation completion status
       match job_type_utils.no_operation_idle(job_state):
           case True:  # All operations complete - transport to output buffer
               target_location = next(iter(get_output_buffers(instance))).id
           case False:  # Operations remain - transport to next idle operation's machine
               next_op_state = get_next_idle_operation(job_state)
               if next_op_state is None:
                   raise InvalidValue("No next operation state found for job")
               target_location = next_op_state.machine_id

Output Buffer Integration
^^^^^^^^^^^^^^^^^^^^^^^^^

Enhanced support for different target component types:

.. code-block:: python

   def complete_transport_task(job_state, transport, target_component_state, time, instance):
       # Handle different target types
       if isinstance(target_component_state, MachineState):
           # For machines, update the prebuffer with the job
           target_component_state = replace(target_component_state, prebuffer=filled_buffer)
       elif isinstance(target_component_state, BufferState):
           # For standalone buffers (like output buffers), replace entire buffer state
           target_component_state = filled_buffer

Travel Time Calculation Enhancement
-----------------------------------

Improved Destination Resolution
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The travel time calculation system now properly handles both operation-based and output buffer destinations:

.. code-block:: python

   def _get_travel_time_for_transport(jobs, job_id, instance):
       job_state = get_job_state_by_id(jobs, job_id)
       
       # Determine destination based on job's operation completion status
       match job_type_utils.no_operation_idle(job_state):
           case True:
               # All operations complete - transport to output buffer
               next_location = next(iter(get_output_buffers(instance))).id
           case False:
               # Operations remain - transport to next operation's machine
               next_op = get_next_idle_operation(job_state)
               next_location = next_op.machine_id

Unified Duration Handling
^^^^^^^^^^^^^^^^^^^^^^^^^

Simplified and consistent duration processing for both deterministic and stochastic times:

.. code-block:: python

   # Handle different types of duration configurations
   match duration:
       case DeterministicTimeConfig() | StochasticTimeConfig():
           return duration.time  # Both types use .time attribute
       case _:
           raise NotImplementedError("Unsupported duration type")

Transport Transition Generation
-------------------------------

Enhanced Possible Transitions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The system now generates more accurate transport transitions by considering job completion status:

.. code-block:: python

   def get_possible_transport_transition(state: State, instance) -> tuple[ComponentTransition, ...]:
       # Get available transports
       possible_transports = get_possible_transports(state.transports, instance.transports)
       
       # Filter jobs that need transport
       jobs_needing_transport = []
       for job_state in state.jobs:
           if not job_type_utils.is_job_running(job_state):
               if is_transportable(job_state, state, instance):
                   jobs_needing_transport.append(job_state)
       
       # Remove jobs already assigned to transports
       jobs_already_assigned = [t.transport_job for t in state.transports if t.transport_job]
       available_jobs = [job for job in jobs_needing_transport 
                        if job.id not in jobs_already_assigned]

**Transportability Assessment Integration:**

The enhanced logic correctly identifies when jobs need transport by considering:
- Job completion status (all operations done vs. operations remaining)
- Current location vs. required destination  
- Output buffer requirements for completed jobs
- Next operation machine requirements for continuing jobs

Advanced Scenarios
------------------

Multi-Stage Job Completion
^^^^^^^^^^^^^^^^^^^^^^^^^^

**Scenario 1: Job with Remaining Operations**

.. code-block:: python

   # Job state: 2 operations done, 1 remaining
   job_state = JobState(
       id="job-1",
       operations=[
           OperationState(id="op-1", operation_state_state=OperationStateState.DONE, ...),
           OperationState(id="op-2", operation_state_state=OperationStateState.DONE, ...),
           OperationState(id="op-3", operation_state_state=OperationStateState.IDLE, ...)
       ],
       location="machine-2-postbuffer"
   )
   
   # Transport decision: Route to machine for op-3
   # no_operation_idle(job_state) → False
   # Destination: machine for op-3

**Scenario 2: Job with All Operations Complete**

.. code-block:: python

   # Job state: All operations done, at machine postbuffer
   job_state = JobState(
       id="job-2", 
       operations=[
           OperationState(id="op-1", operation_state_state=OperationStateState.DONE, ...),
           OperationState(id="op-2", operation_state_state=OperationStateState.DONE, ...)
       ],
       location="machine-3-postbuffer"
   )
   
   # Transport decision: Route to output buffer
   # no_operation_idle(job_state) → True
   # Destination: output buffer

**Scenario 3: Job Already at Output Buffer**

.. code-block:: python

   # Job state: Complete and at final destination
   job_state = JobState(
       id="job-3",
       operations=[...],  # All DONE
       location="output-buffer"
   )
   
   # Transport decision: No transport needed
   # is_done(job_state, instance) → True
   # is_transportable() → False

Complex Buffer Interactions
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The enhanced system handles various buffer configurations:

**Machine-Associated Buffers:**

.. code-block:: python

   # Job at machine's postbuffer
   if buffer_config.parent:  # Buffer belongs to a machine
       current_location = buffer_config.parent  # Use machine ID for routing
   else:
       current_location = job_state.location     # Use buffer ID directly

**Standalone Output Buffers:**

.. code-block:: python

   # Independent output buffers (not part of machines)
   output_buffers = get_output_buffers(instance)
   for buffer in output_buffers:
       if buffer.parent is None:  # Standalone buffer
           # Direct routing to buffer ID
           destination = buffer.id

Error Handling and Robustness
-----------------------------

Enhanced Error Detection
^^^^^^^^^^^^^^^^^^^^^^^

The system provides better error messages and validation:

.. code-block:: python

   def get_next_idle_operation(job: JobState) -> Optional[OperationState]:
       """Returns None instead of raising exceptions for graceful handling."""
       next_operation = next(
           filter(lambda op: op.operation_state_state == OperationStateState.IDLE, 
                 job.operations), None
       )
       return next_operation  # None if no idle operations

**Inconsistent State Detection:**

.. code-block:: python

   def is_transportable(job_state, state, instance):
       next_op = get_next_idle_operation(job_state)
       if next_op is None and not all_operations_done(job_state):
           # Inconsistent state: no idle operations but not all done
           raise InvalidValue(job_state, "Inconsistent job state detected")

Performance Optimizations
-------------------------

Efficient Transport Selection
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The system avoids unnecessary computation by:

1. **Early Filtering**: Jobs are filtered by transport need before expensive calculations
2. **Cached Lookups**: Buffer configurations are retrieved once per calculation
3. **Conditional Logic**: Complex routing logic only applied when needed

**Optimized Job Filtering:**

.. code-block:: python

   # Efficient filtering pipeline
   idle_jobs = filter(lambda x: not is_job_running(x), state.jobs)
   transportable_jobs = filter(lambda x: is_transportable(x, state, instance), idle_jobs)
   available_jobs = filter(lambda x: x.id not in assigned_jobs, transportable_jobs)

Configuration Examples
---------------------

Complete Transport Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

   # Instance configuration with enhanced transport support
   logistics:
     travel_times:
       # Machine to machine routes
       ("machine-1", "machine-2"): 5
       ("machine-2", "machine-3"): 3
       # Machine to output buffer routes  
       ("machine-1", "output-buffer"): 7
       ("machine-2", "output-buffer"): 4
       ("machine-3", "output-buffer"): 6

   buffers:
     - id: "output-buffer"
       type: "flex_buffer"
       capacity: 999999
       role: "output"  # Designated output buffer

   transports:
     - id: "agv-1"
       type: "agv"
       buffer:
         id: "agv-1-buffer"
         capacity: 1

Monitoring and Debugging
------------------------

Transport Decision Tracking
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   def log_transport_decision(job_state: JobState, instance: InstanceConfig) -> str:
       """Log the reasoning behind transport decisions."""
       if is_done(job_state, instance):
           return f"Job {job_state.id}: Complete - no transport needed"
       elif all_operations_done(job_state):
           return f"Job {job_state.id}: Operations done - route to output buffer"
       else:
           next_op = get_next_idle_operation(job_state)
           if next_op:
               return f"Job {job_state.id}: Route to machine {next_op.machine_id}"
           else:
               return f"Job {job_state.id}: ERROR - No idle operations found"

Performance Metrics
^^^^^^^^^^^^^^^^^^^

Track transport efficiency with new metrics:

.. code-block:: python

   def calculate_transport_efficiency(history: List[State], instance: InstanceConfig):
       """Calculate transport system efficiency metrics."""
       total_transports = 0
       output_deliveries = 0
       
       for state in history:
           for transport in state.transports:
               if transport.transport_job:
                   total_transports += 1
                   job = get_job_state_by_id(state.jobs, transport.transport_job)
                   if all_operations_done(job):
                       output_deliveries += 1
       
       return {
           'total_transports': total_transports,
           'output_deliveries': output_deliveries,
           'completion_rate': output_deliveries / total_transports if total_transports > 0 else 0
       }

Future Enhancements
-------------------

The enhanced transport logic enables several future improvements:

- **Multi-Objective Routing**: Consider energy, time, and resource utilization
- **Predictive Transport**: Anticipate future transport needs for better scheduling
- **Dynamic Routing**: Adapt routes based on real-time congestion and availability
- **Load Balancing**: Distribute transport tasks across available resources
- **Quality Control Integration**: Route jobs through inspection stations when needed

This enhanced transport logic provides a solid foundation for realistic, efficient, and scalable job shop scheduling simulations that closely model real-world manufacturing environments.