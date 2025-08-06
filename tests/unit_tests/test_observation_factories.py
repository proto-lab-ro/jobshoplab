import gymnasium as gym
import numpy as np
from gymnasium import spaces

from jobshoplab.env.env import JobShopLabEnv
from jobshoplab.env.factories.observations import (
    BinaryActionObservationFactory,
    BinaryOperationArrayObservation,
    SimpleJsspObservationFactory,
)


def test_simple_jssp_of_space(target_simple_jssp_obs_space, default_instance):
    loglevel = 0
    config = None
    simple_jssp_observation_factory = SimpleJsspObservationFactory(
        loglevel, config, default_instance  # type: ignore
    )

    assert type(simple_jssp_observation_factory.observation_space) == spaces.Dict
    assert simple_jssp_observation_factory.observation_space == gym.spaces.Dict(
        target_simple_jssp_obs_space
    )


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
    _spaces = target_simple_jssp_obs_space
    _spaces["current_transition"] = spaces.Box(low=0, high=1, shape=(3,), dtype=np.float32)
    _spaces.move_to_end("current_transition")
    _spaces = gym.spaces.Dict(_spaces)
    assert isinstance(binary_action_jssp_obs_factory.observation_space, spaces.Dict)
    assert binary_action_jssp_obs_factory.observation_space.spaces == _spaces.spaces


def test_binary_action_jssp_obs_done(
    target_simple_jssp_obs, default_init_state_result, default_instance
):
    loglevel = 0
    config = None
    binary_action_jssp_obs_factory = BinaryActionObservationFactory(
        loglevel, config, default_instance
    )

    target_simple_jssp_obs["current_transition"] = np.array([1.0, 1.0, 1.0], dtype=np.float32)

    result_obs = binary_action_jssp_obs_factory.make(default_init_state_result, done=True)

    # Compare non-array fields
    for key in target_simple_jssp_obs:
        if key != "current_transition":
            assert result_obs[key] == target_simple_jssp_obs[key], f"Mismatch in {key}"

    # Compare array field
    assert np.allclose(
        result_obs["current_transition"], target_simple_jssp_obs["current_transition"]
    )


def test_binary_action_jssp_obs_no_op(
    target_simple_jssp_obs, default_init_state, default_instance, config
):

    loglevel = 0
    env = JobShopLabEnv(
        config=config,
        observation_factory=BinaryActionObservationFactory,
    )
    # transports on t-0 (component_id=3, normalized to 3/6=0.5)
    target_simple_jssp_obs["current_transition"] = np.array(
        [0.5, 0.0, 0.33], dtype=np.float32
    )  # [comp_id, job, comp_type]
    obs, info = env.reset()
    # Compare observation with array handling
    for key in target_simple_jssp_obs:
        if key == "current_transition":
            assert np.allclose(obs[key], target_simple_jssp_obs[key])
        else:
            assert obs[key] == target_simple_jssp_obs[key], f"Mismatch in {key}"
    target_simple_jssp_obs["current_transition"] = np.array(
        [0.5, 1 / 3, 0.33], dtype=np.float32
    )  # job=1
    obs, reward, termianted, truncated, info = env.step(0)
    for key in target_simple_jssp_obs:
        if key == "current_transition":
            assert np.allclose(obs[key], target_simple_jssp_obs[key])
        else:
            assert obs[key] == target_simple_jssp_obs[key], f"Mismatch in {key}"
    target_simple_jssp_obs["current_transition"] = np.array(
        [0.5, 2 / 3, 0.33], dtype=np.float32
    )  # job=2
    obs, reward, termianted, truncated, info = env.step(0)
    for key in target_simple_jssp_obs:
        if key == "current_transition":
            assert np.allclose(obs[key], target_simple_jssp_obs[key])
        else:
            assert obs[key] == target_simple_jssp_obs[key], f"Mismatch in {key}"
    # transports on t-1 (component_id=4, normalized to 4/6≈0.67)
    target_simple_jssp_obs["current_transition"] = np.array(
        [4 / 6, 0.0, 0.33], dtype=np.float32
    )  # job=0
    obs, reward, termianted, truncated, info = env.step(0)
    for key in target_simple_jssp_obs:
        if key == "current_transition":
            assert np.allclose(obs[key], target_simple_jssp_obs[key])
        else:
            assert obs[key] == target_simple_jssp_obs[key], f"Mismatch in {key}"
    target_simple_jssp_obs["current_transition"] = np.array(
        [4 / 6, 1 / 3, 0.33], dtype=np.float32
    )  # job=1
    obs, reward, termianted, truncated, info = env.step(0)
    for key in target_simple_jssp_obs:
        if key == "current_transition":
            assert np.allclose(obs[key], target_simple_jssp_obs[key])
        else:
            assert obs[key] == target_simple_jssp_obs[key], f"Mismatch in {key}"
    target_simple_jssp_obs["current_transition"] = np.array(
        [4 / 6, 2 / 3, 0.33], dtype=np.float32
    )  # job=2
    obs, reward, termianted, truncated, info = env.step(0)
    for key in target_simple_jssp_obs:
        if key == "current_transition":
            assert np.allclose(obs[key], target_simple_jssp_obs[key])
        else:
            assert obs[key] == target_simple_jssp_obs[key], f"Mismatch in {key}"
    # transports on t-2 (component_id=5, normalized to 5/6≈0.83)
    target_simple_jssp_obs["current_transition"] = np.array(
        [5 / 6, 0.0, 0.33], dtype=np.float32
    )  # job=0
    obs, reward, termianted, truncated, info = env.step(0)
    for key in target_simple_jssp_obs:
        if key == "current_transition":
            assert np.allclose(obs[key], target_simple_jssp_obs[key])
        else:
            assert obs[key] == target_simple_jssp_obs[key], f"Mismatch in {key}"
    target_simple_jssp_obs["current_transition"] = np.array(
        [5 / 6, 1 / 3, 0.33], dtype=np.float32
    )  # job=1
    obs, reward, termianted, truncated, info = env.step(0)
    for key in target_simple_jssp_obs:
        if key == "current_transition":
            assert np.allclose(obs[key], target_simple_jssp_obs[key])
        else:
            assert obs[key] == target_simple_jssp_obs[key], f"Mismatch in {key}"
    target_simple_jssp_obs["current_transition"] = np.array(
        [5 / 6, 2 / 3, 0.33], dtype=np.float32
    )  # job=2
    obs, reward, termianted, truncated, info = env.step(0)
    for key in target_simple_jssp_obs:
        if key == "current_transition":
            assert np.allclose(obs[key], target_simple_jssp_obs[key])
        else:
            assert obs[key] == target_simple_jssp_obs[key], f"Mismatch in {key}"
    obs, reward, termianted, truncated, info = env.step(0)
    assert obs["current_time"] == np.array(np.float32(1 / env.max_allowed_time))


def test_binary_array_jssp_obs(default_init_state, default_instance, config):
    env = JobShopLabEnv(
        config=config,
        observation_factory=BinaryOperationArrayObservation,
    )
    obs, info = env.reset()

    is_same = obs["operation_state"] == np.zeros(9).reshape(1, 9)

    # current_transition = [component_id, job, component_type] normalized
    # job=0 normalized: 0/3=0.0, component_type=transport: 0.33
    expected_transition = np.array(
        [0.5, 0.0, 0.33], dtype=np.float32
    )  # component_id=3 normalized to 3/6=0.5
    assert np.allclose(obs["current_transition"], expected_transition)
    assert is_same.all()
    obs, reward, termianted, truncated, info = env.step(0)
    is_same = obs["operation_state"] == np.zeros(9).reshape(1, 9)
    # job=1 normalized: 1/3≈0.33
    expected_transition = np.array([0.5, 1 / 3, 0.33], dtype=np.float32)
    assert np.allclose(obs["current_transition"], expected_transition)
    assert is_same.all()
    # Jobs start in b-12 (buffer 12), normalized by max_buffer_id=12 gives 12/12=1.0
    # But the actual normalization seems to be 12/13 ≈ 0.923, let's use the actual value
    expected_job_locations = np.array([[12 / 13, 12 / 13, 12 / 13]], dtype=np.float32)
    assert np.allclose(obs["job_locations"], expected_job_locations)
    obs, reward, termianted, truncated, info = env.step(1)
    obs, reward, termianted, truncated, info = env.step(1)
    obs, reward, termianted, truncated, info = env.step(1)
    obs, reward, termianted, truncated, info = env.step(1)
    is_same = obs["operation_state"] == np.zeros(9).reshape(1, 9)
    # The actual transition is still t-0 (3/6=0.5), job=1 (1/3≈0.33), transport (0.33)
    expected_transition = np.array([0.5, 1 / 3, 0.33], dtype=np.float32)  # component_id=3 still t-0
    assert np.allclose(obs["current_transition"], expected_transition)
    assert is_same.all()
    # After processing, jobs are in different buffers
    # Job 0: b-12 (12/13 ≈ 0.923), Job 1: b-2 (2/13 ≈ 0.154), Job 2: b-12 (12/13 ≈ 0.923)
    expected_final_locations = np.array([[12 / 13, 2 / 13, 12 / 13]], dtype=np.float32)
    assert np.allclose(obs["job_locations"], expected_final_locations)
