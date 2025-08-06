Output Buffer Completion Model
=============================

JobShopLab has evolved to implement a more realistic completion model that better reflects real-world manufacturing systems. Instead of considering jobs complete when their operations finish, the system now requires jobs to be transported to designated output buffers for true completion.

Overview
--------

The **Output Buffer Completion Model** represents a significant enhancement to JobShopLab's job completion semantics. This change aligns the simulation with real manufacturing workflows where completed work-in-progress must be delivered to final storage or shipping areas.

Key Concepts
------------

Traditional vs. Output Buffer Completion
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Traditional Model (Previous):**
- Jobs were considered "done" when all operations reached DONE state
- No consideration of material flow to final destinations
- Incomplete simulation of manufacturing workflow

**Output Buffer Model (Current):**
- Jobs are "done" only when both conditions are met:
  1. All operations are in DONE state
  2. Job has been transported to an output buffer
- Ensures complete material flow simulation
- Reflects real-world manufacturing closure

.. raw:: html

   <div class="mermaid">
   graph TD
       OpComplete[All Operations Complete] --> CheckLocation{Job at Output Buffer?}
       CheckLocation -->|Yes| JobDone[Job Complete]
       CheckLocation -->|No| NeedTransport[Transport to Output Buffer Required]
       NeedTransport --> Transport[AGV Transport]
       Transport --> JobDone
   </div>

Output Buffer Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Output buffers are defined in the instance configuration with the ``OUTPUT`` role:

.. code-block:: yaml

   buffers:
     - id: "output-buffer"
       type: "flex_buffer"
       capacity: 999999
       role: "output"  # Designates this as an output buffer
       description: "Final destination for completed jobs"

Job Completion Logic
^^^^^^^^^^^^^^^^^^^^

The completion logic is implemented in multiple layers:

1. **Core State Machine** (``core_utils.is_done()``):

.. code-block:: python

   def is_done(state: State, instance: InstanceConfig) -> bool:
       """Check if all jobs are in output buffers."""
       output_buffer_ids = [b.id for b in get_output_buffers(instance)]
       for job in state.jobs:
           if job.location not in output_buffer_ids:
               return False
       return True

2. **Individual Job Completion** (``job_type_utils.is_done()``):

.. code-block:: python

   def is_done(job: JobState, instance: InstanceConfig) -> bool:
       """Check if a job is completely done."""
       output_buffer_ids = [b.id for b in instance.buffers 
                           if b.role == BufferRoleConfig.OUTPUT]
       return (all_operations_done(job) and 
               job.location in output_buffer_ids)

Transport Decision Logic
------------------------

Enhanced Transport Routing
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The transport system now makes intelligent routing decisions based on job completion status:

.. code-block:: python

   # Determine destination based on job's operation completion status
   match job_type_utils.no_operation_idle(job_state):
       case True:  # All operations complete - transport to output buffer
           destination = next(iter(get_output_buffers(instance))).id
       case False:  # Operations remain - transport to next operation's machine
           destination = get_next_idle_operation(job_state).machine_id

Job Transportability Rules
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``is_transportable()`` function implements a comprehensive decision tree:

1. **Jobs at output buffers**: Not transportable (fully complete)
2. **All operations done, not at output**: Transportable to output buffer
3. **Operations remaining, not at next machine**: Transportable to next machine
4. **Operations remaining, at correct machine**: Not transportable

.. raw:: html

   <div class="mermaid">
   graph TD
       CheckJob[Job Evaluation] --> AtOutput{At Output Buffer?}
       AtOutput -->|Yes| NotTransport[Not Transportable - Complete]
       AtOutput -->|No| AllOpsDone{All Operations Done?}
       AllOpsDone -->|Yes| TransportOutput[Transportable to Output Buffer]
       AllOpsDone -->|No| AtCorrectMachine{At Next Operation's Machine?}
       AtCorrectMachine -->|Yes| NotTransport2[Not Transportable - Ready for Processing]
       AtCorrectMachine -->|No| TransportMachine[Transportable to Next Machine]
   </div>

Implementation Details
----------------------

New Functions Added
^^^^^^^^^^^^^^^^^^^

Several new utility functions support the output buffer model:

**Buffer Utilities:**

.. code-block:: python

   def get_output_buffers(instance: InstanceConfig) -> tuple[BufferConfig, ...]:
       """Get all output buffer configurations."""
       return tuple(b for b in instance.buffers 
                   if b.role == BufferRoleConfig.OUTPUT)

**Job Status Utilities:**

.. code-block:: python

   def all_operations_done(job: JobState) -> bool:
       """Check if all operations in a job are in DONE state."""
       return all(op.operation_state_state == OperationStateState.DONE 
                 for op in job.operations)

   def no_operation_idle(job: JobState) -> bool:
       """Check if no operations are in IDLE state."""
       return all(op.operation_state_state != OperationStateState.IDLE 
                 for op in job.operations)

**Transport Logic:**

.. code-block:: python

   def is_transportable(job_state: JobState, state: State, 
                       instance: InstanceConfig) -> bool:
       """Determine if a job needs transportation."""
       # Comprehensive 4-case decision logic for transport needs

API Changes
-----------

Breaking Changes
^^^^^^^^^^^^^^^^

The following function signatures have changed and require updates:

**Before:**

.. code-block:: python

   # Old signature - only state parameter
   def is_done(state: State) -> bool:
       pass

**After:**

.. code-block:: python

   # New signature - requires instance parameter
   def is_done(state: State, instance: InstanceConfig) -> bool:
       pass

**Affected Functions:**

- ``core_utils.is_done()``
- ``job_type_utils.is_done()``
- ``state.is_done()`` (in state machine module)
- ``JobShopLabEnv._is_terminated()`` (in environment)

Migration Guide
^^^^^^^^^^^^^^^

To update existing code:

1. **Function Calls**: Add instance parameter to ``is_done()`` calls:

.. code-block:: python

   # Old
   if is_done(state):
       print("Simulation complete")

   # New
   if is_done(state, instance):
       print("Simulation complete")

2. **Custom Handlers**: Update any custom transition handlers that check completion

3. **Testing**: Update test fixtures to place completed jobs in output buffers:

.. code-block:: python

   # Old test fixture
   job_state_done = JobState(id="j-1", operations=(done_op,), location="m-1")

   # New test fixture  
   job_state_done = JobState(id="j-1", operations=(done_op,), location="output-buffer")

Benefits
--------

Realistic Workflow Modeling
^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Complete Material Flow**: Simulates the entire manufacturing process from input to output
- **Resource Utilization**: AGVs must transport finished jobs, affecting system capacity
- **Bottleneck Analysis**: Output buffer capacity can become a constraint
- **Logistics Integration**: Transport resources are utilized for final delivery

Performance Considerations
^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Simulation Accuracy**: More realistic completion criteria
- **Resource Contention**: Transport resources compete for final delivery tasks
- **Scheduling Complexity**: Agents must consider final transport in their decisions

Example Usage
-------------

Complete Workflow Example
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from jobshoplab import JobShopLabEnv, load_config

   # Load configuration with output buffers
   config = load_config("config_with_output_buffers.yaml")
   env = JobShopLabEnv(config)

   obs, info = env.reset()
   done = False

   while not done:
       action = env.action_space.sample()
       obs, reward, terminated, truncated, info = env.step(action)
       done = terminated or truncated

   # All jobs are now in output buffers
   print("All jobs successfully delivered to output buffers!")

Checking Job Completion Status
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from jobshoplab.utils.state_machine_utils import job_type_utils

   # Check if individual job is complete
   if job_type_utils.is_done(job_state, instance):
       print(f"Job {job_state.id} is complete and at output buffer")
   elif job_type_utils.all_operations_done(job_state):
       print(f"Job {job_state.id} operations done, needs transport to output")
   else:
       print(f"Job {job_state.id} still has operations to complete")

Future Enhancements
-------------------

The output buffer completion model enables several future enhancements:

- **Multiple Output Types**: Different output buffers for different product types
- **Quality Control**: Inspection stations before final output
- **Shipping Integration**: Connection to external logistics systems
- **Performance Metrics**: New KPIs based on complete workflow completion