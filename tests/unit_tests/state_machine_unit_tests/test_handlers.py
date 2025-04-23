from dataclasses import replace

import pytest

from jobshoplab.state_machine.core.state_machine.handler import *

from jobshoplab.types import NoTime, Time
from jobshoplab.types.action_types import ComponentTransition
from jobshoplab.types.instance_config_types import TransportTypeConfig
from jobshoplab.types.state_types import (
    MachineStateState,
    OperationStateState,
    TransportLocation,
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
    assert transition.new_state == TransportStateState.TRANSIT
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


def test_handle_machine_working_to_outage_transition(
    default_state_machine_working,
    default_instance,
    machine_transition_working_to_idle,
    machine_state_working_on_j1,
):
    # TODO: Check if due time is greater or equal to the current time -> needs to be implemented
    default_state_machine_working = replace(
        default_state_machine_working, machines=(machine_state_working_on_j1,)
    )

    new_state = handle_machine_working_to_outage_transition(
        default_state_machine_working,
        default_instance,
        machine_transition_working_to_idle,
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
    assert False


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


def test_handle_transition(
    default_state_machine_idle, default_instance, machine_transition_working
):
    new_state = handle_transition(
        default_state_machine_idle,
        default_instance,
        machine_transition_working,
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
    default_state_machine_idle, default_instance, machine_transition_working
):
    new_state = handle_machine_transition(
        default_state_machine_idle, default_instance, machine_transition_working
    )
    machine = new_state.machines[0]
    assert machine.state == MachineStateState.SETUP
