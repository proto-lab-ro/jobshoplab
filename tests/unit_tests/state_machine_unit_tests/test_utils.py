from dataclasses import replace

from jobshoplab.types.state_types import State, Time, TransportLocation
from jobshoplab.utils.state_machine_utils.core_utils import (
    create_transport_location_from_job,
    is_done,
    is_transport_transition_from_idle_to_working,
    is_transport_transition_from_pickup_to_transit,
    is_transport_transition_from_pickup_to_waitingpickup,
    is_transport_transition_from_waitingpickup_to_transit,
    no_processing_operations,
    sorted_by_transport,
    sorted_done_operations,
)


def test_is_done(job_state_done):
    state = State(
        jobs=(job_state_done,),
        time=Time(0),
        machines=(),
        transports=(),
        buffers=(),
    )
    assert is_done(state) == True


def test_no_processing_operations(job_state_processing):
    assert no_processing_operations(job_state_processing) == False


# def test_is_machine_transition_from_idle_to_working(machine_state_idle, machine_transition_working):
#     assert is_machine_transition_from_idle_to_working(
#         machine_state_idle, machine_transition_working
#     )


# def test_is_machine_transition_from_working_to_idle(
#     machine_state_working, machine_transition_working_to_idle
# ):
#     assert is_machine_transition_from_working_to_idle(
#         machine_state_working, machine_transition_working_to_idle
#     )


def test_is_transport_transition_from_idle_to_working(
    transport_state_idle, transport_transition_working
):
    assert is_transport_transition_from_idle_to_working(
        transport_state_idle, transport_transition_working
    )


# def test_is_transport_transition_from_working_to_idle(
#     transport_state_working, transport_transition_idle
# ):
#     assert is_transport_transition_from_working_to_idle(
#         transport_state_working, transport_transition_idle
#     )


def test_is_transport_transition_from_pickup_to_transit(
    transport_state_pickup, transport_transition_pickup_to_transit
):
    assert is_transport_transition_from_pickup_to_transit(
        transport_state_pickup, transport_transition_pickup_to_transit
    )


def test_is_transport_transition_from_pickup_to_waitingpickup(
    transport_state_pickup, transport_transition_pickup_to_waitingpickup
):
    assert is_transport_transition_from_pickup_to_waitingpickup(
        transport_state_pickup, transport_transition_pickup_to_waitingpickup
    )


def test_is_transport_transition_from_waitingpickup_to_transit(
    transport_state_waitingpickup, transport_transition_waitingpickup_to_transit
):
    assert is_transport_transition_from_waitingpickup_to_transit(
        transport_state_waitingpickup, transport_transition_waitingpickup_to_transit
    )


# def test_is_transport_transition_from_transit_to_idle(
#     transport_state_transit, transport_transition_idle
# ):
#     assert is_transport_transition_from_transit_to_idle(
#         transport_state_transit, transport_transition_idle
#     )


def test_sorted_by_transport(transport_transition_working, machine_transition_working):
    transitions = (machine_transition_working, transport_transition_working)
    sorted_transitions = sorted_by_transport(transitions)
    assert sorted_transitions == (transport_transition_working, machine_transition_working)


def test_create_transport_location_from_job():
    location = create_transport_location_from_job("m-1", "m-2", "m-3")
    assert location == TransportLocation(progress=0.0, location=("m-1", "m-2", "m-3"))


def test_sorted_done_operations(job_state_done_end_time_10, job_state_done_end_time_5):
    job_states = (job_state_done_end_time_10, job_state_done_end_time_5)
    sorted_operations = sorted_done_operations(job_states)
    assert sorted_operations == (
        job_state_done_end_time_5.operations[0],
        job_state_done_end_time_10.operations[0],
    )
