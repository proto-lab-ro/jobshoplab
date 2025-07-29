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

Define custom buffers with specific types, capacities, and roles:

.. code-block:: yaml

    buffer:
      - name: "b-0"
        type: "fifo"        # Buffer type: fifo, lifo, flex_buffer
        capacity: 5         # Maximum capacity
        role: "input"       # Buffer role: input, output, component, compensation
        description: "Main input staging buffer"  # Optional description
      - name: "b-1"
        type: "lifo"
        capacity: 3
        role: "compensation"
        description: "Temporary overflow storage"

**Buffer Types:**
- ``fifo``: First-In-First-Out queue
- ``lifo``: Last-In-First-Out stack  
- ``flex_buffer``: Flexible buffer with no ordering constraints
- ``dummy``: Pass-through buffer with no storage

**Buffer Roles:**
- ``input``: Buffers where jobs enter the system from external sources
- ``output``: Buffers where completed jobs exit the system  
- ``component``: Buffers that are integral parts of machines or transport units (assigned automatically)
- ``compensation``: Buffers used for temporary storage, overflow handling, or workflow compensation

**Buffer Fields:**
- ``name``: Buffer identifier (must start with ``b-``, e.g., ``b-0``, ``b-input``)
- ``type``: Buffer scheduling discipline (required)
- ``capacity``: Maximum number of jobs the buffer can hold (required)
- ``role``: Functional classification of the buffer (required)
- ``description``: Human-readable description of the buffer's purpose (optional)

**Role Assignment Rules:**
- Custom buffers defined in the ``buffer`` section require explicit ``role`` specification
- Machine buffers (prebuffer, buffer, postbuffer) automatically receive ``component`` role
- AGV/transport buffers automatically receive ``component`` role  
- Default system buffers (when no custom buffers are defined) automatically get ``input`` and ``output`` roles

Machine Buffer Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Configure machine-specific prebuffer and postbuffer settings:

**Global Machine Buffer Configuration** (applies to all machines):

.. code-block:: yaml

    machines:
      prebuffer:
        - capacity: 5       # Buffer capacity
          type: "fifo"      # Buffer type: fifo, lifo, flex_buffer, dummy
      postbuffer:
        - capacity: 5       # Buffer capacity  
          type: "fifo"      # Buffer type

**Machine-Specific Buffer Configuration** (overrides global settings):

.. code-block:: yaml

    machines:
      - "m-0":              # Specific machine ID
          prebuffer:
            - capacity: 10
              type: "lifo"
          postbuffer:
            - capacity: 8
              type: "fifo"
      - "m-1":
          prebuffer:
            - capacity: 3
              type: "fifo"

**Buffer Types:**
- ``fifo``: First-In-First-Out queue
- ``lifo``: Last-In-First-Out stack  
- ``flex_buffer``: Flexible buffer with no ordering constraints
- ``dummy``: Pass-through buffer with no storage

**Notes:**
- Machine-specific configurations override global configurations
- Each machine has three buffers: prebuffer (input), buffer (internal), and postbuffer (output)
- Only prebuffer and postbuffer can be configured; the internal buffer is always capacity 1
- If not specified, machines use default buffer settings (unlimited capacity, flex_buffer type)

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
          role: "input"
          description: "Main input buffer"
        - name: "b-1"
          type: "flex_buffer"
          capacity: 5
          role: "output"
          description: "Finished goods buffer"
          
      machines:
        prebuffer:
          - capacity: 5
            type: "fifo"
        postbuffer:
          - capacity: 5
            type: "fifo"
          
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
        store: [j-0, j-1, j-2]  # Jobs start in input buffer
      b-1:
        store: []               # Output buffer starts empty
      j-0:
        location: b-0
      j-1:
        location: b-0
      j-2:
        location: b-0

This example defines a complete scheduling problem with transport, buffers, outages, and stochastic behavior.