import pytest
import os
from jobshoplab.utils.load_config import load_config
from jobshoplab.env.env import JobShopLabEnv


def test_jsl_configs():
    """Test all configs in data/config directory"""
    config_dir = "data/config"

    for filename in os.listdir(config_dir):
        if filename.endswith(".yaml"):
            config_path = os.path.join(config_dir, filename)
            config = load_config(config_path=config_path)
            env = JobShopLabEnv(config)
            obs, info = env.reset()
            done = False
            step_count = 0
            max_steps = 1000  # Limit steps to avoid long runs

            while not done and step_count < max_steps:
                action = 1
                obs, reward, terminated, truncated, inf = env.step(action)
                done = terminated or truncated
                step_count += 1

            # Test passed if we can create env and take steps without errors
            assert env is not None


def test_jsl_test_configs():
    """Test all configs in tests/data directory"""
    test_config_dir = "tests/data/config"

    for filename in os.listdir(test_config_dir):
        if (
            filename.endswith(".yaml")
            and "config" in filename
            and not filename.startswith("invalid")
        ):
            config_path = os.path.join(test_config_dir, filename)
            config = load_config(config_path=config_path)
            env = JobShopLabEnv(config)
            obs, info = env.reset()
            done = False
            step_count = 0
            max_steps = 1000  # Limit steps to avoid long runs

            while not done and step_count < max_steps:
                action = 1
                obs, reward, terminated, truncated, inf = env.step(action)
                done = terminated or truncated
                step_count += 1

            # Test passed if we can create env and take steps without errors
            assert env is not None
