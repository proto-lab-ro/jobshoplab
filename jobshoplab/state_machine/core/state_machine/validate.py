"""
Validation module for state machine transitions.

This module contains functions for validating transitions between different states
in the JobShopLab simulation. It ensures that transitions requested by components
(machines, transports, etc.) are valid according to the state machine rules.
"""

from typing import Tuple

import jobshoplab.utils.state_machine_utils.core_utils as core_utils
from jobshoplab.state_machine.core.transitions import MachineTransition, TransportTransition
from jobshoplab.types import State
from jobshoplab.types.action_types import ComponentTransition
from jobshoplab.types.state_types import (
    BufferState,
    MachineState,
    TransportState,
    TransportStateState,
)
from jobshoplab.utils import get_logger
from jobshoplab.utils.exceptions import NotImplementedError
from jobshoplab.utils.state_machine_utils import component_type_utils, job_type_utils
from jobshoplab.utils.state_machine_utils.buffer_type_utils import (
    get_job_position_in_buffer,
    is_correct_position_for_buffer_type,
)


def is_machine_transition_valid(
    state: State, machine: MachineState, transition: ComponentTransition
) -> Tuple[bool, str]:
    """
    Check if a machine transition is valid according to transition rules.

    This function validates machine state transitions by checking:
    1. If the transition is allowed according to the machine transition rules
    2. Special cases for transitions from outage to idle and working to outage
    3. Whether the job's next operation is assigned to this machine

    Args:
        state: The current state of the job shop system
        machine: The machine state to be transitioned
        transition: The requested transition to validate

    Returns:
        Tuple[bool, str]: A tuple containing:
            - Boolean indicating if the transition is valid
            - String with an error message if invalid, empty string if valid
    """
    # Get current and target states
    from_state = machine.state
    to_state = transition.new_state

    # Check if transition is allowed in the state machine definition
    transition_allowed = MachineTransition().is_valid_transition(from_state, to_state)

    if not transition_allowed:
        return (
            False,
            f"Invalid transition from {from_state} to {to_state} for machine {machine}",
        )

    # Special case: Outage to Idle transitions are always valid
    if core_utils.is_machine_transition_from_outage_to_idle(machine, transition):
        return True, ""

    # Special case: Working to Outage transitions are always valid
    if core_utils.is_machine_transition_from_working_to_outage(machine, transition):
        return True, ""

    # For transitions involving a job, validate that the job's next operation
    # is assigned to this machine
    if transition.job_id is not None:
        job_from_state = job_type_utils.get_job_state_by_id(state.jobs, transition.job_id)
        next_operation = job_type_utils.get_next_not_done_operation(job_from_state)

        # The job's next operation must be assigned to this machine
        if next_operation.machine_id != machine.id:
            return False, "Next operation is not on this machine."

    return True, ""


def is_transport_transition_valid(
    state: State, component: TransportState, transition: ComponentTransition
) -> Tuple[bool, str]:
    """
    Check if a transport transition is valid according to transition rules.

    This function validates transport state transitions using the TransportTransition
    rules defined in the transitions module. For WAITINGPICKUP -> PICKUP transitions,
    it also validates buffer position constraints.

    Args:
        state: The current state of the system
        component: The transport component whose state is being checked
        transition: The component transition to be validated

    Returns:
        Tuple[bool, str]: A tuple containing:
            - Boolean indicating if the transition is valid
            - String with an error message if invalid, empty string if valid
    """
    # Get current and target states
    from_state = component.state
    to_state = transition.new_state

    # Check if transition is allowed in the transport transition rules
    component_valid = TransportTransition().is_valid_transition(from_state, to_state)

    if not component_valid:
        return (
            False,
            f"Invalid state transition from {from_state} to {to_state}",
        )

    return True, ""


def is_transition_valid(
    loglevel: int | str,
    state: State,
    transition: ComponentTransition,
) -> Tuple[bool, str]:
    """
    Check if a transition is valid for a given component.

    This function dispatches the validation to the appropriate component-specific
    validation function based on the type of component being transitioned.

    Args:
        loglevel: The log level for logging messages
        state: The current state of the system
        transition: The component transition to be validated

    Returns:
        Tuple[bool, str]: A tuple containing:
            - Boolean indicating if the transition is valid
            - String with an error message if invalid, empty string if valid

    Raises:
        NotImplementedError: If the component type is not supported for validation
    """
    logger = get_logger("state_machine", loglevel)

    # Get the component being transitioned
    component = component_type_utils.get_comp_by_id(state, transition.component_id)

    # Dispatch to the appropriate validation function based on component type
    match component:
        case MachineState():
            return is_machine_transition_valid(state, component, transition)
        case TransportState():
            return is_transport_transition_valid(state, component, transition)
        case BufferState():
            # Buffer state transitions are not yet implemented
            raise NotImplementedError()
        case _:
            # Unknown component type
            raise NotImplementedError()
