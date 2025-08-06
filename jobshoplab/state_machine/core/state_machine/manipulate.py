"""
State manipulation functions for JobShopLab state machine.

This module contains functions that manipulate the state of machines,
jobs, and transport systems within the JobShopLab simulation. These functions
handle the core state transitions and ensure the correct movement of jobs
and updating of component states.
"""

from dataclasses import replace
from typing import Tuple, Sequence

from jobshoplab.types import InstanceConfig
from jobshoplab.types.instance_config_types import MachineConfig, OperationConfig
from jobshoplab.types.state_types import (
    BufferState,
    DeterministicTimeConfig,
    JobState,
    MachineState,
    MachineStateState,
    NoTime,
    OperationState,
    OperationStateState,
    StochasticTimeConfig,
    Time,
    TransportLocation,
    TransportState,
    TransportStateState,
)
from jobshoplab.utils.exceptions import (
    InvalidValue,
    NotImplementedError,
    InvalidTimeTypeError,
    InvalidSetupTimeTypeError,
)
from jobshoplab.utils.state_machine_utils import (
    buffer_type_utils,
    job_type_utils,
    machine_type_utils,
    outage_utils,
    possible_transition_utils,
)


def complete_transport_task(
    instance: InstanceConfig,
    job_state: JobState,
    transport: TransportState,
    target_component_state: MachineState | BufferState,
    time: Time | NoTime,
) -> Tuple[JobState, TransportState, MachineState | BufferState]:
    """
    Complete a transport task by delivering a job to its destination machine.

    This function handles the process of:
    1. Moving the job from the transport buffer to the machine prebuffer
    2. Setting the transport to OUTAGE state (representing drop-off time)
    3. Calculating and setting the time required for drop-off
    4. Clearing the transport's job assignment

    Args:
        instance: The instance configuration containing time information
        job_state: The state of the job being transported
        transport: The transport state carrying the job
        machine: The destination machine state
        time: The current simulation time

    Returns:
        Tuple containing updated job_state, transport, and machine states

    Raises:
        NotImplementedError: If time is not a Time instance
    """

    if isinstance(time, Time):
        buffer_to_fill = (
            target_component_state.prebuffer
            if isinstance(target_component_state, MachineState)
            else target_component_state
        )
        # Move job from transport buffer to machine prebuffer
        transport_buffer, filled_buffer, job_state = buffer_type_utils.switch_buffer(
            instance=instance,
            buffer_from_state=transport.buffer,
            buffer_to_state=buffer_to_fill,
            job_state=job_state,
        )

        # Calculate outage time for transport (drop-off time)
        outages = outage_utils.get_new_outage_states(transport, instance, time)
        occupied_for = outage_utils.get_occupied_time_from_outage_iterator(outages)

        # Update transport state: remove job, set to outage status, update location
        transport = replace(
            transport,
            buffer=transport_buffer,
            state=TransportStateState.OUTAGE,
            outages=outages,
            occupied_till=Time(time.time + occupied_for),
            location=TransportLocation(0, transport.location.location[2]),
            transport_job=None,
        )

        # Update machine's prebuffer
        if isinstance(target_component_state, MachineState):
            target_component_state = replace(target_component_state, prebuffer=filled_buffer)
        if isinstance(target_component_state, BufferState):
            target_component_state = filled_buffer

        return job_state, transport, target_component_state
    else:
        raise NotImplementedError()


def complete_active_operation_on_machine(
    instance: InstanceConfig,
    jobs: tuple[JobState, ...],
    machine_state: MachineState,
    time: Time | NoTime,
) -> Tuple[JobState, MachineState]:
    """
    Complete the active operation on a machine.

    This function handles the process of:
    1. Moving the job from the machine buffer to the postbuffer
    2. Setting the operation state to DONE
    3. Setting the machine state to IDLE
    4. Clearing machine outages

    Args:
        instance: The instance configuration
        jobs: Tuple of all job states in the system
        machine_state: The machine state to update
        time: The current simulation time

    Returns:
        Tuple containing updated job_state and machine_state

    Raises:
        NotImplementedError: If time is not a Time instance
        InvalidValue: If no job is found in the machine buffer or no active operation exists
    """
    # Only handle Time instances, not NoTime
    match time:
        case NoTime():
            raise NotImplementedError()

    # Get the job from the machine's buffer
    try:
        job_id = machine_state.buffer.store[0]
    except IndexError:
        raise InvalidValue("No job in buffer", machine_state.buffer)

    # Get the job state and its active operation
    job_state = job_type_utils.get_job_state_by_id(jobs, job_id)
    active_op = job_type_utils.get_processing_operation(job_state)

    if not active_op:
        raise InvalidValue("No active operation", active_op)

    # Mark the operation as complete
    active_op = replace(active_op, end_time=time, operation_state_state=OperationStateState.DONE)

    # Update job state with completed operation
    job_state = possible_transition_utils.replace_job_operation_state(job_state, active_op)

    # Remove job from machine buffer
    buffer = buffer_type_utils.remove_from_buffer(machine_state.buffer, job_state.id)

    # Get machine configuration
    machine_config = machine_type_utils.get_machine_config_by_id(
        instance.machines, machine_state.id
    )

    # Move job to machine's postbuffer
    postbuffer, job_state = buffer_type_utils.put_in_buffer(
        machine_state.postbuffer, machine_config.postbuffer, job_state
    )

    # Release machine outages
    outages = tuple(map(outage_utils.release_outage, machine_state.outages))

    # Update machine state to idle with empty buffer
    machine_state = replace(
        machine_state,
        buffer=buffer,
        postbuffer=postbuffer,
        state=MachineStateState.IDLE,
        outages=outages,
    )
    return job_state, machine_state


def _get_duration(time: DeterministicTimeConfig | StochasticTimeConfig) -> int:
    """
    Get the duration from a time configuration object.

    Extracts the time value from either a deterministic or stochastic time
    configuration. For stochastic times, this updates the random value before
    returning it.

    Args:
        time: The time configuration object (either deterministic or stochastic)

    Returns:
        int: The duration in time units

    Raises:
        InvalidTimeTypeError: If the time object is not of a supported type
    """
    match time:
        case DeterministicTimeConfig():
            return time.time
        case StochasticTimeConfig():
            time.update()  # Update the stochastic time with a new random value
            return time.time
        case _:
            raise InvalidTimeTypeError(
                type(time), "DeterministicTimeConfig or StochasticTimeConfig"
            )


def begin_next_job_on_machine(
    instance: InstanceConfig,
    job_state: JobState,
    machine_state: MachineState,
    time: Time | NoTime,
) -> Tuple[JobState, MachineState]:
    """
    Start processing a job on a machine after setup is complete.

    This function handles the transition from setup to working state by:
    1. Setting the operation state to PROCESSING
    2. Calculating operation duration based on the operation configuration
    3. Setting the machine state to WORKING
    4. Setting the machine's occupied_till time based on the operation duration

    Args:
        instance: The instance configuration containing operation durations
        job_state: The state of the job to process
        machine_state: The machine state to update
        time: The current simulation time

    Returns:
        Tuple containing updated job_state and machine_state
    """
    # Get the next operation configuration
    job_configs = instance.instance.specification
    op_state = job_type_utils.get_next_not_done_operation(job_state)
    op_config = job_type_utils.get_operation_config_by_id(job_configs, op_state.id)

    # Calculate when the operation will finish
    occupied_time = Time(time.time + _get_duration(op_config.duration))

    # Create the operation state (processing)
    op_state = OperationState(
        id=op_config.id,
        start_time=time,
        end_time=occupied_time,
        machine_id=machine_state.id,
        operation_state_state=OperationStateState.PROCESSING,
    )

    # Update the job with the new operation state
    job_state = possible_transition_utils.replace_job_operation_state(job_state, op_state)

    # Update the machine state to working with the calculated end time
    machine_state = replace(
        machine_state,
        state=MachineStateState.WORKING,
        occupied_till=occupied_time,
    )

    return job_state, machine_state


def _get_setup_duration(
    machine_state: MachineState, machine_config: MachineConfig, operation_config: OperationConfig
) -> int:
    """
    Calculate the setup time for a machine to change tools.

    This function determines the time required to change from the currently mounted tool
    to the tool required for the next operation. It handles both deterministic and
    stochastic setup times.

    Args:
        machine_state: The current machine state containing the currently mounted tool
        machine_config: The machine configuration containing setup time information
        operation_config: The operation configuration with the required tool

    Returns:
        int: The setup time duration in time units

    Raises:
        InvalidValue: If the setup time for the tool change is not defined
        InvalidSetupTimeTypeError: If the setup time is not of a supported type
    """
    # Get the tools involved in the setup
    new_tool = operation_config.tool
    old_tool = machine_state.mounted_tool

    # Get the setup time for changing from old_tool to new_tool
    s_time = machine_config.setup_times.get((old_tool, new_tool))

    # Handle different types of setup times
    match s_time:
        case DeterministicTimeConfig():
            return s_time.time
        case StochasticTimeConfig():
            setup_time = s_time.time
            s_time.update()
            return setup_time
        case _:
            if s_time is None:
                raise InvalidValue(
                    key=(old_tool, new_tool),
                    value=None,
                    message="setup time not found in mapping (check instance mapping)",
                )

            raise InvalidSetupTimeTypeError(
                type(s_time), "DeterministicTimeConfig or StochasticTimeConfig"
            )


def begin_machine_outage(
    instance: InstanceConfig,
    job_state: JobState,
    machine_state: MachineState,
    time: Time | NoTime,
    occupied_for: int,
    outages: Sequence,
) -> Tuple[JobState, MachineState]:
    """
    Start a machine outage (e.g., maintenance or breakdown).

    This function transitions a machine from WORKING to OUTAGE state:
    1. Sets the machine state to OUTAGE
    2. Updates the machine's outage records
    3. Sets the machine's occupied_till time based on the outage duration
    4. Updates the job's operation end time to match the outage end time

    Args:
        instance: The instance configuration
        job_state: The state of the job currently on the machine
        machine_state: The machine state to update
        time: The current simulation time
        occupied_for: The duration of the outage in time units
        outages: Sequence of outage states for the machine

    Returns:
        Tuple containing updated job_state and machine_state

    Raises:
        NotImplementedError: If time is not a Time instance
    """
    if time == NoTime():
        raise NotImplementedError()

    # Update machine state with outage information
    machine = replace(
        machine_state,
        state=MachineStateState.OUTAGE,
        outages=outages,
        occupied_till=Time(time.time + occupied_for),
    )

    # Update the job's current operation end time to match outage end time
    current_operation = job_type_utils.get_processing_operation(job_state)
    current_operation = replace(current_operation, end_time=Time(time.time + occupied_for))
    job_state = possible_transition_utils.replace_job_operation_state(job_state, current_operation)

    return job_state, machine


def begin_machine_setup(
    instance: InstanceConfig,
    job_state: JobState,
    machine_state: MachineState,
    time: Time | NoTime,
) -> Tuple[JobState, MachineState]:
    """
    Start setting up a machine for a new operation.

    This function handles the transition from IDLE to SETUP by:
    1. Moving the job from the machine's prebuffer to its buffer
    2. Setting the machine state to SETUP
    3. Calculating setup time based on tool change requirements
    4. Setting the machine's occupied_till time based on the setup duration
    5. Updating the machine's mounted tool
    6. Setting the operation state to PROCESSING (during setup)

    Args:
        instance: The instance configuration containing setup time information
        job_state: The state of the job to process
        machine_state: The machine state to update
        time: The current simulation time

    Returns:
        Tuple containing updated job_state and machine_state
    """
    # Get job and machine configurations
    job_configs = instance.instance.specification
    op_state = job_type_utils.get_next_not_done_operation(job_state)
    op_config = job_type_utils.get_operation_config_by_id(job_configs, op_state.id)
    machine_config = machine_type_utils.get_machine_config_by_id(
        instance.machines, machine_state.id
    )

    # Calculate setup duration based on tool change
    current_time = time.time
    setup_duration = _get_setup_duration(machine_state, machine_config, operation_config=op_config)

    # Create operation state for the setup phase
    op_state = OperationState(
        id=op_config.id,
        start_time=time,
        end_time=Time(current_time + setup_duration),
        machine_id=machine_state.id,
        operation_state_state=OperationStateState.PROCESSING,
    )

    # Update job with the new operation state
    job_state = possible_transition_utils.replace_job_operation_state(job_state, op_state)

    # Move job from prebuffer to machine buffer
    prebuffer = buffer_type_utils.remove_from_buffer(machine_state.prebuffer, job_state.id)
    buffer, job_state = buffer_type_utils.put_in_buffer(
        machine_state.buffer, machine_config.buffer, job_state
    )

    # Update machine state with setup information
    machine_state = replace(
        machine_state,
        prebuffer=prebuffer,
        buffer=buffer,
        state=MachineStateState.SETUP,
        occupied_till=Time(current_time + setup_duration),
        mounted_tool=op_config.tool,
    )

    return job_state, machine_state
