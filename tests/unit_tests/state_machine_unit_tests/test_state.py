from dataclasses import replace
from unittest.mock import Mock

import pytest

from jobshoplab import JobShopLabEnv
from jobshoplab.state_machine.core.state_machine.state import (
    apply_transition,
    is_done,
    process_state_transitions,
    step,
)
from jobshoplab.types import NoTime, State, Time
from jobshoplab.types.action_types import Action, ComponentTransition, ActionFactory
from jobshoplab.types.state_types import (
    MachineStateState,
    OperationStateState,
    StateMachineResult,
    TransportStateState,
)
from jobshoplab.utils.exceptions import (
    InvalidValue,
    NotImplementedError,
    UnsuccessfulStateMachineResult,
)


def test_is_done_with_done_job(job_state_done):

    state = State(
        time=Time(0),
        jobs=(job_state_done,),
        machines=(),
        transports=(),
        buffers=(),
    )

    state_result = Mock()
    state_result.state = state

    assert is_done(state_result) is True


def test_is_done_with_processing_job(job_state_processing):
    state = State(
        time=Time(0),
        jobs=(job_state_processing,),
        machines=(),
        transports=(),
        buffers=(),
    )

    state_result = Mock()
    state_result.state = state

    assert is_done(state_result) is False


def test_apply_transition_machine(
    default_state_machine_idle, default_instance, machine_transition_working
):
    result = apply_transition(
        "DEBUG", default_state_machine_idle, default_instance, machine_transition_working
    )
    assert isinstance(result, State)
    assert result.machines[0].state == MachineStateState.WORKING


def test_apply_transition_transport(
    default_state_transport_idle, default_instance, component_transition_transport_idle_to_working
):
    result = apply_transition(
        "DEBUG",
        default_state_transport_idle,
        default_instance,
        component_transition_transport_idle_to_working,
    )
    assert isinstance(result, State)
    assert result.transports[0].state == TransportStateState.PICKUP


def test_apply_transition_invalid_component():
    invalid_transition = ComponentTransition(
        component_id="invalid-1", new_state=MachineStateState.WORKING, job_id="j-1"
    )
    state = State(time=Time(0), jobs=(), machines=(), transports=(), buffers=())

    with pytest.raises(InvalidValue):
        apply_transition("DEBUG", state, None, invalid_transition)


def test_process_state_transitions_empty():
    state = State(time=Time(0), jobs=(), machines=(), transports=(), buffers=())
    result = process_state_transitions((), state, None, "DEBUG")
    assert result.state == state
    assert not result.errors


def test_process_state_transitions_valid(
    default_state_machine_idle, default_instance, machine_transition_working
):
    transitions = (machine_transition_working,)
    result = process_state_transitions(
        transitions, default_state_machine_idle, default_instance, "DEBUG"
    )
    assert not result.errors
    assert result.state.machines[0].state == MachineStateState.WORKING


def test_process_state_transitions_invalid(
    default_state_machine_working, default_instance, machine_transition_working
):
    # Try to transition from WORKING to WORKING (invalid)
    transitions = (machine_transition_working,)
    result = process_state_transitions(
        transitions, default_state_machine_working, default_instance, "DEBUG"
    )
    assert result.errors
    assert "Transition error" in result.errors[0]


def test_step_successful(default_state_machine_idle, default_instance, machine_transition_working):
    def mock_time_machine(*args, **kwargs):
        return Time(2)

    action = Action(
        transitions=(machine_transition_working,),
        action_factory_info=ActionFactoryInfo.Valid,
        time_machine=mock_time_machine,
    )
    config = None  # Add config if needed

    result = step("DEBUG", default_instance, config, default_state_machine_idle, action)
    assert result.success
    assert result.state.machines[0].state == MachineStateState.WORKING


def test_step_transition_error(
    default_state_machine_working, default_instance, machine_transition_working
):
    def mock_time_machine(*args, **kwargs):
        return Time(10)

    # Try invalid transition
    action = Action(
        transitions=(machine_transition_working,),
        action_factory_info=ActionFactoryInfo.Valid,
        time_machine=mock_time_machine,
    )
    config = None

    result = step("DEBUG", default_instance, config, default_state_machine_working, action)
    assert not result.success
    assert "Transition errors" in result.message


def test_step_completion(default_instance, job_state_done, machine_state_idle):
    state = State(
        time=Time(0),
        jobs=(job_state_done,),
        machines=(machine_state_idle,),
        transports=(),
        buffers=(),
    )

    def mock_time_machine(*args, **kwargs):
        return Time(10)

    action = Action(
        transitions=(),
        action_factory_info=ActionFactoryInfo.Valid,
        time_machine=mock_time_machine,
    )
    config = None

    result = step("DEBUG", default_instance, config, state, action)
    assert result.success
    assert result.message == "Done"


# def test_operation_states(config_3x3_transport):
#     """
#     BUG: OperationStateState.Transport is not in operation_states
#     """
#     env = JobShopLabEnv(config=config_3x3_transport)
#     done = False
#     operation_states = []
#     while not done:
#         _, _, term, trunc, _ = env.step(1)
#         done = term or trunc
#     for state_result in env.history:
#         state = state_result.state
#         for job in state.jobs:
#             for operation in job.operations:
#                 operation_states.append(operation.operation_state_state)
#     assert OperationStateState.TRANSPORT in operation_states
#     assert OperationStateState.PROCESSING in operation_states
#     assert OperationStateState.IDLE in operation_states
#     assert OperationStateState.DONE in operation_states
