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
    minimal_instance_dict["instance_config"]["outages"] = outages
    return minimal_instance_dict


@pytest.fixture
def instance_dict_with_stochastic_machine_times(minimal_instance_dict):
    time_behavior = {"type": "beta", "alpha": 2, "beta": 2}
    minimal_instance_dict["instance_config"]["time_behavior"] = time_behavior


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
            "time_behavior": {"type": "beta", "alpha": 2, "beta": 2},
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
def instance_with_outages(minimal_instance):
    pass


@pytest.fixture
def instance_with_stochastic_machine_times(minimal_instance):
    pass


@pytest.fixture
def instance_with_stochastic_job_times(minimal_instance):
    pass


@pytest.fixture
def instance_with_static_setup_times(minimal_instance):
    pass


@pytest.fixture
def instance_with_stochastic_setup_times(minimal_instance):
    pass
