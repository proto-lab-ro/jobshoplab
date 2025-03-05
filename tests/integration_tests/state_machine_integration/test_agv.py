from dataclasses import replace

import pytest

from jobshoplab.state_machine.core.state_machine import step
from jobshoplab.state_machine.time_machines import jump_to_event
from jobshoplab.types.action_types import Action, ComponentTransition, ActionFactory
from jobshoplab.types.instance_config_types import (
    DeterministicDurationConfig,
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
    TransportLocation,
    TransportStateState,
)


def test_start_agv_job0_to_machine0(agv_instance, default_init_state, config, agv_transition):
    # Move j0 to m1 with t-0

    state_result = step(
        loglevel="DEBUG",
        instance=agv_instance,
        config=config,
        state=default_init_state,
        action=Action(
            (agv_transition,), action_factory_info=ActionFactory.Dummy, time_machine=jump_to_event
        ),
    )

    # t-0 moves from b-0 to m-0 and put j-0 in buffer (b-1) with no travel time
    assert state_result.state.time == Time(0)
    assert state_result.state.jobs[0].location == "b-1"
    assert state_result.state.transports[0].location.location == "m-0"
    assert state_result.state.transports[0].state == TransportStateState.IDLE


def test_start_start_j0_at_m0(agv_instance, default_init_state, config, agv_transition):

    comp_transition = ComponentTransition(
        component_id="m-0", new_state=MachineStateState.WORKING, job_id="j-0"
    )

    job0 = replace(default_init_state.jobs[0], location="m-1")
    default_init_state = replace(default_init_state, jobs=(job0, *default_init_state.jobs[1:]))

    action_do_job0 = Action(transitions=(comp_transition,), action_factory_info=ActionFactory.Dummy)

    with pytest.raises(ValueError):
        state_result = step(
            loglevel="DEBUG",
            instance=agv_instance,
            config=config,
            state=default_init_state,
            action=action_do_job0,
            time_machine=jump_to_event,
        )

    t0_j0 = agv_transition

    action_t0_jo = Action(transitions=(t0_j0,), action_factory_info=ActionFactory.Dummy)

    state_result = step(
        loglevel="DEBUG",
        instance=agv_instance,
        config=config,
        state=default_init_state,
        action=action_t0_jo,
        time_machine=jump_to_event,
    )

    assert state_result.state.jobs[0].location == "t-0"
    assert state_result.state.transports[0].occupied_till.time == 5

    state_result = replace(state_result, state=replace(state_result.state, time=Time(5)))

    # GOTO TIME 5 and check if transport jobs is finished
    state_result = step(
        loglevel="DEBUG",
        instance=agv_instance,
        config=config,
        state=state_result.state,
        action=Action((), action_factory_info=ActionFactory.Dummy),
        time_machine=jump_to_event,
    )

    assert state_result.state.time == Time(5)
    assert state_result.state.transports[0].state == TransportStateState.IDLE
    assert state_result.state.transports[0].location.location == "m-0"
    assert state_result.state.transports[0].location.progress == 0
    assert state_result.state.jobs[0].location == "m-0"

    # Start job0 on m0
    state_result = step(
        loglevel="DEBUG",
        instance=agv_instance,
        config=config,
        state=state_result.state,
        action=action_do_job0,
        time_machine=jump_to_event,
    )

    op1_state = replace(
        default_init_state.jobs[0].operations[0],
        operation_state_state=OperationStateState.PROCESSING,
        start_time=Time(5),
        end_time=Time(8),
    )

    assert state_result.state.jobs[0].operations[0] == op1_state
