from pathlib import Path

import pytest

from jobshoplab.compiler import manipulators, repos
from jobshoplab.compiler.compiler import Compiler
from jobshoplab.types import InstanceConfig, State
from jobshoplab.utils.exceptions import FileNotFound, InstanceSchemaError
from jobshoplab.utils.load_config import load_config


def test_default_compiler():
    """Test compiler initialization and compilation with default config"""
    config = load_config()
    compiler = Compiler(config)
    instance_config, init_state = compiler.compile()

    assert isinstance(instance_config, InstanceConfig)
    assert isinstance(init_state, State)
    assert len(instance_config.instance.specification) > 0
    assert len(init_state.jobs) > 0


def test_compiler_with_custom_repo():
    """Test compiler with custom repository"""
    config = load_config()
    custom_repo = repos.DslRepository(
        Path("./tests/data/jssp_instances/instance_with_agvs.yaml"), "info", config
    )
    compiler = Compiler(config, repo=custom_repo)
    instance_config, init_state = compiler.compile()

    assert isinstance(instance_config, InstanceConfig)
    assert isinstance(init_state, State)


def test_compiler_with_manipulators():
    """Test compiler with instance manipulators"""
    config = load_config()
    compiler = Compiler(config, manipulators=[manipulators.InstanceRandomizer])
    instance_config, init_state = compiler.compile()

    assert isinstance(instance_config, InstanceConfig)
    assert isinstance(init_state, State)


def test_compiler_invalid_config():
    """Test compiler handles invalid config"""
    invalid_config = None

    with pytest.raises(AttributeError):
        compiler = Compiler(invalid_config)
        instance_config, init_state = compiler.compile()


def test_compiler_invalid_dir_dls(config):
    """Test compiler with debug logging level"""

    with pytest.raises(FileNotFound):
        compiler = Compiler(
            repo=repos.DslRepository(Path("./asdf"), "info", config),
            config=config,
            loglevel="DEBUG",
        )
        instance_config, init_state = compiler.compile()


def test_compiler_invalid_dls(config):

    with pytest.raises(InstanceSchemaError):
        compiler = Compiler(
            repo=repos.DslRepository(
                Path("tests/data/jssp_instances/invalid_dsl.yaml"), "info", config
            ),
            config=config,
            loglevel="INFO",
        )
        instance_config, init_state = compiler.compile()


def test_compiler_with_spec_repo(config):
    """Test compiler input validation"""
    _repo = repos.SpecRepository(Path("data/jssp_instances/spec_files/abz5"), "info", config)
    compiler = Compiler(repo=_repo, config=config)
    instance_config, init_state = compiler.compile()
    assert isinstance(instance_config, InstanceConfig)
    assert isinstance(init_state, State)
