from typing import Any

from jobshoplab.types.instance_config_types import InstanceConfig
from jobshoplab.types.state_types import (BufferState, FailTime, JobState,
                                          MachineState, NoTime,
                                          OperationStateState, State, Time,
                                          TransportState, TransportStateState)
from jobshoplab.utils.logger import get_logger
from jobshoplab.utils.state_machine_utils import job_type_utils
from jobshoplab.utils.state_machine_utils.possible_transition_utils import \
    get_num_possible_events


def jump_by_one(
    loglevel: int | str, current_time: Time | NoTime, *args: Any, **kwargs: Any
) -> Time:
    """
    Time machine that advances the time by one unit

    Args:
        loglevel: The log level for logging
        current_time: The current time
        *args: Additional arguments
        **kwargs: Additional keyword arguments

    Returns:
        Time: The new time after advancing by one unit
    """
    logger = get_logger("linear time_machine", loglevel)
    if isinstance(current_time, NoTime):
        logger.warning("No time found. Returning 0")
        return Time(time=0)
    logger.info("Jumping by one time unit")
    return Time(time=current_time.time + 1)


def jump_to_event(
    loglevel: int | str,
    instance_config: InstanceConfig,
    current_time: Time | NoTime,
    job_states: tuple[JobState, ...],
    machine_states: tuple[MachineState, ...],
    transport_states: tuple[TransportState, ...],
    buffer_states: tuple[BufferState, ...],
    *args: Any,
    **kwargs: Any,
) -> Time | FailTime:
    """
    Advance time to the next event if no operations are possible at current time.

    This time machine checks if any operations are possible in the current time step.
    If operations are possible, it doesn't advance time. If no operations are possible,
    it advances time to the next event (the next operation or transport end).

    Args:
        loglevel: The log level for logging
        instance_config: The instance configuration
        current_time: The current time
        job_states: The job states
        machine_states: The machine states
        transport_states: The transport states
        buffer_states: The buffer states
        *args: Additional arguments
        **kwargs: Additional keyword arguments

    Returns:
        Time | FailTime: The new time after evaluation, or unchanged if events exist
    """
    helper_state = State(
        jobs=job_states,
        machines=machine_states,
        transports=transport_states,
        buffers=buffer_states,
        time=current_time,
    )
    logger = get_logger("time_machine", loglevel)
    if isinstance(current_time, NoTime):
        logger.warning("No time found. Returning 0")
        current_time = Time(time=0)
    # get possible operations
    num_possible_events = get_num_possible_events(helper_state, instance_config)
    if num_possible_events > 0:
        logger.debug("Event exists in current time step no time jump")
        return current_time
    # get next event
    return force_jump_to_event(
        loglevel=loglevel,
        current_time=current_time,
        job_states=job_states,
        transport_states=transport_states,
    )


def force_jump_to_event(
    loglevel: int | str,
    current_time: Time | NoTime,
    job_states: tuple[JobState, ...],
    transport_states: tuple[TransportState, ...],
    *args: Any,
    **kwargs: Any,
) -> Time | FailTime:
    """
    Time machine that advances the time to the next event without checking for possible operations

    Args:
        loglevel: The log level for logging
        current_time: The current time
        job_states: The job states containing operation information
        transport_states: The transport states containing transport information
        *args: Additional arguments
        **kwargs: Additional keyword arguments

    Returns:
        Time | FailTime: The new time after jumping to the next event, or FailTime if no valid jump can be made
    """
    logger = get_logger("time_machine", loglevel)
    if isinstance(current_time, NoTime):
        logger.warning("No time found. Returning 0")
        current_time = Time(time=0)
    logger.debug("Force jumping to next event:")

    operations_by_state = job_type_utils.group_operations_by_state(job_states)
    # transport_states_by_state = transport_type_utils.group_transports_by_state(transport_states)

    processing_ops = operations_by_state.get(OperationStateState.PROCESSING, [])
    # check if processing_ops.end_time isinstance of Time

    # get processing operation with the smallest end time
    processing_ops = sorted(
        processing_ops,
        key=lambda x: x.end_time.time if x else None,
    )

    # get working transport with the smallest end time
    non_idle_transports = [
        transport for transport in transport_states if transport.state != TransportStateState.IDLE
    ]
    non_idle_transports = sorted(
        non_idle_transports,
        key=lambda x: x.occupied_till.time if x else None,
    )

    # Get the recource that is finishing first
    # Cases:
    # - no jobs and transports
    # - there are jobs and transports
    # - there are only jobs
    # - there are only transports

    if len(processing_ops) + len(non_idle_transports) == 0:
        return jump_by_one(loglevel, current_time)

    possible_smallest_end_time = []

    if len(processing_ops) > 0:
        if processing_ops[0].end_time:
            possible_smallest_end_time.append(processing_ops[0].end_time)

    if len(non_idle_transports) > 0:
        if non_idle_transports[0].occupied_till:
            possible_smallest_end_time.append(non_idle_transports[0].occupied_till)

    return min(possible_smallest_end_time, key=lambda x: x.time)
