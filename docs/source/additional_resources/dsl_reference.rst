DSL Reference
=============

This document provides a complete reference for the JobShopLab Domain Specific Language (DSL) used to define scheduling problem instances.

File Structure
--------------

A DSL file has the following structure:

.. code-block:: yaml

    title: InstanceConfig
    
    instance_config:
      # Problem definition
      
    init_state:
      # Initial state configuration (optional)

Instance Configuration
---------------------

The ``instance_config`` section defines the core scheduling problem.

Basic Structure
^^^^^^^^^^^^^^^

.. code-block:: yaml

    instance_config:
      description: "Problem description"
      instance:
        description: "Instance description"
        specification: |
          # Job specification (see below)
          
      # Optional components
      transport: { }      # Transport configuration
      logistics: { }      # Travel time matrix
      outages: [ ]        # Machine/transport outages
      buffer: [ ]         # Custom buffer definitions
      time_behavior: { }  # Stochastic time behavior

Job Specification
^^^^^^^^^^^^^^^^

The job specification defines the jobs and their operations:

.. code-block:: yaml

    specification: |
      (m0,t)|(m1,t)|(m2,t)
      j0|(0,3) (1,6) (2,4)
      j1|(1,8) (0,5) (2,3)
      j2|(2,5) (0,4) (1,7)

Format:
- First line: Machine definitions ``(machine_id,type)``
- Following lines: Job operations ``job_id|(machine,duration) (machine,duration)...``

Transport Configuration
^^^^^^^^^^^^^^^^^^^^^^

Define transport resources (AGVs, conveyors, etc.):

.. code-block:: yaml

    transport:
      type: "agv"           # Transport type
      amount: 3             # Number of transport units

Logistics Matrix
^^^^^^^^^^^^^^^

Define travel times between locations:

.. code-block:: yaml

    logistics:
      specification: |
        m-0|m-1|m-2|in-buf|out-buf
        m-0|0 10 15 5 5
        m-1|10 0 12 8 8
        m-2|15 12 0 10 10
        in-buf|5 8 10 0 0
        out-buf|5 8 10 0 0

Format:
- First line: Location IDs
- Following lines: Travel time matrix (symmetric)
- Special locations: ``in-buf``, ``out-buf``

Buffer Configuration
^^^^^^^^^^^^^^^^^^^

Define custom buffers:

.. code-block:: yaml

    buffer:
      - name: "b-0"
        type: "fifo"        # Buffer type: fifo, lifo, flex_buffer
        capacity: 5         # Maximum capacity
      - name: "b-1"
        type: "lifo"
        capacity: 3

Outage Configuration
^^^^^^^^^^^^^^^^^^^

Define machine or transport outages:

.. code-block:: yaml

    outages:
      - component: "m"      # Component type: "m" (machine), "t" (transport)
        type: "maintenance" # Outage type: maintenance, recharge, breakdown
        duration:
          type: "poisson"   # Distribution type
          base: 10          # Base duration
        frequency:
          type: "uni"       # Uniform distribution
          offset: 20        # Minimum time between outages
          base: 50          # Range

Time Behavior
^^^^^^^^^^^^

Configure stochastic processing times for machines or transports:

.. code-block:: yaml

    time_behavior:
      type: "uni"           # Distribution type
      offset: 2             # Minimum additional time

Distribution types:
- ``uni``: Uniform distribution
- ``gaussian``: Normal distribution  
- ``poisson``: Poisson distribution

Initial State Configuration
--------------------------

The ``init_state`` section configures the initial system state.

Transport Initialization
^^^^^^^^^^^^^^^^^^^^^^^

Set initial transport positions and states:

.. code-block:: yaml

    init_state:
      t-0:                  # Transport ID
        location: m-0       # Initial location
        occupied_till: 0    # Occupied until time (optional)
        buffer: [j-2]       # Jobs being transported (optional)
        transport_job: null # Transport job (optional)
      t-1:
        location: m-1

Buffer Initialization
^^^^^^^^^^^^^^^^^^^^

Set initial buffer contents:

.. code-block:: yaml

    init_state:
      b-0:                  # Buffer ID
        store: [j-0, j-1]   # Jobs in buffer
      b-1:
        store: []           # Empty buffer

Job Initialization
^^^^^^^^^^^^^^^^^

Set initial job locations:

.. code-block:: yaml

    init_state:
      j-0:                  # Job ID
        location: b-0       # Initial location
      j-1:
        location: b-0
      j-2:
        location: t-0       # Job being transported

Component Naming Conventions
----------------------------

JobShopLab uses consistent naming conventions:

- **Machines**: ``m-0``, ``m-1``, ``m-2``, ...
- **Transport**: ``t-0``, ``t-1``, ``t-2``, ...
- **Buffers**: ``b-0``, ``b-1``, ``b-2``, ...
- **Jobs**: ``j-0``, ``j-1``, ``j-2``, ...
- **Outages**: ``out-0``, ``out-1``, ``out-2``, ...

Special Locations
^^^^^^^^^^^^^^^^
If no buffers are defined, the system uses special locations for input and output by default:

- ``in-buf``: Input buffer (jobs enter system)
- ``out-buf``: Output buffer (jobs exit system)
- ``input``, ``input-buffer``: Aliases for input buffer
- ``output``, ``output-buffer``: Aliases for output buffer

Complete Example
---------------

Here's a complete DSL file example:

.. code-block:: yaml

    title: InstanceConfig
    
    instance_config:
      description: "3x3 problem with AGVs and buffers"
      instance:
        description: "3 machines, 3 jobs, 2 AGVs"
        specification: |
          (m0,t)|(m1,t)|(m2,t)
          j0|(0,3) (1,6) (2,4)
          j1|(1,8) (0,5) (2,3)
          j2|(2,5) (0,4) (1,7)
          
      transport:
        type: "agv"
        amount: 2
        
      logistics:
        specification: |
          m-0|m-1|m-2|in-buf|out-buf
          m-0|0 10 15 5 5
          m-1|10 0 12 8 8
          m-2|15 12 0 10 10
          in-buf|5 8 10 0 0
          out-buf|5 8 10 0 0
          
      buffer:
        - name: "b-0"
          type: "fifo"
          capacity: 3
          
      outages:
        - component: "m"
          type: "maintenance"
          duration:
            type: "poisson"
            base: 5
          frequency:
            type: "uni"
            offset: 30
            base: 60
            
      time_behavior:
        type: "uni"
        offset: 2
        
    init_state:
      t-0:
        location: m-0
      t-1:
        location: m-1
      b-0:
        store: [j-0, j-1, j-2]
      j-0:
        location: b-0
      j-1:
        location: b-0
      j-2:
        location: b-0

This example defines a complete scheduling problem with transport, buffers, outages, and stochastic behavior.