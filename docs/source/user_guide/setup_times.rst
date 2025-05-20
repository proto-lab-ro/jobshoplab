Setup Times
===========

In many manufacturing scenarios, machines need to be reconfigured when switching between different tools or operations. JobShopLab allows you to model these sequence-dependent setup times to create more realistic scheduling environments.

What Are Setup Times?
-------------------

Setup times (also called changeover times) represent the time required to prepare a machine for the next operation when it's different from the previous one. This includes:

- Tool changes
- Machine reconfiguration
- Material handling setup
- Cleaning procedures
- Equipment calibration

Setup Times in JobShopLab
------------------------

JobShopLab implements setup times as a matrix that defines the time needed to switch from one tool to another on a specific machine.
Every machine follows a cylce of states:

- **IDLE**: Waiting for a job
- **SETUP**: Preparing for the next operation
- **PROCESSING**: Actively working on the operation
- **OUTAGE**: Machine is down for maintenance or repair

.. note::
    setup times are zero by default but always applied

Configuration
------------

Setup times are defined in the DSL using the ``setup_times`` section with a matrix-like structure:
Every machine potentially has its own setup time matrix, which can be static or stochastic.
Every operation in a job has a tool assigned to it, and the setup time is determined by the tool used in the previous operation.


.. note::
   tl-0, tl-1, tl-2 are the tool name id's. 

.. code-block:: yaml

  setup_times:
    - machine: "m-0"
      specification: |
        tl-0|tl-1|tl-2
        tl-0|0 2 5
        tl-1|2 0 8
        tl-2|5 2 0
      time_behavior: static
          
    - machine: "m-1"
      specification: |
        tl-0|tl-1|tl-2
        tl-0|0 2 5
        tl-1|2 0 8
        tl-2|5 2 0
      time_behavior:
        type: "uni"
        offset: 2

    - machine: "m-2"
      specification: |
        tl-0|tl-1|tl-2
        tl-0|0 2 5
        tl-1|2 0 8
        tl-2|5 2 0

      time_behavior:
        type: "uni"
        offset: 2

The setup time matrix should be read as:
- Rows represent the "from" tool
- Columns represent the "to" tool
- Values represent the time units needed for the change

.. note::
   The diagonal of the matrix (same tool to same tool) typically has zeros, as no setup is needed when continuing with the same tool.

Tool Usage Definition
^^^^^^^^^^^^^^^^^^^

To use setup times, you must define which tools each operation uses:

.. code-block:: yaml

    tool_usage:
      - job: "j0"
        operation_tools: ["tl-0", "tl-1", "tl-2"]
      - job: "j1"
        operation_tools: ["tl-0", "tl-1", "tl-2"]
      - job: "j2"
        operation_tools: ["tl-0", "tl-1", "tl-2"]

This connects each operation in a job to a specific tool. 

State Transitions with Setup
--------------------------

When a machine needs to change tools between operations, it follows this workflow:

1. Complete the current operation
2. Enter SETUP state
3. Remain in SETUP for the duration specified in the setup time matrix
4. Switch to PROCESSING for the new operation

.. hint::
   Setup times can significantly impact the optimal schedule.

Stochastic Setup Times
--------------------

Setup times can also follow stochastic patterns to model real-world variability:

.. code-block:: yaml

    setup_times:
      - machine: "m-2"
        specification: |
            tl-0|tl-1|tl-2
            tl-0|0 2 5
            tl-1|2 0 8
            tl-2|5 2 0
        time_behavior:
          type: "gaussian"
          mean: 1.0
          std: 0.2

The stochastic model applies a distribution to the base values in the setup matrix.

.. hint::
   read more about stochastic time behavior in :doc:`stochastic_time_behavior`.

Example Implementation
--------------------

Here's a complete example with tools and setup times:

.. code-block:: yaml

    instance_config:
      description: "Example with setup times"
      instance:
        description: "3x3 problem"
        specification: |
          (m0,t)|(m1,t)|(m2,t)
          j0|(0,3) (1,2) (2,2)
          j1|(0,2) (2,1) (1,4)
          j2|(1,4) (2,3) (0,3)
        
        # Define which tool each operation uses
        tool_usage:
          - job: "j0"
            operation_tools: ["tl-0", "tl-1", "tl-2"]
          - job: "j1"
            operation_tools: ["tl-0", "tl-1", "tl-2"]
          - job: "j2"
            operation_tools: ["tl-0", "tl-1", "tl-2"]
      
      # Define setup time matrices
      setup_times:
        - machine: "m-0"
          specification: |
            tl-0|tl-1|tl-2
            tl-0|0 2 5
            tl-1|2 0 8
            tl-2|5 2 0
          time_behavior: static
              
        - machine: "m-1"
          specification: |
            tl-0|tl-1|tl-2
            tl-0|0 2 5
            tl-1|2 0 8
            tl-2|5 2 0
          time_behavior:
            type: "uni"
            offset: 2

Working with Setup Times in Python
--------------------------------

You can access setup time information in your Python code:

.. code-block:: python

    # Access setup time for a specific machine
    setup_times = env.instance.machines[1].setup_times
    
    # Get the time to change from tool1 to tool2
    setup_duration = setup_times[("tl-0", "tl-1")].time
    
    # For stochastic setup times, you can see each update
    # The time is recalculated each time it's needed
    setup_times[("tl-0", "tl-1")].update()
    new_duration = setup_times[("tl-0", "tl-1")].time