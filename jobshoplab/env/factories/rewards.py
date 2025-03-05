from abc import ABC, abstractmethod
from logging import Logger

from jobshoplab.types import Config, InstanceConfig, StateMachineResult
from jobshoplab.types.state_types import NoTime
from jobshoplab.utils import calculate_lower_bound
from jobshoplab.utils.exceptions import InvalidValue
from jobshoplab.utils.logger import get_logger


class RewardFactory(ABC):
    """
    Abstract base class for reward factories.
    Args:
        loglevel (int): The log level.
        config (Config): The configuration object.
        instance (InstanceConfig): The instance configuration object.
    Raises:
        NotImplementedError: If the method has not been implemented.
    """

    @abstractmethod
    def __init__(
        self, loglevel: int | str, config: Config, instance: InstanceConfig, *args, **kwargs
    ):
        """
        Initialize the RewardFactory.

        Args:
            loglevel (int): The log level.
            config (Config): The configuration object.
        """
        self.logger: Logger = get_logger(__name__, loglevel)
        self.config: Config = config
        self.instance: InstanceConfig = instance

    @abstractmethod
    def make(self, state: StateMachineResult, terminated: bool, truncated: bool) -> float:
        """
        Create a reward based on the given state.

        Args:
            state (State): The state to create the reward from.

        Returns:
            float: The created reward.
        """

    @abstractmethod
    def __repr__(self) -> str:
        """
        Return a string representation of the RewardFactory.

        Returns:
            str: The string representation of the RewardFactory.
        """
        return ""


class DummyRewardFactory(RewardFactory):
    """
    A dummy reward factory for testing purposes.
    """

    def __init__(self, loglevel: int, config: Config, instance: InstanceConfig, *args, **kwargs):
        """
        Initialize the DummyRewardFactory.
        Args:
            loglevel (int): The log level.
            config (Config): The configuration object.
            instance (InstanceConfig): The instance configuration object.
        """
        super().__init__(loglevel, config, instance)
        self.logger.info("DummyRewardFactory initialized.")

    def make(self, state: StateMachineResult, done: bool) -> float:
        """
        Create a dummy reward.

        Args:
            state (State): The state to create the reward from.

        Returns:
            float: The created reward.
        """
        self.logger.debug("Creating dummy reward.")
        return 0.0


class BinaryActionJsspReward(RewardFactory):
    def __init__(
        self,
        loglevel: int | str,
        config: Config,
        instance: InstanceConfig,
        sparse_bias: float,
        dense_bias: float,
        truncation_bias: float,
        max_allowed_time: int,
    ):
        self.sparse_bias = sparse_bias
        self.dense_bias = dense_bias
        self.truncation_bias = truncation_bias
        self.max_allowed_time = max_allowed_time
        self.lower_bound = calculate_lower_bound(instance)
        self.instance = instance
        self.no_op_counter = 0
        self.total_no_ops = 0
        self.total_actions = 0
        self.num_operations = len(
            [o for job in instance.instance.specification for o in job.operations]
        )
        super().__init__(loglevel, config, instance)

    def _truncation_reward(self) -> float:
        return 1

    def _sparse_reward(self, state: StateMachineResult, terminated, truncated) -> float:
        if truncated:
            return (
                self.truncation_bias * self._truncation_reward()
            ) / self.sparse_bias  # devided by sparse bias to make sure not to overlay sparse bias (gets multiplied by sparse bias in make method)
        if not terminated:
            return 0.0
        # terminated
        if isinstance(state.state.time, NoTime):
            raise InvalidValue("time", state.state.time, "NoTime")
        time = state.state.time.time
        # makespan based
        return (self.max_allowed_time - time) / (self.max_allowed_time - self.lower_bound)

    def _dense_reward(self, state: StateMachineResult) -> float:
        self.total_actions += 1
        if len(state.action.transitions) == 0:
            self.no_op_counter += 1
            self.total_no_ops += 1
        else:
            self.no_op_counter = 0
        return (
            -int(self.no_op_counter >= len(self.instance.instance.specification))
            / self.num_operations
        )
        # ) + (int(len(state.action.transitions) == 0) / self.num_operations)

    def make(self, state: StateMachineResult, terminated, truncated) -> float:
        s_reward = self._sparse_reward(state, terminated, truncated)
        d_reward = self._dense_reward(state)
        return s_reward * self.sparse_bias + d_reward * self.dense_bias

    def __repr__(self) -> str:
        return (
            f"BinaryActionJsspReward(sparse_bias={self.sparse_bias}, dense_bias={self.dense_bias})"
        )
