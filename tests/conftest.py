import sys
import tempfile
from collections import OrderedDict
from dataclasses import replace
from pathlib import Path

import gymnasium as gym
import numpy as np
import pytest
from heracless import load_config

from jobshoplab.state_machine.time_machines import jump_to_event
from jobshoplab.types.action_types import Action, ActionFactoryInfo, ComponentTransition
from jobshoplab.types.instance_config_types import (
    BufferConfig,
    BufferRoleConfig,
    BufferTypeConfig,
    DeterministicTimeConfig,
    InstanceConfig,
    JobConfig,
    LogisticsConfig,
    MachineConfig,
    OperationConfig,
    ProblemInstanceConfig,
    ProblemInstanceTypeConfig,
    Product,
    TransportConfig,
    TransportTypeConfig,
)
from jobshoplab.types.state_types import (
    BufferState,
    BufferStateState,
    JobState,
    MachineState,
    MachineStateState,
    NoTime,
    OperationState,
    OperationStateState,
    State,
    StateMachineResult,
    Time,
    TransportLocation,
    TransportState,
    TransportStateState,
)


@pytest.fixture
def minimal_instance_dict():
    return {
        "instance_config": {
            "description": "dummy instance with 3 products, machines, and 9 operations",
            "instance": {
                "specification": """
                    (m0,t)|(m1,t)|(m2,t)
                    j0|(0,3) (1,2) (2,2)
                    j1|(0,2) (2,1) (1,4)
                    j2|(1,4) (2,3) (0,3)
                """
            },
        },
    }


@pytest.fixture
def minimal_instance_dict_with_intralogistics():
    return {
        "instance_config": {
            "description": "dummy instance with 3 products, machines, and 9 operations",
            "instance": {
                "specification": """
                    (m0,t)|(m1,t)|(m2,t)
                    j0|(0,3) (1,2) (2,2)
                    j1|(0,2) (2,1) (1,4)
                    j2|(1,4) (2,3) (0,3)
                """,
            },
            "logistics": {
                "type": "agv",
                "amount": 3,
                "specification": """
                    m-0|m-1|m-2|in-buf|out-buf
                    m-0|0 5 4 0 0
                    m-1|5 0 2 0 0
                    m-2|4 2 0 0 0
                    in-buf|0 0 0 0 0
                    out-buf|0 0 0 0 0
                """,
            },
        },
        "init_state": {
            "t-0": {"location": "m-1"},
            "t-1": {"location": "m-2"},
            "t-2": {"location": "m-2"},
        },
    }


@pytest.fixture
def test_yaml_instance_dir():
    return Path("tests/data/jssp_instances/test_instance.yaml")


@pytest.fixture
def test_spec_instance_dir():
    return Path("data/jssp_instances/spec_files/3x3")


@pytest.fixture
def config():
    temp_file = tempfile.NamedTemporaryFile(delete=False).name
    config = load_config(Path("tests/data/config/test_config0.yaml"), Path(temp_file), False)
    return config


@pytest.fixture
def config_simple_3x3():
    temp_file = tempfile.NamedTemporaryFile(delete=False).name
    config = load_config(
        Path("tests/data/config/test_config_end_to_end_3x3.yaml"), Path(temp_file), True
    )
    return config


@pytest.fixture
def config_3x3_transport():
    temp_file = tempfile.NamedTemporaryFile(delete=False).name
    config = load_config(
        Path("tests/data/config/test_config_end_to_end_transport.yaml"), Path(temp_file), True
    )
    return config


@pytest.fixture
def config_full_feature_3x3():
    """Configuration for full feature 3x3 instance with stochastic elements"""
    temp_file = tempfile.NamedTemporaryFile(delete=False).name
    # Use the test_config_end_to_end.yaml with our special instance
    config = load_config(
        Path("tests/data/config/test_config_end_to_end.yaml"), Path(temp_file), True
    )

    # Override the instance path
    from dataclasses import replace

    config = replace(
        config,
        compiler=replace(
            config.compiler,
            dsl_repository=replace(
                config.compiler.dsl_repository,
                dir="tests/data/jssp_instances/full_feature_3x3_instance.yaml",
            ),
        ),
    )
    return config


@pytest.fixture
def default_products() -> tuple[Product, Product, Product]:
    product0 = Product(id="p-0", name="Product1")
    product1 = Product(id="p-1", name="Product2")
    product2 = Product(id="p-2", name="Product3")
    return product0, product1, product2


@pytest.fixture
def default_tools() -> tuple[str, str, str]:
    return "tl-0", "tl-1", "tl-2"


@pytest.fixture
def default_setup_times(
    default_tools,
) -> dict[tuple[Product, Product], DeterministicTimeConfig]:
    tool0, tool1, tool2 = default_tools
    return {
        (tool0, tool0): DeterministicTimeConfig(0),
        (tool1, tool1): DeterministicTimeConfig(0),
        (tool2, tool2): DeterministicTimeConfig(0),
        (tool0, tool1): DeterministicTimeConfig(0),
        (tool1, tool0): DeterministicTimeConfig(0),
        (tool0, tool2): DeterministicTimeConfig(0),
        (tool2, tool0): DeterministicTimeConfig(0),
        (tool1, tool2): DeterministicTimeConfig(0),
        (tool2, tool1): DeterministicTimeConfig(0),
    }


@pytest.fixture
def default_machines(default_setup_times) -> tuple[MachineConfig, MachineConfig, MachineConfig]:
    _inf = sys.maxsize
    machine0 = MachineConfig(
        id="m-0",
        outages=(),
        setup_times=default_setup_times,  # Using setup_times here
        prebuffer=BufferConfig(
            id="b-0",
            type=BufferTypeConfig.FLEX_BUFFER,
            capacity=_inf,
            resources=(),
            parent="m-0",
            role=BufferRoleConfig.COMPONENT,
        ),
        postbuffer=BufferConfig(
            id="b-1",
            type=BufferTypeConfig.FLEX_BUFFER,
            capacity=_inf,
            resources=(),
            parent="m-0",
            role=BufferRoleConfig.COMPONENT,
        ),
        batches=1,
        resources=(),
        buffer=BufferConfig(
            id="b-2",
            type=BufferTypeConfig.FLEX_BUFFER,
            capacity=1,
            resources=(),
            parent="m-0",
            role=BufferRoleConfig.COMPONENT,
        ),
    )
    machine1 = MachineConfig(
        id="m-1",
        outages=(),
        setup_times=default_setup_times,  # Using setup_times here
        prebuffer=BufferConfig(
            id="b-3",
            type=BufferTypeConfig.FLEX_BUFFER,
            capacity=_inf,
            resources=(),
            parent="m-1",
            role=BufferRoleConfig.COMPONENT,
        ),
        postbuffer=BufferConfig(
            id="b-4",
            type=BufferTypeConfig.FLEX_BUFFER,
            capacity=_inf,
            resources=(),
            parent="m-1",
            role=BufferRoleConfig.COMPONENT,
        ),
        batches=1,
        resources=(),
        buffer=BufferConfig(
            id="b-5",
            type=BufferTypeConfig.FLEX_BUFFER,
            capacity=1,
            resources=(),
            parent="m-1",
            role=BufferRoleConfig.COMPONENT,
        ),
    )
    machine2 = MachineConfig(
        id="m-2",
        outages=(),
        setup_times=default_setup_times,  # Using setup_times here
        prebuffer=BufferConfig(
            id="b-6",
            type=BufferTypeConfig.FLEX_BUFFER,
            capacity=_inf,
            resources=(),
            parent="m-2",
            role=BufferRoleConfig.COMPONENT,
        ),
        postbuffer=BufferConfig(
            id="b-7",
            type=BufferTypeConfig.FLEX_BUFFER,
            capacity=_inf,
            resources=(),
            parent="m-2",
            role=BufferRoleConfig.COMPONENT,
        ),
        batches=1,
        resources=(),
        buffer=BufferConfig(
            id="b-8",
            type=BufferTypeConfig.FLEX_BUFFER,
            capacity=1,
            resources=(),
            parent="m-2",
            role=BufferRoleConfig.COMPONENT,
        ),
    )
    return machine0, machine1, machine2


@pytest.fixture
def default_buffer() -> tuple[BufferConfig, BufferConfig]:
    return (
        BufferConfig(
            id="b-12",
            type=BufferTypeConfig.FLEX_BUFFER,
            capacity=sys.maxsize,
            resources=(),
            parent=None,
            description="input buffer",
            role=BufferRoleConfig.INPUT,
        ),
        BufferConfig(
            id="b-13",
            type=BufferTypeConfig.FLEX_BUFFER,
            capacity=sys.maxsize,
            resources=(),
            parent=None,
            description="output buffer",
            role=BufferRoleConfig.OUTPUT,
        ),
    )


@pytest.fixture
def default_jobs(default_products, default_machines) -> tuple[JobConfig, ...]:
    product0, product1, product2 = default_products
    machine0, machine1, machine2 = default_machines
    operation0 = OperationConfig(
        id="o-0-0", machine=machine0.id, duration=DeterministicTimeConfig(time=3), tool="tl-0"
    )
    operation1 = OperationConfig(
        id="o-0-1", machine=machine0.id, duration=DeterministicTimeConfig(time=2), tool="tl-0"
    )
    operation2 = OperationConfig(
        id="o-0-2", machine=machine1.id, duration=DeterministicTimeConfig(time=4), tool="tl-0"
    )
    operation3 = OperationConfig(
        id="o-1-3", machine=machine1.id, duration=DeterministicTimeConfig(time=2), tool="tl-0"
    )
    operation4 = OperationConfig(
        id="o-1-4", machine=machine2.id, duration=DeterministicTimeConfig(time=1), tool="tl-0"
    )
    operation5 = OperationConfig(
        id="o-1-5", machine=machine2.id, duration=DeterministicTimeConfig(time=3), tool="tl-0"
    )
    operation6 = OperationConfig(
        id="o-2-6", machine=machine2.id, duration=DeterministicTimeConfig(time=2), tool="tl-0"
    )
    operation7 = OperationConfig(
        id="o-2-7", machine=machine1.id, duration=DeterministicTimeConfig(time=4), tool="tl-0"
    )
    operation8 = OperationConfig(
        id="o-2-8", machine=machine0.id, duration=DeterministicTimeConfig(time=3), tool="tl-0"
    )

    job1 = JobConfig(
        id="j-0", product=product0, operations=(operation0, operation3, operation6), priority=0
    )
    job2 = JobConfig(
        id="j-1", product=product1, operations=(operation1, operation4, operation7), priority=0
    )
    job3 = JobConfig(
        id="j-2", product=product2, operations=(operation2, operation5, operation8), priority=0
    )
    return job1, job2, job3


@pytest.fixture
def default_transports() -> tuple[TransportConfig, ...]:
    return tuple(
        TransportConfig(
            id=f"t-{i}",
            type=TransportTypeConfig.AGV,
            outages=tuple(),
            resources=(),
            buffer=BufferConfig(
                id=f"b-{9 + i}",
                type=BufferTypeConfig.FLEX_BUFFER,
                capacity=1,
                resources=(),
                parent=f"t-{i}",
                description="AGV buffer",
                role=BufferRoleConfig.COMPONENT,
            ),
        )
        for i in range(3)
    )


@pytest.fixture
def default_logistics(default_machines, default_buffer) -> LogisticsConfig:
    machine0, machine1, machine2 = default_machines
    input_buffer_id = "b-12"  # default_buffer[0].id
    output_buffer_id = "b-13"  # default_buffer[1].id
    return LogisticsConfig(
        capacity=sys.maxsize,
        travel_times={
            (machine0.id, machine0.id): DeterministicTimeConfig(0),
            (machine1.id, machine1.id): DeterministicTimeConfig(0),
            (machine2.id, machine2.id): DeterministicTimeConfig(0),
            (machine0.id, machine1.id): DeterministicTimeConfig(0),
            (machine1.id, machine0.id): DeterministicTimeConfig(0),
            (machine0.id, machine2.id): DeterministicTimeConfig(0),
            (machine2.id, machine0.id): DeterministicTimeConfig(0),
            (machine1.id, machine2.id): DeterministicTimeConfig(0),
            (machine2.id, machine1.id): DeterministicTimeConfig(0),
            (input_buffer_id, machine0.id): DeterministicTimeConfig(0),
            (input_buffer_id, machine1.id): DeterministicTimeConfig(0),
            (input_buffer_id, machine2.id): DeterministicTimeConfig(0),
            (machine0.id, input_buffer_id): DeterministicTimeConfig(0),
            (machine2.id, input_buffer_id): DeterministicTimeConfig(0),
            (machine1.id, input_buffer_id): DeterministicTimeConfig(0),
            (output_buffer_id, machine0.id): DeterministicTimeConfig(0),
            (output_buffer_id, machine1.id): DeterministicTimeConfig(0),
            (output_buffer_id, machine2.id): DeterministicTimeConfig(0),
            (machine0.id, output_buffer_id): DeterministicTimeConfig(0),
            (machine1.id, output_buffer_id): DeterministicTimeConfig(0),
            (machine2.id, output_buffer_id): DeterministicTimeConfig(0),
            (input_buffer_id, output_buffer_id): DeterministicTimeConfig(0),
            (output_buffer_id, input_buffer_id): DeterministicTimeConfig(0),
            (input_buffer_id, input_buffer_id): DeterministicTimeConfig(0),
            (output_buffer_id, output_buffer_id): DeterministicTimeConfig(0),
        },
    )


@pytest.fixture
def default_instance(
    default_machines, default_jobs, default_transports, default_logistics, default_buffer
) -> InstanceConfig:
    machine0, machine1, machine2 = default_machines

    logistics = default_logistics
    # (m0,t)|(m1,t)|(m2,t)
    # j0|(0,3) (1,2) (2,2)
    # j1|(0,2) (2,1) (1,4)
    # j2|(1,4) (2,3) (0,3)
    # Define 9 dummy operations, 3 per job, each using a different machine and product
    job0, job1, job2 = default_jobs

    # Define the problem instance configuration with the 3 jobs
    problem_instance = ProblemInstanceConfig(
        type=ProblemInstanceTypeConfig.JOB_SHOP, specification=(job0, job1, job2)
    )

    # Define the instance configuration with the problem instance
    instance = InstanceConfig(
        description="dummy instance with 3 products, machines, and 9 operations",
        instance=problem_instance,
        logistics=logistics,
        machines=(machine0, machine1, machine2),
        buffers=default_buffer,
        transports=default_transports,
    )

    return instance


def map_op_config_to_op_state(op_config: OperationConfig) -> OperationState:
    return OperationState(
        id=op_config.id,
        start_time=NoTime(),
        end_time=NoTime(),
        machine_id=op_config.machine,
        operation_state_state=OperationStateState.IDLE,
    )


@pytest.fixture
def default_init_state(default_instance: InstanceConfig) -> State:
    machines = default_instance.machines
    teleporters = default_instance.transports
    jobs = tuple()
    for job in default_instance.instance.specification:
        operation_configs = job.operations
        operation_states = tuple(map(map_op_config_to_op_state, operation_configs))
        job_state = JobState(
            id=job.id, location=default_instance.buffers[0].id, operations=operation_states
        )
        operations = tuple()
        for op in job.operations:
            op_state = OperationState(
                id=op.id,
                start_time=NoTime(),
                end_time=NoTime(),
                machine_id=op.machine,
                operation_state_state=OperationStateState.IDLE,
            )
            operations += (op_state,)
        job_state = JobState(
            id=job.id,
            operations=operations,
            location=default_instance.buffers[0].id,
        )
        jobs += (job_state,)
    machine_states = tuple()
    for machine in machines:
        machine_state = MachineState(
            id=machine.id,
            buffer=BufferState(id=machine.buffer.id, state=BufferStateState.EMPTY, store=()),
            occupied_till=NoTime(),
            prebuffer=BufferState(
                id=machine.prebuffer.id,
                state=BufferStateState.EMPTY,
                store=(),
            ),
            mounted_tool="tl-0",
            outages=(),
            postbuffer=BufferState(
                id=machine.postbuffer.id,
                state=BufferStateState.EMPTY,
                store=(),
            ),
            state=MachineStateState.IDLE,
            resources=(),
        )

        machine_states += (machine_state,)
    teleproter_states = tuple()
    for i, tele in enumerate(teleporters):
        tele_state = TransportState(
            id=tele.id,
            outages=(),
            state=TransportStateState.IDLE,
            buffer=BufferState(id=tele.buffer.id, state=BufferStateState.EMPTY, store=()),
            occupied_till=NoTime(),
            location=TransportLocation(progress=1.0, location=f"m-{i}"),
            transport_job=None,
        )
        teleproter_states += (tele_state,)
    default_buffer = (
        BufferState(
            id=default_instance.buffers[0].id,
            state=BufferStateState.NOT_EMPTY,
            store=("j-0", "j-1", "j-2"),
        ),
        BufferState(id=default_instance.buffers[1].id, state=BufferStateState.EMPTY, store=()),
    )
    return State(
        time=Time(0),
        jobs=jobs,
        machines=machine_states,
        transports=teleproter_states,
        buffers=default_buffer,
    )


@pytest.fixture
def default_init_state_result(default_init_state):
    return StateMachineResult(
        state=default_init_state,
        sub_states=tuple(),
        action=Action(
            transitions=tuple(),
            action_factory_info=ActionFactoryInfo.Dummy,
            time_machine=jump_to_event,
        ),
        possible_transitions=(
            ComponentTransition(
                component_id="m-0", new_state=MachineStateState.WORKING, job_id="j-0"
            ),
            ComponentTransition(
                component_id="m-1", new_state=MachineStateState.WORKING, job_id="j-1"
            ),
            ComponentTransition(
                component_id="m-2", new_state=MachineStateState.WORKING, job_id="j-2"
            ),
        ),
        success=True,
        message="",
    )


@pytest.fixture
def target_simple_jssp_obs_space():
    spaces = OrderedDict(
        {
            "job_running": gym.spaces.Box(low=0, high=1, shape=(3,), dtype=np.int8),
            "job_executed_on_machine": gym.spaces.Box(low=0, high=1, shape=(3, 3), dtype=np.int8),
            "job_progression": gym.spaces.Box(low=0, high=3, shape=(3,), dtype=np.int32),
            "machine_running": gym.spaces.Box(low=0, high=1, shape=(3,), dtype=np.int8),
            "machine_progression": gym.spaces.Box(low=0, high=3, shape=(3,), dtype=np.int32),
            "available_jobs": gym.spaces.Box(low=0, high=1, shape=(3,), dtype=np.int8),
            "current_time": gym.spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32),
        }
    )
    return spaces


@pytest.fixture
def target_simple_jssp_obs():
    return {
        "job_running": (False, False, False),
        "job_executed_on_machine": (
            (False, False, False),
            (False, False, False),
            (False, False, False),
        ),
        "job_progression": (0, 0, 0),
        "machine_running": (False, False, False),
        "machine_progression": (0, 0, 0),
        "available_jobs": (True, True, True),
        "current_time": np.array([0.0]),
    }


@pytest.fixture
def target_simple_jssp_bin_obs_arr0():
    return [
        {
            "job_running": (False, False, False),
            "job_executed_on_machine": (
                (False, False, False),
                (False, False, False),
                (False, False, False),
            ),
            "job_progression": (0, 0, 0),
            "machine_running": (False, False, False),
            "machine_progression": (0, 0, 0),
            "available_jobs": (True, True, True),
            "current_time": np.array([np.float32(0.0)]),
            "current_job": 0,
        },
        {
            "job_running": (True, False, False),
            "job_executed_on_machine": (
                (False, False, False),
                (False, False, False),
                (False, False, False),
            ),
            "job_progression": (0, 0, 0),
            "machine_running": (True, False, False),
            "machine_progression": (0, 0, 0),
            "available_jobs": (False, True, True),
            "current_time": np.array([np.float32(0.0)]),
            "current_job": 2,
        },
        {
            "job_running": (False, False, True),
            "job_executed_on_machine": (
                (True, False, False),
                (False, False, False),
                (False, False, False),
            ),
            "job_progression": (1, 0, 0),
            "machine_running": (False, True, False),
            "machine_progression": (1, 0, 0),
            "available_jobs": (True, True, False),
            "current_time": np.array([np.float32(0.0)]),
            "current_job": 1,
        },
        {
            "job_running": (False, True, False),
            "job_executed_on_machine": (
                (True, False, False),
                (False, False, False),
                (False, True, False),
            ),
            "job_progression": (1, 0, 1),
            "machine_running": (True, False, False),
            "machine_progression": (1, 1, 0),
            "available_jobs": (True, False, True),
            "current_time": np.array([np.float32(0.0)]),
            "current_job": 0,
        },
        {
            "job_running": (True, True, False),
            "job_executed_on_machine": (
                (True, False, False),
                (False, False, False),
                (False, True, False),
            ),
            "job_progression": (1, 0, 1),
            "machine_running": (True, True, False),
            "machine_progression": (1, 1, 0),
            "available_jobs": (False, False, True),
            "current_time": np.array([np.float32(0.0)]),
            "current_job": 2,
        },
        {
            "job_running": (False, False, False),
            "job_executed_on_machine": (
                (True, True, False),
                (True, False, False),
                (False, True, True),
            ),
            "job_progression": (2, 1, 2),
            "machine_running": (False, False, False),
            "machine_progression": (2, 2, 1),
            "available_jobs": (True, True, True),
            "current_time": np.array([np.float32(0.0)]),
            "current_job": 0,
        },
        {
            "job_running": (True, False, False),
            "job_executed_on_machine": (
                (True, True, False),
                (True, False, False),
                (False, True, True),
            ),
            "job_progression": (2, 1, 2),
            "machine_running": (False, False, True),
            "machine_progression": (2, 2, 1),
            "available_jobs": (False, True, True),
            "current_time": np.array([np.float32(0.0)]),
            "current_job": 2,
        },
        {
            "job_running": (False, False, True),
            "job_executed_on_machine": (
                (True, True, True),
                (True, False, False),
                (False, True, True),
            ),
            "job_progression": (3, 1, 2),
            "machine_running": (True, False, False),
            "machine_progression": (2, 2, 2),
            "available_jobs": (False, True, False),
            "current_time": np.array([np.float32(0.0)]),
            "current_job": 1,
        },
        {
            "job_running": (False, False, False),
            "job_executed_on_machine": (
                (True, True, True),
                (True, False, True),
                (True, True, True),
            ),
            "job_progression": (3, 2, 3),
            "machine_running": (False, False, False),
            "machine_progression": (3, 2, 3),
            "available_jobs": (False, True, False),
            "current_time": np.array([np.float32(0.0)]),
            "current_job": 1,
        },
        {
            "job_running": (False, False, False),
            "job_executed_on_machine": ((True, True, True), (True, True, True), (True, True, True)),
            "job_progression": (3, 3, 3),
            "machine_running": (False, False, False),
            "machine_progression": (3, 3, 3),
            "available_jobs": (False, False, False),
            "current_time": np.array([np.float32(0.0)]),
            "current_job": 3,
        },
    ]


@pytest.fixture
def target_simple_jssp_obs_started_first_job():
    return {
        "job_running": (True, False, False),
        "job_executed_on_machine": (
            (False, False, False),
            (False, False, False),
            (False, False, False),
        ),
        "job_progression": (0, 0, 0),
        "machine_running": (True, False, False),
        "machine_progression": (0, 0, 0),
        "available_jobs": (False, True, True),
    }


# MARK: Fixtures for testing the state machine
# Actions
@pytest.fixture
def action_start_job0_on_machine0():
    comp_transition = ComponentTransition(
        component_id="m-0", new_state=MachineStateState.WORKING, job_id="j-0"
    )
    return Action(
        transitions=(comp_transition,),
        action_factory_info=ActionFactoryInfo.Dummy,
        time_machine=jump_to_event,
    )


@pytest.fixture
def action_start_t0_for_j0():
    comp_transition = ComponentTransition(
        component_id="t-0", new_state=TransportStateState.WORKING, job_id="j-0"
    )
    return Action(
        transitions=(comp_transition,),
        action_factory_info=ActionFactoryInfo.Dummy,
        time_machine=jump_to_event,
    )


@pytest.fixture
def actions_allowed_at_time_dict():
    """
    Returns a dictionary with the allowed actions at a given time
    Dict[int, Action] where the key is the time and the value is a allowed action
    """
    m0_j0 = ComponentTransition(
        component_id="m-0", new_state=MachineStateState.WORKING, job_id="j-0"
    )
    m1_j2 = ComponentTransition(
        component_id="m-1", new_state=MachineStateState.WORKING, job_id="j-2"
    )

    a0 = Action((m0_j0, m1_j2), ActionFactoryInfo.Dummy, time_machine=jump_to_event)

    m0_j1 = ComponentTransition(
        component_id="m-0", new_state=MachineStateState.WORKING, job_id="j-1"
    )

    a1 = Action((m0_j1,), ActionFactoryInfo.Dummy, time_machine=jump_to_event)

    return {0: a0, 3: a1}


@pytest.fixture
def invalid_first_action():
    """
    Returns a list of invalid actions
    Assigns two jobs to the same machine at the same time
    """
    m0_j0 = ComponentTransition(
        component_id="m-0", new_state=MachineStateState.WORKING, job_id="j-0"
    )
    m0_j0 = ComponentTransition(
        component_id="m-0", new_state=MachineStateState.WORKING, job_id="j-1"
    )

    return Action((m0_j0, m0_j0), ActionFactoryInfo.Dummy, time_machine=jump_to_event)


@pytest.fixture
def default_agvs() -> tuple[TransportConfig, ...]:
    return tuple(
        TransportConfig(
            id=f"t-{i}",
            type=TransportTypeConfig.AGV,
            outages=tuple(),
            resources=(),
            buffer=BufferConfig(
                id=f"b-{9 + i}",
                type=BufferTypeConfig.FLEX_BUFFER,
                capacity=1,
                resources=(),
                parent=f"t-{i}",
                description="AGV buffer",
                role=BufferRoleConfig.COMPONENT,
            ),
        )
        for i in range(3)
    )


@pytest.fixture
def default_deterministic_logistics(default_machines, default_buffer) -> LogisticsConfig:
    machine0, machine1, machine2 = default_machines
    input_buffer_id = "b-12"  # default_buffer[0].id
    output_buffer_id = "b-13"  # default_buffer[1].id
    return LogisticsConfig(
        capacity=sys.maxsize,
        #    m0 m1 m2
        # m0 0  5  4
        # m1 5  0  2
        # m2 4  2  0
        travel_times={
            (machine0.id, machine0.id): DeterministicTimeConfig(0),
            (machine1.id, machine1.id): DeterministicTimeConfig(0),
            (machine2.id, machine2.id): DeterministicTimeConfig(0),
            (machine0.id, machine1.id): DeterministicTimeConfig(5),
            (machine1.id, machine0.id): DeterministicTimeConfig(5),
            (machine0.id, machine2.id): DeterministicTimeConfig(4),
            (machine2.id, machine0.id): DeterministicTimeConfig(4),
            (machine1.id, machine2.id): DeterministicTimeConfig(2),
            (machine2.id, machine1.id): DeterministicTimeConfig(2),
            (input_buffer_id, machine0.id): DeterministicTimeConfig(0),
            (input_buffer_id, machine1.id): DeterministicTimeConfig(0),
            (input_buffer_id, machine2.id): DeterministicTimeConfig(0),
            (machine0.id, input_buffer_id): DeterministicTimeConfig(0),
            (machine2.id, input_buffer_id): DeterministicTimeConfig(0),
            (machine1.id, input_buffer_id): DeterministicTimeConfig(0),
            (output_buffer_id, machine0.id): DeterministicTimeConfig(0),
            (output_buffer_id, machine1.id): DeterministicTimeConfig(0),
            (output_buffer_id, machine2.id): DeterministicTimeConfig(0),
            (machine0.id, output_buffer_id): DeterministicTimeConfig(0),
            (machine1.id, output_buffer_id): DeterministicTimeConfig(0),
            (machine2.id, output_buffer_id): DeterministicTimeConfig(0),
            (input_buffer_id, output_buffer_id): DeterministicTimeConfig(0),
            (output_buffer_id, input_buffer_id): DeterministicTimeConfig(0),
            (input_buffer_id, input_buffer_id): DeterministicTimeConfig(0),
            (output_buffer_id, output_buffer_id): DeterministicTimeConfig(0),
        },
    )


@pytest.fixture
def default_instance_with_intralogistics(
    default_machines, default_jobs, default_agvs, default_deterministic_logistics, default_buffer
) -> InstanceConfig:
    machine0, machine1, machine2 = default_machines

    logistics = default_deterministic_logistics
    # (m0,t)|(m1,t)|(m2,t)
    # j0|(0,3) (1,2) (2,2)
    # j1|(0,2) (2,1) (1,4)
    # j2|(1,4) (2,3) (0,3)
    # Define 9 dummy operations, 3 per job, each using a different machine and product
    job0, job1, job2 = default_jobs

    # Define the problem instance configuration with the 3 jobs
    problem_instance = ProblemInstanceConfig(
        type=ProblemInstanceTypeConfig.JOB_SHOP, specification=(job0, job1, job2)
    )

    # Define the instance configuration with the problem instance
    instance = InstanceConfig(
        description="dummy instance with 3 products, machines, and 9 operations",
        instance=problem_instance,
        logistics=logistics,
        machines=(machine0, machine1, machine2),
        buffers=default_buffer,
        transports=default_agvs,
    )

    return instance


@pytest.fixture
def default_instance_with_intralogistics_and_buffer(default_instance_with_intralogistics):
    _instance = default_instance_with_intralogistics
    machines = tuple()
    for machine in _instance.machines:
        _machine = replace(
            machine,
            prebuffer=BufferConfig(
                id=machine.prebuffer.id,
                type=BufferTypeConfig.FLEX_BUFFER,
                capacity=sys.maxsize,
                resources=tuple(),
                parent=machine.prebuffer.parent,
                role=BufferRoleConfig.COMPONENT,
            ),
            postbuffer=BufferConfig(
                id=machine.postbuffer.id,
                type=BufferTypeConfig.FLEX_BUFFER,
                capacity=sys.maxsize,
                resources=tuple(),
                parent=machine.postbuffer.parent,
                role=BufferRoleConfig.COMPONENT,
            ),
        )

        machines += (_machine,)
    _instance = replace(_instance, machines=machines)
    return _instance
