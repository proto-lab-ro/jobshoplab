from jobshoplab.types import State
from jobshoplab.types.action_types import ComponentTransition
from jobshoplab.types.state_types import (JobState, MachineState,
                                          MachineStateState, OperationState,
                                          OperationStateState,
                                          TransportLocation, TransportState,
                                          TransportStateState)
from jobshoplab.utils.state_machine_utils import job_type_utils


def print_state(state: State):
    print(f"TIME: {state.time}")
    print("--- Machines: ---")
    print("ID \t State \t\t\t\t Occupied till")
    for machine in state.machines:
        print(f"{machine.id} 	 {machine.state} 	 {machine.occupied_till}")
        print("Buffer")
        print(machine.prebuffer)
        print(machine.buffer)
        print(machine.postbuffer)

    print("--- Transports: ---")
    print("ID \t State \t\t\t\t Occupied till \t Job")
    for transport in state.transports:
        print(
            f"{transport.id} 	 {transport.state}  {transport.occupied_till} {transport.transport_job} {transport.location.location} {transport.buffer.store}"
        )
    print("--- Jobs: ---")
    print("Job \t Location")
    for job in state.jobs:
        print("----------------------------")
        print(f"{job.id} \t {job.location}")
        print("Operation \t Machine \t State")
        for operation in job.operations:
            print(f"{operation.id} \t {operation.machine_id} \t{operation.operation_state_state}")


def is_done(state: State) -> bool:
    """
    Check if the state machine is done.
    Args:
        state (State): The current state of the state machine.
    Returns:
        bool: A boolean indicating if the state machine is done.
    """
    for job in state.jobs:
        for op in job.operations:
            if op.operation_state_state != OperationStateState.DONE:
                return False
    return True


def no_processing_operations(job: JobState) -> bool:
    """
    Checks if a job has any processing operations.

    Args:
        job (JobState): The job to check.

    Returns:
        bool: True if the job has no processing operations, False otherwise.
    """
    for op in job.operations:
        if op.operation_state_state == OperationStateState.PROCESSING:
            # if machine_state != MachineStateState.SETUP:
            # return False
            return False
    return True


def is_machine_transition_from_idle_to_setup(machine: MachineState, transition):
    return (
        machine.state == MachineStateState.IDLE and transition.new_state == MachineStateState.SETUP
    )


def is_machine_transition_from_setup_to_working(machine: MachineState, transition):
    return (
        machine.state == MachineStateState.SETUP
        and transition.new_state == MachineStateState.WORKING
    )


def is_machine_transition_from_working_to_outage(machine: MachineState, transition):
    return (
        machine.state == MachineStateState.WORKING
        and transition.new_state == MachineStateState.OUTAGE
    )


def is_machine_transition_from_outage_to_idle(machine: MachineState, transition):
    return (
        machine.state == MachineStateState.OUTAGE and transition.new_state == MachineStateState.IDLE
    )


## Transport transitions checker


def is_transport_transition_from_idle_to_working(transport: TransportState, transition):
    return (
        transport.state == TransportStateState.IDLE
        and transition.new_state == TransportStateState.WORKING
    )


def is_transport_transition_from_pickup_to_transit(transport: TransportState, transition):
    return (
        transport.state == TransportStateState.PICKUP
        and transition.new_state == TransportStateState.TRANSIT
    )


def is_transport_transition_from_pickup_to_waitingpickup(transport: TransportState, transition):
    return (
        transport.state == TransportStateState.PICKUP
        and transition.new_state == TransportStateState.WAITINGPICKUP
    )


def is_transport_transition_from_waitingpickup_to_transit(transport: TransportState, transition):
    return (
        transport.state == TransportStateState.WAITINGPICKUP
        and transition.new_state == TransportStateState.TRANSIT
    )


def is_transport_transition_from_working_to_outage(transport: TransportState, transition):
    return (
        transport.state == TransportStateState.WORKING
        and transition.new_state == TransportStateState.OUTAGE
    )


def is_transport_transition_from_transit_to_outage(transport: TransportState, transition):
    return (
        transport.state == TransportStateState.TRANSIT
        and transition.new_state == TransportStateState.OUTAGE
    )


def is_transport_transition_from_outage_to_idle(transport: TransportState, transition):
    return (
        transport.state == TransportStateState.OUTAGE
        and transition.new_state == TransportStateState.IDLE
    )


def is_transport_transition_from_waiting_pickup_waiting_pickup(
    transport: TransportState, transition
):
    return (
        transport.state == TransportStateState.WAITINGPICKUP
        and transition.new_state == TransportStateState.WAITINGPICKUP
    )


def sorted_by_transport(
    transitions: tuple[ComponentTransition, ...],
) -> tuple[ComponentTransition, ...]:
    _transitions = sorted(
        transitions,
        key=lambda t: int(
            not isinstance(t.new_state, TransportStateState)
        ),  # sorting so transports are processed first
    )
    return tuple(_transitions)


def create_transport_location_from_job(
    current_dest: str, pickup_dest: str, dropoff_dest: str
) -> TransportLocation:
    return TransportLocation(progress=0.0, location=(current_dest, pickup_dest, dropoff_dest))


def sorted_done_operations(job_states: tuple[JobState, ...]) -> tuple[OperationState, ...]:
    operations_by_state = job_type_utils.group_operations_by_state(job_states)
    return tuple(
        sorted(
            operations_by_state.get(OperationStateState.DONE, []),
            key=lambda x: x.end_time.time if x else None,
        )
    )
