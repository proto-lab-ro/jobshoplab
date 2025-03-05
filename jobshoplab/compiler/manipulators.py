import logging
import random
from abc import ABC, abstractmethod
from dataclasses import replace

import numpy as np

from jobshoplab.types import Config, DeterministicDurationConfig, InstanceConfig, State
from jobshoplab.utils import get_logger
from jobshoplab.utils.exceptions import NotImplementedError


class Manipulator(ABC):
    """
    Abstract base class for manipulators.
    """

    @abstractmethod
    def __init__(self, loglevel: int | str, config: Config, *args, **kwargs):
        """
        Initialize the Manipulator.

        Args:
            loglevel (int): The log level.
            config (Config): The configuration object.
        """
        self.config: Config = config
        self.logger: logging.Logger = get_logger(__name__, loglevel)

    @abstractmethod
    def manipulate(
        self, init_state: State, instance: InstanceConfig
    ) -> tuple[InstanceConfig, State]:
        """
        Perform manipulation on the initial state and instance configuration.

        Args:
            init_state (State): The initial state.
            instance (InstanceConfig): The instance configuration.

        Returns:
            tuple[InstanceConfig, State]: The manipulated instance configuration and state.
        """
        raise NotImplementedError

    @abstractmethod
    def __repr__(self) -> str:
        """
        Return a string representation of the Manipulator.

        Returns:
            str: The string representation.
        """
        raise NotImplementedError


class DummyManipulator(Manipulator):
    """
    A dummy manipulator implementation.
    """

    def __init__(self, loglevel: int | str, config: Config, *args, **kwargs):
        """
        Initialize the DummyManipulator.

        Args:
            loglevel (int): The log level.
            config (Config): The configuration object.
        """
        super().__init__(loglevel, config)
        self.logger.debug(f"Init DummyManipulator")

    def manipulate(
        self, instance_config: InstanceConfig, init_state: State
    ) -> tuple[InstanceConfig, State]:
        """
        Perform manipulation on the instance configuration and initial state.

        Args:
            instance_config (InstanceConfig): The instance configuration.
            init_state (State): The initial state.

        Returns:
            tuple[InstanceConfig, State]: The manipulated instance configuration and state.
        """
        self.logger.debug(f"Manipulate")
        return instance_config, init_state

    def __repr__(self) -> str:
        """
        Return a string representation of the DummyManipulator.

        Returns:
            str: The string representation.
        """
        return f"DummyManipulator()"


class InstanceRandomizer(Manipulator):
    """
    A manipulator that randomizes the instance configuration. but keeps the num jobs and machines the same.
    """

    def __init__(self, loglevel: int | str, config: Config, *args, **kwargs):
        super().__init__(loglevel, config, *args, **kwargs)
        self.logger.debug(f"Init InstanceRandomizer")

    def manipulate(
        self, instance_config: InstanceConfig, init_state: State
    ) -> tuple[InstanceConfig, State]:
        """
        Perform manipulation on the instance configuration and initial state.

        Args:
            instance_config (InstanceConfig): The instance configuration.
            init_state (State): The initial state.

        Returns:
            tuple[InstanceConfig, State]: The manipulated instance configuration and state.
        """
        self.logger.debug(f"Manipulate")
        jobs = instance_config.instance.specification
        operations = [o for j in jobs for o in j.operations]
        max_duration, min_duration = max([o.duration.duration for o in operations]), min(
            [o.duration.duration for o in operations]
        )
        new_jobs = tuple()
        for job in jobs:
            new_operations = tuple()
            operations = np.array(job.operations)
            operations = np.random.permutation(operations)
            for i, operation in enumerate(operations):
                _operation = replace(
                    operation,
                    duration=DeterministicDurationConfig(
                        duration=random.randrange(min_duration, max_duration)
                    ),
                    id=f"o-{job.id.split("-")[1]}-{i}",
                )
                new_operations += (_operation,)
            new_jobs += (replace(job, operations=new_operations),)
        instance_config = replace(
            instance_config, instance=replace(instance_config.instance, specification=new_jobs)
        )
        self.logger.debug(f"Manipulated instance_config {new_jobs}")
        return instance_config, init_state

    def __repr__(self) -> str:
        return f"InstanceRandomizer() "


if __name__ == "__main__":
    from jobshoplab.env.env import JobShopLabEnv

    env = JobShopLabEnv()
    state = env.state
    instance = env.instance_config
    instance_randomizer = InstanceRandomizer(loglevel="debug", config=env.config)
    new_instance, new_state = instance_randomizer.manipulate(
        instance_config=instance, init_state=state
    )
    assert (
        new_instance.instance.specification[1].operations
        != instance.instance.specification[1].operations
    )
