"""
Time advancement mechanisms for the JobShopLab state machine.

This module contains "time machine" functions that control how time advances
in the discrete event simulation. These functions determine whether to advance
time and by how much, based on the current state of the system and the availability
of possible actions/events.
"""

from typing import Any, Sequence

from jobshoplab.types.instance_config_types import InstanceConfig
from jobshoplab.types.state_types import (
    BufferState,
    FailTime,
    TimeDependency,
    JobState,
    MachineState,
    NoTime,
    OperationStateState,
    State,
    Time,
    TransportState,
    TransportStateState,
)
from jobshoplab.utils.logger import get_logger
from jobshoplab.utils.state_machine_utils import job_type_utils
from jobshoplab.utils.state_machine_utils.possible_transition_utils import get_num_possible_events


def jump_by_one(
    loglevel: int | str, current_time: Time | NoTime, *args: Any, **kwargs: Any
) -> Time:
    """
    Advance simulation time by exactly one time unit.

    This simple time machine increases the current time by one unit,
    regardless of when the next event is scheduled. It provides a fixed
    time increment approach to simulation advancement.

    Args:
        loglevel: The log level for diagnostic messages
        current_time: The current simulation time
        *args: Additional arguments (not used)
        **kwargs: Additional keyword arguments (not used)

    Returns:
        Time: The new time after advancing by one unit
    """
    logger = get_logger("linear time_machine", loglevel)

    # Handle the case where no time is defined yet
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
    Advance time to the next event only if no operations are possible at current time.

    This time machine implements a "lazy" time advancement strategy. It first checks
    if any operations are possible at the current time step. If operations are possible,
    it doesn't advance time, allowing those operations to be processed. If no operations
    are possible, it advances time to the next scheduled event.

    This approach ensures the simulation doesn't skip over time points where actions
    could be taken, while efficiently jumping ahead when nothing can happen.

    Args:
        loglevel: The log level for diagnostic messages
        instance_config: The instance configuration containing problem setup
        current_time: The current simulation time
        job_states: Current states of all jobs in the system
        machine_states: Current states of all machines in the system
        transport_states: Current states of all transports in the system
        buffer_states: Current states of all buffers in the system
        *args: Additional arguments (not used)
        **kwargs: Additional keyword arguments (not used)

    Returns:
        Time | FailTime:
            - The unchanged current time if operations are possible now
            - The time of the next event if no operations are possible now
            - FailTime if no valid time advancement can be determined
    """
    # Create a temporary state object to evaluate possible events
    helper_state = State(
        jobs=job_states,
        machines=machine_states,
        transports=transport_states,
        buffers=buffer_states,
        time=current_time,
    )
    logger = get_logger("time_machine", loglevel)

    # Handle the case where no time is defined yet
    if isinstance(current_time, NoTime):
        logger.warning("No time found. Returning 0")
        current_time = Time(time=0)

    # Check if any operations/events are possible at the current time
    num_possible_events = get_num_possible_events(helper_state, instance_config)

    if num_possible_events > 0:
        # If events are possible now, don't advance time
        logger.debug("Event exists in current time step no time jump")
        return current_time

    # If no events are possible now, jump to the next scheduled event
    return force_jump_to_event(
        loglevel=loglevel,
        current_time=current_time,
        job_states=job_states,
        transport_states=transport_states,
    )


def force_jump_to_event(
    loglevel: int | str,
    current_time: Time | NoTime,
    job_states: Sequence[JobState],
    transport_states: Sequence[TransportState],
    *args: Any,
    **kwargs: Any,
) -> Time | FailTime:
    """
    Unconditionally advance time to the next scheduled event.

    This time machine identifies the next event that will occur in the simulation
    by examining all processing operations and active transports. It then advances
    time directly to the earliest scheduled event, skipping any "empty" time periods.

    The function handles four cases:
    1. No active jobs or transports: advance by one time unit
    2. Both active jobs and transports: jump to whichever finishes first
    3. Only active jobs: jump to the earliest job completion
    4. Only active transports: jump to the earliest transport completion

    Args:
        loglevel: The log level for diagnostic messages
        current_time: The current simulation time
        job_states: Current states of all jobs in the system
        transport_states: Current states of all transports in the system
        *args: Additional arguments (not used)
        **kwargs: Additional keyword arguments (not used)

    Returns:
        Time | FailTime:
            - The time of the next event
            - FailTime if no valid time advancement can be determined
    """
    logger = get_logger("time_machine", loglevel)

    # Handle the case where no time is defined yet
    if isinstance(current_time, NoTime):
        logger.warning("No time found. Returning 0")
        current_time = Time(time=0)

    logger.debug("Force jumping to next event:")

    # Group operations by their state
    operations_by_state = job_type_utils.group_operations_by_state(job_states)

    # Get operations that are currently processing
    processing_ops = operations_by_state.get(OperationStateState.PROCESSING, [])

    # Sort processing operations by their end time
    processing_ops = sorted(
        processing_ops,
        key=lambda x: x.end_time.time if x.end_time else float("inf"),
    )

    # Get transports that are currently active (not idle)
    non_idle_transports = [
        transport for transport in transport_states if transport.state != TransportStateState.IDLE
    ]
    non_idle_transports = list(
        filter(
            lambda x: not isinstance(x.occupied_till, TimeDependency),
            non_idle_transports,
        )
    )

    # Sort active transports by their occupied_till time
    non_idle_transports = sorted(
        non_idle_transports,
        key=lambda x: x.occupied_till.time if x.occupied_till else float("inf"),
    )

    # CASE 1: No active components - advance by one time unit
    if len(processing_ops) + len(non_idle_transports) == 0:
        return jump_by_one(loglevel, current_time)

    # Find the earliest end time among all active components
    possible_smallest_end_time = []

    # Add the earliest job completion time if there are processing operations
    if len(processing_ops) > 0 and processing_ops[0].end_time:
        possible_smallest_end_time.append(processing_ops[0].end_time)

    # Add the earliest transport completion time if there are active transports
    if len(non_idle_transports) > 0 and non_idle_transports[0].occupied_till:
        possible_smallest_end_time.append(non_idle_transports[0].occupied_till)

    # Return the minimum time from all possible end times
    return min(possible_smallest_end_time, key=lambda x: x.time)
