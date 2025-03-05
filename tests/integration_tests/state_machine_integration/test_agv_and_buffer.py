from functools import partial

from jobshoplab.state_machine.core.state_machine.state import step
from jobshoplab.state_machine.time_machines import jump_by_one
from jobshoplab.types.action_types import Action, ComponentTransition, ActionFactory
from jobshoplab.types.instance_config_types import InstanceConfig
from jobshoplab.types.state_types import (
    BufferStateState,
    OperationStateState,
    State,
    TransportStateState,
)


def get_next_action(state: State):
    transitions = tuple()
    for agv in state.transports:
        if agv.state == TransportStateState.IDLE:
            for job in state.jobs:
                is_processing = any(
                    operation.operation_state_state
                    in [OperationStateState.PROCESSING, OperationStateState.TRANSPORT]
                    for operation in job.operations
                )
                is_done = all(
                    operation.operation_state_state in [OperationStateState.DONE]
                    for operation in job.operations
                )
                in_transitions = any(
                    (
                        transition.component_id == agv.id or transition.job_id == job.id
                        for transition in transitions
                    )
                )
                if not is_processing and not is_done and not in_transitions:
                    transitions += (
                        ComponentTransition(
                            component_id=agv.id,
                            new_state=TransportStateState.WORKING,
                            job_id=job.id,
                        ),
                    )
    if len(transitions) > 0:
        return Action(transitions, action_factory_info=ActionFactoryInfo.Valid)
    return Action(tuple(), action_factory_info=ActionFactoryInfo.NoOperation)


class AgvAndBufferAssertions:

    def __init__(self):
        self.max_i = 10
        self.min_i = 0

    @staticmethod
    def assert_1(state: State):
        assert state.time.time == 1
        assert state.transports[0].state == TransportStateState.WORKING
        assert state.transports[1].state == TransportStateState.WORKING
        assert state.transports[2].state == TransportStateState.WORKING
        assert state.buffers[0].state == BufferStateState.NOT_EMPTY
        assert state.buffers[1].state == BufferStateState.EMPTY
        assert state.buffers[0].store == ("j-0", "j-1", "j-2")
        assert state.buffers[1].store == ()

    @staticmethod
    def assert_2(state: State):
        pass

    def get_assert_for_i(self, i, state):
        if hasattr(self, f"assert_{i}"):
            return getattr(self, f"assert_{i}")(state)
        else:
            return


def test_agv_and_buffer(
    agv_and_buffer_state,
    # target_agv_and_buffer_states,
    agv_and_buffer_instance,
    config,
):
    time_machine = jump_by_one
    assertions = AgvAndBufferAssertions()
    for i in range(assertions.max_i):
        next_action = get_next_action(agv_and_buffer_state)
        _agv_and_buffer_state = step(
            "info",
            agv_and_buffer_instance,
            config,
            agv_and_buffer_state,
            action=next_action,
            time_machine=time_machine,
        )
        assertions.get_assert_for_i(i, _agv_and_buffer_state.state)
