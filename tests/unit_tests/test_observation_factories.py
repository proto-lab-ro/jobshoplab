import tempfile
from functools import partial
from pathlib import Path

import numpy as np
from gymnasium import spaces
from heracless import load_config

from jobshoplab.env.env import JobShopLabEnv
from jobshoplab.env.factories.observations import (
    BinaryActionObservationFactory,
    BinaryOperationArrayObservation,
    SimpleJsspObservationFactory,
)
from jobshoplab.state_machine.core.state_machine import step
from jobshoplab.state_machine.time_machines import jump_to_event


def test_simple_jssp_of_space(target_simple_jssp_obs_space, default_instance):
    loglevel = 0
    config = None
    simple_jssp_observation_factory = SimpleJsspObservationFactory(
        loglevel, config, default_instance  # type: ignore
    )
    assert type(simple_jssp_observation_factory.observation_space) == spaces.Dict
    assert simple_jssp_observation_factory.observation_space == target_simple_jssp_obs_space


def test_simple_jssp_obs(target_simple_jssp_obs, default_init_state_result, default_instance):
    loglevel = 0
    config = None
    simple_jssp_observation_factory = SimpleJsspObservationFactory(
        loglevel, config, default_instance  # type: ignore
    )

    assert simple_jssp_observation_factory.make(default_init_state_result) == target_simple_jssp_obs


def test_binary_action_jssp_obs_space(
    target_simple_jssp_obs_space, default_instance, default_init_state
):
    loglevel = 0
    config = None
    binary_action_jssp_obs_factory = BinaryActionObservationFactory(
        loglevel, config, default_instance
    )
    _spaces = target_simple_jssp_obs_space.spaces
    _spaces["current_job"] = spaces.Discrete(4, start=0)
    _spaces["current_component_id"] = spaces.Discrete(7, start=0)
    _spaces["current_component_type"] = spaces.Discrete(3, start=0)
    _spaces.move_to_end("current_job")
    _spaces.move_to_end("current_component_id")
    _spaces.move_to_end("current_component_type")
    assert isinstance(binary_action_jssp_obs_factory.observation_space, spaces.Dict)
    assert (
        binary_action_jssp_obs_factory.observation_space.spaces
        == target_simple_jssp_obs_space.spaces
    )


def test_binary_action_jssp_obs_done(
    target_simple_jssp_obs, default_init_state_result, default_instance
):
    loglevel = 0
    config = None
    binary_action_jssp_obs_factory = BinaryActionObservationFactory(
        loglevel, config, default_instance
    )

    target_simple_jssp_obs["current_job"] = 3
    target_simple_jssp_obs["current_component_type"] = 3
    target_simple_jssp_obs["current_component_id"] = 6

    assert (
        binary_action_jssp_obs_factory.make(default_init_state_result, done=True)
        == target_simple_jssp_obs
    )


def test_binary_action_jssp_obs_no_op(
    target_simple_jssp_obs, default_init_state, default_instance, config
):

    loglevel = 0
    env = JobShopLabEnv(
        config=config,
        observation_factory=BinaryActionObservationFactory,
    )
    # transports on t-0
    target_simple_jssp_obs["current_job"] = 0
    target_simple_jssp_obs["current_component_type"] = 1
    target_simple_jssp_obs["current_component_id"] = 3
    obs, info = env.reset()
    assert obs == target_simple_jssp_obs
    target_simple_jssp_obs["current_job"] = 1
    target_simple_jssp_obs["current_component_type"] = 1
    target_simple_jssp_obs["current_component_id"] = 3
    obs, reward, termianted, truncated, info = env.step(0)
    assert obs == target_simple_jssp_obs
    target_simple_jssp_obs["current_job"] = 2
    target_simple_jssp_obs["current_component_type"] = 1
    target_simple_jssp_obs["current_component_id"] = 3
    obs, reward, termianted, truncated, info = env.step(0)
    assert obs == target_simple_jssp_obs
    # transports on t-1
    target_simple_jssp_obs["current_job"] = 0
    target_simple_jssp_obs["current_component_type"] = 1
    target_simple_jssp_obs["current_component_id"] = 4
    obs, reward, termianted, truncated, info = env.step(0)
    assert obs == target_simple_jssp_obs
    target_simple_jssp_obs["current_job"] = 1
    target_simple_jssp_obs["current_component_type"] = 1
    target_simple_jssp_obs["current_component_id"] = 4
    obs, reward, termianted, truncated, info = env.step(0)
    assert obs == target_simple_jssp_obs
    target_simple_jssp_obs["current_job"] = 2
    target_simple_jssp_obs["current_component_type"] = 1
    target_simple_jssp_obs["current_component_id"] = 4
    obs, reward, termianted, truncated, info = env.step(0)
    assert obs == target_simple_jssp_obs
    # transports on t-2
    target_simple_jssp_obs["current_job"] = 0
    target_simple_jssp_obs["current_component_type"] = 1
    target_simple_jssp_obs["current_component_id"] = 5
    obs, reward, termianted, truncated, info = env.step(0)
    assert obs == target_simple_jssp_obs
    target_simple_jssp_obs["current_job"] = 1
    target_simple_jssp_obs["current_component_type"] = 1
    target_simple_jssp_obs["current_component_id"] = 5
    obs, reward, termianted, truncated, info = env.step(0)
    assert obs == target_simple_jssp_obs
    target_simple_jssp_obs["current_job"] = 2
    target_simple_jssp_obs["current_component_type"] = 1
    target_simple_jssp_obs["current_component_id"] = 5
    obs, reward, termianted, truncated, info = env.step(0)
    assert obs == target_simple_jssp_obs
    obs, reward, termianted, truncated, info = env.step(0)
    assert obs["current_time"] == np.array(np.float32(1 / env.max_allowed_time))


def test_binary_array_jssp_obs(default_init_state, default_instance, config):
    env = JobShopLabEnv(
        config=config,
        observation_factory=BinaryOperationArrayObservation,
    )
    obs, info = env.reset()

    is_same = obs["operation_state"] == np.zeros(9).reshape(1, 9)

    assert obs["current_job"] == 0
    assert obs["current_component_type"] == 1
    assert is_same.all()
    obs, reward, termianted, truncated, info = env.step(0)
    is_same = obs["operation_state"] == np.zeros(9).reshape(1, 9)
    assert obs["current_job"] == 1
    assert obs["current_component_type"] == 1
    assert is_same.all()
    is_same = obs["job_locations"] == np.array([[0, 0, 0]], dtype=np.float32)
    assert is_same.all()
    obs, reward, termianted, truncated, info = env.step(1)
    obs, reward, termianted, truncated, info = env.step(1)
    obs, reward, termianted, truncated, info = env.step(1)
    obs, reward, termianted, truncated, info = env.step(1)
    is_same = obs["operation_state"] == np.zeros(9).reshape(1, 9)
    assert obs["current_job"] == 1
    assert obs["current_component_type"] == 1
    assert is_same.all()
    is_same = obs["job_locations"] == np.array([[0, 3.0, 0]], dtype=np.float32)
    assert is_same.all()
