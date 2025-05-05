"""
Functional state machine implementation for JobShopLab.

This module contains the core state machine functionality for the JobShopLab simulation.
It handles state transitions, action processing, and determines possible transitions
for a given state.
"""

from dataclasses import replace
from typing import Callable, Iterator, Optional, Union

import jobshoplab.state_machine.core.state_machine.handler as handler
import jobshoplab.state_machine.core.state_machine.validate as validate
import jobshoplab.utils.state_machine_utils.core_utils as core_utils
from jobshoplab.state_machine import time_machines
from jobshoplab.types import (
    Config,
    InstanceConfig,
    JobState,
    OperationState,
    State,
    StateMachineResult,
    TransitionResult,
)
from jobshoplab.types.action_types import Action, ComponentTransition
from jobshoplab.types.state_types import (
    DeterministicTimeConfig,
    MachineState,
    MachineStateState,
    StochasticTimeConfig,
    TransportState,
)
from jobshoplab.utils import get_logger
from jobshoplab.utils.exceptions import (
    InvalidTimeBehaviorError,
    InvalidTransportConfig,
    InvalidValue,
    NotImplementedError,
)
from jobshoplab.utils.state_machine_utils import (
    buffer_type_utils,
    component_type_utils,
    job_type_utils,
    possible_transition_utils,
)


def is_done(state: StateMachineResult) -> bool:
    """
    Check if the state machine has completed all jobs.

    This function checks if all operations in all jobs have been completed.

    Args:
        state: The state machine result to check

    Returns:
        bool: True if all operations are done, False otherwise
    """
    return core_utils.is_done(state.state)


def apply_transition(
    loglevel: Union[int, str],
    state: State,
    instance: InstanceConfig,
    transition: ComponentTransition,
) -> State:
    """
    Apply a transition to the state machine.

    This function routes the transition to the appropriate handler based on the
    component type (machine or transport).

    Args:
        loglevel: The logging level to use
        state: The current state of the system
        instance: The instance configuration
        transition: The transition to apply

    Returns:
        State: The updated state after applying the transition

    Raises:
        InvalidValue: If the component ID does not exist
        NotImplementedError: If the component type is not supported
    """
    logger = get_logger("state_machine", loglevel)
    _component = component_type_utils.get_comp_by_id(state, transition.component_id)

    match _component:
        case MachineState():
            logger.debug(f"Applying machine transition: {transition} for {_component}")
            return handler.handle_machine_transition(state, instance, transition)
        case TransportState():
            logger.debug(f"Applying transport transition: {transition} for {_component}")
            return handler.handle_transport_transition(state, instance, transition)
        case _:
            # This should only happen if a new component type is added but not handled
            raise NotImplementedError()


def process_state_transitions(
    transitions: tuple[ComponentTransition, ...],
    state: State,
    instance: InstanceConfig,
    loglevel: Union[int, str],
    sort: Optional[
        Callable[[tuple[ComponentTransition, ...]], tuple[ComponentTransition, ...]]
    ] = None,
) -> TransitionResult:
    """
    Process a list of transitions for a given state.

    This function validates and applies each transition in sequence. If a sorting
    function is provided, the transitions will be sorted before processing.

    Args:
        transitions: The transitions to process
        state: The current state
        instance: The instance configuration
        loglevel: The log level
        sort: Optional function to sort transitions

    Returns:
        TransitionResult: The result of processing the transitions containing
            the updated state and any errors that occurred
    """
    errors: list[str] = []

    if not transitions:
        return TransitionResult(state=state, errors=errors)

    # Apply optional sorting function to determine transition order
    transitions = sort(transitions) if sort else transitions  # FELIX use dummy sort func

    for transition in transitions:
        valid, err = validate.is_transition_valid(loglevel, state, transition)
        if valid:
            state = apply_transition(loglevel, state, instance, transition)
        else:
            errors.append(f"Transition error: {err}")

    return TransitionResult(state=state, errors=errors)


def step(
    loglevel: Union[int, str],
    instance: InstanceConfig,
    config: Config,
    state: State,
    action: Action,
) -> StateMachineResult:
    """
    Execute a single step in the state machine.

    This function applies the transitions provided in the action, advances time, and
    creates and processes any timed transitions that should occur. It handles teleport
    transitions (zero travel time) and ensures that the state machine correctly processes
    all events in the proper sequence.

    Args:
        loglevel: The logging level to use
        instance: The instance configuration
        config: The global configuration
        state: The current state
        action: The action to apply, containing transitions and time machine

    Returns:
        StateMachineResult: The result of the step, including the updated state,
            intermediate sub-states, success status, and possible next transitions
    """
    logger = get_logger("state_machine", loglevel)
    _old_state = state
    _all_transitions = action.transitions
    sub_states = tuple()
    # HERE IT IS IMPORTANT TO SORT THE TRANSITIONS
    # FIRST APPLY THE TRANSPORT TRANSITIONS
    # THEN APPLY THE MACHINE TRANSITIONS
    # THIS ENABLES THAT A JOB CAN ARRIVE AT A MACHINE
    # AND THEN THE MACHINE CAN START WORKING ON IT IN THE SAME TIME STEP
    transition_result = process_state_transitions(
        action.transitions, state, instance, loglevel, core_utils.sorted_by_transport
    )
    sub_states += (transition_result.state,)
    if transition_result.errors:
        return StateMachineResult(
            state=_old_state,
            sub_states=sub_states,
            action=action,
            success=False,
            message=f"Transition errors: {transition_result.errors}",
            possible_transitions=(),  #! EVAL RETURN OLD VALUES
        )
    state = transition_result.state

    new_time = action.time_machine(
        loglevel=loglevel,
        current_time=state.time,
        instance_config=instance,
        job_states=state.jobs,
        machine_states=state.machines,
        transport_states=state.transports,
        buffer_states=state.buffers,
    )

    state = replace(state, time=new_time)

    timed_transitions = handler.create_timed_transitions(loglevel, state)
    _possible_transitions = get_possible_transitions(state, instance)
    teleport_transitions = _filter_teleport_transitions(_possible_transitions, instance, state)

    timed_transitions += tuple(teleport_transitions)

    while timed_transitions:
        _all_transitions += timed_transitions

        # HERE IT IS IMPORTANT THAT FIRST THE MACHINE TRANSITIONS ARE APPLIED
        # THEN THE TRANSPORT TRANSITIONS
        # SO THAT A MACHINE CAN FINISH WORKING ON A JOB
        # AND THEN THE JOB CAN BE TRANSPORTED IN THE SAME TIME STEP

        transition_result = process_state_transitions(timed_transitions, state, instance, loglevel)
        if transition_result.errors:
            return StateMachineResult(
                state=_old_state,
                sub_states=sub_states,
                action=action,
                success=False,
                message=f"Transition errors: {transition_result.errors}",
                possible_transitions=(),  #! EVAL RETURN OLD VALUES
            )
        state = transition_result.state

        new_time = time_machines.jump_to_event(
            loglevel=loglevel,
            current_time=state.time,
            instance_config=instance,
            job_states=state.jobs,
            machine_states=state.machines,
            transport_states=state.transports,
            buffer_states=state.buffers,
        )  # ! Hartcoded time machine
        state = replace(state, time=new_time)
        sub_states += (state,)
        timed_transitions = handler.create_timed_transitions(loglevel, state)

    if core_utils.is_done(state):
        logger.info("State machine is done")
        running_ops = core_utils.sorted_done_operations(state.jobs)
        if running_ops:
            finish_time = running_ops[-1].end_time
            state = replace(state, time=finish_time)
        return StateMachineResult(
            state=state,
            sub_states=sub_states[:-1],
            action=action,
            success=True,
            message="Done",
            possible_transitions=(),
        )

    logger.debug(f"_all_transitions: {_all_transitions}")
    possible_transitions = get_possible_transitions(state, instance)
    return StateMachineResult(
        state=state,
        sub_states=sub_states[:-1],
        action=action,
        success=True,
        message="Success",
        possible_transitions=possible_transitions,
    )


def get_possible_transitions(
    state: State, instance: InstanceConfig
) -> tuple[ComponentTransition, ...]:
    """
    Get all possible transitions for a given state.

    This function identifies jobs that can be processed and transports that can
    move jobs, then creates appropriate transitions for each.

    Args:
        state: The current state of the system
        instance: The instance configuration

    Returns:
        tuple[ComponentTransition, ...]: A tuple of all possible transitions
    """
    # Find jobs that can be processed
    possible_jobs = tuple(
        filter(
            lambda x: possible_transition_utils.is_action_possible(x, state, instance), state.jobs
        )
    )

    # Get possible transport transitions
    possible_transports = possible_transition_utils.get_possible_transport_transition(
        state, instance
    )

    # FELIX make dedicated func
    transitions = tuple()
    for job in possible_jobs:
        next_op = job_type_utils.get_next_idle_operation(job)
        transitions += (
            ComponentTransition(
                component_id=next_op.machine_id,
                new_state=MachineStateState.SETUP,
                job_id=job.id,
            ),
        )
    transitions += possible_transports

    return transitions  # ? NEED TO SORT


# This section needs refactoring in the future
##################################################################
def _get_travel_time_for_transport(
    instance: InstanceConfig, jobs: tuple[JobState, ...], job_id: str
) -> int:
    """
    Calculate the travel time for a transport operation.

    This function determines how long it will take to transport a job from its
    current location to the location of its next operation.

    Args:
        instance: The instance configuration
        jobs: The current job states
        job_id: The ID of the job to transport

    Returns:
        int: The travel time in time units

    Raises:
        InvalidValue: If the job ID is not found
        InvalidTransportConfig: If no travel time is defined for the route
        NotImplementedError: If the duration type is not supported
    """
    job_state: JobState = job_type_utils.get_job_state_by_id(jobs, job_id)
    next_op: OperationState = job_type_utils.get_next_idle_operation(job_state)

    # Get machine or buffer location
    all_buffer_configs = buffer_type_utils.get_all_buffer_configs(instance)
    buffer_config = buffer_type_utils.get_buffer_config_by_id(
        all_buffer_configs, job_state.location
    )

    # If the job is in a buffer that belongs to a machine, use the machine as the location
    if buffer_config.parent:
        current_location = buffer_config.parent
    else:
        current_location = job_state.location

    # Get the destination location from the next operation
    next_location = next_op.machine_id

    # If current and next locations are the same, no travel time needed
    if current_location == next_location:
        return 0

    # Get the travel time from the logistics configuration
    duration = instance.logistics.travel_times.get((current_location, next_location))

    # Handle different types of duration configurations
    match duration:
        case DeterministicTimeConfig():  # Simple deterministic time
            return duration.time
        case StochasticTimeConfig():  # For stochastic times, return the base time
            return duration.base_time
        case _:
            # This can happen if a new time configuration type is added but not handled
            raise NotImplementedError()


############################################################################################


def _filter_teleport_transitions(
    possible_transitions: tuple[ComponentTransition, ...],
    instance: InstanceConfig,
    state: State,
) -> Iterator[ComponentTransition]:
    """
    Filter transitions that can happen instantaneously (teleport).

    This function identifies transport transitions that have zero travel time,
    which allows them to be processed immediately (teleportation).

    Args:
        possible_transitions: The possible transitions
        instance: The instance configuration
        state: The current state

    Returns:
        Iterator[ComponentTransition]: Iterator of filtered teleport transitions
    """

    # Filter transitions to only include transport transitions with zero travel time
    # TODO: This filtering could be simplified in future refactoring
    possible_transitions = tuple(
        filter(
            lambda x: all(
                [
                    # Only consider transport components
                    x.component_id.startswith("t"),
                    # Only include transitions with zero travel time
                    _get_travel_time_for_transport(instance, state.jobs, x.job_id) == 0,
                ]
            ),
            possible_transitions,
        )
    )

    # Yield transitions one by one, removing conflicts after each yield
    while len(possible_transitions) > 0:
        # Take the first teleport transition
        next_transition = possible_transitions[0]
        yield next_transition

        # Remove any transitions that involve the same job or transport
        # This prevents multiple transports from handling the same job
        # and prevents the same transport from handling multiple jobs simultaneously
        possible_transitions = tuple(
            filter(
                lambda x: x.job_id != next_transition.job_id
                and x.component_id != next_transition.component_id,
                possible_transitions,
            )
        )
