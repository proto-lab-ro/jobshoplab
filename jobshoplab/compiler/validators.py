from abc import ABC, abstractmethod
from logging import Logger

from jobshoplab.types import Config
from jobshoplab.utils import get_logger
from jobshoplab.utils.exceptions import NotImplementedError


class AbstractValidator(ABC):
    """
    Abstract base class for validators.
    """

    @abstractmethod
    def __init__(self, loglevel: int | str, config: Config, *args, **kwargs):
        """
        Initializes the AbstractValidator.

        Args:
            loglevel (int): The log level for the logger.
            config (Config): The configuration object.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        self.logger: Logger = get_logger(__name__, loglevel)
        self.config: Config = config

    @abstractmethod
    def validate(self, spec_dict: dict) -> None:
        """
        Validates the given spec_dict.

        Args:
            spec_dict (dict): The dictionary to be validated.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        raise NotImplementedError

    @abstractmethod
    def __repr__(self) -> str:
        """
        Returns a string representation of the validator.

        Returns:
            str: The string representation of the validator.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        raise NotImplementedError


class DummyValidator(AbstractValidator):
    """
    A dummy validator for testing purposes.
    """

    def __init__(self, loglevel: int | str, config: Config, *args, **kwargs):
        """
        Initializes the DummyValidator.

        Args:
            loglevel (int): The log level for the logger.
            config (Config): The configuration object.
        """
        super().__init__(loglevel, config)
        self.logger.debug(f"Init DummyValidator")

    def validate(self, spec_dict: dict) -> None:
        """
        Validates the given spec_dict.

        Args:
            spec_dict (dict): The dictionary to be validated.

        Returns:
            None

        """
        self.logger.debug(f"Validate")

    def __repr__(self) -> str:
        """
        Returns a string representation of the DummyValidator.

        Returns:
            str: The string representation of the DummyValidator.
        """
        return f"DummyValidator()"
