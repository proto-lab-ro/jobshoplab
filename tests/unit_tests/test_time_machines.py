from jobshoplab.state_machine.time_machines import force_jump_to_event, jump_by_one, jump_to_event
from jobshoplab.types.state_types import NoTime, Time


def test_jump_by_one():
    assert jump_by_one(0, NoTime()) == Time(0)
    assert jump_by_one(0, Time(0)) == Time(1)


def test_jump_to_next_init(default_instance, default_init_state_result, config):
    args = (
        default_init_state_result.state.jobs,
        default_init_state_result.state.machines,
        default_init_state_result.state.transports,
        default_init_state_result.state.buffers,
    )
    assert jump_to_event(
        0,
        default_instance,
        Time(0),
        *args,
        config,
    ) == Time(0)
    assert jump_to_event(0, default_instance, Time(10), *args, config) == Time(10)
    assert jump_to_event(0, default_instance, NoTime(), *args, config) == Time(0)


def test_force_jump_to_event(default_instance, default_init_state):

    assert force_jump_to_event(
        0, Time(0), default_init_state.jobs, default_init_state.transports
    ) == Time(time=1)
    #! Changed behavior of force_jump_to_event
    # assert isinstance(
    #     force_jump_to_event(0, Time(0), default_init_state.jobs, default_init_state.transports),
    #     FailTime,
    # )


# to do test jump_to_event in case of active operations no possible operations and no transport
