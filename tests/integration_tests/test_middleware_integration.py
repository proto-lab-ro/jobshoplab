from functools import partial
from unittest.mock import Mock

from jobshoplab.env.factories.actions import BinaryJobActionFactory
from jobshoplab.env.factories.observations import BinaryActionObservationFactory
from jobshoplab.state_machine.core.state_machine import step
from jobshoplab.state_machine.middleware.middleware import EventBasedBinaryActionMiddleware
from jobshoplab.state_machine.time_machines import force_jump_to_event, jump_to_event
from jobshoplab.types import Time
from jobshoplab.types.action_types import Action, ComponentTransition, ActionFactoryInfo
from jobshoplab.types.state_types import BufferStateState, MachineStateState, StateMachineResult


def test_event_based_middleware_integration_reset(config, default_instance, default_init_state):
    middelware = EventBasedBinaryActionMiddleware(
        0,
        config=config,
        instance=default_instance,
        init_state=default_init_state,
        state_machine_step=step,
        truncation_joker=1,
        truncation_active=True,
        observation_factory=BinaryActionObservationFactory(0, config, default_instance),
        action_factory=BinaryJobActionFactory(0, config, default_instance),
    )
    state_result, observation = middelware.reset(default_init_state)

    # The state should be the same as the initial state
    assert state_result.state.buffers[0].state == BufferStateState.EMPTY
    assert state_result.state.machines[0].prebuffer.store == ("j-0", "j-1")
    assert state_result.state.machines[1].prebuffer.store == ("j-2",)
    assert state_result.state.machines[2].prebuffer.store == ()

    # Whe should get possible transitions
    assert len(state_result.possible_transitions) > 0


def test_event_based_middleware_integration_noop(
    config, default_instance, default_init_state_result
):
    middelware = EventBasedBinaryActionMiddleware(
        0,
        config=config,
        instance=default_instance,
        init_state=default_init_state_result.state,
        state_machine_step=step,
        truncation_joker=1,
        truncation_active=True,
        observation_factory=BinaryActionObservationFactory(0, config, default_instance),
        action_factory=BinaryJobActionFactory(0, config, default_instance),
    )

    no_op_action = 0
    state_result, observation = middelware.step(default_init_state_result, no_op_action)
    assert default_init_state_result.state == state_result.state
    assert len(state_result.possible_transitions) == 2

    state_result, observation = middelware.step(state_result, no_op_action)
    assert default_init_state_result.state == state_result.state
    assert len(state_result.possible_transitions) == 1


def test_simple_event_based_middle_ware_mixed_actions(config, default_instance, default_init_state):

    middelware = EventBasedBinaryActionMiddleware(
        0,
        config=config,
        instance=default_instance,
        init_state=default_init_state,
        state_machine_step=step,
        truncation_joker=0,
        truncation_active=True,
        observation_factory=BinaryActionObservationFactory(0, config, default_instance),
        action_factory=BinaryJobActionFactory(0, config, default_instance),
    )

    state, _ = middelware.reset(default_init_state)
    actions = [
        (1, 1, False),  # -> 1
        (3, 0, False),  # -> 3 reset
        (1, 1, False),  # -> 1
        (3, 0, False),  # -> 3 reset
        (2, 0, False),  # -> 2
        (1, 0, False),  # -> 1
        (3, 0, True),  # -> 3 reset and truncation
    ]
    middelware.truncation_joker = 0
    for num_pos_actions, action, _truncation in actions:
        state, _ = middelware.step(state, action)
        truncated = middelware.is_truncated()
        assert num_pos_actions == len(state.possible_transitions)
        assert truncated == _truncation


def test_simple_event_based_middle_ware_truncation1(config, default_instance, default_init_state):
    middelware = EventBasedBinaryActionMiddleware(
        0,
        config=config,
        instance=default_instance,
        init_state=default_init_state,
        state_machine_step=step,
        truncation_joker=0,
        truncation_active=True,
        observation_factory=BinaryActionObservationFactory(0, config, default_instance),
        action_factory=BinaryJobActionFactory(0, config, default_instance),
    )

    state, _ = middelware.reset(default_init_state)
    actions = [(0, False), (0, False), (0, True)]
    middelware.truncation_joker = 0
    for action, _truncation in actions:
        state, _ = middelware.step(state, action)
        truncated = middelware.is_truncated()
        assert truncated == _truncation


def test_simple_event_based_middle_ware_active_actions(
    config, default_instance, default_init_state
):
    middelware = EventBasedBinaryActionMiddleware(
        0,
        config=config,
        instance=default_instance,
        init_state=default_init_state,
        state_machine_step=step,
        truncation_joker=0,
        truncation_active=True,
        observation_factory=BinaryActionObservationFactory(0, config, default_instance),
        action_factory=BinaryJobActionFactory(0, config, default_instance),
    )

    state, _ = middelware.reset(default_init_state)
    num_actions_till_done = 9
    for i in range(num_actions_till_done):
        state, _ = middelware.step(state, 1)
    assert len(state.possible_transitions) == 0
    assert (
        len(state.state.buffers[1].store) == 3
    )  #! TODO: Jonathan -> Put job in output buffer if done
