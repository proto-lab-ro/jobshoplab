import pytest

from jobshoplab.env.factories.actions import BinaryJobActionFactory
from jobshoplab.state_machine.time_machines import jump_to_event
from jobshoplab.types.action_types import Action, ActionFactoryInfo, ComponentTransition
from jobshoplab.types.state_types import MachineStateState
from jobshoplab.utils.exceptions import ActionOutOfActionSpace


def test_binary_action_factory(default_init_state_result, default_instance, config):
    action_factory = BinaryJobActionFactory(0, config, default_instance)
    action0 = 0
    action1 = 1
    action10 = 10
    i_action0 = action_factory.interpret(action0, default_init_state_result)
    i_action1 = action_factory.interpret(action1, default_init_state_result)
    assert i_action0 == Action(
        transitions=(),
        action_factory_info=ActionFactoryInfo.NoOperation,
        time_machine=jump_to_event,
    )
    assert i_action1 == Action(
        transitions=(
            ComponentTransition(
                component_id="m-0",
                new_state=MachineStateState.WORKING,
                job_id="j-0",
            ),
        ),
        action_factory_info=ActionFactoryInfo.Valid,
        time_machine=jump_to_event,
    )
    with pytest.raises(ActionOutOfActionSpace):
        _ = action_factory.interpret(action10, default_init_state_result)


# def test_multidiscrete_action_factory():
#     raise NotImplementedError
