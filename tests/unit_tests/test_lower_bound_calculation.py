import os
from pathlib import Path

from jobshoplab import JobShopLabEnv
from jobshoplab.compiler import Compiler
from jobshoplab.compiler.repos import SpecRepository
from jobshoplab.utils.load_config import load_config


def test_ft06_lb():
    instance_dir = "data/jssp_instances/"
    problem = "ft06"
    config = load_config()
    repo = SpecRepository(
        dir=Path(os.path.join(instance_dir, problem)), loglevel="error", config=config
    )
    compiler = Compiler(config=config, loglevel="error", repo=repo)
    env = JobShopLabEnv(config=config, compiler=compiler, loglevel="error")
    lb = env.lower_bound
    assert lb == 52


def test_ft10_lb():
    instance_dir = "data/jssp_instances/"
    problem = "ft10"
    config = load_config()
    repo = SpecRepository(
        dir=Path(os.path.join(instance_dir, problem)), loglevel="error", config=config
    )
    compiler = Compiler(config=config, loglevel="error", repo=repo)
    env = JobShopLabEnv(config=config, compiler=compiler, loglevel="error")
    lb = env.lower_bound
    assert lb == 796


def test_la01_lb():
    instance_dir = "data/jssp_instances/"
    problem = "la01"
    config = load_config()
    repo = SpecRepository(
        dir=Path(os.path.join(instance_dir, problem)), loglevel="error", config=config
    )
    compiler = Compiler(config=config, loglevel="error", repo=repo)
    env = JobShopLabEnv(config=config, compiler=compiler, loglevel="error")
    lb = env.lower_bound
    assert lb == 666


def test_la02_lb():
    instance_dir = "data/jssp_instances/"
    problem = "la02"
    config = load_config()
    repo = SpecRepository(
        dir=Path(os.path.join(instance_dir, problem)), loglevel="error", config=config
    )
    compiler = Compiler(config=config, loglevel="error", repo=repo)
    env = JobShopLabEnv(config=config, compiler=compiler, loglevel="error")
    lb = env.lower_bound
    assert lb == 655


def test_ta01_lb():
    instance_dir = "data/jssp_instances/"
    problem = "ta01"
    config = load_config()
    repo = SpecRepository(
        dir=Path(os.path.join(instance_dir, problem)), loglevel="error", config=config
    )
    compiler = Compiler(config=config, loglevel="error", repo=repo)
    env = JobShopLabEnv(config=config, compiler=compiler, loglevel="error")
    lb = env.lower_bound
    assert lb == 1005
