from pathlib import Path

import pytest

from jobshoplab.compiler.repos import DslRepository, SpecRepository
from jobshoplab.utils.exceptions import FileNotFound


def test_yaml_repo_parsing(test_yaml_instance_dir, config):
    repo = DslRepository(test_yaml_instance_dir, "debug", config)
    _dict = repo._parse()
    assert isinstance(_dict, dict)


def test_yaml_repo_file_handeling(test_yaml_instance_dir, config):
    correct_path = test_yaml_instance_dir
    wrong_path = Path("./test/data/test_instance_wrong.yaml")
    log_level = "debug"
    with pytest.raises(FileNotFound):
        wrong_repo = DslRepository(
            wrong_path,
            log_level,
            config,
        )
    try:
        correct_repo = DslRepository(correct_path, log_level, config)
    except Exception as e:
        pytest.fail(f"Unexpected exception raised: {e}")


def test_yaml_repo_load_as_dict(test_yaml_instance_dir, config):
    _dict = DslRepository(test_yaml_instance_dir, "debug", config).load_as_dict()
    # digging into the dictionary to check if the structure is correct and the values are correct
    # not checking exhaustively, just a few key points to see if the parsing is working
    assert isinstance(_dict, dict)
    assert "instance_config" in _dict.keys()
    assert "init_state" in _dict.keys()
    assert list(_dict["instance_config"].keys()) == [
        "description",
        "components",
        "instance",
        "logistics",
    ]
    assert list(_dict["instance_config"]["components"].keys()) == [
        "machines",
        "buffer",
        "transport",
    ]
    assert isinstance(_dict["instance_config"]["components"]["machines"], dict)
    assert _dict["instance_config"]["components"]["machines"][0]["post_buffer"]["type"] == "lifo"


def test_spec_repo_file_handeling(test_spec_instance_dir: Path, config):
    correct_path: Path = test_spec_instance_dir
    wrong_path = Path("test/data/test_spec_wrong.txt")
    log_level = "debug"
    with pytest.raises(FileNotFound):
        wrong_repo = SpecRepository(
            wrong_path,
            log_level,
            config,
        )
    try:

        print(correct_path.absolute())
        correct_repo = SpecRepository(correct_path, log_level, config)
    except Exception as e:
        pytest.fail(f"Unexpected exception raised: {e}")


def test_spec_repo_load_as_dict(test_spec_instance_dir, config):
    _dict = SpecRepository(test_spec_instance_dir, "debug", config).load_as_dict()
    assert isinstance(_dict, dict)
    assert "instance_config" in _dict.keys()
    # only info received from the spec file is the specification
    assert isinstance(_dict["instance_config"]["instance"]["specification"], str)


def test_spec_repo_parsing(test_spec_instance_dir, config):
    repo = DslRepository(test_spec_instance_dir, "debug", config)
    _str = repo._parse()
    assert isinstance(_str, str)
