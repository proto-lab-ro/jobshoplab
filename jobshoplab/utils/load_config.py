from pathlib import Path

from hydra import compose, initialize
from hydra.utils import instantiate
from omegaconf import OmegaConf

from jobshoplab.types.config_types import Config

# Default paths relative to the project root
CONFIG_DIR = "../../data/config"
CONFIG_NAME = "default_config"


def load_config(
    config_path: str = CONFIG_NAME,
    config_dir: str = CONFIG_DIR,
    overrides: list[str] | None = None,
) -> Config:
    """
    Load the configuration using Hydra.

    Args:
        config_path (str): The name of the config file (without .yaml).
        config_dir (str): The directory containing the config files, relative to this script.
        overrides (list[str], optional): A list of Hydra-style overrides (e.g., ["compiler.loglevel=debug"]).

    Returns:
        Config: The loaded and validated configuration object.
    """
    with initialize(version_base=None, config_path=config_dir):
        cfg = compose(config_name=config_path, overrides=overrides or [])

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
