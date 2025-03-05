import tempfile
from pathlib import Path

from heracless import load_config
from pytest import fixture


@fixture
def multi_discrete_conf0():
    temp_file = tempfile.NamedTemporaryFile(delete=False).name
    config = load_config(Path("tests/data/test_multi_discrete_conf0.yaml"), Path(temp_file), True)
    return config
