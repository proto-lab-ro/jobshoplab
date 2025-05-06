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
   
   Symmetric distribution around a mean value, defined by a mean and standard deviation.
   
   Useful for: Processing times with symmetrical variations.
   
   .. code-block:: yaml
   
       time_behavior:
         type: "gaussian"
         mean: 10
         std: 2
         base: 0

2. **Poisson Distribution**
   
   Discrete distribution for counting events in fixed intervals.
   
   Useful for: Events that occur independently at a constant average rate.
   
   .. code-block:: yaml
   
       time_behavior:
         type: "poisson"
         mean: 5
         base: 10

3. **Beta Distribution**
   
   Flexible distribution bounded between 0 and 1, scaled by the base time.
   
   Useful for: When variations have upper and lower bounds, or modeling proportions.
   
   .. code-block:: yaml
   
       time_behavior:
         type: "beta"
         alpha: 2
         beta: 5
         base: 20

4. **Gamma Distribution**
   
   Continuous distribution for positive values with a skewed shape.
   
   Useful for: Waiting times, service times with a minimum but potentially long tail.
   
   .. code-block:: yaml
   
       time_behavior:
         type: "gamma"
         shape: 2
         scale: 1
         base: 10



Configuring Stochastic Times
--------------------------

You can apply stochastic behavior to various components in JobShopLab:

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
          mean: 1.0
          std: 0.2

This applies the stochastic model to all operation times in the specification.

Transport Times
^^^^^^^^^^^^^

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
        mean: 1
        base: 0

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
          type: "beta"
          alpha: 2
          beta: 2

Outage Timing
^^^^^^^^^^^

Both outage durations and frequencies can be stochastic:

.. code-block:: yaml

    outages:
      - component: "m"
        type: "maintenance"
        duration:
          type: "gaussian"
          mean: 5
          std: 1
        frequency: 
          type: "gamma"
          shape: 2
          scale: 5
          base: 10

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
        mean = stochastic_time.mean
        std = stochastic_time.std


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
          mean: 1.0
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
            type: "beta"
            alpha: 2
            beta: 2
      
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
          mean: 1
      
      outages:
        - component: "m"
          type: "maintenance"
          duration:
            type: "gaussian"
            mean: 5
            std: 1
          frequency: 
            type: "gamma"
            shape: 2
            scale: 5
            base: 10

