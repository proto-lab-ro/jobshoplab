"""
Transition definitions for the JobShopLab state machine.

This module defines the valid state transitions for various components
(machines, transports, buffers) in the JobShopLab simulation. It implements
a state machine pattern where each component type has its own set of allowed
state transitions.
"""

from jobshoplab.types.state_types import TransportStateState
from jobshoplab.utils.exceptions import NotImplementedError


class StateEnum:
    """
    Enumeration of generalized component states for the state machine.

    These states represent the common high-level states that different
    components can be in, abstracting away component-specific state details.
    """

    IDLE = "Idle"  # Component is available and not performing any task
    RUNNING = "running"  # Component is actively working on a task
    OUTAGE = "outage"  # Component is unavailable (maintenance, breakdown, etc.)
    FULL = "full"  # Buffer is at capacity
    EMPTY = "empty"  # Buffer is empty
    SETUP = "setup"  # Machine is being prepared for a task


class Transition:
    """
    Base class for defining state transitions in the state machine.

    This class provides the core functionality for validating state transitions
    by mapping component-specific states to general state categories and checking
    if transitions between these categories are allowed.

    Attributes:
        states: List of valid states for the component type
        transitions: Dictionary mapping from states to allowed target states
    """

    def __init__(self, states, transitions):
        """
        Initialize a transition validator with states and valid transitions.

        Args:
            states: List of valid states for this component type
            transitions: Dictionary mapping from states to tuples of valid target states
        """
        self.states = states
        self.transitions = transitions

    def _match_state(self, state):
        """
        Map a component-specific state to a general state category.

        Args:
            state: Component state enum value to map

        Returns:
            StateEnum: The generalized state category

        Raises:
            NotImplementedError: If the state cannot be mapped to a known category
        """
        match state.value.lower():
            case "idle":
                return StateEnum.IDLE
            case "setup":
                return StateEnum.SETUP
            case "running" | "working" | "pickup" | "transit" | "waitingpickup":
                # Various "active" states are all mapped to RUNNING
                return StateEnum.RUNNING
            case "outage" | "maintenance":
                return StateEnum.OUTAGE
            case _:
                raise NotImplementedError()

    def is_valid_transition(self, current_state, new_state):
        """
        Check if a transition from current_state to new_state is valid.

        Rules:
        1. Self-transitions (to same state) are generally invalid
        2. Exception: WAITINGPICKUP can transition to itself (to extend waiting)
        3. The transition must be in the allowed transitions map

        Args:
            current_state: The current state of the component
            new_state: The proposed new state for the component

        Returns:
            bool: True if the transition is valid, False otherwise
        """
        # Prevent transitions to same state (except for WAITINGPICKUP)
        if current_state == new_state and current_state != TransportStateState.WAITINGPICKUP:
            return False

        # Map component-specific states to general categories
        _state = self._match_state(current_state)
        _new_state = self._match_state(new_state)

        # Check if transition is allowed
        return _new_state in self.transitions[_state]


class BufferTransition(Transition):
    """
    Defines valid state transitions for buffer components.

    Buffers can transition between IDLE, EMPTY, FULL, and OUTAGE states
    according to the defined transition rules.
    """

    def __init__(self):
        """
        Initialize the buffer transition validator with buffer-specific rules.
        """
        states = [StateEnum.IDLE, StateEnum.EMPTY, StateEnum.FULL, StateEnum.OUTAGE]
        transitions = {
            StateEnum.IDLE: (StateEnum.EMPTY, StateEnum.FULL, StateEnum.OUTAGE),
            StateEnum.EMPTY: (StateEnum.IDLE, StateEnum.FULL, StateEnum.OUTAGE),
            StateEnum.FULL: (StateEnum.IDLE, StateEnum.EMPTY, StateEnum.OUTAGE),
            StateEnum.OUTAGE: (StateEnum.IDLE, StateEnum.EMPTY, StateEnum.FULL),
        }
        super().__init__(states, transitions)


class MachineTransition(Transition):
    """
    Defines valid state transitions for machine components.

    Machines follow a specific cycle:
    1. IDLE → SETUP: Machine prepares for processing a job
    2. SETUP → RUNNING: Machine begins processing the job
    3. RUNNING → OUTAGE: Machine finishes processing or encounters a failure
    4. OUTAGE → IDLE: Machine becomes available again
    """

    def __init__(self):
        """
        Initialize the machine transition validator with machine-specific rules.
        """
        states = [StateEnum.IDLE, StateEnum.RUNNING, StateEnum.OUTAGE, StateEnum.SETUP]
        transitions = {
            StateEnum.IDLE: (StateEnum.SETUP,),  # Idle machines can only go to setup
            StateEnum.SETUP: (StateEnum.RUNNING,),  # Setup can only lead to running
            StateEnum.RUNNING: (
                # Machines in running state can go to outage or stay running
                StateEnum.OUTAGE,
                StateEnum.RUNNING,  # Self-transitions for running are allowed
            ),
            StateEnum.OUTAGE: (StateEnum.IDLE,),  # After outage, machines return to idle
        }
        super().__init__(states, transitions)


class TransportTransition(Transition):
    """
    Defines valid state transitions for transport components.

    Transport components (like AGVs) follow a specific cycle:
    1. IDLE → RUNNING: Transport starts moving to pick up or deliver a job
    2. RUNNING → OUTAGE: Transport completes its movement task
    3. OUTAGE → IDLE: Transport becomes available again

    Transports can also transition from RUNNING to RUNNING (as in TRANSIT to WAITINGPICKUP).
    """

    def __init__(self):
        """
        Initialize the transport transition validator with transport-specific rules.
        """
        states = [StateEnum.IDLE, StateEnum.RUNNING, StateEnum.OUTAGE]
        transitions = {
            StateEnum.IDLE: (StateEnum.RUNNING,),  # Idle transports can only start running
            StateEnum.RUNNING: (
                StateEnum.OUTAGE,  # Running can complete and go to outage
                StateEnum.RUNNING,  # Or transition between different running states
            ),
            StateEnum.OUTAGE: (StateEnum.IDLE,),  # After outage, transports return to idle
        }
        super().__init__(states, transitions)
