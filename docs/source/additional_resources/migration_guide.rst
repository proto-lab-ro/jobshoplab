Migration Guide: Output Buffer Completion Model
============================================

This guide helps you migrate existing JobShopLab code to work with the new Output Buffer Completion Model and enhanced transport logic. The changes are primarily focused on job completion semantics and require updates to function calls and test fixtures.

Overview of Changes
-------------------

The major changes in this release include:

1. **Job Completion Model**: Jobs are now complete only when at output buffers
2. **Function Signatures**: Several ``is_done()`` functions now require an ``instance`` parameter  
3. **Transport Logic**: Enhanced routing decisions and destination selection
4. **Time Dependencies**: New system for handling buffer ordering constraints
5. **Test Fixtures**: Updated to reflect new completion requirements

Breaking Changes
---------------

is_done() Function Signature Changes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Affected Functions:**

- ``jobshoplab.utils.state_machine_utils.core_utils.is_done()``
- ``jobshoplab.utils.state_machine_utils.job_type_utils.is_done()``
- ``jobshoplab.state_machine.core.state_machine.state.is_done()``

**Old Signature:**

.. code-block:: python

   def is_done(state: State) -> bool:
       pass

**New Signature:**

.. code-block:: python

   def is_done(state: State, instance: InstanceConfig) -> bool:
       pass

**Migration Required:**

.. code-block:: python

   # Before
   if core_utils.is_done(current_state):
       print("Simulation complete")

   # After  
   if core_utils.is_done(current_state, instance_config):
       print("Simulation complete")

get_next_idle_operation() Return Type Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Function:** ``jobshoplab.utils.state_machine_utils.job_type_utils.get_next_idle_operation()``

**Old Return Type:** ``OperationState`` (raised exception if none found)

**New Return Type:** ``Optional[OperationState]`` (returns None if none found)

**Migration Required:**

.. code-block:: python

   # Before - assumed operation always existed
   next_op = get_next_idle_operation(job_state)
   machine_id = next_op.machine_id

   # After - handle None case
   next_op = get_next_idle_operation(job_state)
   if next_op is not None:
       machine_id = next_op.machine_id
   else:
       # Handle job with no idle operations
       handle_completed_operations(job_state)

Step-by-Step Migration
---------------------

Step 1: Update Function Calls
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Search your codebase for calls to ``is_done()`` and add the ``instance`` parameter:

**Core Utils:**

.. code-block:: python

   # Find and replace pattern
   # Old: core_utils.is_done(state)  
   # New: core_utils.is_done(state, instance)

   from jobshoplab.utils.state_machine_utils import core_utils

   # Before
   simulation_complete = core_utils.is_done(current_state)

   # After
   simulation_complete = core_utils.is_done(current_state, instance_config)

**Job Type Utils:**

.. code-block:: python

   # Find and replace pattern
   # Old: job_type_utils.is_done(job)
   # New: job_type_utils.is_done(job, instance)

   from jobshoplab.utils.state_machine_utils import job_type_utils

   # Before
   job_complete = job_type_utils.is_done(job_state)

   # After  
   job_complete = job_type_utils.is_done(job_state, instance_config)

**State Machine:**

.. code-block:: python

   # Find and replace pattern
   # Old: state.is_done(result)
   # New: state.is_done(result, instance)

   from jobshoplab.state_machine.core.state_machine import state

   # Before
   done = state.is_done(state_machine_result)

   # After
   done = state.is_done(state_machine_result, instance_config)

Step 2: Update Custom Handlers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you have custom transition handlers that check job completion:

.. code-block:: python

   class CustomHandler:
       def __init__(self, instance: InstanceConfig):
           self.instance = instance  # Store instance for completion checks

       def handle_custom_transition(self, state: State, transition: ComponentTransition):
           # Before
           # if core_utils.is_done(state):
           #     return handle_completion(state)

           # After
           if core_utils.is_done(state, self.instance):
               return handle_completion(state)

Step 3: Update Test Fixtures
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Update test fixtures to place completed jobs in output buffers:

**Before:**

.. code-block:: python

   @pytest.fixture
   def completed_job():
       return JobState(
           id="job-1",
           operations=(
               OperationState(
                   id="op-1", 
                   operation_state_state=OperationStateState.DONE,
                   machine_id="machine-1"
               ),
           ),
           location="machine-1"  # Job at machine (old completion model)
       )

**After:**

.. code-block:: python

   @pytest.fixture
   def completed_job():
       return JobState(
           id="job-1", 
           operations=(
               OperationState(
                   id="op-1",
                   operation_state_state=OperationStateState.DONE,
                   machine_id="machine-1"
               ),
           ),
           location="output-buffer"  # Job at output buffer (new completion model)
       )

Step 4: Update Instance Configurations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Ensure your instance configurations include output buffers:

.. code-block:: yaml

   # Add output buffer to your instance configuration
   buffers:
     - id: "input-buffer"
       type: "flex_buffer"
       capacity: 999999
       role: "input"
       description: "Initial job storage"
       
     - id: "output-buffer"  # Required for new completion model
       type: "flex_buffer" 
       capacity: 999999
       role: "output"
       description: "Final destination for completed jobs"

   # Ensure transport routes to output buffer exist
   logistics:
     travel_times:
       # Add routes from all machines to output buffer
       ("machine-1", "output-buffer"): 5
       ("machine-2", "output-buffer"): 4
       ("machine-3", "output-buffer"): 6

Step 5: Handle Optional Return Types
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Update code that uses ``get_next_idle_operation()``:

.. code-block:: python

   # Before - assumed operation always exists
   def process_job(job_state: JobState):
       next_op = job_type_utils.get_next_idle_operation(job_state)
       return f"Next operation: {next_op.id}"

   # After - handle None case
   def process_job(job_state: JobState, instance: InstanceConfig):
       next_op = job_type_utils.get_next_idle_operation(job_state)
       if next_op is not None:
           return f"Next operation: {next_op.id}"
       elif job_type_utils.all_operations_done(job_state):
           return "All operations complete - ready for output buffer"
       else:
           return "No idle operations available"

Common Migration Patterns
-------------------------

Pattern 1: Completion Checking
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Before
   class SimulationRunner:
       def run_until_complete(self, state: State):
           while not core_utils.is_done(state):
               state = self.step(state)
           return state

   # After
   class SimulationRunner:
       def __init__(self, instance: InstanceConfig):
           self.instance = instance

       def run_until_complete(self, state: State):
           while not core_utils.is_done(state, self.instance):
               state = self.step(state)
           return state

Pattern 2: Job Status Analysis
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Before  
   def analyze_jobs(jobs: List[JobState]):
       completed = [job for job in jobs if job_type_utils.is_done(job)]
       return len(completed)

   # After
   def analyze_jobs(jobs: List[JobState], instance: InstanceConfig):
       completed = [job for job in jobs if job_type_utils.is_done(job, instance)]
       return len(completed)

Pattern 3: Custom Environment Integration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Before
   class CustomJobShopEnv(gym.Env):
       def _is_terminated(self):
           return core_utils.is_done(self.current_state)

   # After
   class CustomJobShopEnv(gym.Env):
       def _is_terminated(self):
           return core_utils.is_done(self.current_state, self.instance)

Testing Migration
----------------

Automated Migration Testing
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use this script to identify locations needing updates:

.. code-block:: python

   #!/usr/bin/env python3
   """
   Migration helper script to find is_done() calls needing updates.
   """
   import re
   import os
   from pathlib import Path

   def find_is_done_calls(directory: str):
       """Find all is_done() function calls that need migration."""
       pattern = r'is_done\s*\([^)]*\)'
       results = []
       
       for root, dirs, files in os.walk(directory):
           for file in files:
               if file.endswith('.py'):
                   filepath = Path(root) / file
                   try:
                       content = filepath.read_text()
                       matches = re.finditer(pattern, content)
                       for match in matches:
                           line_num = content[:match.start()].count('\n') + 1
                           results.append({
                               'file': str(filepath),
                               'line': line_num,
                               'match': match.group(0)
                           })
                   except Exception as e:
                       print(f"Error reading {filepath}: {e}")
       
       return results

   # Usage
   if __name__ == "__main__":
       calls = find_is_done_calls("./")
       for call in calls:
           print(f"{call['file']}:{call['line']} - {call['match']}")

Validation Testing
^^^^^^^^^^^^^^^^^

After migration, run these validation tests:

.. code-block:: python

   def test_migration_completeness():
       """Test that migration was successful."""
       from jobshoplab import JobShopLabEnv, load_config
       
       # Load test configuration
       config = load_config("test_config.yaml")
       env = JobShopLabEnv(config)
       
       # Run simulation
       obs, info = env.reset()
       done = False
       step_count = 0
       
       while not done and step_count < 1000:
           action = env.action_space.sample()
           obs, reward, terminated, truncated, info = env.step(action)
           done = terminated or truncated
           step_count += 1
       
       # Validate completion
       assert done, "Simulation should complete within 1000 steps"
       
       # Check that all jobs are at output buffers
       final_state = env.state.state
       output_buffer_ids = [b.id for b in env.instance.buffers 
                           if b.role == BufferRoleConfig.OUTPUT]
       
       for job in final_state.jobs:
           assert job.location in output_buffer_ids, \
               f"Job {job.id} not at output buffer: {job.location}"

Performance Impact
-----------------

Expected Changes
^^^^^^^^^^^^^^^

The new completion model may impact performance characteristics:

**Positive Impacts:**
- More realistic simulation behavior
- Better resource utilization modeling  
- Improved bottleneck identification

**Potential Considerations:**
- Slightly longer episodes (due to final transport requirements)
- Additional transport resource contention
- More complex state space (output buffer status matters)

**Monitoring Performance:**

.. code-block:: python

   def monitor_completion_metrics(env):
       """Monitor new completion-related metrics."""
       metrics = {
           'jobs_completed': 0,
           'jobs_at_output': 0,
           'avg_completion_time': 0,
           'transport_utilization': 0
       }
       
       state = env.state.state
       output_buffers = [b.id for b in env.instance.buffers 
                        if b.role == BufferRoleConfig.OUTPUT]
       
       for job in state.jobs:
           if job_type_utils.all_operations_done(job):
               metrics['jobs_completed'] += 1
               if job.location in output_buffers:
                   metrics['jobs_at_output'] += 1
       
       return metrics

Troubleshooting
--------------

Common Issues and Solutions
^^^^^^^^^^^^^^^^^^^^^^^^^^

**Issue 1: "TypeError: is_done() missing 1 required positional argument: 'instance'"**

*Solution:* Add the instance parameter to your is_done() calls.

.. code-block:: python

   # Fix
   result = core_utils.is_done(state, instance_config)

**Issue 2: "Jobs never complete in tests"**

*Solution:* Update test fixtures to place jobs in output buffers.

.. code-block:: python

   # Fix test fixture
   job_state = JobState(..., location="output-buffer")

**Issue 3: "Simulation runs forever"**

*Solution:* Ensure your instance configuration includes output buffers and transport routes to them.

.. code-block:: yaml

   # Fix configuration
   buffers:
     - id: "output-buffer"
       role: "output"

**Issue 4: "AttributeError: 'NoneType' object has no attribute 'machine_id'"**

*Solution:* Handle the new Optional return type from get_next_idle_operation().

.. code-block:: python

   # Fix
   next_op = get_next_idle_operation(job_state)
   if next_op is not None:
       machine_id = next_op.machine_id

Version Compatibility
---------------------

This migration guide applies to:

- **From Version**: Pre-output buffer model
- **To Version**: Output buffer completion model  
- **Compatibility**: Breaking changes require code updates
- **Timeline**: All updates should be made before using new features

For additional help with migration, please refer to:

- :doc:`../concepts/output_buffer_completion` - Detailed explanation of new completion model
- :doc:`../concepts/enhanced_transport_logic` - Transport system improvements  
- :doc:`../concepts/time_dependency_resolution` - New dependency handling system

Contact the development team if you encounter issues not covered in this guide.