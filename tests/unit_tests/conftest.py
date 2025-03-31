import tempfile
from dataclasses import replace
from pathlib import Path

import pytest
from heracless import load_config

from jobshoplab.compiler import Compiler
from jobshoplab.env.factories import observations, rewards
from jobshoplab.env.factories.actions import ActionFactory
from jobshoplab.types import Config, State
from jobshoplab.types.instance_config_types import InstanceConfig, JobConfig, MachineConfig
from dataclasses import replace
from jobshoplab.types.instance_config_types import OutageConfig, OutageTypeConfig
from jobshoplab.types.instance_config_types import DeterministicTimeConfig, StochasticTimeConfig
from jobshoplab.utils.stochasticy_models import (
    GammaFunction,
    GaussianFunction,
    PoissonFunction,
    BetaFunction,
)

from jobshoplab.types.instance_config_types import (
    DeterministicTimeConfig,
    StochasticTimeConfig,
    Product,
)
from jobshoplab.utils.stochasticy_models import BetaFunction
from tests.conftest import default_instance
from jobshoplab.types.instance_config_types import StochasticTimeConfig


@pytest.fixture
def test_config():
    with tempfile.NamedTemporaryFile(suffix=".pyi", delete=False) as tmp_file:
        dump_dir = Path(tmp_file.name)
        config_dir = Path("./tests/data/test_config3.yaml")
        return load_config(config_dir, dump_dir, True)


@pytest.fixture
def mock_compiler(test_config):
    compiler = Compiler(test_config)
    return compiler


@pytest.fixture
def mock_observation_factory():
    return observations.SimpleJSSPObservationFactory


@pytest.fixture
def mock_reward_factory():
    return rewards.SimpleJSSPRewardFactory


@pytest.fixture
def mock_action_factory(test_config):
    return ActionFactory(test_config)


@pytest.fixture
def mock_invalid_config(test_config):
    # Create an invalid config by removing required fields
    return replace(test_config, env=None)


## MAPPER FIXTURES
### INSTANCE DICT FIXTURES
@pytest.fixture
def instance_dict_with_outages(minimal_instance_dict):
    outages = [
        {
            "component": "m-1",  # set one machine
            "type": "maintenance",
            "duration": 5,
            "frequency": {"type": "gamma", "shape": 2, "scale": 5, "base": 10},
        },
        {
            "component": "t",  # set all transports
            "type": "recharge",
            "duration": {"type": "gaussian", "mean": 5, "std": 1, "base": 10},
            "frequency": 10,
        },
    ]
    minimal_instance_dict["instance_config"]["logistics"] = {
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
    }
    minimal_instance_dict["instance_config"]["outages"] = outages
    return minimal_instance_dict


@pytest.fixture
def instance_dict_with_stochastic_machine_times(minimal_instance_dict):
    time_behavior = {"type": "beta", "alpha": 2, "beta": 2}
    minimal_instance_dict["instance_config"]["instance"]["time_behavior"] = time_behavior
    return minimal_instance_dict


@pytest.fixture
def instance_dict_with_stochastic_transport_times(minimal_instance_dict):
    # Add intralogistics with stochastic behavior
    minimal_instance_dict["instance_config"]["logistics"] = {
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
        "time_behavior": {"type": "poisson", "mean": 2},
    }
    return minimal_instance_dict


@pytest.fixture
def instance_dict_with_static_setup_times(minimal_instance_dict):
    setup_times = [
        {"machine": "m-0", "specification": "tl-0|tl-1|tl-2\ntl-0|0 2 5\ntl-1|2 0 8\ntl-2|5 2 0"},
        {"machine": "m-1", "specification": "tl-0|tl-1|tl-2\ntl-0|0 2 5\ntl-1|2 0 8\ntl-2|5 2 0"},
        {"machine": "m-2", "specification": "tl-0|tl-1|tl-2\ntl-0|0 2 5\ntl-1|2 0 8\ntl-2|5 2 0"},
    ]
    tool_usage = [
        {"job": "j0", "operation_tools": ["tl-0", "tl-1", "tl-2"]},
        {"job": "j1", "operation_tools": ["tl-0", "tl-1", "tl-2"]},
        {"job": "j2", "operation_tools": ["tl-0", "tl-1", "tl-2"]},
    ]
    minimal_instance_dict["instance_config"]["setup_times"] = setup_times
    minimal_instance_dict["instance_config"]["instance"]["tool_usage"] = tool_usage
    return minimal_instance_dict


@pytest.fixture
def instance_dict_with_stochastic_setup_times(minimal_instance_dict):
    setup_times = [
        {
            "machine": "m-0",
            "specification": "tl-0|tl-1|tl-2\ntl-0|0 2 5\ntl-1|2 0 8\ntl-2|5 2 0",
            "time_behavior": "static",
        },
        {
            "machine": "m-1",
            "specification": "tl-0|tl-1|tl-2\ntl-0|0 2 5\ntl-1|2 0 8\ntl-2|5 2 0",
            "time_behavior": {"type": "beta", "alpha": 2, "beta": 2},
        },
        {
            "machine": "m-2",
            "specification": "tl-0|tl-1|tl-2\ntl-0|0 2 5\ntl-1|2 0 8\ntl-2|5 2 0",
        },
    ]
    tool_usage = [
        {"job": "j0", "operation_tools": ["tl-0", "tl-1", "tl-2"]},
        {"job": "j1", "operation_tools": ["tl-0", "tl-1", "tl-2"]},
        {"job": "j2", "operation_tools": ["tl-0", "tl-1", "tl-2"]},
    ]
    minimal_instance_dict["instance_config"]["setup_times"] = setup_times
    minimal_instance_dict["instance_config"]["instance"]["tool_usage"] = tool_usage
    return minimal_instance_dict


### INSTANCE FIXTURES


@pytest.fixture
def instance_with_outages(default_instance, default_machines):
    # Create machine with maintenance outage
    machine1 = default_machines[1]  # Use m-1
    gamma_func = GammaFunction(10, 2.0, 5.0)
    maintenance_outage = OutageConfig(
        frequency=StochasticTimeConfig(gamma_func),
        duration=DeterministicTimeConfig(5),
        type=OutageTypeConfig.MAINTENANCE,
    )
    modified_machine1 = replace(machine1, outages=(maintenance_outage,))

    # Create modified transports with recharge outage
    gaussian_func = GaussianFunction(10, 5.0, 1.0)
    recharge_outage = OutageConfig(
        frequency=DeterministicTimeConfig(10),
        duration=StochasticTimeConfig(gaussian_func),
        type=OutageTypeConfig.RECHARGE,
    )

    modified_transports = tuple(
        replace(transport, outages=(recharge_outage,)) for transport in default_instance.transports
    )

    # Replace the machines and transports in the minimal instance
    new_machines = list(default_instance.machines)
    new_machines[1] = modified_machine1

    return replace(default_instance, machines=tuple(new_machines), transports=modified_transports)


@pytest.fixture
def instance_with_stochastic_machine_times(default_instance):

    # Create stochastic job operations
    modified_jobs = []
    for job in default_instance.instance.specification:
        modified_operations = []
        for op in job.operations:
            # Replace deterministic duration with stochastic beta function
            beta_func = BetaFunction(
                base_time=op.duration.time, alpha=2, beta=2  # Use the original time as base
            )
            modified_op = replace(op, duration=StochasticTimeConfig(beta_func))
            modified_operations.append(modified_op)

        modified_job = replace(job, operations=tuple(modified_operations))
        modified_jobs.append(modified_job)

    # Create modified problem instance
    modified_problem_instance = replace(
        default_instance.instance, specification=tuple(modified_jobs)
    )

    # Return modified instance
    return replace(default_instance, instance=modified_problem_instance)


@pytest.fixture
def instance_with_stochastic_transport_times(default_instance_with_intralogistics):
    # Add intralogistics with stochastic behavior
    default_instance = default_instance_with_intralogistics
    tt_time = dict()
    for locations, _time in default_instance.logistics.travel_times.items():
        # Replace deterministic duration with stochastic beta function
        beta_func = PoissonFunction(base_time=_time.time, mean=2.0)
        tt_time[locations] = StochasticTimeConfig(beta_func)
    logistics = replace(default_instance.logistics, travel_times=tt_time)
    instance = replace(default_instance, logistics=logistics)
    return instance


@pytest.fixture
def instance_with_static_setup_times(default_instance, default_products):
    from dataclasses import replace
    from jobshoplab.types.instance_config_types import DeterministicTimeConfig, Product

    # Create tool-based setup times for each machine
    modified_machines = []
    tools = ["tl-0", "tl-1", "tl-2"]

    # Setup time matrix (symmetric in this case for simplicity)
    setup_times_matrix = {
        ("tl-0", "tl-0"): DeterministicTimeConfig(0),
        ("tl-0", "tl-1"): DeterministicTimeConfig(2),
        ("tl-0", "tl-2"): DeterministicTimeConfig(5),
        ("tl-1", "tl-0"): DeterministicTimeConfig(2),
        ("tl-1", "tl-1"): DeterministicTimeConfig(0),
        ("tl-1", "tl-2"): DeterministicTimeConfig(8),
        ("tl-2", "tl-0"): DeterministicTimeConfig(5),
        ("tl-2", "tl-1"): DeterministicTimeConfig(2),
        ("tl-2", "tl-2"): DeterministicTimeConfig(0),
    }

    # Apply setup times to each machine
    for machine in default_instance.machines:
        modified_machine = replace(machine, setup_times=setup_times_matrix)
        modified_machines.append(modified_machine)

    # Modify jobs to use specific tools for operations
    modified_jobs = []
    tool_assignments = [
        ["tl-0", "tl-1", "tl-2"],  # job 0
        ["tl-0", "tl-1", "tl-2"],  # job 1
        ["tl-0", "tl-1", "tl-2"],  # job 2
    ]

    for job_idx, job in enumerate(default_instance.instance.specification):
        modified_operations = []
        for op_idx, op in enumerate(job.operations):
            tool = tool_assignments[job_idx][op_idx]
            modified_op = replace(op, tool=tool)
            modified_operations.append(modified_op)

        modified_job = replace(job, operations=tuple(modified_operations))
        modified_jobs.append(modified_job)

    # Create modified problem instance
    modified_problem_instance = replace(
        default_instance.instance, specification=tuple(modified_jobs)
    )

    # Return modified instance
    return replace(
        default_instance, machines=tuple(modified_machines), instance=modified_problem_instance
    )


@pytest.fixture
def instance_with_stochastic_setup_times(default_instance, default_products):

    # Create tool-based setup times for each machine
    modified_machines = []
    tools = ["tl-0", "tl-1", "tl-2"]

    # For m-0: deterministic setup times
    setup_times_m0 = {
        ("tl-0", "tl-0"): DeterministicTimeConfig(0),
        ("tl-0", "tl-1"): DeterministicTimeConfig(2),
        ("tl-0", "tl-2"): DeterministicTimeConfig(5),
        ("tl-1", "tl-0"): DeterministicTimeConfig(2),
        ("tl-1", "tl-1"): DeterministicTimeConfig(0),
        ("tl-1", "tl-2"): DeterministicTimeConfig(8),
        ("tl-2", "tl-0"): DeterministicTimeConfig(5),
        ("tl-2", "tl-1"): DeterministicTimeConfig(2),
        ("tl-2", "tl-2"): DeterministicTimeConfig(0),
    }

    # For m-1 and m-2: stochastic setup times using beta distribution
    setup_times_m1_m2 = {}
    for key, value in setup_times_m0.items():
        # Skip cases where the same tool is used (setup time is always 0)
        if key[0] == key[1]:
            setup_times_m1_m2[key] = DeterministicTimeConfig(0)
        else:
            beta_func = BetaFunction(base_time=value.time, alpha=2, beta=2)
            setup_times_m1_m2[key] = StochasticTimeConfig(beta_func)

    # Apply different setup times to different machines
    for idx, machine in enumerate(default_instance.machines):
        if idx == 0:
            modified_machine = replace(machine, setup_times=setup_times_m0)
        else:
            modified_machine = replace(machine, setup_times=setup_times_m1_m2)
        modified_machines.append(modified_machine)

    # Modify jobs to use specific tools for operations
    modified_jobs = []
    tool_assignments = [
        ["tl-0", "tl-1", "tl-2"],  # job 0
        ["tl-0", "tl-1", "tl-2"],  # job 1
        ["tl-0", "tl-1", "tl-2"],  # job 2
    ]

    for job_idx, job in enumerate(default_instance.instance.specification):
        modified_operations = []
        for op_idx, op in enumerate(job.operations):
            tool = tool_assignments[job_idx][op_idx]
            modified_op = replace(op, tool=tool)
            modified_operations.append(modified_op)

        modified_job = replace(job, operations=tuple(modified_operations))
        modified_jobs.append(modified_job)

    # Create modified problem instance
    modified_problem_instance = replace(
        default_instance.instance, specification=tuple(modified_jobs)
    )

    # Return modified instance
    return replace(
        default_instance, machines=tuple(modified_machines), instance=modified_problem_instance
    )
