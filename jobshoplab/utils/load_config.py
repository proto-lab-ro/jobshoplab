import tempfile
from pathlib import Path
from typing import TypeVar

from heracless import load_config as _load_config

CONFIG_YAML_PATH = Path("./data/config/default_config.yaml")
DUMP_PATH = file_path = Path(__file__).resolve()
Config = TypeVar("Config")


def load_config(
    frozen: bool = True,
    stub_file_path: Path | None = DUMP_PATH,
    config_path: Path = CONFIG_YAML_PATH,
) -> Config:
    """
    Load the configuration from the specified directory and return a Config object.

    Args:
        frozen (bool, optional): Whether the configuration should be frozen. Defaults to True.

    Returns:
        Config: The loaded configuration object.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        yaml.YAMLError: If there is an error parsing the YAML configuration file.

    Note:
        CONFIG_YAML_PATH is a global variable that sets the path of your YAML config file.
    """

    if stub_file_path is None:
        stub_file_path: Path = Path(tempfile.NamedTemporaryFile(delete=False).name)
    return _load_config(config_path, stub_file_path, frozen=frozen)


if __name__ == "__main__":
    load_config()
