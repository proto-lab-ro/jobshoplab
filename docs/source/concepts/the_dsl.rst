The Domain Specific Language (DSL)
================================

JobShopLab uses a Domain Specific Language (DSL) to define job shop scheduling problems. The DSL is implemented as a YAML-based specification language that allows users to define complex production environments with various constraints.

Overview
--------

The DSL enables the definition of:

- Machines and their capabilities
- Jobs with their operations and processing requirements
- Transport resources (AGVs, conveyors, etc.)
- Buffer spaces and capacities
- Setup times and constraints
- Stochastic processing times

The DSL is processed by the compiler, which generates the internal problem representation used by the state machine.

.. raw:: html

   <div class="mermaid">
   graph TD
       DSL[DSL File] --> Compiler
       Compiler --> Repository
       Repository --> Validator[Validator]
       Compiler --> Manipulator[Manipulators]
       Validator --> Instance[Instance Config]
       Manipulator --> Instance
       Instance --> StateMachine[State Machine]
   </div>

Basic Structure
--------------

A DSL file consists of two main sections:

1. **instance_config**: Defines the problem instance (machines, jobs, etc.)
2. **init_state**: Defines the initial state of the environment

Here's a simplified example:

.. code-block:: yaml

    title: InstanceConfig
    
    instance_config:
      description: "Simple job shop problem"
      instance:
        description: "2x2 problem"
        specification: |
          (m0,t)|(m1,t)
          j0|(0,3) (1,2)
          j1|(1,2) (0,4)
      
    init_state:
      # Optional initial state configuration
      transport:
        - location: "m-0"

Job and Machine Specification
---------------------------

The core of the DSL is the specification matrix, which defines jobs, operations, and processing times:

.. code-block:: text

    (m0,t)|(m1,t)|(m2,t)
    j0|(0,3) (1,6) (2,4)
    j1|(1,8) (0,5) (2,3)

This example defines:
- 3 machines (m0, m1, m2)
- 2 jobs (j0, j1)
- Each job's operations in sequence with (machine_id, processing_time)

Transport Logistics
-----------------

For transport-aware scheduling, the DSL can define transport resources and travel times:

.. code-block:: yaml

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

This defines:
- 2 AGVs for transport
- A travel time matrix between locations

Advanced Features
---------------

The DSL supports several advanced features for realistic production modeling:
Refer to :doc:`../additional_resources/dsl_reference` for detailed syntax and examples.


