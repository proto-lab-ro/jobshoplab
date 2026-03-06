import tempfile
from pathlib import Path

from jobshoplab.utils.load_config import load_config
from pytest import fixture


@fixture
def multi_discrete_conf0():
    config = load_config(config_path="test_multi_discrete_conf0", config_dir="../../tests/data")
    return config
