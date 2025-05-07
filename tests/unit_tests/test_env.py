import numpy as np
import pytest

from jobshoplab import JobShopLabEnv
from jobshoplab.compiler import Compiler
from jobshoplab.env.env import DependencyBuilder
from jobshoplab.env.factories.actions import ActionFactory
from jobshoplab.env.factories.observations import ObservationFactory
from jobshoplab.env.factories.rewards import RewardFactory
from jobshoplab.state_machine.middleware.middleware import Middleware
from jobshoplab.utils.exceptions import EnvDone, ConfigurationError


def test_component_builder(test_config):
    builder = DependencyBuilder(test_config)
    assert builder.config(test_config) == test_config
    compiler = builder.compiler(None)
    instance, state = compiler.compile()
    assert isinstance(compiler, Compiler)
    obs_fact = builder.observation_factory(None, 0, instance)
    rwd_fact = builder.reward_factory(None, 0, instance, 10)
    interp = builder.action_factory(None, 0, instance)
    assert isinstance(interp, ActionFactory)
    assert isinstance(obs_fact, ObservationFactory)
    assert isinstance(rwd_fact, RewardFactory)
    assert isinstance(builder.state_simulator(None, 0, instance, interp, obs_fact), Middleware)


def test_constructor_invalid_config(mock_invalid_config):
    with pytest.raises(ConfigurationError):
        JobShopLabEnv(config=mock_invalid_config)


def test_reset(test_config):
    env = JobShopLabEnv(config=test_config, seed=42)

    # Initial reset
    obs, info = env.reset()
    initial_state = env.state

    # Take some steps
    for _ in range(3):
        env.step(0)

    # Reset again
    new_obs, info = env.reset()

    assert env.state == initial_state
    assert env.history == tuple()
    assert not env.truncated
    assert not env.terminated
    assert np.array_equal(obs, new_obs)


# def test_reset_with_manipulator():
#     # is the new env instance diffrent from the old one when reset is called
#     # is the seeding behavior as wanted
#     raise NotImplemented
#     assert True


def test_step_valid_action(test_config):
    env = JobShopLabEnv(config=test_config, seed=42)
    env.reset()

    obs, reward, terminated, truncated, info = env.step(0)

    assert obs is not None
    assert isinstance(reward, (int, float))
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
    assert isinstance(info, dict)
    assert len(env.history) == 1


def test_step_invalid_action(test_config):
    env = JobShopLabEnv(config=test_config, seed=42)
    env.reset()

    # Test with out-of-bounds action
    with pytest.raises(Exception):
        obs, reward, terminated, truncated, info = env.step(999)


def test_step_episode_end(test_config):
    env = JobShopLabEnv(config=test_config, seed=42)
    env.state_simulator.stepper.truncation_active = True

    terminated = False
    truncated = False
    steps = 0
    max_steps = 1000

    while not (terminated or truncated) and steps < max_steps:
        _, _, terminated, truncated, _ = env.step(0)
        steps += 1

    assert steps < max_steps, "Episode didn't end within maximum steps"
    assert truncated


def test_render_modes(test_config):
    env = JobShopLabEnv(config=test_config, seed=42)
    env.reset()
    env.step(0)

    # Test that render doesn't raise an exception
    try:
        env.render()
    except Exception as e:
        pytest.fail(f"render() raised {e} unexpectedly!")
    try:
        env.render(mode="simulation")
    except Exception as e:
        pytest.fail(f"render() raised {e} unexpectedly!")


def test_seeding(test_config):
    env1 = JobShopLabEnv(config=test_config, seed=42)
    env2 = JobShopLabEnv(config=test_config, seed=42)

    obs1, _ = env1.reset()
    obs2, _ = env2.reset()

    assert np.array_equal(obs1, obs2)

    action = 1
    obs1, r1, _, _, _ = env1.step(action)
    obs2, r2, _, _, _ = env2.step(action)

    assert np.array_equal(obs1, obs2)
    assert r1 == r2


def test_env_done_exception(test_config):
    # test if the env is done and the step function is called
    # if the env is done an exception should be raised
    env = JobShopLabEnv(config=test_config, seed=42)
    with pytest.raises(EnvDone):
        while True:
            env.step(1)
