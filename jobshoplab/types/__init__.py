try:
    from jobshoplab.utils.load_config import Config
except:
    from typing import TypeVar

    @dataclass
    class Config:
        dummy_val: str
        # Add other settings as needed

    config = Config(dummy_val="auto_config.py not found")
    print("Warning: 'auto_config.py' not found. Using default configuration.")

# Export Config and config for easy import in other modules
__all__ = ["Config", "config"]

from jobshoplab.types.action_types import *
from jobshoplab.types.instance_config_types import *
from jobshoplab.types.state_types import *
