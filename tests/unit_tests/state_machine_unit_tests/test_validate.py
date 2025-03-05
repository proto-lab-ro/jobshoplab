from dataclasses import replace

import pytest

from jobshoplab.state_machine.core.state_machine.validate import (
    is_machine_transition_valid,
    is_transition_valid,
    is_transport_transition_valid,
)
from jobshoplab.types.state_types import MachineStateState, TransportStateState
from jobshoplab.utils.exceptions import InvalidValue


def test_is_machine_transition_valid_idle_to_working(
    default_state_machine_idle,
    machine_state_idle,
    machine_transition_working,
):
    valid, message = is_machine_transition_valid(
        default_state_machine_idle, machine_state_idle, machine_transition_working
    )
    assert valid is True
    assert message == ""


def test_is_machine_transition_valid_working_to_idle(
    default_state_machine_working,
    machine_state_working,
    machine_transition_working_to_idle,
):
    valid, message = is_machine_transition_valid(
        default_state_machine_working,
        machine_state_working,
        machine_transition_working_to_idle,
    )
    assert valid is True
    assert message == ""


def test_is_machine_transition_invalid_state(
    default_state_machine_idle,
    machine_state_idle,
    machine_transition_working_to_idle,
):
    valid, message = is_machine_transition_valid(
        default_state_machine_idle, machine_state_idle, machine_transition_working_to_idle
    )
    assert valid is False
    assert "Invalid transition" in message


def test_is_transport_transition_valid_idle_to_pickup(
    default_state_transport_idle,
    transport_state_idle,
    component_transition_transport_idle_to_working,
):
    valid, message = is_transport_transition_valid(
        default_state_transport_idle,
        transport_state_idle,
        component_transition_transport_idle_to_working,
    )
    assert valid is True
    assert message == ""


def test_is_transport_transition_valid_pickup_to_transit(
    default_state_transport_pickup_ready,
    transport_state_pickup,
    transport_transition_pickup_to_transit,
):
    valid, message = is_transport_transition_valid(
        default_state_transport_pickup_ready,
        transport_state_pickup,
        transport_transition_pickup_to_transit,
    )
    assert valid is True
    assert message == ""


def test_is_transport_transition_invalid_state(
    default_state_transport_idle,
    transport_state_idle,
    transport_transition_idle,
):
    valid, message = is_transport_transition_valid(
        default_state_transport_idle,
        transport_state_idle,
        transport_transition_idle,
    )
    assert valid is False
    assert "Invalid state transition" in message


def test_is_transition_valid_machine(
    default_state_machine_idle,
    machine_transition_working,
):
    valid, message = is_transition_valid(
        "INFO", default_state_machine_idle, machine_transition_working
    )
    assert valid is True
    assert message == ""


def test_is_transition_valid_transport(
    default_state_transport_idle,
    component_transition_transport_idle_to_working,
):
    valid, message = is_transition_valid(
        "INFO", default_state_transport_idle, component_transition_transport_idle_to_working
    )
    assert valid is True
    assert message == ""


def test_is_transition_valid_invalid_component(
    default_state_machine_idle,
    machine_transition_working,
):
    # Modify component_id to be invalid
    invalid_transition = machine_transition_working
    invalid_transition = replace(invalid_transition, component_id="invalid-id")

    with pytest.raises(InvalidValue):
        is_transition_valid("INFO", default_state_machine_idle, invalid_transition)
