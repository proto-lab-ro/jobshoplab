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
    
    init_state:
      transport:
        - location: "m-0"
        - location: "m-1"

This defines:
- 2 AGVs for material transport
- Travel times between all locations
- Initial positions of the transport units


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

Advanced Instance Features
------------------------

JobShopLab supports advanced features including:

- **Setup times**: Sequence-dependent changeover times
- **Stochastic processing**: Distribution-based processing durations 
- **Machine breakdowns**: Scheduled or random downtime events
- **Alternative process plans**: Multiple operation sequences for jobs