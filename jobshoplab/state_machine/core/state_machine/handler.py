"""
Handler module for state machine transitions.

This module contains functions for handling transitions between different states
for machines and transports in the JobShopLab simulation.
"""

from dataclasses import replace
from typing import Any, Callable, Dict, Optional, Tuple, Union

import jobshoplab.state_machine.core.state_machine.manipulate as manipulate
import jobshoplab.utils.state_machine_utils.core_utils as core_utils
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
    TransportState,
    TransportStateState,
)
from jobshoplab.utils.exceptions import InvalidValue, NotImplementedError
from jobshoplab.utils.state_machine_utils import (
    buffer_type_utils,
    job_type_utils,
    machine_type_utils,
    outage_utils,
    possible_transition_utils,
    transport_type_utils,
)
from jobshoplab.utils.state_machine_utils.time_utils import _get_travel_time_from_spec

#! TODO FELIX -> add timed transitions for machines and transports


def _waiting_time_and_op_time_differ(state, transport) -> bool:
    """
    Check if the waiting time and operation time differ.

    This function checks if the waiting time of a transport is different from the
    operation time of the job it is carrying. If they differ, it returns True,
    indicating that the transport should wait for the job to be ready.

    Args:
        state: Current state of the system
        transport: The transport state being checked

    Returns:
        bool: True if waiting time and operation time differ, False otherwise
    """
    job = job_type_utils.get_job_state_by_id(state.jobs, transport.transport_job)
    running_op = job_type_utils.get_processing_operation(job)
    return running_op.end_time != transport.occupied_till


def create_timed_machine_transitions(
    loglevel: int | str, state: State
) -> tuple[ComponentTransition, ...]:
    """
    Create timed machine transitions based on the given state.

    Checks if any machine's occupied_till time has passed and creates ComponentTransitions
    to set those machines to idle state.

    Args:
        loglevel: Log level for the function
        state: Current state of the system

    Returns:
        A tuple of ComponentTransition objects for machines that need to transition to idle
    """
    transitions = []

    # check machines is available -> if yes -> set to idle -> release job!
    for machine in state.machines:  # FELIX maby use sieve
        if isinstance(machine.occupied_till, Time) and isinstance(state.time, Time):
            if machine.occupied_till.time <= state.time.time:
                # Set machine to idle
                match machine.state:
                    case MachineStateState.SETUP:
                        transition = ComponentTransition(
                            component_id=machine.id,
                            new_state=MachineStateState.WORKING,
                            job_id=machine.buffer.store[0],
                        )
                    case MachineStateState.WORKING:
                        transition = ComponentTransition(
                            component_id=machine.id,
                            new_state=MachineStateState.OUTAGE,
                            job_id=machine.buffer.store[0],
                        )

                    case MachineStateState.OUTAGE:
                        transition = ComponentTransition(
                            component_id=machine.id,
                            new_state=MachineStateState.IDLE,
                            job_id=machine.buffer.store[0],
                        )
                    case _:
                        transition = None
                if transition is not None:
                    transitions.append(transition)

    return tuple(transitions)


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

    if len(transport.buffer.store) == 1:
        _job = job_type_utils.get_job_state_by_id(jobs=state.jobs, job_id=transport.buffer.store[0])
    else:
        raise NotImplementedError()

    transition = ComponentTransition(
        component_id=transport.id,
        new_state=TransportStateState.OUTAGE,
        job_id=_job.id,
    )
    return transition


def create_avg_idle_to_pick_transition(
    state: State, transport: TransportState
) -> Optional[ComponentTransition]:
    """
    Creates transition from IDLE to PICKUP or WAITINGPICKUP.

    This function determines the appropriate next transition for an AGV in the IDLE state.
    If the job is ready to be transported (has no processing operations), it creates a
    transition to TRANSIT state. If the AGV is in PICKUP state and the job is not ready,
    it creates a transition to WAITINGPICKUP state.

    Args:
        state: Current state of the system
        transport: The transport state that is performing the transition

    Returns:
        Optional[ComponentTransition]: A transition for the transport's next state,
            or None if no appropriate transition is found

    Raises:
        InvalidValue: If the transport has no assigned job (transport_job is None)
    """

    # check if job is free
    if transport.transport_job is not None:
        job = job_type_utils.get_job_state_by_id(state.jobs, transport.transport_job)
    else:
        raise ValueError("transport_job", transport.transport_job, "No transport_job")

    running_op = job_type_utils.get_processing_operation(job)
    running_op_will_be_done = False
    if running_op is not None:
        running_op_end_time = extract_time(
            running_op.end_time if running_op is not None else NoTime()
        )
        running_op_will_be_done = running_op_end_time <= extract_time(state.time)

    # check if job is in post_buffer
    # machine_state = machine_type_utils.get_machine_state_by_id(state.machines, job.loc)
    # in_postbuffer = machine_state.postbuffer.id == job.location

    # check if job is ready or gets ready in the same timestep
    if core_utils.no_processing_operations(
        job
    ):  # or running_op_will_be_done: note uncommented because of potential bug FELIX (empties buffer bevor outage)
        transit_transition = ComponentTransition(
            component_id=transport.id,
            new_state=TransportStateState.TRANSIT,
            job_id=job.id,
        )

        return transit_transition

    elif transport.state == TransportStateState.PICKUP:
        waiting_transition = ComponentTransition(
            component_id=transport.id,
            new_state=TransportStateState.WAITINGPICKUP,
            job_id=job.id,
        )
        return waiting_transition
    elif (
        transport.state == TransportStateState.WAITINGPICKUP
    ) and _waiting_time_and_op_time_differ(
        state, transport
    ):  # extend the waiting time in case of a stochastic outage
        waiting_transition = ComponentTransition(
            component_id=transport.id,
            new_state=TransportStateState.WAITINGPICKUP,
            job_id=job.id,
        )
        return waiting_transition
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
        job_id=None,
    )


def create_timed_transport_transitions(
    loglevel: Union[int, str], state: State
) -> Tuple[ComponentTransition, ...]:
    """
    Creates timed transport transitions based on the given state.

    Checks if any transport's occupied_till time has been reached and creates appropriate
    transitions based on the transport's current state. This function is responsible for
    advancing transport components to their next states when their current tasks finish.

    Args:
        loglevel: The log level to use
        state: Current state of the system

    Returns:
        Tuple[ComponentTransition, ...]: A tuple of transitions for transports that
            have reached their occupied_till time

    Raises:
        NotImplementedError: If a transport is in the WORKING state and needs a transition
    """
    transitions = []
    # Check if transport is available -> if yes -> set to idle -> update job location
    for transport in state.transports:
        # Set transport to idle
        if isinstance(transport.occupied_till, Time) and isinstance(state.time, Time):
            if transport.occupied_till.time <= state.time.time:
                match transport.state:
                    case TransportStateState.PICKUP | TransportStateState.WAITINGPICKUP:
                        transition = create_avg_idle_to_pick_transition(state, transport)
                    case TransportStateState.TRANSIT:
                        transition = create_avg_pickup_to_drop_transition(state, transport)
                    case TransportStateState.OUTAGE:
                        transition = create_agv_drop_to_idle_transition(state, transport)
                    case TransportStateState.WORKING:
                        raise NotImplementedError()
                    case _:
                        transition = None
                if transition is not None:
                    transitions.extend([transition])
    return tuple(transitions)


def create_timed_transitions(
    loglevel: Union[int, str], state: State
) -> Tuple[ComponentTransition, ...]:
    """
    Create timed transitions for the given state.

    This function combines machine and transport timed transitions into a single list.
    It checks if occupation time of components is over and creates transitions to
    advance them to their next state. The order of transitions is important to ensure
    proper sequencing of events.

    Args:
        loglevel: The log level to use
        state: Current state of the system

    Returns:
        Tuple[ComponentTransition, ...]: A tuple of all timed transitions for the current state
    """
    transitions = []
    # ORDER IS IMPORTANT
    # https://3.basecamp.com/4286581/buckets/38177464/card_tables/cards/7988333079
    transitions.extend(create_timed_machine_transitions(loglevel, state))
    transitions.extend(create_timed_transport_transitions(loglevel, state))
    return tuple(transitions)


def handle_machine_idle_to_setup_transition(
    state: State, instance: InstanceConfig, transition: ComponentTransition, machine: MachineState
) -> State:
    """
    Handles the transition from machine IDLE to SETUP state.

    This function moves a job from the machine's prebuffer to its buffer
    and sets up the machine to start processing the job.

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

    # Move job from prebuffer to buffer and execute operation
    job_state, _machine = manipulate.begin_machine_setup(
        job_state=job_state,
        instance=instance,
        machine_state=machine,
        time=state.time,
    )

    state = possible_transition_utils.replace_job_state(state, job_state)
    state = possible_transition_utils.replace_machine_state(state, _machine)
    return state


def handle_machine_setup_to_working_transition(
    state: State, instance: InstanceConfig, transition: ComponentTransition, machine: MachineState
) -> State:
    """
    Handles the transition from machine SETUP to WORKING state.

    This function moves a job from setup phase to active processing.
    It updates both job and machine state to reflect the new status.

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

    # Move job from prebuffer to buffer and execute operation
    job_state, _machine = manipulate.begin_next_job_on_machine(
        job_state=job_state,
        instance=instance,
        machine_state=machine,
        time=state.time,
    )

    state = possible_transition_utils.replace_job_state(state, job_state)
    state = possible_transition_utils.replace_machine_state(
        state, _machine
    )  # add setup somewhere here
    return state


def handle_machine_working_to_outage_transition(
    state: State, instance: InstanceConfig, transition: ComponentTransition, machine: MachineState
) -> State:
    """
    Handles the transition from machine WORKING to OUTAGE state.

    This function places the machine in an outage state, which may represent
    planned maintenance, a breakdown, or other non-operational period.
    It calculates the duration of the outage and updates the machine's state.

    Args:
        state: Current state of the system
        instance: The instance configuration
        transition: The transition object containing component and job IDs
        machine: The machine state being transitioned

    Returns:
        State: Updated state after handling the transition
    """

    # Update job and machine state, but job in postbuffer
    outages = outage_utils.get_new_outage_states(machine, instance, state.time)
    occupied_for = outage_utils.get_occupied_time_from_outage_iterator(outages)

    job_state, machine = manipulate.begin_machine_outage(
        instance=instance,
        job_state=job_type_utils.get_job_state_by_id(state.jobs, transition.job_id),
        machine_state=machine,
        time=state.time,
        occupied_for=occupied_for,
        outages=outages,
    )
    state = possible_transition_utils.replace_machine_state(state, machine)
    state = possible_transition_utils.replace_job_state(state, job_state=job_state)
    return state


def handle_machine_outage_to_idle_transition(
    state: State, instance: InstanceConfig, _transition: ComponentTransition, machine: MachineState
) -> State:
    """
    Handles the transition from machine OUTAGE to IDLE state.

    This function completes the current outage period and finishes the job operation.
    It moves the job to the machine's postbuffer and updates both the job and machine states.

    Args:
        state: Current state of the system
        instance: The instance configuration
        _transition: The transition object (not directly used in this function)
        machine: The machine state being transitioned

    Returns:
        State: Updated state after handling the transition
    """
    job, machine = manipulate.complete_active_operation_on_machine(
        instance=instance, jobs=state.jobs, machine_state=machine, time=state.time
    )
    state = possible_transition_utils.replace_job_state(state, job)
    state = possible_transition_utils.replace_machine_state(state, machine)

    return state


def handle_agv_transport_pickup_to_waitingpickup_transition(
    state: State,
    instance: InstanceConfig,
    transition: ComponentTransition,
    transport: TransportState,
) -> State:
    """
    AGV is at the pickup location and waits for the job to be ready.

    Functionality:
        - Get time until job is ready
        - Set occupied_till to time until job is ready
        - Update transport state to waitingpickup
    """

    if transition.job_id is None:
        raise ValueError("No job_id in transition")

    job_state = job_type_utils.get_job_state_by_id(state.jobs, transition.job_id)
    processing_op = job_type_utils.get_processing_operation(job_state)

    if processing_op is None:
        raise ValueError("No processing operation found -> AGV can not wait for pickup!")

    # update transport
    transport = replace(
        transport,
        state=TransportStateState.WAITINGPICKUP,
        occupied_till=processing_op.end_time,
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
    Try to pickup the job and move it to the next operation location.
    If the job is not ready we will wait for the job to be ready.
    """
    if transition.job_id is None:
        raise ValueError("No job_id in transition")

    job_state = job_type_utils.get_job_state_by_id(state.jobs, transition.job_id)

    next_job_operation = job_type_utils.get_next_not_done_operation(job_state)
    transport_source = job_state.location

    transport_source = machine_type_utils.get_machine_id_from_buffer(
        instance.machines, job_state.location
    )
    if not transport_source:
        transport_source = job_state.location

    transport_destination = next_job_operation.machine_id

    travel_time = _get_travel_time_from_spec(instance, transport_source, transport_destination)

    # TODO: CLEANUP -> bad code
    # This means the job is in a solo buffer with no parent machine
    if transport_source.startswith("b"):
        from_buffer_state: BufferState = buffer_type_utils.get_buffer_state_by_id(
            state.buffers, transport_source
        )

        from_buffer_state, transport_buffer, job_state = buffer_type_utils.switch_buffer(
            instance=instance,
            buffer_to_state=transport.buffer,
            buffer_from_state=from_buffer_state,
            job_state=job_state,
        )

        state = buffer_type_utils.replace_buffer_state(state, from_buffer_state)

    else:

        # get the machine where the job is currently located an get the job from the postbuffer
        machine_state = machine_type_utils.get_machine_state_by_id(state.machines, transport_source)
        buffer_id = job_state.location

        buffer_state = machine_type_utils.get_buffer_state_from_machine(machine_state, buffer_id)

        # get job from buffer
        buffer_from_state, transport_buffer, job_state = buffer_type_utils.switch_buffer(
            instance=instance,
            buffer_to_state=transport.buffer,
            buffer_from_state=buffer_state,
            job_state=job_state,
        )
        # update machine buffer
        machine_state = machine_type_utils.replace_buffer_state_in_machine(
            machine_state, buffer_from_state
        )
        state = possible_transition_utils.replace_machine_state(state, machine_state)

    current_time = extract_time(state.time)

    # update transport progress and occupied_till
    occupied_till = Time(current_time + travel_time)
    transport_location = replace(transport.location, progress=0.5)  # TODO: hardcoded progress...

    # update transport
    transport = replace(
        transport,
        state=TransportStateState.TRANSIT,
        occupied_till=occupied_till,
        location=transport_location,
        buffer=transport_buffer,
    )

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
        ValueError: If travel time calculation fails
    """
    if transition.job_id is None:
        raise InvalidValue("job_id", None, "No job_id in transition")

    if not isinstance(transport_state.location.location, str):
        raise InvalidValue(
            "transport.location.location",
            transport_state.location.location,
            "transport location is not a string. Tuple could be an progress object -> tuple[str, str, str]",
        )

    # create transport job
    job_state = job_type_utils.get_job_state_by_id(jobs=state.jobs, job_id=transition.job_id)
    next_op_state = job_type_utils.get_next_idle_operation(job_state)

    all_buffer_configs = buffer_type_utils.get_all_buffer_configs(instance)
    source_buffer_config: BufferConfig = buffer_type_utils.get_buffer_config_by_id(
        all_buffer_configs, job_state.location
    )

    # None if it is a buffer that has no parent like the arrival buffer
    if source_buffer_config.parent is None:
        source_id: str = job_state.location
    # If parent is a machine
    elif source_buffer_config.parent.startswith("m"):
        source_id: str = source_buffer_config.parent
    else:
        raise ValueError("source_buffer_config.parent", source_buffer_config.parent)

    time_to_pickup = instance.logistics.travel_times.get(
        (transport_state.location.location, source_id)
    )

    if not isinstance(time_to_pickup, (DeterministicTimeConfig, StochasticTimeConfig)):
        raise ValueError("time_to_pickup", time_to_pickup)

    time_to_pickup = time_to_pickup.time

    current_time = extract_time(state.time)

    occupied_till = Time(current_time + time_to_pickup)

    new_transport_location = core_utils.create_transport_location_from_job(
        transport_state.location.location, source_buffer_config.id, next_op_state.machine_id
    )

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
):

    if transition.job_id is None:
        raise ValueError("No job_id in transition")
    else:
        job_state = job_type_utils.get_job_state_by_id(jobs=state.jobs, job_id=transition.job_id)
        machine_state = machine_type_utils.get_machine_state_by_id(
            state.machines,
            transport.location.location[
                2
            ],  # TODO: hardcoded index -> assumes that the last index is the destination machine
        )

        job_state, transport_state, machine_state = manipulate.complete_transport_task(
            instance, job_state, transport=transport, machine=machine_state, time=state.time
        )

        state = possible_transition_utils.replace_job_state(state, job_state)
        state = possible_transition_utils.replace_transport_state(state, transport_state)
        state = possible_transition_utils.replace_machine_state(state, machine_state)
        return state


def handle_agv_transport_outage_to_idle_transition(
    state: State,
    instance: InstanceConfig,
    transition: ComponentTransition,
    transport: TransportState,
):
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

    This function updates the transport's state to WAITINGPICKUP and sets its
    occupied_till time based on the job's processing operation end time.

    Args:
        state: Current state of the system
        instance: The instance configuration
        transition: The transition object containing component and job IDs
        transport: The transport state being transitioned

    Returns:
        State: Updated state after handling the transition
    """
    if transition.job_id is None:
        raise ValueError("No job_id in transition")

    job_state = job_type_utils.get_job_state_by_id(state.jobs, transition.job_id)
    processing_op = job_type_utils.get_processing_operation(job_state)

    if processing_op is None:
        raise ValueError("No processing operation found -> AGV can not wait for pickup!")

    # update transport
    transport = replace(
        transport,
        state=TransportStateState.WAITINGPICKUP,
        occupied_till=processing_op.end_time,
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

    Iterates through a dictionary of condition-handler pairs, where conditions are functions
    that determine if the handler should be applied based on the component and transition.
    When a condition evaluates to True, its corresponding handler is called.

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
    for condition, handler in transition_handlers.items():
        if condition(component, transition):
            return handler(state, instance, transition, component)
    raise NotImplementedError()


def handle_transport_transition(
    state: State, instance: InstanceConfig, transition: ComponentTransition
) -> State:
    """
    Handle transitions for transport components in the state machine.

    Identifies the appropriate transition handler based on the transport type
    (currently only AGV supported) and the transition requested.

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

    transport_state = transport_type_utils.get_transport_state_by_id(
        transports=state.transports, transport_id=transition.component_id
    )

    transport_config = transport_type_utils.get_transport_config_by_id(
        instance.transports, transport_state.id
    )

    match transport_config.type:
        case TransportTypeConfig.AGV:
            # TODO: Implement Progress of Transport
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
            raise NotImplementedError()

    # Iterate through the dictionary and call the appropriate handler function
    for condition, handler in transition_handlers.items():
        if condition(transport_state, transition):
            return handler(state, instance, transition, transport_state)

    raise NotImplementedError()


def handle_machine_transition(
    state: State, instance: InstanceConfig, transition: ComponentTransition
) -> State:
    """
    Handle transitions for machine components in the state machine.

    Identifies and executes the appropriate transition handler for machines
    based on the current state and requested transition.

    Args:
        state: Current state of the system
        instance: Instance configuration
        transition: The transition object containing component and job IDs

    Returns:
        State: Updated state after handling the machine transition

    Raises:
        NotImplementedError: If no matching handler is found for the transition
    """
    machine = machine_type_utils.get_machine_state_by_id(state.machines, transition.component_id)

    transition_handlers = {
        core_utils.is_machine_transition_from_idle_to_setup: handle_machine_idle_to_setup_transition,
        core_utils.is_machine_transition_from_setup_to_working: handle_machine_setup_to_working_transition,
        core_utils.is_machine_transition_from_working_to_outage: handle_machine_working_to_outage_transition,
        core_utils.is_machine_transition_from_outage_to_idle: handle_machine_outage_to_idle_transition,
    }

    return handle_transition(state, instance, transition, machine, transition_handlers)


def extract_time(time_obj: Time | NoTime) -> int:
    """
    Extract the integer time value from a Time object or raise an error for NoTime.

    Args:
        time_obj: A Time object

    Returns:
        int: The time value

    Raises:
        NotImplementedError: If time_obj is not a Time instance
    """
    if isinstance(time_obj, Time):
        return time_obj.time
    raise NotImplementedError()
