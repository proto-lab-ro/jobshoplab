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
