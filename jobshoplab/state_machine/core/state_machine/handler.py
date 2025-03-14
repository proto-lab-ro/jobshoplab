from dataclasses import replace
from typing import Tuple, Any

import jobshoplab.state_machine.core.state_machine.manipulate as manipulate
import jobshoplab.utils.state_machine_utils.core_utils as core_utils
from jobshoplab.types import InstanceConfig, State
from jobshoplab.types.action_types import ComponentTransition
from jobshoplab.types.instance_config_types import BufferConfig, TransportTypeConfig
from jobshoplab.types.state_types import (
    BufferState,
    DeterministicDurationConfig,
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
    possible_transition_utils,
    transport_type_utils,
)


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
    for machine in state.machines:
        if isinstance(machine.occupied_till, Time) and isinstance(state.time, Time):
            if machine.occupied_till.time <= state.time.time:
                if len(machine.buffer.store) == 1:
                    job_id = machine.buffer.store[0]
                    if not job_id.startswith("j"):
                        raise ValueError("job_id", job_id, "Job ID does not start with 'j'")
                else:
                    raise NotImplementedError()

                # Set machine to idle
                transition = ComponentTransition(
                    component_id=machine.id, new_state=MachineStateState.IDLE, job_id=job_id
                )
                transitions.append(transition)

    return tuple(transitions)


def create_avg_pickup_to_drop_transition(
    state: State, transport: TransportState
) -> ComponentTransition:
    """
    Creates transition from PICKUP to move to drop location.
    """

    if len(transport.buffer.store) == 1:
        _job = job_type_utils.get_job_state_by_id(jobs=state.jobs, job_id=transport.buffer.store[0])
    else:
        raise NotImplementedError()

    transition = ComponentTransition(
        component_id=transport.id,
        new_state=TransportStateState.IDLE,
        job_id=_job.id,
    )
    return transition


def create_avg_idle_to_pick_transition(
    state: State, transport: TransportState
) -> ComponentTransition:
    """
    Creates transition from IDLE to PICKUP.
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

    # check if job is ready or gets ready in the same timestep
    if core_utils.no_processing_operations(job) or running_op_will_be_done:
        transit_transition = ComponentTransition(
            component_id=transport.id,
            new_state=TransportStateState.TRANSIT,
            job_id=job.id,
        )
        return transit_transition
    else:
        waiting_transition = ComponentTransition(
            component_id=transport.id,
            new_state=TransportStateState.WAITINGPICKUP,
            job_id=job.id,
        )
        return waiting_transition


def create_timed_transport_transitions(
    loglevel: int | str | str, state: State
) -> Tuple[ComponentTransition]:
    """
    Creates timed transport transitions based on the given state.
    Checks if states due time is over and creates a  transition to set the transport to idle.
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
                    case TransportStateState.WORKING:
                        raise NotImplementedError()
                    case _:
                        raise NotImplementedError()
                if transition is not None:
                    transitions.extend([transition])
    return tuple(transitions)


def create_timed_transitions(loglevel: int | str | str, state: State) -> Tuple[ComponentTransition]:
    """
    Create timed transitions for the given state.
    Checks if occupation time of components is over and creates transitions to set them to idle.
    """
    transitions = []
    # ORDER IS IMPORTANT
    # https://3.basecamp.com/4286581/buckets/38177464/card_tables/cards/7988333079
    transitions.extend(create_timed_machine_transitions(loglevel, state))
    transitions.extend(create_timed_transport_transitions(loglevel, state))
    return tuple(transitions)


# MARK: Transition Handlers
def handle_machine_idle_to_working_transition(
    state: State, instance: InstanceConfig, transition: ComponentTransition, machine: MachineState
) -> State:
    """
    Handles the transition from machine idle to working state.
    -> Moves job from prebuffer to buffer and executes operation.
    -> Updates job and machine state.
    """
    if transition.job_id is None:
        raise ValueError("No job_id in transition")

    # Get the job state
    job_state = job_type_utils.get_job_state_by_id(jobs=state.jobs, job_id=transition.job_id)

    # Check if job is in prebuffer
    if not buffer_type_utils.is_job_in_buffer(machine.prebuffer, job_state.id):
        raise ValueError("Job is not in buffer")

    # Move job from prebuffer to buffer and execute operation
    job_state, _machine = manipulate.begin_next_job_on_machine(
        job_state=job_state,
        instance=instance,
        machine_state=machine,
        time=state.time,
    )

    state = possible_transition_utils.replace_job_state(state, job_state)
    state = possible_transition_utils.replace_machine_state(state, _machine)
    return state


def handle_machine_working_to_idle_transition(
    state: State, instance: InstanceConfig, transition: ComponentTransition, machine: MachineState
) -> State:
    """
    Handles the transition from machine working to idle state.
    -> Completes the active operation on the machine.
    -> Updates job and machine state.
    """

    # Update job and machine state, but job in postbuffer
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

    if transport_source.startswith("m") or transport_destination.startswith("m"):
        travel_time = instance.logistics.travel_times.get((transport_source, transport_destination))
        match travel_time:
            case DeterministicDurationConfig(duration):
                travel_time = duration
            case None:
                raise ValueError(
                    "No travel time found between", transport_source, transport_destination
                )
            case _:
                raise NotImplementedError()
    else:
        raise NotImplementedError()

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
    Therefore it calculates the time to pickup based on the tranport.poistion and the next operations positions and sets the transport to the pickup state.
    """
    if transition.job_id is None:
        raise ValueError("No job_id in transition")

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

    if not isinstance(time_to_pickup, DeterministicDurationConfig):
        raise ValueError("time_to_pickup", time_to_pickup)

    time_to_pickup = time_to_pickup.duration

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


def handle_agv_transport_transit_to_idle_transition(
    state: State,
    instance: InstanceConfig,
    transition: ComponentTransition,
    transport: TransportState,
) -> State:
    """
    Handles the transition from 'transit' to 'idle' state for an AGV transport component.

    When an AGV completes transport and arrives at the destination, it transitions to idle
    and completes the transport task, updating the job location and machine state.

    Args:
        state: Current state of the system
        instance: Instance configuration
        transition: The transition object containing component and job IDs
        transport: The transport state object being transitioned

    Returns:
        State: Updated state after handling the transition

    Raises:
        ValueError: If no job_id is specified in the transition
    """
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
                core_utils.is_transport_transition_from_working_to_idle: handle_agv_transport_transit_to_idle_transition,
                core_utils.is_transport_transition_from_transit_to_idle: handle_agv_transport_transit_to_idle_transition,
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
        core_utils.is_machine_transition_from_idle_to_working: handle_machine_idle_to_working_transition,
        core_utils.is_machine_transition_from_working_to_idle: handle_machine_working_to_idle_transition,
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
