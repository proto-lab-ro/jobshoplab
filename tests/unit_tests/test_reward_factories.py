from dataclasses import replace

from jobshoplab.env.factories.rewards import BinaryActionJsspReward
from jobshoplab.types.state_types import FailTime, Time
from jobshoplab.utils.load_config import Config


def test_binary_action_jssp_reward(config: Config, default_instance, default_init_state_result):
    sparse_bias = config.reward_factory.binary_action_jssp_reward.sparse_bias
    dense_bias = config.reward_factory.binary_action_jssp_reward.dense_bias
    truncation_bias = config.reward_factory.binary_action_jssp_reward.truncation_bias
    reward_factory = BinaryActionJsspReward(
        0, config, default_instance, sparse_bias, dense_bias, truncation_bias, max_allowed_time=1000
    )
    state = default_init_state_result

    assert 0 == reward_factory.make(state, False, False)

    _state = replace(state.state, time=Time(500))
    state = replace(state, state=_state)
    assert 0.5 == round(
        reward_factory.make(state, True, False), 1
    )  # makespann based reward need to be round(1000 - 500 / 1000 - 10,1) = 0.5 where 10 is the lower bound wicht gets calculated after tassl (estimation of the lower bound)

    _state = replace(state.state, time=FailTime(reason="No time found. Returning 0"))
    state = replace(state, state=_state)
    assert truncation_bias == round(reward_factory.make(state, True, True))
