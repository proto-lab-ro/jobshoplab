from dataclasses import replace
from typing import Generator

from jobshoplab.types import InstanceConfig
from jobshoplab.types.action_types import ComponentTransition
from jobshoplab.types.instance_config_types import TransportTypeConfig
from jobshoplab.types.state_types import (BufferState, JobState, MachineState,
                                          MachineStateState, OperationState,
                                          OperationStateState, State,
                                          TransportState, TransportStateState)
from jobshoplab.utils.exceptions import InvalidKey, InvalidType, InvalidValue
from jobshoplab.utils.state_machine_utils import (job_type_utils,
                                                  machine_type_utils)
from jobshoplab.utils.utils import get_id_int


def is_job_next_operation_free(job_state: JobState) -> bool:
    """
    Checks if a operation at a job is possible
    -> Job is not finished
    -> Job is not active
    """

    grouped_operations = job_type_utils.group_operations_by_state(job_state)

    # operation is active and not finished hence not possible
    if grouped_operations.get(OperationStateState.PROCESSING) is not None:
        return False

    # no open operations
    if len(grouped_operations.get(OperationStateState.IDLE, [])) == 0:
        return False

    else:
        return True


def is_job_at_machine(job_state: JobState, machine_state: MachineState) -> bool:
    """
    Check if a job is at a machine.

    Args:
        job_state (JobState): The job to check.
        machine (MachineState): The machine to check.

    Returns:
        bool: True if the job is at the machine, False otherwise.
    """
    # TODO: This legacy old code -> location should not be the machine id!
    at_machine_id = (
        job_state.location == job_type_utils.get_next_not_done_operation(job_state).machine_id
    )
    in_prebuffer = machine_state.prebuffer.id == job_state.location

    return at_machine_id or in_prebuffer


def is_action_possible(job_state: JobState, state: State, instance: InstanceConfig) -> bool:
    """
    Checks if a action at a job is possible
    -> Machine action
    -> Transport action

    Returns:
    True if the operation is possible, False otherwise
    """

    if not is_job_next_operation_free(job_state):
        return False

    # if job is not at the next operation location
    is_teleporter = instance.transports[0].type == TransportTypeConfig.TELEPORTER
    if not is_teleporter:
        next_operation = job_type_utils.get_next_not_done_operation(job_state)
        next_machine = machine_type_utils.get_machine_state_by_id(
            state.machines, next_operation.machine_id
        )

        # Only check location if we can not teleport
        if not is_job_at_machine(job_state, next_machine):
            return False

    # if we have teleporter we can always schedule the job
    # if any instance is of type teleporter we can schedule the job
    # -> TransportTypeConfig.TELEPORTER
    if instance.transports[0].type == TransportTypeConfig.TELEPORTER:
        return next_machine.state == MachineStateState.IDLE

    # This is not valid for teleporter
    # -> only if the machine is ready we can schedule the job,
    # otherwise we need to wait because we dont have a buffer
    elif job_state.location.startswith("m-"):  # at other machine and transport is ready means goo
        # is there a transport possible
        transporters = state.transports
        transporters = filter(
            lambda x: x.state == TransportStateState.IDLE,
            transporters,
        )
        return len(tuple(transporters)) > 0
    elif job_state.location.startswith("t-"):  # is already in transport
        return False
    elif job_state.location.startswith(
        "b-"
    ):  # at buffer first in queue means and transport is ready means gooo
        return next_machine.state == MachineStateState.IDLE
    # elif job_state.location == next_operation.machine_id:  # at machine and idl means gooo
    #     return next_machine.state == MachineStateState.IDLE
    raise InvalidKey(job_state.location)


def get_possible_transports(
    transport_states: tuple[TransportState, ...], transport_configs: tuple[TransportTypeConfig, ...]
) -> Generator[
    TransportState,
    None,
    None,
]:
    """
    Checks if the transport is possible

    Returns:
    True if the transport is possible, False otherwise
    """
    for c in transport_states:
        transport_config = next(filter(lambda x: x.id == c.id, transport_configs), None)
        if transport_config is None:
            raise InvalidKey(c.id)
        if c.state == TransportStateState.IDLE and transport_config.type == TransportTypeConfig.AGV:
            yield c


def get_num_possible_events(state, instance) -> int:
    """
    Get the number of possible events

    Returns:
    The number of possible events
    """
    # Possible transports does not mean the AGV has a job to transport
    # possible_transports = tuple(get_possible_transports(state.transports, instance.transports))

    possible_transports_transitions = get_possible_transport_transition(
        state, instance
    )  # ? INEFFICIENT

    # TODO: CHECK
    possible_jobs = tuple(filter(lambda x: is_action_possible(x, state, instance), state.jobs))
    return len(possible_transports_transitions) + len(possible_jobs)


def sort_by_id(
    components: tuple[JobState | TransportState, ...],
) -> tuple[JobState | TransportState, ...]:
    return tuple(sorted(components, key=lambda x: get_id_int(x.id)))


def get_possible_transport_transition(state: State, instance) -> tuple[ComponentTransition, ...]:
    """
    Get all available transports and mach each transport with each possible job
    Jobs are possible when:
        - Job is in state working -> when finised it need to be transported to next op
        - Job is in state idle and next op is not the current location
        - Jobs that are not getting are already assigned to an agv

    Returns:
    The tuple of possible ComponentTransitions
    """
    possible_transports = tuple(get_possible_transports(state.transports, instance.transports))

    jobs_already_assigned_to_transport = tuple(
        transport.transport_job for transport in state.transports if transport.transport_job
    )

    jobs_to_transport = tuple()

    running_jobs = tuple(filter(lambda x: job_type_utils.is_job_running(x), state.jobs))
    running_jobs = tuple(
        filter(
            lambda x: job_type_utils.is_job_running(x)
            and not job_type_utils.is_last_operation_running(x),
            state.jobs,
        )
    )
    jobs_to_transport += running_jobs

    idle_jobs = tuple(filter(lambda x: not job_type_utils.is_job_running(x), state.jobs))

    for job_state in idle_jobs:
        if job_type_utils.is_done(job_state):
            continue
        next_op = job_type_utils.get_next_idle_operation(job_state)

        if is_job_at_machine(
            job_state,
            machine_type_utils.get_machine_state_by_id(state.machines, next_op.machine_id),
        ):
            continue
        jobs_to_transport += (job_state,)

    # Remove jobs that are already assigned to a transport
    lonely_jobs_to_transport = tuple(
        filter(lambda x: x.id not in jobs_already_assigned_to_transport, jobs_to_transport)
    )

    transport_jobs = tuple()
    for transport in possible_transports:
        for job_state in lonely_jobs_to_transport:
            transport_jobs += (
                ComponentTransition(
                    component_id=transport.id,
                    new_state=TransportStateState.WORKING,
                    job_id=job_state.id,
                ),
            )
    return transport_jobs


def get_possible_transitions(state, instance) -> tuple[ComponentTransition, ...]:
    """
    Get all possible transitions for the state
    """
    # possible_transports = tuple(get_possible_transports(state.transports, instance.transports))
    possible_jobs = tuple(filter(lambda x: is_action_possible(x, state, instance), state.jobs))

    possible_transports = get_possible_transport_transition(state, instance)

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
    # return sort_by_id(possible_jobs) + sort_by_id(possible_transports)


def replace_machine_state(state, machine_state):
    state = replace(
        state,
        machines=tuple(
            machine_state if machine.id == machine_state.id else machine
            for machine in state.machines
        ),
    )

    return state


def replace_job_state(state, job_state) -> State:
    return replace(
        state, jobs=tuple(job_state if job.id == job_state.id else job for job in state.jobs)
    )


def replace_transport_state(state, transport_state) -> State:
    return replace(
        state,
        transports=tuple(
            transport_state if transport.id == transport_state.id else transport
            for transport in state.transports
        ),
    )


def replace_job_operation_state(job: JobState, operation: OperationState) -> JobState:
    return replace(
        job,
        operations=tuple(operation if op.id == operation.id else op for op in job.operations),
    )


def get_component_by_obj(state, obj):
    _id = obj.id
    _type = type(obj)
    return get_component_by_id_and_type(state, _id, _type)


def get_component_by_id(components, id):
    comp = next(filter(lambda x: x.id == id, components), None)
    if comp is None:
        raise InvalidValue("id", id, "id not found in components")
    return comp


def get_component_by_id_and_type(state, id, dtype):
    match dtype.__name__:
        case "MachineConfig" | "MachineState":
            return get_component_by_id(state.machines, id)
        case "BufferConfig" | "BufferState":
            return get_component_by_id(state.buffers, id)
        case "TransportConfig" | "TransportState":
            return get_component_by_id(state.transports, id)
        case _:
            raise InvalidType("dtype", dtype, "MachineConfig, BufferConfig, TransportConfig")


def replace_component_by_id_and_type(state, id, dtype, new_obj):
    match dtype.__name__:
        case "MachineConfig" | "MachineState":
            components = state.machines
        case "BufferConfig" | "BufferState":
            components = state.buffers
        case "TransportConfig" | "TransportState":
            components = state.transports
        case _:
            raise InvalidType("dtype", dtype, "MachineConfig, BufferConfig, TransportConfig")
    components = [new_obj if x.id == id else x for x in components]
    return components


def replace_component_by_obj(state, obj):
    _id = obj.id
    _type = type(obj)
    return replace_component_by_id_and_type(state, _id, _type, obj)


def replace_components(state, updated_components):
    if isinstance(updated_components, (tuple, list)) and all(
        isinstance(comp, MachineState) for comp in updated_components
    ):
        state = replace(state, machines=updated_components)
    elif isinstance(updated_components, (tuple, list)) and all(
        isinstance(comp, BufferState) for comp in updated_components
    ):
        state = replace(state, buffers=updated_components)
    elif isinstance(updated_components, (tuple, list)) and all(
        isinstance(comp, TransportState) for comp in updated_components
    ):
        state = replace(state, transports=updated_components)
    return state
