from dataclasses import replace

import pytest

from jobshoplab.state_machine.core.state_machine import step
from jobshoplab.state_machine.time_machines import jump_to_event
from jobshoplab.types.action_types import Action, ComponentTransition, ActionFactoryInfo
from jobshoplab.types.instance_config_types import (
    DeterministicTimeConfig,
    JobConfig,
    OperationConfig,
)
from jobshoplab.types.state_types import (
    BufferState,
    BufferStateState,
    JobState,
    MachineState,
    MachineStateState,
    OperationState,
    OperationStateState,
    State,
    Time,
    TransportStateState,
)
from functools import partial


def test_start_teleport_job0_to_machine0(
    default_instance, default_init_state, config, action_start_t0_for_j0
):
    state_result = step(
        loglevel="DEBUG",
        instance=default_instance,
        config=config,
        state=default_init_state,
        action=action_start_t0_for_j0,
    )

    expected_job0 = replace(default_init_state.jobs[0], location="m-0")
    expected_teleporter0 = replace(default_init_state.transports[0])

    assert state_result.state.jobs[0] == expected_job0
    assert state_result.state.transports[0] == expected_teleporter0
    assert state_result.state.time == Time(0)


def test_assign_job1_to_machine0(
    default_instance, default_init_state, config, action_start_job0_on_machine0
):
    state_result = step(
        loglevel="DEBUG",
        instance=default_instance,
        config=config,
        state=default_init_state,
        action=action_start_job0_on_machine0,
    )
    op1_state = replace(
        default_init_state.jobs[0].operations[0],
        operation_state_state=OperationStateState.PROCESSING,
        start_time=Time(0),
        end_time=Time(3),
    )

    assert state_result.state.jobs[0].operations[0] == op1_state

    expected_m0_buffer = replace(
        default_init_state.machines[0].buffer,
        store=(state_result.state.jobs[0].id,),
        state=BufferStateState.FULL,
    )

    expected_machine_0_state = replace(
        default_init_state.machines[0],
        state=MachineStateState.WORKING,
        occupied_till=Time(3),
        buffer=expected_m0_buffer,
    )

    assert state_result.state.machines[0] == expected_machine_0_state
    assert state_result.state.time == Time(0)


def test_step_for_multiple_actions(
    default_instance, default_init_state, config, actions_allowed_at_time_dict
):
    # m2
    # m1 2222
    # m0 00011
    # t  123456789

    state = default_init_state
    for time, action in actions_allowed_at_time_dict.items():
        state_result = step(
            loglevel="DEBUG",
            instance=default_instance,
            config=config,
            state=state,
            action=action,
        )
        state = state_result.state
        if time == 0:
            # m2
            # m1 2222
            # m0 000
            # t  123456789
            assert state_result.state.time == Time(3)

        if time == 3:
            # m2
            # m1 2222
            # m0 00011
            # t  123456789
            assert state_result.state.time == Time(4)

        assert state_result.success


def test_step_for_invalid_first_action(
    default_instance, default_init_state, config, invalid_first_action
):
    state_result = step(
        loglevel="DEBUG",
        instance=default_instance,
        config=config,
        state=default_init_state,
        action=invalid_first_action,
    )
    assert not state_result.success
    assert state_result.state == default_init_state


def test_teleporter(default_instance, default_init_state, config):
    t0_j0 = ComponentTransition(
        component_id="t-0", new_state=TransportStateState.WORKING, job_id="j-0"
    )
    t1_j1 = ComponentTransition(
        component_id="t-1", new_state=TransportStateState.WORKING, job_id="j-1"
    )

    state_result = step(
        loglevel="DEBUG",
        instance=default_instance,
        config=config,
        state=default_init_state,
        action=Action(
            (t0_j0, t1_j1),
            ActionFactoryInfo.Dummy,
            time_machine=jump_to_event,
        ),
    )

    expected_job0 = replace(default_init_state.jobs[0], location="m-0")
    expected_teleporter0 = replace(default_init_state.transports[0])

    expected_job1 = replace(default_init_state.jobs[1], location="m-0")

    assert state_result.state.jobs[0] == expected_job0
    assert state_result.state.jobs[1] == expected_job1
    assert state_result.state.transports[0] == expected_teleporter0
    assert state_result.state.time == Time(0)
