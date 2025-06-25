Custom Instances
===============

JobShopLab provides flexible ways to define custom scheduling problem instances. This tutorial covers how to create and use your own problem specifications.

Instance Types
-------------

JobShopLab supports three ways to define problem instances:

1. **Spec Files**: Academic JSSP problem definitions found in literature
2. **DSL Files**: YAML files using the JobShopLab Domain Specific Language 
3. **DSL Strings**: Inline DSL definitions (useful in Jupyter notebooks)

.. mermaid::

   graph TD
       A[DSL file] -->|DslRepo| D[AbstractRepo]
       B[Spec file] -->|SpecRepo| D
       C[DSL String] -->|DslStrRepo| D
       D --> E[Compiler]
       E --> F[Env]

Using Academic Instances
----------------------

To use standard academic instances from literature:

.. code-block:: yaml

    # In your config.yaml
    compiler:
      repo: "SpecRepository"
      spec_repository:
        dir: "data/jssp_instances/ft06"  # Path to instance file

Or via dependency injection:

.. code-block:: python

    from jobshoplab.compiler.repos import SpecRepository
    from jobshoplab.compiler import Compiler
    
    repo = SpecRepository(dir=Path("data/jssp_instances/ft06"), loglevel="warning", config=config)
    compiler = Compiler(config=config, loglevel="warning", repo=repo)
    env = JobShopLabEnv(config=config, compiler=compiler)

Creating DSL Instances
--------------------

For real-world problems with more complex constraints, use DSL files:

Basic DSL Structure
^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

    title: InstanceConfig
    
    instance_config:
      description: "My custom instance"
      instance:
        description: "3x3 problem"
        specification: |
          (m0,t)|(m1,t)|(m2,t)
          j0|(0,3) (1,6) (2,4)
          j1|(1,8) (0,5) (2,3)
          j2|(2,5) (0,4) (1,7)
      
    init_state:
      # Optional initial state configuration

The DSL file must contain:
- An `instance_config` section defining the problem
- An optional `init_state` section for custom initialization

Loading DSL Files
^^^^^^^^^^^^^^^^

Configure the environment to use your DSL file:

.. code-block:: yaml

    # In your config.yaml
    compiler:
      repo: "DslRepository"
      dsl_repository:
        dir: "path/to/your/instance.yaml"

Or via dependency injection:

.. code-block:: python

    from jobshoplab.compiler.repos import DslRepository
    
    repo = DslRepository(dir=Path("path/to/your/instance.yaml"), loglevel="warning", config=config)
    compiler = Compiler(config=config, loglevel="warning", repo=repo)
    env = JobShopLabEnv(config=config, compiler=compiler)

Adding Transport Resources
------------------------

To model material handling:

.. code-block:: yaml

    instance_config:
      # Standard job and machine definitions
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
    
    # Optional
    init_state:
      t-0:
        location: m-0
      t-1:
        location: m-1

This defines:
- 2 AGVs for material transport  
- Travel times between all locations
- Initial positions of the transport units (using transport ID as key)

Adding Custom Buffers
--------------------

Define custom buffers with specific capacities and types:

.. code-block:: yaml

    instance_config:
      buffer:
        - name: "b-0"
          type: "fifo"
          capacity: 3
        - name: "b-1" 
          type: "fifo"
          capacity: 2

    init_state:
      b-0:
        store: [j-0, j-1]  # Jobs initially in buffer
      b-1:
        store: []          # Empty buffer
      j-0:
        location: b-0      # Job location
      j-1:
        location: b-0

Configuring Machine Buffers
---------------------------

Each machine has three buffers: prebuffer (input), buffer (internal), and postbuffer (output). You can customize the prebuffer and postbuffer settings:

**Global Configuration** (applies to all machines):

.. code-block:: yaml

    instance_config:
      machines:
        prebuffer:
          - capacity: 5
            type: "fifo"
        postbuffer:
          - capacity: 5
            type: "fifo"

**Machine-Specific Configuration** (overrides global settings):

.. code-block:: yaml

    instance_config:
      machines:
        - "m-0":
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

This configuration allows you to:

- Control buffer capacity for queueing behavior
- Set buffer types (FIFO, LIFO, flex_buffer, dummy) for different processing strategies
- Override global settings for specific machines that need special handling
- Model realistic shop floor constraints where different workstations have different buffer limitations

Advanced Initial State Configuration
----------------------------------

The ``init_state`` section supports detailed component initialization:

.. code-block:: yaml

    init_state:
      # Transport initialization (by transport ID)
      t-0:
        location: m-0
        buffer: [j-2]      # Job being transported
      t-1:
        location: m-1
        
      # Buffer initialization  
      b-0:
        store: [j-0, j-1]  # Jobs in buffer
        
      # Job initialization
      j-0:
        location: b-0      # Where job starts
      j-1:
        location: b-0
      j-2:
        location: t-0      # Job being transported

Using DSL Strings
----------------

For quick experiments, define instances inline:

.. code-block:: python

    dsl_str = """
    title: InstanceConfig
    
    instance_config:
      description: "Inline instance"
      instance:
        description: "2x2 problem"
        specification: |
          (m0,t)|(m1,t)
          j0|(0,3) (1,2)
          j1|(1,2) (0,4)
    """
    
    from jobshoplab.compiler.repos import DslStrRepository
    
    repo = DslStrRepository(dsl_str=dsl_str, loglevel="warning", config=config)
    compiler = Compiler(config=config, loglevel="warning", repo=repo)
    env = JobShopLabEnv(config=config, compiler=compiler)

Real-World Example: Scaliro Protolab
----------------------------------

The Scaliro protolab instance demonstrates a comprehensive real-world scheduling problem with multiple advanced features:

.. code-block:: yaml

    # Reference: data/config/scaliro_protolab_instance.yaml
    instance_config:
      description: "protolab config for scaliro"
      instance:
        description: "6x6"
        specification: |
          (m0,t)|(m1,t)|(m2,t)|(m3,t)|(m4,t)|(m5,t)
          j0|(2,1) (0,3) (1,6) (3,7) (5,3) (4,6)
          # ... additional jobs
          
      transport:
        type: "agv"
        amount: 6
        
      # Travel time matrix from real measurements
      logistics:
        specification: |
          m-0|m-1|m-2|m-3|m-4|m-5|b-0|b-1|b-2|b-3|b-4|b-5
          m-0|   0  21  16   9  37  41  12  18  22  15  28  31
          # ... complete matrix
          
      # Machine maintenance and AGV recharging
      outages:
        - component: "m"
          type: "maintenance"
          duration: 
            type: "poisson"
            base: 1
          frequency: 
            type: "uni"
            offset: 20
            base: 50
        - component: "t"
          type: "recharge"
          duration: 
            type: "gaussian"
            std: 1
            base: 5
          frequency: 
            type: "gaussian"
            std: 3
            base: 40
            
      # Custom buffer configuration
      buffer:
        - name: "b-0"
          type: "fifo"
          capacity: 1
        # ... additional buffers
        
      # Machine buffer configuration
      machines:
        prebuffer:
          - capacity: 5
            type: "fifo"
        postbuffer:
          - capacity: 5
            type: "fifo"
        
    init_state:
      # Jobs start in dedicated buffers
      b-0:
        store: [j-0]
      j-0:
        location: b-0
      # AGVs positioned at machines
      t-0:
        location: m-0
      # ... additional initialization

This example showcases:

- **Realistic travel times**: Based on actual measurements from Scaliro's webapp
- **Stochastic outages**: Machine maintenance with Poisson durations, AGV recharging with Gaussian distributions
- **Buffer management**: Dedicated input buffers for each job with FIFO behavior
- **Machine buffer configuration**: Standardized prebuffer and postbuffer settings across all machines
- **Complex initialization**: Jobs pre-positioned in buffers, AGVs at machine locations

Advanced Instance Features
------------------------

JobShopLab supports advanced features including:

- **Setup times**: Sequence-dependent changeover times
- **Stochastic processing**: Distribution-based processing durations 
- **Machine breakdowns**: Scheduled or random downtime events
- **Machine buffer configuration**: Customizable prebuffer and postbuffer settings
- **Alternative process plans**: Multiple operation sequences for jobs