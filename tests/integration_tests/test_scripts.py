import json
from tempfile import NamedTemporaryFile

from scripts import make_test_json_dump


def test_json_dump():
    temp_file = NamedTemporaryFile()
    make_test_json_dump.make_dump(temp_file.name)
    dumped_interface = json.load(temp_file)
    assert list(dumped_interface.keys()) == ["state_history", "instance", "loglevel"]
