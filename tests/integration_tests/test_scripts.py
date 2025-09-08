import json
import pytest
from tempfile import NamedTemporaryFile

from scripts import make_test_json_dump


@pytest.mark.skip(reason="make_json_dump function not yet implemented")
def test_json_dump():
    temp_file = NamedTemporaryFile()
    make_test_json_dump.make_dump(temp_file.name)
    dumped_interface = json.load(temp_file)
    assert list(dumped_interface.keys()) == ["state_history", "instance", "loglevel"]
