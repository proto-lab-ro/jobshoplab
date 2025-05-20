Stochastic Time Behavior
=======================

Real-world manufacturing systems rarely operate with deterministic timing. JobShopLab provides comprehensive support for modeling stochastic time behavior in various aspects of the scheduling environment.

Modeling Uncertainty
------------------

JobShopLab uses probability distributions to model time-related uncertainty in:

- Operation durations
- Setup times
- Transport times
- Outage frequencies and durations

This approach creates more realistic scheduling challenges that better reflect real-world conditions.

Available Distributions
---------------------

JobShopLab supports four main probability distributions:

1. **Gaussian (Normal) Distribution**
   
   Symmetric distribution around a mean value, defined by a base time and standard deviation.
   
   Useful for: Processing times with symmetrical variations.
   
   .. code-block:: yaml
   
       time_behavior:
         type: "gaussian"
         std: 2

2. **Poisson Distribution**
   
   Discrete distribution for counting events in fixed intervals.
   
   Useful for: Events that occur independently at a constant average rate.
   
   .. code-block:: yaml
   
       time_behavior:
         type: "poisson"

3. **Uniform Distribution**
   
   Distribution with equal probability between a low (base-offset) and high value (base+offset).
   
   Useful for: When any value within a range is equally likely.
   
   .. code-block:: yaml
   
       time_behavior:
         type: "uniform"
         offset: 2

4. **Gamma Distribution**
   
   Continuous distribution for positive values with a skewed shape.
   
   Useful for: Waiting times, service times with a minimum but potentially long tail.
   
   .. code-block:: yaml
   
       time_behavior:
         type: "gamma"
         scale: 2

.. note::
   The `base_time` parameter is the "main" time value for each distribution. It sets the *mode* for each distribution, which is the most likely value to be generated.
   For Gaussian, it is the mean; for Uniform, it is the lower bound; and for Poisson, it is the average rate of occurrence.

Configuring Stochastic Times
--------------------------

You can apply stochastic behavior to various components in JobShopLab. The base time is automatically taken from the time values in your specification matrix, and the stochastic distributions will apply variations to those base values.

Operation Durations
^^^^^^^^^^^^^^^^^^

To make processing times stochastic:

.. code-block:: yaml

    instance_config:
      instance:
        description: "3x3 problem"
        specification: |
          (m0,t)|(m1,t)|(m2,t)
          j0|(0,3) (1,2) (2,2)
          j1|(0,2) (2,1) (1,4)
          j2|(1,4) (2,3) (0,3)
        time_behavior:
          type: "gaussian"
          std: 0.2

This applies the Gaussian distribution to all operation times in the specification, with each operation's specified time used as the base (mean) value.

Transport Times
^^^^^^^^^^^^^^^^

For stochastic transport times between locations:

.. code-block:: yaml

    logistics:
      type: "agv"
      amount: 3
      specification: |
        m-0|m-1|m-2|in-buf|out-buf
        m-0|0 2 5 2 7
        m-1|2 0 8 3 6
        m-2|5 2 0 6 2
        in-buf|2 3 6 0 9
        out-buf|7 5 2 9 0
      time_behavior:
        type: "poisson"

The transport times in the matrix serve as base times for the Poisson distribution.

Setup Times
^^^^^^^^^^

For stochastic machine setup/changeover times:

.. code-block:: yaml

    setup_times:
      - machine: "m-1"
        specification: |
          tl-0|tl-1|tl-2
          tl-0|0 2 5
          tl-1|2 0 8
          tl-2|5 2 0
        time_behavior:
          type: "uniform"
          offset: 2

The setup times in the matrix serve as the lower bound (base_time) for the uniform distribution.

Outage Timing
^^^^^^^^^^^

Both outage durations and frequencies can be stochastic:

.. code-block:: yaml

    outages:
      - component: "m"
        type: "maintenance"
        duration:
          type: "gaussian"
          std: 1
          base: 5   # Explicitly setting base time for duration
        frequency: 
          type: "gamma"
          scale: 2
          base: 10  # Explicitly setting base time for frequency

For outages, you need to explicitly set the base time as there is no corresponding specification matrix.

Working with Stochastic Models in Python
--------------------------------------

Stochastic time models can be accessed and manipulated in Python:

.. code-block:: python

    # Access a stochastic setup time
    stochastic_time = env.instance.machines[1].setup_times[("tl-0", "tl-1")]
    
    # Check the current time value
    current_value = stochastic_time.time
    
    # Generate a new random value
    stochastic_time.update()
    new_value = stochastic_time.time
    
    # Check the distribution parameters
    if isinstance(stochastic_time, GaussianFunction):
        std = stochastic_time.std
        base_time = stochastic_time.base_time


.. hint::
   For a more interactive exploration of distributions, see the Jupyter notebook: `jupyter/stochastic_behavior.ipynb`

Example: Fully Stochastic Environment
-----------------------------------

Here's a complete example combining multiple stochastic elements:

.. code-block:: yaml

    instance_config:
      description: "Stochastic factory environment"
      instance:
        description: "3x3 problem"
        specification: |
          (m0,t)|(m1,t)|(m2,t)
          j0|(0,3) (1,2) (2,2)
          j1|(0,2) (2,1) (1,4)
          j2|(1,4) (2,3) (0,3)
        time_behavior:
          type: "gaussian"
          std: 0.1
        
        tool_usage:
          - job: "j0"
            operation_tools: ["tl-0", "tl-1", "tl-2"]
          - job: "j1"
            operation_tools: ["tl-0", "tl-1", "tl-2"]
          - job: "j2"
            operation_tools: ["tl-0", "tl-1", "tl-2"]
      
      setup_times:
        - machine: "m-1"
          specification: |
            tl-0|tl-1|tl-2
            tl-0|0 2 5
            tl-1|2 0 8
            tl-2|5 2 0
          time_behavior:
            type: "uniform"
            offset: 1
      
      logistics: 
        type: "agv"
        amount: 3
        specification: |
          m-0|m-1|m-2|in-buf|out-buf
          m-0|0 2 5 2 7
          m-1|2 0 8 3 6
          m-2|5 2 0 6 2
          in-buf|2 3 6 0 9
          out-buf|7 5 2 9 0
        time_behavior:
          type: "poisson"
      
      outages:
        - component: "m"
          type: "maintenance"
          duration:
            type: "gaussian"
            std: 1
            base: 5
          frequency: 
            type: "gamma"
            scale: 2
            base: 10