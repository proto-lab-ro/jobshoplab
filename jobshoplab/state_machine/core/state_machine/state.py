"""
functional state machine implementation for jobshoplab
"""

from dataclasses import replace
from typing import Callable, Iterator, Optional

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
    TransportState,
)
from jobshoplab.utils import get_logger
from jobshoplab.utils.exceptions import NotImplementedError
from jobshoplab.utils.state_machine_utils import (
    buffer_type_utils,
    component_type_utils,
    job_type_utils,
    possible_transition_utils,
)


def is_done(state: StateMachineResult) -> bool:
    return core_utils.is_done(state.state)


def apply_transition(
    loglevel: int | str | str,
    state: State,
    instance: InstanceConfig,
    transition: ComponentTransition,
) -> State:
    """
    Apply a transition to the state machine.

    Returns:
        State: The updated state after applying the transition.
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
            raise NotImplementedError()


def process_state_transitions(
    transitions: tuple[ComponentTransition, ...],
    state: State,
    instance: InstanceConfig,
    loglevel: int | str,
    sort: Optional[
        Callable[[tuple[ComponentTransition, ...]], tuple[ComponentTransition, ...]]
    ] = None,
) -> TransitionResult:
    """
    Process a list of transitions for a given state.

    Args:
        transitions: The transitions to process
        state: The current state
        instance: The instance configuration
        loglevel: The log level
        sort: Optional function to sort transitions

    Returns:
        TransitionResult: The result of processing the transitions
    """
    errors: list[str] = []

    if not transitions:
        return TransitionResult(state=state, errors=errors)

    transitions = sort(transitions) if sort else transitions
    for transition in transitions:
        valid, err = validate.is_transition_valid(loglevel, state, transition)
        if valid:
            state = apply_transition(loglevel, state, instance, transition)
        else:
            errors.append(f"Transition error: {err}")

    return TransitionResult(state=state, errors=errors)


def step(
    loglevel: int | str | str,
    instance: InstanceConfig,
    config: Config,
    state: State,
    action: Action,
) -> StateMachineResult:
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
    return StateMachineResult(
        state=state,
        sub_states=sub_states[:-1],
        action=action,
        success=True,
        message="Success",
        possible_transitions=get_possible_transitions(state, instance),
    )


def get_possible_transitions(
    state: State, instance: InstanceConfig
) -> tuple[ComponentTransition, ...]:
    """
    Get all possible transitions for a given state.
    """
    possible_jobs = tuple(
        filter(
            lambda x: possible_transition_utils.is_action_possible(x, state, instance), state.jobs
        )
    )

    possible_transports = possible_transition_utils.get_possible_transport_transition(
        state, instance
    )

    transitions = tuple()
    for job in possible_jobs:
        next_op = job_type_utils.get_next_idle_operation(job)
        transitions += (
            ComponentTransition(
                component_id=next_op.machine_id,
                new_state=MachineStateState.WORKING,
                job_id=job.id,
            ),
        )
    transitions += possible_transports

    return transitions  # ? NEED TO SORT


def _get_travel_time_for_transport(
    instance: InstanceConfig, jobs: tuple[JobState, ...], job_id: str
) -> int:
    """
    Calculate the travel time for a transport operation.

    Args:
        instance: The instance configuration
        jobs: The current job states
        job_id: The ID of the job to transport

    Returns:
        int: The travel time in time units

    Raises:
        NotImplementedError: If the duration type is not supported
    """
    job_state: JobState = job_type_utils.get_job_state_by_id(jobs, job_id)
    next_op: OperationState = job_type_utils.get_next_idle_operation(job_state)

    # Get machin to buffer
    all_buffer_configs = buffer_type_utils.get_all_buffer_configs(instance)
    buffer_config = buffer_type_utils.get_buffer_config_by_id(
        all_buffer_configs, job_state.location
    )

    if buffer_config.parent:
        current_location = buffer_config.parent
    else:
        current_location = job_state.location

    next_location = next_op.machine_id

    if current_location == next_location:
        return 0

    duration = instance.logistics.travel_times.get((current_location, next_location))
    match duration:
        case DeterministicTimeConfig():
            return duration.time
        case _:
            raise NotImplementedError()


def _filter_teleport_transitions(
    possible_transitions: tuple[ComponentTransition, ...],
    instance: InstanceConfig,
    state: State,
) -> Iterator[ComponentTransition]:
    """
    Filter transitions that can happen instantaneously (teleport).

    Args:
        possible_transitions: The possible transitions
        instance: The instance configuration
        state: The current state

    Returns:
        Iterator[ComponentTransition]: Iterator of filtered teleport transitions
    """

    ####### filter transport time
    possible_transitions = tuple(
        filter(
            lambda x: all(
                [
                    x.component_id.startswith("t"),
                    _get_travel_time_for_transport(instance, state.jobs, x.job_id) == 0,
                ]
            ),
            possible_transitions,
        )
    )
    while len(possible_transitions) > 0:
        next_transition = possible_transitions[0]
        yield next_transition
        possible_transitions = tuple(
            filter(
                lambda x: x.job_id != next_transition.job_id
                and x.component_id != next_transition.component_id,
                possible_transitions,
            )
        )
