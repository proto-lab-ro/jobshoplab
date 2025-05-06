Outages
=======

In real-world manufacturing environments, machines and transport units experience downtime due to failures, maintenance, or recharging. JobShopLab provides a flexible system to model different types of outages.

Outage Types
-----------

JobShopLab supports three primary outage types:

- **FAIL**: Unexpected breakdowns that require repair
- **MAINTENANCE**: Scheduled maintenance activities
- **RECHARGE**: common for transport units

.. hint::
   The system can be extended to include other outage types as needed. 
   The outage types DONOT have an effect on the behavior. They are only used for visualization and logging purposes.

Each outage type can be configured with:

- **Frequency**: How often the outage occurs
- **Duration**: How long the outage lasts

Both frequency and duration can be defined as fixed values or using stochastic models.

Configuration
------------

Outages are defined in the DSL using the ``outages`` section:

.. code-block:: yaml

    outages:
      # Machine outages (applies to all machines)
      - component: "m"
        type: "maintenance"
        duration: 5                # Fixed duration
        frequency: 20              # Fixed frequency
      
      # Specific machine outage
      - component: "m-0"
        type: "fail"
        duration:                  # Stochastic duration
          type: "gaussian"
          mean: 10
          std: 2
        frequency: 30
      
      # Transport unit outages
      - component: "t"
        type: "recharge"
        duration: 8
        frequency:                 # Stochastic frequency
          type: "gamma"
          shape: 2
          scale: 5
          base: 10

Component Specification
^^^^^^^^^^^^^^^^^^^^^^

- Use ``component: "m"`` to apply to all machines
- Use ``component: "m-0"`` to apply to a specific machine
- Use ``component: "t"`` to apply to all transport units 
- Use ``component: "t-0"`` to apply to a specific transport unit

.. note::
   When multiple outage definitions apply to the same component, they will all be active simultaneously.

Implementing Outages
-------------------

When an outage occurs:

1. The component transitions to a non-operational state
2. All operations on that component are paused and not released
3. After the outage duration elapses, the component returns to operational state



Stochastic Outages
^^^^^^^^^^^^^^^^^

Both the frequency and duration of outages can follow stochastic patterns:

.. code-block:: yaml

    outages:
      - component: "m"
        type: "maintenance"
        duration:
          type: "gaussian"  # Normal distribution
          mean: 5
          std: 1
        frequency: 
          type: "gamma"     # Gamma distribution
          shape: 2
          scale: 5
          base: 10

.. hint::
   read more about stochastic time behavior in the :doc:`stochastic_time_behavior` section.


Example: Full Implementation
---------------------------

Here's a complete example with multiple outage types:

.. code-block:: yaml

    instance_config:
      # Standard job and machine definitions...
      
      outages:
        # Regular maintenance for all machines
        - component: "m"
          type: "maintenance"
          duration: 5
          frequency: 100
          
        # Random failures for machine 0
        - component: "m-0"
          type: "fail"
          duration:
            type: "gaussian"
            mean: 8
            std: 2
          frequency:
            type: "gamma"
            shape: 3
            scale: 10
            
        # Recharging for AGVs
        - component: "t"
          type: "recharge"
          duration: 10
          frequency: 50
