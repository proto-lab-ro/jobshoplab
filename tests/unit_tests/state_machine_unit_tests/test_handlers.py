from dataclasses import replace
from jobshoplab.utils.state_machine_utils import machine_type_utils
from jobshoplab.state_machine.core.state_machine.handler import *
from jobshoplab.types import NoTime, Time
from jobshoplab.types.state_types import (
    MachineStateState,
    OperationStateState,
    TransportStateState,
)
from jobshoplab.utils.state_machine_utils import machine_type_utils


def test_create_timed_machine_transitions(default_state_with_machine_occupied):
    transitions = create_timed_machine_transitions("debug", default_state_with_machine_occupied)
    assert len(transitions) == 1
    transition = transitions[0]
    assert transition.component_id == "m-1"
    assert transition.new_state == MachineStateState.OUTAGE
    assert transition.job_id == "j-2"


def test_create_transit_to_dropoff_transition(default_state_transport_transit):
    transport = default_state_transport_transit.transports[0]
    transition = create_avg_pickup_to_drop_transition(default_state_transport_transit, transport)
    assert transition.component_id == transport.id
    assert transition.new_state == TransportStateState.OUTAGE
    assert transition.job_id == transport.buffer.store[0]


def test_create_pickup_to_transit_transition(default_state_transport_pickup):
    transport = default_state_transport_pickup.transports[0]
    transition = create_avg_idle_to_pick_transition(default_state_transport_pickup, transport)
    assert transition.component_id == transport.id
    assert transition.new_state == TransportStateState.WAITINGPICKUP
    assert transition.job_id == transport.transport_job


def test_create_timed_transport_transitions(default_state_with_transport_occupied):
    transitions = create_timed_transport_transitions("debug", default_state_with_transport_occupied)
    assert len(transitions) == 1
    transition = transitions[0]
    assert transition.component_id == "t-1"
    assert transition.new_state in [
        TransportStateState.TRANSIT,
        TransportStateState.IDLE,
        TransportStateState.WAITINGPICKUP,
        TransportStateState.OUTAGE,
    ]
    assert transition.job_id == "j-1"


def test_create_timed_transitions(default_state_with_machine_and_transport_occupied):
    transitions = create_timed_transitions(
        "debug", default_state_with_machine_and_transport_occupied
    )
    assert len(transitions) == 2
    machine_transition = next((t for t in transitions if t.component_id.startswith("m")), None)
    transport_transition = next((t for t in transitions if t.component_id.startswith("t")), None)
    assert machine_transition is not None
    assert transport_transition is not None


def test_handle_machine_idle_to_setup_transition(
    default_state_machine_idle, default_instance, machine_transition_working
):
    new_state = handle_machine_idle_to_setup_transition(
        default_state_machine_idle,
        default_instance,
        machine_transition_working,
        default_state_machine_idle.machines[0],
    )
    machine = machine_type_utils.get_machine_state_by_id(new_state.machines, "m-1")
    assert machine.state == MachineStateState.SETUP
    assert machine.occupied_till != NoTime()
    job = new_state.jobs[0]
    assert job.operations[0].operation_state_state == OperationStateState.PROCESSING


def test_machine_setup_to_working_transition(
    default_state_machine_setup,
    default_instance,
    machine_transition_working,
    machine_state_working_on_j1,
):
    new_state = handle_machine_setup_to_working_transition(
        default_state_machine_setup,
        default_instance,
        machine_transition_working,
        default_state_machine_setup.machines[0],
    )
    machine = new_state.machines[0]
    assert machine.state == MachineStateState.WORKING
    assert machine.occupied_till != NoTime()
    job = new_state.jobs[0]
    assert job.operations[0].operation_state_state == OperationStateState.PROCESSING


def test_machine_setup_to_working_transition_with_setup_time(
    default_state_machine_setup,
    default_instance,
    machine_transition_working,
    machine_state_with_tool0,
    machine_with_deterministic_setup_times,
    job_with_tool1_operation,
    simple_op_config_with_tool1,
    job_config_with_tool_operations,
):

    # Arrange - set up initial state with machine in SETUP state
    current_time = Time(10)
    expected_setup_duration = 1  # For tool0 to tool1, the fixture returns 1

    # Create a machine state that's in SETUP with tool1 mounted and appropriate occupied_till time
    machine_in_setup = replace(
        machine_state_with_tool0,
        state=MachineStateState.SETUP,
        mounted_tool="tl-1",  # Tool changed during setup
        occupied_till=Time(current_time.time + expected_setup_duration),
        buffer=replace(machine_state_with_tool0.buffer, store=("j-setup",)),
    )

    # Create a state with the machine in setup
    setup_state = replace(
        default_state_machine_setup,
        time=current_time,
        machines=(machine_in_setup,),
        jobs=(job_with_tool1_operation,),
    )

    # Create a custom instance with the necessary job and machine configurations
    # We need this to ensure that the operation ID 'o-setup-1' is found in the job configs
    instance = replace(
        default_instance,
        machines=(machine_with_deterministic_setup_times,) + default_instance.machines[1:],
        instance=replace(
            default_instance.instance,
            specification=(job_config_with_tool_operations,)
            + default_instance.instance.specification,
        ),
    )

    # Check for transitions before setup time has elapsed - should be none
    before_completion_time = Time(current_time.time + expected_setup_duration - 0.1)
    before_completion_state = replace(setup_state, time=before_completion_time)

    transitions_before = create_timed_machine_transitions("debug", before_completion_state)
    assert len(transitions_before) == 0  # No transitions should occur before setup is done

    # Check for transitions at exactly the setup completion time
    at_completion_time = Time(current_time.time + expected_setup_duration)
    at_completion_state = replace(setup_state, time=at_completion_time)

    transitions_at = create_timed_machine_transitions("debug", at_completion_state)
    assert len(transitions_at) == 1  # Should have one transition
    assert transitions_at[0].new_state == MachineStateState.WORKING
    assert transitions_at[0].component_id == machine_in_setup.id

    # Now execute the transition from SETUP to WORKING
    final_state = handle_machine_setup_to_working_transition(
        at_completion_state, instance, transitions_at[0], machine_in_setup
    )

    # Get the machine after transition
    final_machine = machine_type_utils.get_machine_state_by_id(
        final_state.machines, machine_in_setup.id
    )

    # Verify transition completed as expected
    assert final_machine.state == MachineStateState.WORKING
    # Machine should be occupied until end of operation (setup_time + operation_time)
    # The operation time for tool1 is 10 based on simple_op_config_with_tool1
    assert final_machine.occupied_till.time > current_time.time + expected_setup_duration

    # Get the job after transition and verify its operation state
    final_job = next((j for j in final_state.jobs if j.id == job_with_tool1_operation.id), None)
    assert final_job is not None

    # The operation should be in PROCESSING state
    op = final_job.operations[0]
    assert op.operation_state_state == OperationStateState.PROCESSING


def test_handle_machine_working_to_outage_transition(
    default_state_machine_working,
    default_instance,
    machine_transition_outage,
    machine_state_working_on_j1,
):
    # TODO: Check if due time is greater or equal to the current time -> needs to be implemented
    default_state_machine_working = replace(
        default_state_machine_working, machines=(machine_state_working_on_j1,)
    )

    new_state = handle_machine_working_to_outage_transition(
        default_state_machine_working,
        default_instance,
        machine_transition_outage,
        default_state_machine_working.machines[0],
    )
    machine = new_state.machines[0]
    assert machine.state == MachineStateState.OUTAGE
    assert machine.occupied_till == Time(10)
    job = new_state.jobs[0]
    assert job.operations[0].operation_state_state == OperationStateState.PROCESSING


def test_machine_outage_to_idle_transition(
    default_state_machine_outage,
    default_instance,
    machine_transition_outage_to_idle,
    machine_state_working_on_j1,
):
    new_state = handle_machine_outage_to_idle_transition(
        default_state_machine_outage,
        default_instance,
        machine_transition_outage_to_idle,
        default_state_machine_outage.machines[0],
    )
    machine = new_state.machines[0]
    assert machine.state == MachineStateState.IDLE
    assert machine.occupied_till == NoTime()
    job = new_state.jobs[0]
    assert job.operations[0].operation_state_state == OperationStateState.DONE


def test_handle_agv_transport_pickup_to_waitingpickup_transition(
    default_state_transport_pickup, default_instance, transport_transition_pickup_to_waitingpickup
):
    new_state = handle_agv_transport_pickup_to_waitingpickup_transition(
        default_state_transport_pickup,
        default_instance,
        transport_transition_pickup_to_waitingpickup,
        default_state_transport_pickup.transports[0],
    )
    transport = new_state.transports[0]
    assert transport.state == TransportStateState.WAITINGPICKUP
    assert transport.occupied_till != NoTime()


def test_handle_agv_transport_pickup_to_transit_transition(
    default_state_transport_pickup_ready, default_instance, transport_transition_pickup_to_transit
):
    modified_job = replace(default_state_transport_pickup_ready.jobs[0], location="b-5")
    state = replace(default_state_transport_pickup_ready, jobs=(modified_job,))

    new_state = handle_agv_transport_pickup_to_transit_transition(
        state,
        default_instance,
        transport_transition_pickup_to_transit,
        state.transports[0],
    )
    transport = new_state.transports[0]
    assert transport.state == TransportStateState.TRANSIT
    assert transport.occupied_till != NoTime()
    assert transport.buffer.store == ("j-1",)
    job = new_state.jobs[0]
    assert job.location == "b-11"


def test_handle_agv_transport_idle_to_working_transition(
    default_state_transport_idle, default_instance, component_transition_transport_idle_to_working
):
    new_state = handle_agv_transport_idle_to_working_transition(
        default_state_transport_idle,
        default_instance,
        component_transition_transport_idle_to_working,
        default_state_transport_idle.transports[0],
    )
    transport = new_state.transports[0]
    assert transport.state == TransportStateState.PICKUP
    assert transport.occupied_till != NoTime()
    assert transport.transport_job == "j-1"


def test_handle_agv_transport_transit_to_idle_transition(
    default_state_transport_transit,
    default_instance,
    transport_transition_idle,
    machine_state_idle_empty,
):
    # Add machine to state
    default_state_transport_transit = replace(
        default_state_transport_transit, machines=(machine_state_idle_empty,)
    )

    new_state = handle_agv_transport_transit_to_outage_transition(
        default_state_transport_transit,
        default_instance,
        transport_transition_idle,
        default_state_transport_transit.transports[0],
    )
    transport = new_state.transports[0]
    assert transport.state == TransportStateState.OUTAGE
    assert transport.buffer.store == ()
    job = new_state.jobs[0]
    assert job.location == "b-1"


def test_handle_transition(default_state_machine_idle, default_instance, machine_transition_setup):
    new_state = handle_transition(
        default_state_machine_idle,
        default_instance,
        machine_transition_setup,
        default_state_machine_idle.machines[0],
        {
            lambda comp, trans: comp.state == MachineStateState.IDLE
            and trans.new_state == MachineStateState.SETUP: handle_machine_idle_to_setup_transition,
        },
    )
    machine = new_state.machines[0]

    assert machine.state == MachineStateState.SETUP


def test_handle_transport_transition(
    default_state_transport_idle, default_instance, component_transition_transport_idle_to_working
):
    new_state = handle_transport_transition(
        default_state_transport_idle,
        default_instance,
        component_transition_transport_idle_to_working,
    )
    transport = new_state.transports[0]
    assert transport.state == TransportStateState.PICKUP


def test_handle_machine_transition(
    default_state_machine_idle, default_instance, machine_transition_setup
):
    new_state = handle_machine_transition(
        default_state_machine_idle, default_instance, machine_transition_setup
    )
    machine = new_state.machines[0]
    assert machine.state == MachineStateState.SETUP
