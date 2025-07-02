from dataclasses import replace
from typing import Optional

from jobshoplab.types import InstanceConfig, State
from jobshoplab.types.instance_config_types import BufferConfig, BufferTypeConfig
from jobshoplab.types.state_types import BufferState, BufferStateState, JobState
from jobshoplab.utils.exceptions import BufferFullError, InvalidValue, JobNotInBufferError


def replace_buffer_state(state: State, buffer_state) -> State:
    return replace(
        state,
        buffers=tuple(buffer_state if buf.id == buffer_state.id else buf for buf in state.buffers),
    )


def get_buffer_state_by_id(buffers: tuple[BufferState, ...], buffer_id: str) -> BufferState:
    buffer = next(filter(lambda buffer: buffer.id == buffer_id, buffers), None)
    if buffer is None:
        raise InvalidValue(buffer_id, buffers, "desired buffer not found")
    return buffer


def get_buffer_config_by_id(buffers: tuple[BufferConfig, ...], buffer_id: str) -> BufferConfig:
    """
    Get a buffer config by its ID from a tuple of BufferConfig objects.

    Args:
        buffers (tuple[BufferConfig, ...]): A tuple of BufferConfig objects.
        buffer_id (str): The ID of the desired buffer.

    Returns:
        BufferConfig: The BufferConfig object with the specified ID.

    Raises:
        InvalidValue: If the desired buffer is not found in the given tuple of buffers.
    """
    buffer = next(filter(lambda buffer: buffer.id == buffer_id, buffers), None)
    if buffer is None:
        raise InvalidValue(buffer_id, buffers, "desired buffer not found")
    return buffer


def is_job_in_buffer(buffer_state: BufferState, job_id: str) -> bool:
    """
    Check if a job is in a buffer.

    Args:
        buffer_state (BufferState): The buffer to check.
        job_id (str): The ID of the job to check.

    Returns:
        bool: True if the job is in the buffer, False otherwise.
    """
    return job_id in buffer_state.store


def put_in_buffer(
    buffer_state: BufferState, buffer_config: BufferConfig, job_state: JobState
) -> tuple[BufferState, JobState]:
    """
    Put a job in a buffer.

    Args:
        buffer_state (BufferState): The buffer to put the job in.
        job_state (JobState): The job to put in the buffer.

    Returns:
        BufferState: The updated buffer state.
    """
    if len(buffer_state.store) >= buffer_config.capacity:
        raise BufferFullError(buffer_state.id)

    store = buffer_state.store + (job_state.id,)
    job_state = replace(job_state, location=buffer_state.id)

    if len(store) == buffer_config.capacity:
        buffer_state = replace(buffer_state, store=store, state=BufferStateState.FULL)
    else:
        buffer_state = replace(
            buffer_state,
            store=(buffer_state.store + (job_state.id,)),
            state=BufferStateState.NOT_EMPTY,
        )

    return buffer_state, job_state


def switch_buffer(
    instance: InstanceConfig,
    buffer_from_state: BufferState,
    buffer_to_state: BufferState,
    job_state: JobState,
) -> tuple[BufferState, BufferState, JobState]:
    """
    Switch a job from one buffer to another.

    Args:
        buffer_from_state (BufferState): The buffer to remove the job from.
        buffer_to_state (BufferState): The buffer to put the job in.
        job_state (JobState): The job to switch buffers.

    Returns:
        tuple[BufferState, BufferState, JobState]: The updated buffer states and job state.
    """
    if job_state.id not in buffer_from_state.store:
        raise JobNotInBufferError(job_state.id, buffer_from_state.id)

    buffer_from_state = remove_from_buffer(buffer_from_state, job_state.id)

    buffer_state_in_config = get_buffer_config_by_id(
        get_all_buffer_configs(instance), buffer_to_state.id
    )

    buffer_to_state, job_state = put_in_buffer(buffer_to_state, buffer_state_in_config, job_state)

    return buffer_from_state, buffer_to_state, job_state


def remove_from_buffer(buffer_state: BufferState, job_id: str) -> BufferState:
    """
    Remove a job from a buffer.

    Args:
        buffer_state (BufferState): The buffer to remove the job from.
        job_id (str): The id of the job to remove from the buffer.

    Returns:
        BufferState: The updated buffer state.
    """
    if job_id not in buffer_state.store:
        raise JobNotInBufferError(job_id, buffer_state.id)

    store = tuple(j for j in buffer_state.store if j != job_id)

    if len(store) == 0:
        buffer_state = replace(buffer_state, store=store, state=BufferStateState.EMPTY)
    else:
        buffer_state = replace(
            buffer_state,
            store=store,
            state=BufferStateState.NOT_EMPTY,
        )

    return buffer_state


def get_all_buffer_configs(instance: InstanceConfig) -> tuple[BufferConfig, ...]:
    """
    Get all buffer configurations from the instance configuration.

    Args:
        instance (InstanceConfig): The instance configuration.

    Returns:
        list[BufferConfig]: A list of all buffer configurations.
    """
    all_buffer_configs = []

    all_buffer_configs.extend(instance.buffers)

    for machine in instance.machines:
        all_buffer_configs.append(machine.prebuffer)
        all_buffer_configs.append(machine.buffer)
        all_buffer_configs.append(machine.postbuffer)

    for agv in instance.transports:
        all_buffer_configs.append(agv.buffer)

    return tuple(all_buffer_configs)


def get_all_buffer_states(state: State) -> tuple[BufferState, ...]:
    """
    Get all buffer states from the state.

    Args:
        state (State): The state.

    Returns:
        list[BufferState]: A list of all buffer states.
    """
    all_buffer_state = []
    all_buffer_state.extend(state.buffers)

    for machine in state.machines:
        all_buffer_state.append(machine.prebuffer)
        all_buffer_state.append(machine.buffer)
        all_buffer_state.append(machine.postbuffer)

    for agv in state.transports:
        all_buffer_state.append(agv.buffer)

    return tuple(all_buffer_state)


def get_buffer_state_by_id(buffers: tuple[BufferState, ...], buffer_id: str) -> BufferState:
    """
    Get a buffer state by its ID from a tuple of BufferState objects.

    Args:
        buffers (tuple[BufferState, ...]): A tuple of BufferState objects.
        buffer_id (str): The ID of the desired buffer.

    Returns:
        BufferState: The BufferState object with the specified ID.

    Raises:
        InvalidValue: If the desired buffer is not found in the given tuple of buffers.
    """
    buffer = next(filter(lambda buffer: buffer.id == buffer_id, buffers), None)
    if buffer is None:
        raise InvalidValue(buffer_id, buffers, "desired buffer not found")
    return buffer


def get_next_job_from_buffer(
    buffer_state: BufferState, buffer_config: BufferConfig
) -> Optional[str]:
    """
    Get the next job ID to process based on buffer type.

    Args:
        buffer_state: The current state of the buffer containing job IDs
        buffer_config: The buffer configuration specifying type (FIFO, LIFO, etc.)

    Returns:
        str  < /dev/null |  None: The job ID to process next, or None if no automatic ordering applies
    """
    if not buffer_state.store:
        return None

    match buffer_config.type:
        case BufferTypeConfig.FIFO:
            return buffer_state.store[0]  # First job in, first out
        case BufferTypeConfig.LIFO:
            return buffer_state.store[-1]  # Last job in, first out
        case BufferTypeConfig.FLEX_BUFFER:
            return None  # No automatic ordering - requires manual selection
        case BufferTypeConfig.DUMMY:
            return buffer_state.store[0] if buffer_state.store else None
        case _:
            return None


def get_job_position_in_buffer(job_id: str, postbuffer_state: BufferState) -> Optional[int]:
    """
    Get the position (index) of a job within a postbuffer.

    Args:
        job_id: The ID of the job to find
        postbuffer_state: The postbuffer state containing job IDs

    Returns:
        int | None: The index position of the job, or None if not found
    """
    try:
        return postbuffer_state.store.index(job_id)
    except ValueError:
        return None


def is_correct_position_for_buffer_type(
    job_position: int, buffer_length: int, buffer_type: BufferTypeConfig
) -> bool:
    """
    Check if a job position is valid for pickup based on buffer type.

    Args:
        job_position: The index position of the job in the buffer
        buffer_length: The total number of jobs in the buffer
        buffer_type: The type of buffer (FIFO, LIFO, FLEX, etc.)

    Returns:
        bool: True if the job can be picked up from this position, False otherwise
    """
    if buffer_length <= 0:
        return False

    match buffer_type:
        case BufferTypeConfig.FIFO | BufferTypeConfig.DUMMY:
            # FIFO: only first job (index 0) can be picked up
            return job_position == 0
        case BufferTypeConfig.LIFO:
            # LIFO: only last job (index buffer_length-1) can be picked up
            return job_position == buffer_length - 1
        case BufferTypeConfig.FLEX_BUFFER:
            # FLEX: any job can be picked up
            return 0 <= job_position < buffer_length
        case _:
            return False


def job_in_correct_buffer_for_pickup(instance: InstanceConfig, buffer: BufferState) -> bool:
    """

    Check if a job is in the correct buffer for pickup based on buffer type constraints.
    Args:
        instance: The instance configuration containing buffer configurations
        buffer: The buffer to check against
    """
    if buffer.id in [b.id for b in instance.buffers]:  # Standard buffers
        return True
    if buffer.id in [m.postbuffer.id for m in instance.machines]:  # Postbuffers of machines
        return True
    return False


def is_job_ready_for_pickup_from_postbuffer(
    job_state: JobState, state: State, instance_config: InstanceConfig
) -> bool:
    """
    Check if a job is ready for pickup from its postbuffer based on buffer type constraints.

    Args:
        job_state: The state of the job to check
        state: The current state of the system
        instance_config: The instance configuration containing buffer configurations

    Returns:
        bool: True if the job can be picked up, False otherwise
    """
    # Find which postbuffer contains the job
    all_buffer_configs = get_all_buffer_configs(instance_config)
    all_buffer_states = get_all_buffer_states(state)
    job_location = job_state.location
    buffer_state = get_buffer_state_by_id(all_buffer_states, job_location)
    buffer_config = get_buffer_config_by_id(all_buffer_configs, job_location)
    job_position = get_job_position_in_buffer(job_state.id, buffer_state)
    is_postbuffer_or_std_buffer = job_in_correct_buffer_for_pickup(instance_config, buffer_state)
    is_correct_pos = is_correct_position_for_buffer_type(
        job_position, len(buffer_state.store), buffer_config.type
    )
    return is_postbuffer_or_std_buffer and is_correct_pos
