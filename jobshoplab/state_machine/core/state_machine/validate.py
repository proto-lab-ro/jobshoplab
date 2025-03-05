from typing import Tuple

import jobshoplab.utils.state_machine_utils.core_utils as core_utils
from jobshoplab.state_machine.core.transitions import MachineTransition, TransportTransition
from jobshoplab.types import State
from jobshoplab.types.action_types import ComponentTransition
from jobshoplab.types.state_types import BufferState, MachineState, TransportState
from jobshoplab.utils import get_logger
from jobshoplab.utils.exceptions import NotImplementedError
from jobshoplab.utils.state_machine_utils import component_type_utils, job_type_utils


def is_machine_transition_valid(
    state: State, machine: MachineState, transition: ComponentTransition
) -> Tuple[bool, str]:
    """
    Check if a machine transition is valid.
    Args:
        state (State): The current state of the job shop.
        machine (MachineState): The state of the machine.
        transition (ComponentTransition): The transition to be checked.
    Returns:
        Tuple[bool, str]: A tuple containing a boolean indicating if the transition is valid
        and a string with an error message if the transition is invalid.
    """
    from_state = machine.state
    to_state = transition.new_state

    transition_allowed = MachineTransition().is_valid_transition(from_state, to_state)

    if not transition_allowed:
        return (
            False,
            f"Invalid transition from {from_state} to {to_state} for machine {machine}",
        )

    if core_utils.is_machine_transition_from_working_to_idle(machine, transition):
        return True, ""

    if transition.job_id is not None:
        job_from_state = job_type_utils.get_job_state_by_id(state.jobs, transition.job_id)
        no_processing_ops = core_utils.no_processing_operations(job_from_state)
        if not no_processing_ops:
            return False, "There are processing operations that prevent the transition."
        next_operation = job_type_utils.get_next_not_done_operation(job_from_state)
        if next_operation.machine_id != machine.id:
            return False, "Next operation is not on this machine."

    return True, ""


def is_transport_transition_valid(state, component, transition) -> Tuple[bool, str]:
    """
    Check if the transport state transition is valid.
    Args:
        state: The current state of the system.
        _component: The component whose state is being checked.
        transition: The component transition to be checked.
    Returns:
        Tuple[bool, str]: A tuple containing a boolean indicating if the new state is valid
        and a string with an error message if the new state is invalid.
    """
    from_state = component.state
    to_state = transition.new_state

    component_valid = TransportTransition().is_valid_transition(from_state, to_state)

    if component_valid:
        return component_valid, ""
    else:
        return (
            False,
            "Invalid state transition: component_valid={}".format(component_valid),
        )


def is_transition_valid(
    loglevel: int | str | str,
    state: State,
    transition: ComponentTransition,
) -> Tuple[bool, str]:
    """
    Check if a new state is valid for a given component transition.
    Args:
        loglevel (int | str | str): The log level for logging messages.
        state (State): The current state of the system.
        transition (ComponentTransition): The component transition to be checked.
    Returns:
        Tuple[bool, str]: A tuple containing a boolean indicating if the new state is valid
        and a string with an error message if the new state is invalid.
    Raises:
        NotImplementedError: If the component state is not recognized.
    """
    logger = get_logger("state_machine", loglevel)
    component = component_type_utils.get_comp_by_id(state, transition.component_id)
    match component:

        case MachineState():
            return is_machine_transition_valid(state, component, transition)

        case TransportState():
            return is_transport_transition_valid(state, component, transition)

        case BufferState():
            raise NotImplementedError()

        case _:
            raise NotImplementedError()
