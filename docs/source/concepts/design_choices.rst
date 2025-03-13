Design Choices
==============

JobShopLab is designed with a focus on flexibility, extensibility, and reusability. This document outlines the key design choices that shape the framework.

Core Architecture
----------------

At its core, JobShopLab implements a state machine in a functional programming style. This design offers several advantages:

- **Immutability**: The state machine operates on immutable data type objects, preventing unexpected side effects
- **Separation of concerns**: Clear boundaries between components make the system easier to extend and maintain
- **Testability**: Pure functions are easier to test in isolation
- **Reproducibility**: Deterministic behavior ensures consistent results for the same inputs

.. raw:: html

   <div class="mermaid">
   graph TD
       GymEnv[Gym Environment] <-->|Interface| Middleware
       Middleware <-->|Interface| StateMachine[State Machine]
       Middleware -->|Injects| Factories[Observation/Reward Factories]
       StateMachine -->|Updates| State[Immutable State]
       StateMachine -->|Uses| Instance[Problem Instance]
   </div>

Middleware Layer
---------------

The middleware layer bridges the gap between the OpenAI Gym interface and the state machine. It:

- Translates gym actions into state machine operations
- Converts state machine outputs into gym observations
- Manages time progression within simulations
- Handles reward calculation and termination conditions

This separation allows the core state machine to remain agnostic to RL specifics, while the middleware can be customized for different algorithms and use cases.

Factory Pattern Implementation
-----------------------------

JobShopLab extensively uses factory patterns to enable customization:

- **Observation factories**: Define what state information is available to the RL agent
- **Reward factories**: Calculate rewards based on different optimization objectives
- **Action interpreters**: Translate agent actions into concrete scheduling decisions

All factories can be replaced via dependency injection, allowing researchers to implement custom components without modifying the framework core.

.. raw:: html

   <div class="mermaid">
   graph LR
       Config[Configuration] --> DI[Dependency Injection]
       DI --> OF[Observation Factory]
       DI --> RF[Reward Factory]
       DI --> AI[Action Interpreter]
       OF --> Middleware
       RF --> Middleware
       AI --> Middleware
   </div>

Configuration Management
-----------------------

JobShopLab implements a comprehensive configuration system with two primary types:

1. **Framework configuration**: Controls framework behavior via YAML files
   - Observation space settings
   - Rendering modes
   - Truncation behavior
   - Logging levels

2. **Problem instance configuration**: Defines the scheduling problem via DSL (Domain Specific Language)
   - Machine definitions and constraints
   - Job specifications
   - Transport logistics
   - Buffer settings

Configuration is parsed into immutable dataclass objects providing:
   - Type validation
   - Dot notation access
   - IDE autocompletion support

.. raw:: html

   <div class="mermaid">
   graph TD
       YAML[YAML Config Files] --> Parser[Config Parser]
       DSL[DSL Instance Files] --> Compiler[Instance Compiler]
       Parser --> DataClass[Immutable DataClasses]
       Compiler --> Instance[Problem Instance]
       DataClass --> Framework[Framework Components]
       Instance --> StateMachine[State Machine]
   </div>

Rendering Infrastructure
-----------------------

The visualization system supports multiple modes:

- **Gantt Chart Dashboard**: Interactive Dash application showing schedule timelines
- **CLI Debug Utilities**: Rich text-based visualization for debugging
- **3D Simulation**: WebApp-based 3D rendering of the production environment

Each rendering backend can be selected at runtime or configured as the default mode.

.. raw:: html

   <div class="mermaid">
   graph LR
       Env[Environment] --> |history & instance| Render[env.render]
       Render -->|debug| Debug[CLI Debug Util]
       Render -->|dashboard| Gantt[Gantt Chart]
       Render -->|simulation| Simulation[3D Rendering]
   </div>

Extensible Type System
---------------------

The framework uses a well-defined type system based on dataclasses to represent:

- Machine states and configurations
- Job and operation specifications
- Transport resources and logistics
- Buffer capacities and constraints

This structured approach ensures type safety while allowing straightforward extension for new component types.