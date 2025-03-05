import unittest
from dataclasses import replace

import jobshoplab.types.instance_config_types as config_types

# from jobshoplab.types.state_types import JobState, OperationStateState
import jobshoplab.types.state_types as state_types
from jobshoplab.types.instance_config_types import (
    DeterministicDurationConfig,
    InstanceConfig,
    JobConfig,
    OperationConfig,
    Product,
)
from jobshoplab.utils.exceptions import InvalidValue
from jobshoplab.utils.state_machine_utils import (
    buffer_type_utils,
    job_type_utils,
    machine_type_utils,
)


def test_get_job_state_by_id(default_init_state: state_types.State):

    job1: state_types.JobState = job_type_utils.get_job_state_by_id(default_init_state.jobs, "j-1")
    assert isinstance(job1, state_types.JobState)
    assert job1.id == "j-1"

    with unittest.TestCase().assertRaises(InvalidValue):
        job_type_utils.get_job_state_by_id(default_init_state.jobs, "j-1000")


def test_get_job_config_by_id(default_instance: InstanceConfig):

    o1 = OperationConfig(id="o-1", machine="m-0", duration=DeterministicDurationConfig(duration=3))
    o4 = OperationConfig(id="o-4", machine="m-1", duration=DeterministicDurationConfig(duration=2))
    o7 = OperationConfig(id="o-7", machine="m-2", duration=DeterministicDurationConfig(duration=2))
    product0 = Product(id="p-0", name="Product1")
    expected_job1 = JobConfig(id="j-1", product=product0, operations=(o1, o4, o7), priority=0)

    job1 = job_type_utils.get_job_config_by_id(default_instance.instance.specification, "j-1")
    assert isinstance(job1, JobConfig)
    assert job1 == expected_job1

    with unittest.TestCase().assertRaises(InvalidValue):
        job_type_utils.get_job_config_by_id(default_instance.instance.specification, "j-1000")


def test_get_operation_state_by_id(default_init_state: InstanceConfig):

    operation1 = job_type_utils.get_operation_state_by_id(default_init_state.jobs, "o-0-1")
    assert isinstance(operation1, state_types.OperationState)
    assert operation1.id == "o-0-1"
    assert operation1.operation_state_state == state_types.OperationStateState.IDLE

    with unittest.TestCase().assertRaises(InvalidValue):
        job_type_utils.get_operation_state_by_id(default_init_state.jobs, "o-1-1000")


def test_get_operation_config_by_id(default_instance: InstanceConfig):
    o1 = OperationConfig(
        id="o-0-0", machine="m-0", duration=DeterministicDurationConfig(duration=3)
    )
    operation1 = job_type_utils.get_operation_config_by_id(
        default_instance.instance.specification, "o-0-0"
    )
    assert isinstance(operation1, OperationConfig)
    assert operation1 == o1

    with unittest.TestCase().assertRaises(InvalidValue):
        job_type_utils.get_operation_config_by_id(
            default_instance.instance.specification, "o-0-1000"
        )


def test_get_next_not_done_operation(default_init_state: state_types.State):
    job1 = job_type_utils.get_job_state_by_id(default_init_state.jobs, "j-1")
    operation1 = job_type_utils.get_next_not_done_operation(job1)
    assert isinstance(operation1, state_types.OperationState)
    assert operation1 == job1.operations[0]

    operation1 = replace(
        operation1, operation_state_state=state_types.OperationStateState.PROCESSING
    )
    job1 = replace(job1, operations=(operation1, *job1.operations[1:]))
    operation2 = job_type_utils.get_next_not_done_operation(job1)
    assert operation2 == job1.operations[0]

    operation1 = replace(operation1, operation_state_state=state_types.OperationStateState.DONE)
    job1 = replace(job1, operations=(operation1, *job1.operations[1:]))
    operation2 = job_type_utils.get_next_not_done_operation(job1)
    assert operation2 == job1.operations[1]


def test_get_next_idle_operation(default_init_state: state_types.State):
    job1 = job_type_utils.get_job_state_by_id(default_init_state.jobs, "j-1")
    operation1 = job_type_utils.get_next_idle_operation(job1)
    assert isinstance(operation1, state_types.OperationState)
    assert operation1 == job1.operations[0]

    operation1 = replace(
        operation1, operation_state_state=state_types.OperationStateState.PROCESSING
    )
    job1 = replace(job1, operations=(operation1, *job1.operations[1:]))
    operation2 = job_type_utils.get_next_idle_operation(job1)
    assert operation2 == job1.operations[1]

    operation1 = replace(operation1, operation_state_state=state_types.OperationStateState.DONE)
    job1 = replace(job1, operations=(operation1, *job1.operations[1:]))
    operation2 = job_type_utils.get_next_idle_operation(job1)
    assert operation2 == job1.operations[1]


def test_get_processing_operation(default_init_state: state_types.State):
    job1 = job_type_utils.get_job_state_by_id(default_init_state.jobs, "j-1")

    operation1 = replace(
        job1.operations[0], operation_state_state=state_types.OperationStateState.PROCESSING
    )

    job1 = replace(job1, operations=(operation1, *job1.operations[1:]))

    assert job_type_utils.get_processing_operation(job1) == job1.operations[0]


def test_get_machine_config_by_id(default_instance: InstanceConfig):
    machine0 = machine_type_utils.get_machine_config_by_id(default_instance.machines, "m-0")
    assert isinstance(machine0, config_types.MachineConfig)
    assert machine0.id == "m-0"

    with unittest.TestCase().assertRaises(InvalidValue):
        machine_type_utils.get_machine_config_by_id(default_instance.machines, "m-1000")


def test_put_in_buffer(default_instance: InstanceConfig, default_init_state: state_types.State):
    m0_state = machine_type_utils.get_machine_state_by_id(default_init_state.machines, "m-0")
    m0_conf = machine_type_utils.get_machine_config_by_id(default_instance.machines, "m-0")

    buffer_state = m0_state.buffer
    buffer_config = m0_conf.buffer

    # TODO: assert job_state
    buffer_state, job_state = buffer_type_utils.put_in_buffer(
        buffer_state, buffer_config, default_init_state.jobs[0]
    )
    expected_buffer = replace(buffer_state, store=("j-0",))
    assert buffer_state == expected_buffer


def test_remove_from_buffer(
    default_instance: InstanceConfig, default_init_state: state_types.State
):
    m0_state = machine_type_utils.get_machine_state_by_id(default_init_state.machines, "m-0")
    m0_conf = machine_type_utils.get_machine_config_by_id(default_instance.machines, "m-0")

    buffer_state = m0_state.buffer
    buffer_config = m0_conf.buffer

    # TODO: assert job state
    buffer_state, job_state = buffer_type_utils.put_in_buffer(
        buffer_state, buffer_config, default_init_state.jobs[0]
    )
    buffer_state = buffer_type_utils.remove_from_buffer(buffer_state, "j-0")
    expected_buffer = replace(buffer_state, store=())
    assert buffer_state == expected_buffer
    with unittest.TestCase().assertRaises(ValueError):
        buffer_type_utils.remove_from_buffer(buffer_state, "j-0")
    with unittest.TestCase().assertRaises(ValueError):
        buffer_type_utils.remove_from_buffer(buffer_state, "j-1000")


# TODO
def test_is_next_operation_free():
    # possible_transition_utils.is_job_next_operation_free()
    pass


def test_is_job_at_machine():
    # possible_transition_utils.is_job_at_machine()
    pass


def test_is_action_possible():
    # possible_transition_utils.is_action_possible()
    pass


def test_get_possible_transports():
    # possible_transition_utils.get_possible_transports()
    pass


def test_get_num_possible_events():
    # possible_transition_utils.get_num_possible_events()
    pass


# ...
