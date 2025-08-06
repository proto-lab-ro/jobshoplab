import sys
from dataclasses import replace

import pytest

from jobshoplab.state_machine.time_machines import jump_to_event
from jobshoplab.types.action_types import (
    Action,
    ActionFactoryInfo,
    ComponentTransition,
    TransportStateState,
)
from jobshoplab.types.instance_config_types import (
    BufferConfig,
    BufferRoleConfig,
    BufferTypeConfig,
    DeterministicTimeConfig,
    InstanceConfig,
)
from jobshoplab.types.state_types import BufferState, BufferStateState, State


@pytest.fixture
def agv_instance(default_instance_with_intralogistics):
    _instance = default_instance_with_intralogistics
    return _instance


@pytest.fixture
def agv_and_buffer_instance(default_instance_with_intralogistics_and_buffer: InstanceConfig):
    _instance = default_instance_with_intralogistics_and_buffer
    # add buffers to the instance
    _instance = replace(
        _instance,
        buffers=(
            # start buffer
            BufferConfig(
                id="b-100",
                type=BufferTypeConfig.FLEX_BUFFER,
                capacity=sys.maxsize,
                resources=(),
                description="start buffer",
                role=BufferRoleConfig.INPUT,
            ),
            # end buffer
            BufferConfig(
                id="b-101",
                type=BufferTypeConfig.FLEX_BUFFER,
                capacity=sys.maxsize,
                resources=(),
                description="end buffer",
                role=BufferRoleConfig.OUTPUT,
            ),
        ),
    )
    ## add traveltimes

    _travel_times = _instance.logistics.travel_times
    for machine in _instance.machines:
        s_time = int(machine.id.split("-")[-1]) + 1
        e_time = DeterministicTimeConfig(time=3 - s_time)
        s_time = DeterministicTimeConfig(time=s_time)
        _travel_times[("b-100", machine.id)] = s_time
        _travel_times[(machine.id, "b-100")] = s_time
        _travel_times[("b-101", machine.id)] = e_time
        _travel_times[(machine.id, "b-101")] = e_time

    _instance = replace(
        _instance, logistics=replace(_instance.logistics, travel_times=_travel_times)
    )

    return _instance


@pytest.fixture
def agv_transition():
    return ComponentTransition(
        component_id="t-0", new_state=TransportStateState.WORKING, job_id="j-0"
    )


@pytest.fixture
def agv_action(agv_transition):
    return Action(
        transitions=(agv_transition,),
        action_factory_info=ActionFactoryInfo.Valid,
        time_machine=jump_to_event,
    )


@pytest.fixture
def agv_state(default_init_state):
    return default_init_state


@pytest.fixture
def target_agv_state(agv_state):
    pass


@pytest.fixture
def agv_and_buffer_state(agv_state: State):
    # add start and end buffer
    agv_state = replace(
        agv_state,
        buffers=agv_state.buffers
        + (
            BufferState(id="b-100", state=BufferStateState.NOT_EMPTY, store=("j-0", "j-1", "j-2")),
            BufferState(id="b-101", state=BufferStateState.EMPTY, store=()),
        ),
    )
    # put jobs into the buffer
    agv_state = replace(
        agv_state,
        jobs=(
            replace(agv_state.jobs[0], location="b-100"),
            replace(agv_state.jobs[1], location="b-100"),
            replace(agv_state.jobs[2], location="b-100"),
        ),
    )
    return agv_state
