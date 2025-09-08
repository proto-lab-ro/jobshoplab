from dataclasses import replace
from typing import Generator

from jobshoplab.types import InstanceConfig
from jobshoplab.types.action_types import ComponentTransition
from jobshoplab.types.instance_config_types import TransportTypeConfig
from jobshoplab.types.state_types import (
    BufferState,
    JobState,
    MachineState,
    MachineStateState,
    OperationState,
    OperationStateState,
    State,
    TransportState,
    TransportStateState,
)
from jobshoplab.utils.exceptions import InvalidKey, InvalidType, InvalidValue
from jobshoplab.utils.state_machine_utils import (
    buffer_type_utils,
    job_type_utils,
    machine_type_utils,
)
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


def get_num_possible_events(state, instance, config) -> int:
    """
    Get the number of possible events

    Returns:
    The number of possible events
    """
    # Possible transports does not mean the AGV has a job to transport
    # possible_transports = tuple(get_possible_transports(state.transports, instance.transports))

    possible_transports_transitions = get_possible_transport_transition(
        state, instance, config.state_machine.allow_early_transport
    )  # ? INEFFICIENT

    # TODO: CHECK
    possible_jobs = tuple(filter(lambda x: is_action_possible(x, state, instance), state.jobs))
    return len(possible_transports_transitions) + len(possible_jobs)


def sort_by_id(
    components: tuple[JobState | TransportState, ...],
) -> tuple[JobState | TransportState, ...]:
    return tuple(sorted(components, key=lambda x: get_id_int(x.id)))


def is_transportable(job_state: JobState, state: State, instance: InstanceConfig) -> bool:
    """
    Determine if a job needs transportation in the job shop system.

    This function implements the core logic for deciding when jobs require transport:
    1. Jobs already at output buffers don't need transport (fully complete)
    2. Jobs with all operations done but not at output need transport to finish
    3. Jobs with remaining operations need transport if they're not at the correct machine
    4. Jobs already at their next operation's machine don't need transport

    Args:
        job_state (JobState): The job to evaluate for transport needs.
        state (State): Current system state containing all component states.
        instance (InstanceConfig): Configuration with buffer and machine definitions.

    Returns:
        bool: True if the job needs transport (either to next operation or output buffer),
            False if the job is already at the correct location or fully complete.

    Raises:
        InvalidValue: If job state is inconsistent (no operations but not at output).
    """
    # Case 1: Job is fully complete (operations done AND at output buffer)
    if job_type_utils.is_done(job_state, instance):
        # No more transport needed - job has reached its final destination
        return False

    # Case 2: All operations are done but job is not at output buffer
    if job_type_utils.all_operations_done(job_state):
        # Job needs transport to output buffer to complete the workflow
        return True

    # Case 3: Job has remaining operations - check if transport is needed
    next_op = job_type_utils.get_next_idle_operation(job_state)
    if next_op is None:
        # Inconsistent state: no idle operations but not all operations done
        raise InvalidValue(job_state, "job has no more operations. all operations are done.")

    # Case 4: Check if job is already at the machine for its next operation
    if is_job_at_machine(
        job_state, machine_type_utils.get_machine_state_by_id(state.machines, next_op.machine_id)
    ):
        # Job is already at correct machine - no transport needed
        return False

    # Default: Job needs transport to reach its next operation's machine
    return True


def is_early_transport(job_state: JobState, state: State, instance: InstanceConfig) -> bool:
    """
    Determine if a job is eligible for early transport in the job shop system.

    An early transport is triggered once the job (operation) has started its processing cycle on a machine.
    Some systems allow scheduling a transport "early" meaning the AGV is "called" early to avoid waiting times.
    This can lead to deadlock situations in AGV traffic management. Hence some systems disallow early transport.

    In this function we are checking if a job is early meaning not in the correct buffer location.

    Args:
        job_state (JobState): The job state to evaluate.
        state (State): The current state of the system.
        instance (InstanceConfig): The instance configuration.

    Returns:
        bool: True if the job is eligible for early transport, False otherwise.
    """
    ready_for_pickup = buffer_type_utils.is_job_ready_for_pickup_from_postbuffer(
        job_state=job_state, state=state, instance_config=instance
    )
    return not ready_for_pickup  # Job is not ready for pickup meaning its a early transport


def get_possible_transport_transition(
    state: State, instance, allow_early_transport: bool
) -> tuple[ComponentTransition, ...]:
    """
    Get all available transports and mach each transport with each possible job
    Jobs are possible when:
        - Job is in state working -> when finised it need to be transported to next op
        - Job is in state idle and next op is not the current location
        - Jobs that are not getting are already assigned to an agv
        - Jobs where all operations are done but not at the output buffer

    Returns:
    The tuple of possible ComponentTransitions
    """
    possible_transports = tuple(get_possible_transports(state.transports, instance.transports))

    # getting all jobs that need to be transported now or later
    jobs_to_transport = tuple()
    running_jobs = tuple(filter(lambda x: job_type_utils.is_job_running(x), state.jobs))
    running_jobs = tuple(
        filter(lambda x: job_type_utils.is_job_running(x), state.jobs)
    )  # job is running means a transport is needed in any scenario
    jobs_to_transport += running_jobs

    idle_jobs = filter(lambda x: not job_type_utils.is_job_running(x), state.jobs)
    jobs_to_transport += tuple(filter(lambda x: is_transportable(x, state, instance), idle_jobs))

    # Remove jobs that are already assigned to a transport
    jobs_already_assigned_to_transport = tuple(
        transport.transport_job for transport in state.transports if transport.transport_job
    )
    lonely_jobs_to_transport = tuple(
        filter(lambda x: x.id not in jobs_already_assigned_to_transport, jobs_to_transport)
    )
    if not allow_early_transport:
        lonely_jobs_to_transport = tuple(
            filter(lambda x: not is_early_transport(x, state, instance), lonely_jobs_to_transport)
        )

    # building permutations between transports and jobs
    # -> each transport can transport each job
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


def replace_buffer_state(state, buffer_state) -> State:
    return replace(
        state,
        buffers=tuple(
            buffer_state if buffer.id == buffer_state.id else buffer for buffer in state.buffers
        ),
    )


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
