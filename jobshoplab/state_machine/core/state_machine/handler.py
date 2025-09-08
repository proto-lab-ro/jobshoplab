"""
Handler module for state machine transitions.

This module contains functions for handling transitions between different states
for machines and transports in the JobShopLab simulation. Each handler function is
responsible for updating the state of the system based on the specific transition
being processed.
"""

from dataclasses import replace
from typing import Any, Optional, Tuple, Union

import jobshoplab.state_machine.core.state_machine.manipulate as manipulate
import jobshoplab.utils.state_machine_utils.core_utils as core_utils
from jobshoplab.state_machine.time_machines import force_jump_to_event
from jobshoplab.types import InstanceConfig, State
from jobshoplab.types.action_types import ComponentTransition
from jobshoplab.types.instance_config_types import (
    BufferConfig,
    StochasticTimeConfig,
    TransportTypeConfig,
)
from jobshoplab.types.state_types import (
    BufferState,
    DeterministicTimeConfig,
    MachineState,
    MachineStateState,
    NoTime,
    Time,
    TimeDependency,
    TransportState,
    TransportStateState,
)
from jobshoplab.utils.exceptions import (
    InvalidValue,
    MissingJobIdError,
    MissingProcessingOperationError,
    NotImplementedError,
    TransportConfigError,
    TransportJobError,
    TravelTimeError,
)
from jobshoplab.utils.state_machine_utils import (
    buffer_type_utils,
    job_type_utils,
    machine_type_utils,
    outage_utils,
    possible_transition_utils,
    transport_type_utils,
)
from jobshoplab.utils.state_machine_utils.component_type_utils import get_comp_by_id
from jobshoplab.utils.state_machine_utils.time_utils import _get_travel_time_from_spec


def create_timed_machine_transitions(
    loglevel: Union[int, str], state: State, instance: InstanceConfig
) -> tuple[ComponentTransition, ...]:
    """
    Create timed machine transitions based on the given state.

    This function checks all machines in the system to determine if any have reached
    their occupied_till time and need to transition to their next state. It creates
    appropriate ComponentTransitions based on the current state of each machine.

    Args:
        loglevel: Log level for the function
        state: Current state of the system

    Returns:
        tuple[ComponentTransition, ...]: A tuple of ComponentTransition objects for machines
            that need to transition to their next state
    """
    transitions = []
    all_buffer_configs = buffer_type_utils.get_all_buffer_configs(instance)
    # Check each machine to see if it's time to change its state
    for machine in state.machines:

        # Check for timed transitions (when occupation time is over)
        transition = None
        if isinstance(machine.occupied_till, Time) and isinstance(state.time, Time):
            if machine.occupied_till.time <= state.time.time:
                # Create appropriate transition based on current machine state
                match machine.state:
                    case MachineStateState.SETUP:
                        # From SETUP -> WORKING when setup time is complete
                        transition = ComponentTransition(
                            component_id=machine.id,
                            new_state=MachineStateState.WORKING,
                            job_id=machine.buffer.store[0],
                        )
                    case MachineStateState.WORKING:
                        # From WORKING -> OUTAGE when processing is complete
                        transition = ComponentTransition(
                            component_id=machine.id,
                            new_state=MachineStateState.OUTAGE,
                            job_id=machine.buffer.store[0],
                        )
                    case MachineStateState.OUTAGE:
                        # From OUTAGE -> IDLE when outage is complete
                        transition = ComponentTransition(
                            component_id=machine.id,
                            new_state=MachineStateState.IDLE,
                            job_id=machine.buffer.store[0],
                        )
                    case _:
                        pass
        if transition is None and machine.state == MachineStateState.IDLE:
            transition = create_machine_setup_transition(
                all_buffer_configs, machine
            )  # Create setup transition if applicable
        if transition is not None:
            transitions.append(transition)

    return tuple(transitions)


def create_machine_setup_transition(
    all_buffer_configs: tuple[BufferConfig, ...], machine: MachineState
) -> Optional[ComponentTransition]:
    """
    Create a machine setup transition if a job is available in the prebuffer.

    This function determines whether a machine can transition from idle to setup
    state based on job availability in its prebuffer. The transition is only
    created for buffer types that support automatic scheduling (FIFO, LIFO, DUMMY)
    but not for flexible (FLEX) buffers that require manual job selection.

    Args:
        all_buffer_configs: Configuration information for all buffers in the system
        machine: The machine state to potentially create a setup transition for

    Returns:
        Optional[ComponentTransition]: A setup transition if conditions are met,
            None otherwise
    """
    transition = None
    if len(machine.prebuffer.store) > 0:
        prebuffer_config = buffer_type_utils.get_buffer_config_by_id(
            all_buffer_configs, machine.prebuffer.id
        )

        # Determine if automatic transition should be created based on buffer type
        next_job_id = buffer_type_utils.get_next_job_from_buffer(
            machine.prebuffer, prebuffer_config
        )
        if next_job_id is not None:  # FIFO/LIFO/DUMMY, not flex
            transition = ComponentTransition(
                component_id=machine.id,
                new_state=MachineStateState.SETUP,
                job_id=next_job_id,
            )

    return transition


def create_avg_pickup_to_drop_transition(
    state: State, transport: TransportState
) -> ComponentTransition:
    """
    Creates transition from PICKUP to move to drop location.

    This function creates a transition for an AGV (Automated Guided Vehicle) to
    move from the PICKUP state to the OUTAGE state, representing the completion
    of a pickup operation and the transition to dropping off the job.

    Args:
        state: Current state of the system
        transport: The transport state that is performing the transition

    Returns:
        ComponentTransition: A transition for the transport to move to OUTAGE state

    Raises:
        NotImplementedError: If the transport buffer contains more than one job
    """
    # Currently only supports one job per transport buffer
    if len(transport.buffer.store) == 1:
        _job = job_type_utils.get_job_state_by_id(jobs=state.jobs, job_id=transport.buffer.store[0])
    else:
        raise NotImplementedError()

    # Create the transition to OUTAGE state (representing drop-off process)
    transition = ComponentTransition(
        component_id=transport.id,
        new_state=TransportStateState.OUTAGE,
        job_id=_job.id,
    )
    return transition


def create_avg_idle_to_pick_transition(
    state: State, transport: TransportState, instance: InstanceConfig
) -> Optional[ComponentTransition]:
    """
    Creates transition from IDLE to PICKUP or WAITINGPICKUP.

    This function determines the appropriate next transition for an AGV based on
    the job's readiness state. It has three possible outcomes:
    1. If job has no processing operations pending: return TRANSIT transition
    2. If AGV is in PICKUP state and job is not ready: return WAITINGPICKUP transition
    3. If job has waiting time and operation time differ: return WAITINGPICKUP transition

    Args:
        state: Current state of the system
        transport: The transport state that is performing the transition

    Returns:
        Optional[ComponentTransition]: A transition for the transport's next state,
            or None if no appropriate transition is found

    Raises:
        TransportJobError: If the transport has no assigned job (transport_job is None)
    """
    # Check if transport has an assigned job
    if transport.transport_job is not None:
        job = job_type_utils.get_job_state_by_id(state.jobs, transport.transport_job)
    else:
        raise TransportJobError(transport.id)

    ready_for_pickup = buffer_type_utils.is_job_ready_for_pickup_from_postbuffer(
        job, state, instance
    )

    # CASE 1: Job is ready to be transported (is in correct postbuffer pos)
    if (transport.state == TransportStateState.WAITINGPICKUP) and ready_for_pickup:
        transit_transition = ComponentTransition(
            component_id=transport.id,
            new_state=TransportStateState.TRANSIT,
            job_id=job.id,
        )
        return transit_transition

    # CASE 2: AGV is at pickup location but job is not ready yet
    elif transport.state == TransportStateState.PICKUP:
        waiting_transition = ComponentTransition(
            component_id=transport.id,
            new_state=TransportStateState.WAITINGPICKUP,
            job_id=job.id,
        )
        return waiting_transition
    elif transport.state == TransportStateState.WAITINGPICKUP and not ready_for_pickup:
        # If the transport is already waiting for pickup and the job is not ready,
        # we return a waiting transition to keep it in WAITINGPICKUP state.
        waiting_transition = ComponentTransition(
            component_id=transport.id,
            new_state=TransportStateState.WAITINGPICKUP,
            job_id=job.id,
        )
        return waiting_transition
    # No appropriate transition found
    else:
        return None


def create_agv_drop_to_idle_transition(
    state: State, transport: TransportState
) -> ComponentTransition:
    """
    Creates a transition from drop-off completion to IDLE state.

    This function creates a transition for an AGV to return to the IDLE state
    after completing a job delivery, allowing it to be assigned to a new job.

    Args:
        state: Current state of the system
        transport: The transport state that is performing the transition

    Returns:
        ComponentTransition: A transition for the transport to return to IDLE state
    """
    return ComponentTransition(
        component_id=transport.id,
        new_state=TransportStateState.IDLE,
        job_id=None,  # No job is associated with an idle transport
    )


def _time_dependency_is_resolved(
    transport: TransportState, state: State, instance: InstanceConfig
) -> bool:
    """
    Checks if a transport's time dependency can be resolved for pickup.

    Time dependencies occur when a transport wants to pick up a job from a buffer,
    but the job is not yet at the correct position according to the buffer's type
    (FIFO, LIFO, etc.). This function determines if conditions have changed to
    allow the transport to proceed with pickup.

    Two conditions can resolve the dependency:
    1. The job is now at the correct position in the buffer (e.g., front of FIFO)
    2. Another transport is handling the blocking job, clearing the path

    Args:
        transport (TransportState): The transport waiting for dependency resolution.
        state (State): Current system state with all component states.
        instance (InstanceConfig): Configuration defining buffer types and behaviors.

    Returns:
        bool: True if the time dependency is resolved and transport can proceed,
            False if the transport must continue waiting. This prevents deadlocks
            while respecting buffer ordering constraints.
    """
    # Get the buffer where the job is located
    buffer_state = buffer_type_utils.get_buffer_state_by_id(
        tuple(m.postbuffer for m in state.machines), transport.occupied_till.buffer_id
    )
    buffer_instance = buffer_type_utils.get_buffer_config_by_id(
        tuple(m.postbuffer for m in instance.machines), buffer_state.id
    )

    job_id = transport.transport_job
    blocking_job = transport.occupied_till.job_id

    # Check if the job is now next in line according to buffer type (FIFO/LIFO rules)
    if job_id == buffer_type_utils.get_next_job_from_buffer(buffer_state, buffer_instance):
        # Transport's job has moved to correct position - can proceed with pickup
        return True

    # Check if another transport is handling the blocking job (clearing the dependency)
    for transport_state in state.transports:
        if transport_state.transport_job == blocking_job:
            # Blocking job is being handled by another transport - dependency resolved
            return True

    # Dependency not yet resolved - transport must continue waiting
    return False


def create_timed_transport_transitions(
    loglevel: Union[int, str], state: State, instance: InstanceConfig
) -> Tuple[ComponentTransition, ...]:
    """
    Creates timed transport transitions based on the given state.

    This function examines all transports to determine if any have reached their
    occupied_till time and need to transition to a new state. It creates appropriate
    transitions based on each transport's current state and context.

    Args:
        loglevel: The log level to use
        state: Current state of the system
        instance: The instance configuration

    Returns:
        Tuple[ComponentTransition, ...]: A tuple of transitions for transports that
            have reached their occupied_till time

    Raises:
        NotImplementedError: If a transport is in the WORKING state and needs a transition
            (this state is not yet implemented)
    """
    transitions = []

    # Check each transport to see if it's time to change its state
    for transport in state.transports:
        if isinstance(transport.occupied_till, TimeDependency) and _time_dependency_is_resolved(
            transport, state, instance
        ):
            transitions.append(transport.occupied_till.transition)
        if isinstance(transport.occupied_till, Time) and isinstance(state.time, Time):
            if transport.occupied_till.time <= state.time.time:
                # Create appropriate transition based on current transport state
                match transport.state:
                    case TransportStateState.PICKUP | TransportStateState.WAITINGPICKUP:
                        transition = create_avg_idle_to_pick_transition(state, transport, instance)
                    case TransportStateState.TRANSIT:
                        transition = create_avg_pickup_to_drop_transition(state, transport)
                    case TransportStateState.OUTAGE:
                        transition = create_agv_drop_to_idle_transition(state, transport)
                    case TransportStateState.WORKING:
                        # This state is not yet implemented
                        raise NotImplementedError()
                    case _:
                        transition = None

                if transition is not None:
                    transitions.extend([transition])

    return tuple(transitions)


def create_timed_transitions(
    loglevel: Union[int, str], state: State, instance: InstanceConfig
) -> Tuple[ComponentTransition, ...]:
    """
    Create timed transitions for the given state.

    This function combines machine and transport timed transitions into a single list.
    It checks if occupation time of components is over and creates transitions to
    advance them to their next state.

    The order of transitions is important to ensure proper sequencing of events:
    1. Machine transitions are processed first
    2. Transport transitions are processed second

    Args:
        loglevel: The log level to use
        state: Current state of the system

    Returns:
        Tuple[ComponentTransition, ...]: A tuple of all timed transitions for the current state
    """
    transitions = []

    # ORDER IS IMPORTANT
    # First handle machine transitions, then transport transitions
    # This ordering ensures machines complete their work before transports try to move jobs
    transitions.extend(create_timed_machine_transitions(loglevel, state, instance))
    transitions.extend(create_timed_transport_transitions(loglevel, state, instance))

    return tuple(transitions)


def handle_machine_idle_to_setup_transition(
    state: State, instance: InstanceConfig, transition: ComponentTransition, machine: MachineState
) -> State:
    """
    Handles the transition from machine IDLE to SETUP state.

    This function moves a job from the machine's prebuffer to its buffer
    and sets up the machine to start processing the job. It calculates setup times
    based on the tools needed for the operation.

    Args:
        state: Current state of the system
        instance: The instance configuration
        transition: The transition object containing component and job IDs
        machine: The machine state being transitioned

    Returns:
        State: Updated state after handling the transition

    Raises:
        InvalidValue: If transition has no job_id or job is not in prebuffer
    """
    if transition.job_id is None:
        raise InvalidValue("job_id", None, "No job_id in transition")

    # Get the job state
    job_state = job_type_utils.get_job_state_by_id(jobs=state.jobs, job_id=transition.job_id)

    # Check if job is in prebuffer
    if not buffer_type_utils.is_job_in_buffer(machine.prebuffer, job_state.id):
        raise InvalidValue("job_location", job_state.location, "Job is not in machine's prebuffer")

    # Move job from prebuffer to buffer and start setup for operation
    job_state, _machine = manipulate.begin_machine_setup(
        job_state=job_state,
        instance=instance,
        machine_state=machine,
        time=state.time,
    )

    # Update the state with new job and machine states
    state = possible_transition_utils.replace_job_state(state, job_state)
    state = possible_transition_utils.replace_machine_state(state, _machine)
    return state


def handle_machine_setup_to_working_transition(
    state: State, instance: InstanceConfig, transition: ComponentTransition, machine: MachineState
) -> State:
    """
    Handles the transition from machine SETUP to WORKING state.

    This function moves a job from setup phase to active processing.
    It updates both job and machine state to reflect the new processing status
    and calculates the operation duration.

    Args:
        state: Current state of the system
        instance: The instance configuration
        transition: The transition object containing component and job IDs
        machine: The machine state being transitioned

    Returns:
        State: Updated state after handling the transition

    Raises:
        InvalidValue: If transition has no job_id or job is not in machine's buffer
    """
    if transition.job_id is None:
        raise InvalidValue("job_id", None, "No job_id in transition")

    # Get the job state
    job_state = job_type_utils.get_job_state_by_id(jobs=state.jobs, job_id=transition.job_id)

    # Check if job is in machine's buffer
    if not buffer_type_utils.is_job_in_buffer(machine.buffer, job_state.id):
        raise InvalidValue("job_location", job_state.location, "Job is not in machine's buffer")

    # Begin processing the job on the machine
    job_state, _machine = manipulate.begin_next_job_on_machine(
        job_state=job_state,
        instance=instance,
        machine_state=machine,
        time=state.time,
    )

    # Update the state with new job and machine states
    state = possible_transition_utils.replace_job_state(state, job_state)
    state = possible_transition_utils.replace_machine_state(state, _machine)
    return state


def handle_machine_working_to_outage_transition(
    state: State, instance: InstanceConfig, transition: ComponentTransition, machine: MachineState
) -> State:
    """
    Handles the transition from machine WORKING to OUTAGE state.

    This function places the machine in an outage state, which may represent
    planned maintenance, a breakdown, or other non-operational period.
    It calculates the duration of the outage and updates both the machine
    and job states accordingly.

    Args:
        state: Current state of the system
        instance: The instance configuration
        transition: The transition object containing component and job IDs
        machine: The machine state being transitioned

    Returns:
        State: Updated state after handling the transition
    """
    # Get outage data and calculate duration
    outages = outage_utils.get_new_outage_states(machine, instance, state.time)
    occupied_for = outage_utils.get_occupied_time_from_outage_iterator(outages)

    # Update job and machine state for outage
    job_state, machine = manipulate.begin_machine_outage(
        instance=instance,
        job_state=job_type_utils.get_job_state_by_id(state.jobs, transition.job_id),
        machine_state=machine,
        time=state.time,
        occupied_for=occupied_for,
        outages=outages,
    )

    # Update the state with new machine and job states
    state = possible_transition_utils.replace_machine_state(state, machine)
    state = possible_transition_utils.replace_job_state(state, job_state=job_state)
    return state


def handle_machine_outage_to_idle_transition(
    state: State, instance: InstanceConfig, _transition: ComponentTransition, machine: MachineState
) -> State:
    """
    Handles the transition from machine OUTAGE to IDLE state.

    This function completes the current outage period and finishes the job operation.
    It moves the job to the machine's postbuffer, marks the operation as complete,
    and resets the machine to idle state.

    Args:
        state: Current state of the system
        instance: The instance configuration
        _transition: The transition object (not directly used in this function)
        machine: The machine state being transitioned

    Returns:
        State: Updated state after handling the transition
    """
    # Complete operation and move job to postbuffer
    job, machine = manipulate.complete_active_operation_on_machine(
        instance=instance, jobs=state.jobs, machine_state=machine, time=state.time
    )

    # Update the state with new job and machine states
    state = possible_transition_utils.replace_job_state(state, job)
    state = possible_transition_utils.replace_machine_state(state, machine)

    return state


def _get_waiting_time(
    state: State, transition: ComponentTransition, instance: InstanceConfig
) -> Union[Time, NoTime, TimeDependency]:
    job_state = job_type_utils.get_job_state_by_id(state.jobs, transition.job_id)
    job_location_id = job_state.location
    _all_buffer_configs = buffer_type_utils.get_all_buffer_configs(instance)
    buffer_config: BufferConfig = buffer_type_utils.get_buffer_config_by_id(
        _all_buffer_configs, job_location_id
    )
    if buffer_config.parent is None:  # standalone buffer
        return state.time  # setting time to now.. hence pick up gets performed in thise time step
    if buffer_config.parent.startswith("m"):  # machine buffer
        # Get the machine state and its buffer
        machine_state = machine_type_utils.get_machine_state_by_id(
            state.machines, buffer_config.parent
        )
        if job_state.id in machine_state.postbuffer.store:  # job is done and in postbuffer
            if buffer_type_utils.is_job_ready_for_pickup_from_postbuffer(
                job_state, state, instance
            ):

                return (
                    state.time
                )  # setting time to now.. hence pick up could be performed in this time step as job is ready to get transported
            else:
                # in case the job is not ready to get transported we have to wait until the prior jobs are transported.
                # considering the nature of the state machine and waiting to waiting transitions the simplest solution is to set the time to the time next jobs pickup estimate.
                # Hence if fifo and job in 5 were hitting waiting to waiting transitions for multiple times during different time steps.

                next_job_in_queue = buffer_type_utils.get_next_job_from_buffer(
                    machine_state.postbuffer, buffer_config
                )
                if next_job_in_queue is None:
                    raise InvalidValue(
                        key="next_job_in_queue",
                        value=next_job_in_queue,
                    )  # bug
                transport_state = transport_type_utils.get_transport_state_by_job_id(
                    state, next_job_in_queue
                )
                next_job_state_in_queue = job_type_utils.get_job_state_by_id(
                    state.jobs, next_job_in_queue
                )
                if job_type_utils.is_done(next_job_state_in_queue, instance):
                    # if the next job is done and the end pos is the machines buffer (wre cheating)
                    return (
                        state.time
                    )  # setting time to now.. hence pick up gets performed in this time step
                if transport_state is None:
                    # means no transport is assigned to this job. (Wre having a situation where the next job locks the queue)
                    # this could potentially happen.
                    # returning a time dependency to the next job in queue
                    return TimeDependency(
                        job_id=next_job_in_queue, buffer_id=job_location_id, transition=transition
                    )
                return transport_state.occupied_till
        # job is either being processed or waiting in the prebuffer
        processing_op = job_type_utils.get_processing_operation(job_state)
        if processing_op is None:
            raise MissingProcessingOperationError(transition.job_id)
        return processing_op.end_time
    else:
        raise NotImplementedError()  # very likely a bug


def handle_agv_transport_pickup_to_waitingpickup_transition(
    state: State,
    instance: InstanceConfig,
    transition: ComponentTransition,
    transport: TransportState,
) -> State:
    """
    Handles when an AGV is at the pickup location and waits for the job to be ready.

    This function updates the transport to wait at the pickup location until the job
    completes its current processing operation. It sets the transport's occupied_till
    time to match the job's operation end time.

    Args:
        state: Current state of the system
        instance: The instance configuration
        transition: The transition object containing component and job IDs
        transport: The transport state being transitioned

    Returns:
        State: Updated state after handling the transition

    Raises:
        MissingJobIdError: If transition has no job_id
        MissingProcessingOperationError: If the job has no processing operation
    """
    if transition.job_id is None:
        raise MissingJobIdError("pickup_to_waitingpickup")

    # Get job and its current processing operation
    # job_state = job_type_utils.get_job_state_by_id(state.jobs, transition.job_id)
    # processing_op = job_type_utils.get_processing_operation(job_state)

    # if processing_op is None:
    #     # check if the job has allready landed in the postbuffer thise can happen if the job finished in the same time step as the agv arives at the machine
    #     last_op = job_type_utils.get_prior_executed_operation(job_state)
    #     if last_op is None:  # no operation was executed before were hitting a bug
    #         raise MissingProcessingOperationError(transition.job_id)
    #     machine_state = machine_type_utils.get_machine_state_by_id(
    #         state.machines, last_op.machine_id
    #     )
    #     if not buffer_type_utils.is_job_in_buffer(
    #         machine_state.postbuffer, job_state.id
    #     ):  # if the job is not in the postbuffer we have a bug
    #         raise MissingProcessingOperationError(transition.job_id)
    #     else:  # the
    #         processing_op = last_op
    # else:
    #     occupied_till = processing_op.end_time
    occupied_till = _get_waiting_time(state, transition, instance)

    # Update transport to wait until job's operation is complete
    transport = replace(
        transport,
        state=TransportStateState.WAITINGPICKUP,
        occupied_till=occupied_till,
    )

    state = possible_transition_utils.replace_transport_state(state, transport)

    return state


def handle_agv_transport_pickup_to_transit_transition(
    state: State,
    instance: InstanceConfig,
    transition: ComponentTransition,
    transport: TransportState,
) -> State:
    """
    Handles picking up a job and moving it to the next operation location.

    This function picks up a job from its current location (either a standalone buffer
    or a machine's buffer), transfers it to the transport's buffer, and sets up the
    transport to move the job to its next destination.

    Args:
        state: Current state of the system
        instance: The instance configuration
        transition: The transition object containing component and job IDs
        transport: The transport state being transitioned

    Returns:
        State: Updated state after handling the transition

    Raises:
        MissingJobIdError: If transition has no job_id
    """
    if transition.job_id is None:
        raise MissingJobIdError("pickup_to_transit")

    # Get job and determine source and destination locations
    job_state = job_type_utils.get_job_state_by_id(state.jobs, transition.job_id)
    transport_source = job_state.location

    # Get the actual machine ID from the buffer if applicable
    transport_source = machine_type_utils.get_machine_id_from_buffer(
        instance.machines, job_state.location
    )
    if not transport_source:
        transport_source = job_state.location

    # Determine transport destination based on job's operation state
    match job_type_utils.no_operation_idle(job_state):
        case True:  # All operations complete - transport to output buffer for final delivery
            transport_destination = next(iter(buffer_type_utils.get_output_buffers(instance))).id
        case False:  # Operations remain - transport to next operation's machine
            transport_destination = job_type_utils.get_next_not_done_operation(job_state).machine_id
    travel_time = _get_travel_time_from_spec(instance, transport_source, transport_destination)

    # Handle job transfer from different source types
    if transport_source.startswith("b"):
        # Job is in a standalone buffer (not part of a machine)
        from_buffer_state: BufferState = buffer_type_utils.get_buffer_state_by_id(
            state.buffers, transport_source
        )

        # Move job from buffer to transport
        from_buffer_state, transport_buffer, job_state = buffer_type_utils.switch_buffer(
            instance=instance,
            buffer_to_state=transport.buffer,
            buffer_from_state=from_buffer_state,
            job_state=job_state,
        )

        state = buffer_type_utils.replace_buffer_state(state, from_buffer_state)
    else:
        # Job is in a machine's buffer
        machine_state = machine_type_utils.get_machine_state_by_id(state.machines, transport_source)
        buffer_id = job_state.location
        buffer_state = machine_type_utils.get_buffer_state_from_machine(machine_state, buffer_id)

        # Move job from machine buffer to transport
        buffer_from_state, transport_buffer, job_state = buffer_type_utils.switch_buffer(
            instance=instance,
            buffer_to_state=transport.buffer,
            buffer_from_state=buffer_state,
            job_state=job_state,
        )

        # Update machine buffer and state
        machine_state = machine_type_utils.replace_buffer_state_in_machine(
            machine_state, buffer_from_state
        )
        state = possible_transition_utils.replace_machine_state(state, machine_state)

    # Update transport for transit
    current_time = extract_time(state.time)
    occupied_till = Time(current_time + travel_time)
    transport_location = replace(transport.location, progress=0.5)  # TODO: hardcoded progress...

    transport = replace(
        transport,
        state=TransportStateState.TRANSIT,
        occupied_till=occupied_till,
        location=transport_location,
        buffer=transport_buffer,
    )

    # Update state with new job and transport states
    state = possible_transition_utils.replace_job_state(state, job_state)
    state = possible_transition_utils.replace_transport_state(state, transport)

    return state


def handle_agv_transport_idle_to_working_transition(
    state: State,
    instance: InstanceConfig,
    transition: ComponentTransition,
    transport_state: TransportState,
) -> State:
    """
    Moves the transport to the pickup location of the next operation.

    This function calculates the time required to reach the pickup location based on
    the transport's current position and the job's location. It updates the transport's
    state and sets its occupied_till time accordingly.

    Args:
        state: Current state of the system
        instance: The instance configuration
        transition: The transition object containing component and job IDs
        transport_state: The transport state being transitioned

    Returns:
        State: Updated state after handling the transition

    Raises:
        InvalidValue: If transition has no job_id or transport location is invalid
        TransportConfigError: If source buffer configuration is invalid or travel time is not found
    """
    if transition.job_id is None:
        raise InvalidValue("job_id", None, "No job_id in transition")

    # Validate transport location format
    if not isinstance(transport_state.location.location, str):
        raise InvalidValue(
            "transport.location.location",
            transport_state.location.location,
            "transport location is not a string. Tuple could be an progress object -> tuple[str, str, str]",
        )

    # Get job and destination information
    job_state = job_type_utils.get_job_state_by_id(jobs=state.jobs, job_id=transition.job_id)
    # Determine target location based on job's operation completion status
    match job_type_utils.no_operation_idle(job_state):
        case True:  # All operations complete - transport to output buffer for workflow completion
            target_location = next(iter(buffer_type_utils.get_output_buffers(instance))).id
        case False:  # Operations remain - transport to next idle operation's machine
            next_op_state = job_type_utils.get_next_idle_operation(job_state)
            if next_op_state is None:
                raise InvalidValue(
                    "next_op_state",
                    next_op_state,
                    "No next operation state found for job",
                )
            target_location = next_op_state.machine_id

    # Get source location information
    all_buffer_configs = buffer_type_utils.get_all_buffer_configs(instance)
    source_buffer_config: BufferConfig = buffer_type_utils.get_buffer_config_by_id(
        all_buffer_configs, job_state.location
    )

    # Determine actual source location ID
    if source_buffer_config.parent is None:
        source_id: str = job_state.location
    elif source_buffer_config.parent.startswith("m"):
        source_id: str = source_buffer_config.parent
    else:
        raise TransportConfigError("parent", source_buffer_config.parent)

    # Get travel time to pickup location
    time_to_pickup = instance.logistics.travel_times.get(
        (transport_state.location.location, source_id)
    )

    if not isinstance(time_to_pickup, (DeterministicTimeConfig, StochasticTimeConfig)):
        raise TransportConfigError("time_to_pickup", time_to_pickup)

    time_to_pickup = time_to_pickup.time
    current_time = extract_time(state.time)
    occupied_till = Time(current_time + time_to_pickup)

    # Create location information for transport route
    new_transport_location = core_utils.create_transport_location_from_job(
        transport_state.location.location, source_buffer_config.id, target_location
    )

    # Update transport state for movement to pickup
    transport_state = replace(
        transport_state,
        location=new_transport_location,
        state=TransportStateState.PICKUP,
        occupied_till=occupied_till,
        transport_job=job_state.id,
    )

    state = possible_transition_utils.replace_transport_state(state, transport_state)
    return state


def handle_agv_transport_transit_to_outage_transition(
    state: State,
    instance: InstanceConfig,
    transition: ComponentTransition,
    transport: TransportState,
) -> State:
    """
    Handles the transition from transport TRANSIT to OUTAGE state.

    This function completes the transport task by delivering the job to its
    destination machine. It moves the job from the transport buffer to the
    machine's prebuffer and updates all relevant states.

    Args:
        state: Current state of the system
        instance: The instance configuration
        transition: The transition object containing component and job IDs
        transport: The transport state being transitioned

    Returns:
        State: Updated state after handling the transition

    Raises:
        MissingJobIdError: If transition has no job_id
    """
    if transition.job_id is None:
        raise MissingJobIdError("transit_to_outage")

    # Get job and destination machine
    job_state = job_type_utils.get_job_state_by_id(jobs=state.jobs, job_id=transition.job_id)
    target_component_state = get_comp_by_id(
        state,
        transport.location.location[
            2
        ],  # TODO: hardcoded index -> assumes the last index is the destination machine
    )

    # Complete transport task - deliver job to machine or buffer(out)
    job_state, transport_state, target_component_state = manipulate.complete_transport_task(
        instance,
        job_state,
        transport=transport,
        target_component_state=target_component_state,
        time=state.time,
    )

    # Update all states
    state = possible_transition_utils.replace_job_state(state, job_state)
    state = possible_transition_utils.replace_transport_state(state, transport_state)
    if isinstance(target_component_state, MachineState):
        state = possible_transition_utils.replace_machine_state(state, target_component_state)
    if isinstance(target_component_state, BufferState):  # replacing output buffer state
        state = possible_transition_utils.replace_buffer_state(state, target_component_state)
    return state


def handle_agv_transport_outage_to_idle_transition(
    state: State,
    instance: InstanceConfig,
    transition: ComponentTransition,
    transport: TransportState,
) -> State:
    """
    Handles the transition from transport OUTAGE to IDLE state.

    This function releases all outages on the transport and returns it to
    idle state so it can be assigned to a new task.

    Args:
        state: Current state of the system
        instance: The instance configuration
        transition: The transition object containing component and job IDs
        transport: The transport state being transitioned

    Returns:
        State: Updated state after handling the transition
    """
    # Release all outages and return to idle state
    outages = tuple(map(outage_utils.release_outage, transport.outages))
    transport = replace(transport, state=TransportStateState.IDLE, outages=outages)
    state = possible_transition_utils.replace_transport_state(state, transport)
    return state


def handle_agv_waiting_pickup_to_waiting_pickup_transition(
    state: State,
    instance: InstanceConfig,
    transition: ComponentTransition,
    transport: TransportState,
) -> State:
    """
    Handles the transition from AGV WAITINGPICKUP to WAITINGPICKUP state.

    This function updates the transport's occupied_till time based on the job's
    processing operation end time. This is used to extend waiting time, especially
    in cases of stochastic operation durations.

    Args:
        state: Current state of the system
        instance: The instance configuration
        transition: The transition object containing component and job IDs
        transport: The transport state being transitioned

    Returns:
        State: Updated state after handling the transition

    Raises:
        MissingJobIdError: If transition has no job_id
        MissingProcessingOperationError: If the job has no processing operation
    """
    occupied_till = _get_waiting_time(state, transition, instance)
    # if occupied_till.time <= state.time.time:
    #     occupied_till = _get_waiting_time(state, transition, instance)
    #     raise ValueError()  # if this happens wre traversiing from waiting to waiting (bug)
    #     # occupied_till = Time(
    #     #     state.time.time + 1
    #     # )  # Ensure occupied_till is in the future as we're in transition for waiting to waiting
    # # Update transport to continue waiting
    transport = replace(
        transport,
        state=TransportStateState.WAITINGPICKUP,
        occupied_till=occupied_till,
    )

    state = possible_transition_utils.replace_transport_state(state, transport)
    return state


def handle_transition(
    state: State,
    instance: InstanceConfig,
    transition: ComponentTransition,
    component: Any,
    transition_handlers: dict[callable, callable],
) -> State:
    """
    Handle a transition by finding and executing the appropriate handler function.

    This function acts as a dispatcher that finds the correct handler for a given
    transition based on conditional functions. It iterates through a dictionary of
    condition-handler pairs, where conditions are functions that determine if the
    handler should be applied based on the component and transition state.

    Args:
        state: Current state of the system
        instance: Instance configuration
        transition: The transition object containing component and job IDs
        component: The component (machine, transport, etc.) being transitioned
        transition_handlers: Dictionary mapping condition functions to handler functions

    Returns:
        State: Updated state after handling the transition

    Raises:
        NotImplementedError: If no matching handler is found for the transition
    """
    # Try each condition in the handlers dictionary
    for condition, handler in transition_handlers.items():
        if condition(component, transition):
            return handler(state, instance, transition, component)

    # No appropriate handler found
    raise NotImplementedError()


def handle_transport_transition(
    state: State, instance: InstanceConfig, transition: ComponentTransition
) -> State:
    """
    Handle transitions for transport components in the state machine.

    This function identifies the appropriate transition handler based on the transport type
    (currently only AGV supported) and the transition requested. It maintains a dictionary
    of transition conditions and their corresponding handler functions.

    Args:
        state: Current state of the system
        instance: Instance configuration
        transition: The transition object containing component and job IDs

    Returns:
        State: Updated state after handling the transport transition

    Raises:
        NotImplementedError: If the transport type is not supported or no matching
                            handler is found for the transition
    """
    # Get transport state and configuration
    transport_state = transport_type_utils.get_transport_state_by_id(
        transports=state.transports, transport_id=transition.component_id
    )

    transport_config = transport_type_utils.get_transport_config_by_id(
        instance.transports, transport_state.id
    )

    # Handle different transport types
    match transport_config.type:
        case TransportTypeConfig.AGV:
            # Map of condition functions to handler functions for AGV transitions
            transition_handlers = {
                core_utils.is_transport_transition_from_idle_to_working: handle_agv_transport_idle_to_working_transition,
                core_utils.is_transport_transition_from_pickup_to_waitingpickup: handle_agv_transport_pickup_to_waitingpickup_transition,
                core_utils.is_transport_transition_from_waitingpickup_to_transit: handle_agv_transport_pickup_to_transit_transition,
                core_utils.is_transport_transition_from_pickup_to_transit: handle_agv_transport_pickup_to_transit_transition,
                core_utils.is_transport_transition_from_working_to_outage: handle_agv_transport_transit_to_outage_transition,
                core_utils.is_transport_transition_from_transit_to_outage: handle_agv_transport_transit_to_outage_transition,
                core_utils.is_transport_transition_from_outage_to_idle: handle_agv_transport_outage_to_idle_transition,
                core_utils.is_transport_transition_from_waiting_pickup_waiting_pickup: handle_agv_waiting_pickup_to_waiting_pickup_transition,
            }
        case _:
            # Transport type not supported
            raise NotImplementedError()

    # Try each condition to find matching handler
    for condition, handler in transition_handlers.items():
        if condition(transport_state, transition):
            return handler(state, instance, transition, transport_state)

    # No appropriate handler found
    raise NotImplementedError()


def handle_machine_transition(
    state: State, instance: InstanceConfig, transition: ComponentTransition
) -> State:
    """
    Handle transitions for machine components in the state machine.

    This function identifies and executes the appropriate transition handler for machines
    based on the current state and requested transition. It maintains a dictionary
    of transition conditions and their corresponding handler functions.

    Args:
        state: Current state of the system
        instance: Instance configuration
        transition: The transition object containing component and job IDs

    Returns:
        State: Updated state after handling the machine transition

    Raises:
        NotImplementedError: If no matching handler is found for the transition
    """
    # Get machine state
    machine = machine_type_utils.get_machine_state_by_id(state.machines, transition.component_id)

    # Map of condition functions to handler functions for machine transitions
    transition_handlers = {
        core_utils.is_machine_transition_from_idle_to_setup: handle_machine_idle_to_setup_transition,
        core_utils.is_machine_transition_from_setup_to_working: handle_machine_setup_to_working_transition,
        core_utils.is_machine_transition_from_working_to_outage: handle_machine_working_to_outage_transition,
        core_utils.is_machine_transition_from_outage_to_idle: handle_machine_outage_to_idle_transition,
    }

    # Use the generic transition handler to find and execute the appropriate handler
    return handle_transition(state, instance, transition, machine, transition_handlers)


def extract_time(time_obj: Time | NoTime) -> int:
    """
    Extract the integer time value from a Time object or raise an error for NoTime.

    This utility function safely extracts the numeric time value from a Time object,
    or raises an error if given a NoTime object.

    Args:
        time_obj: A Time or NoTime object

    Returns:
        int: The time value as an integer

    Raises:
        NotImplementedError: If time_obj is not a Time instance
    """
    if isinstance(time_obj, Time):
        return time_obj.time
    raise NotImplementedError()
