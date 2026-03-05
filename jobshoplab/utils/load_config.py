from pathlib import Path
from typing import Union

from hydra import compose, initialize
from hydra.utils import instantiate
from omegaconf import OmegaConf

from jobshoplab.types.config_types import Config

# Default paths relative to the project root
CONFIG_DIR = "../../data/config"
CONFIG_NAME = "default_config"


def load_config(
    config_path: Union[str, Path] = CONFIG_NAME,
    config_dir: str = CONFIG_DIR,
    overrides: list[str] | None = None,
) -> Config:
    """
    Load the configuration using Hydra.

    Args:
        config_path (Union[str, Path]): The name of the config file (without .yaml) or a Path to a config file.
        config_dir (str): The directory containing the config files, relative to this script.
        overrides (list[str], optional): A list of Hydra-style overrides (e.g., ["compiler.loglevel=debug"]).

    Returns:
        Config: The loaded and validated configuration object.
    """
    # If a full path or a Path object is provided, extract its stem and its directory if needed
    if isinstance(config_path, Path) or (isinstance(config_path, str) and "/" in config_path):
        p = Path(config_path)
        # If it's an absolute path or exists relative to the current CWD, 
        # we might want to use its directory. 
        # However, Hydra's initialize() 'config_path' is relative to the *module*.
        # For simplicity and to fix the immediate error, we ensure config_name is a string (stem).
        config_name = p.stem
    else:
        config_name = str(config_path)

    with initialize(version_base=None, config_path=config_dir):
        cfg = compose(config_name=config_name, overrides=overrides or [])

        # Merge with structured config for type safety and validation
        schema = OmegaConf.structured(Config)
        merged_cfg = OmegaConf.merge(schema, cfg)

        # Convert to a pure Python object (dataclass instance)
        return cast_to_config(merged_cfg)


def cast_to_config(cfg) -> Config:
    """Helper to convert OmegaConf to the Config dataclass."""
    return OmegaConf.to_object(cfg)


if __name__ == "__main__":
    c = load_config()
    print(c.title)
