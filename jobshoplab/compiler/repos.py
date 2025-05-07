from abc import ABC, abstractmethod
from logging import Logger
from pathlib import Path
from typing import Any, Dict
from venv import logger

import yaml

from jobshoplab.utils import get_logger
from jobshoplab.utils.exceptions import (FileNotFound, InvalidValue,
                                         NotImplementedError)
from jobshoplab.utils.load_config import Config


class Repository(ABC):
    """
    Abstract base class for repositories.
    """

    @abstractmethod
    def __init__(self, loglevel: int | str, config: Config, *args, **kwargs):
        """
        Initialize the Repository.

        Args:
            loglevel (int): The log level.
            config (Config): The configuration object.
        """
        self.logger: Logger = get_logger(__name__, loglevel)
        self.config: Config = config

    def check_dir(self, dir: Path | str) -> Path:
        """
        Check if the given directory exists.

        Args:
            dir (Path): The directory to check.
        """
        if not isinstance(dir, Path):
            if isinstance(dir, str):
                dir = Path(dir)
                logger.debug(f"Converted dir to Path object: {dir}")
                return dir
            else:
                raise InvalidValue(f"dir must be a Path object not {type(dir)}", dir)
        if not dir.exists():
            raise FileNotFound(f"Directory {dir} not found.")
        return dir

    @abstractmethod
    def _parse(self) -> Any:
        """
        Parse the given file.

        Returns:
            Any: The parsed data.
        """

    @abstractmethod
    def load_as_dict(self) -> Dict[str, Any]:
        """
        Load the repository data as a dictionary.

        Returns:
            Dict[str, Any]: The repository data as a dictionary.
        """

    @abstractmethod
    def __repr__(self) -> str:
        """
        Return a string representation of the Repository.

        Returns:
            str: The string representation of the Repository.
        """
        return ""


class DslRepository(Repository):
    """
    Repository for YAML files.
    """

    def __init__(self, dir: Path, loglevel: int | str, config: Config, *args, **kwargs):
        """
        Initialize the DslRepository.

        Args:
            dir (Path): The directory of the repository.
            loglevel (int): The log level.
            config (Config): The configuration object.
        """
        super().__init__(loglevel, config)
        self.dir = self.check_dir(dir)
        self.logger.debug(f"Init DslRepository with dir={self.dir}")

    def _parse(self) -> Dict[str, Any]:
        """
        Parse the given YAML file.

        Args:
            file (Path): The YAML file to parse.

        Returns:
            Dict[str, Any]: The parsed YAML data.
        """
        file = self.dir
        self.logger.debug(f"Parse file={file}")
        return yaml.safe_load(file.read_text())

    def load_as_dict(self) -> Dict[str, Any]:
        """
        Load the repository data as a dictionary.

        Returns:
            Dict[str, Any]: The repository data as a dictionary.
        """
        _dict = self._parse()
        self.logger.debug(f"Loaded as dict")
        return _dict

    def __repr__(self) -> str:
        """
        Return a string representation of the DslRepository.

        Returns:
            str: The string representation of the DslRepository.
        """
        return f"DslRepository(dir={self.dir})"


class DslStrRepository(Repository):
    def __init__(self, dsl_str: str, loglevel: int | str, config: Config, *args, **kwargs):
        """
        Initialize the DslStrRepository.

        Args:
            dir (Path): The directory of the repository.
            loglevel (int): The log level.
            config (Config): The configuration object.
        """
        super().__init__(loglevel=loglevel, config=config)
        self.dsl_str = dsl_str
        self.logger.debug(f"Init DslStrRepository with {self.dsl_str}")

    def _parse(self) -> Dict[str, Any]:
        return yaml.safe_load(self.dsl_str)

    def load_as_dict(self) -> Dict[str, Any]:
        """
        Load the repository data as a dictionary.

        Returns:
            Dict[str, Any]: The repository data as a dictionary.
        """
        _dict = self._parse()
        self.logger.debug(f"Loaded as dict")
        return _dict

    def __repr__(self) -> str:
        """
        Return a string representation of the DslRepository.

        Returns:
            str: The string representation of the DslRepository.
        """
        return f"DslStrRepository(dsl_str={self.dsl_str})"


class SpecRepository(Repository):
    """
    Repository for specification files.
    """

    def __init__(self, dir: Path, loglevel: int | str, config: Config, *args, **kwargs):
        """
        Initialize the SpecRepository.

        Args:
            dir (Path): The directory of the repository.
            loglevel (int): The log level.
            config (Config): The configuration object.
        """
        super().__init__(loglevel, config)
        if isinstance(dir, str):
            dir = Path(dir)
        self.dir = dir
        self.check_dir(dir)
        self.logger.debug(f"Init SpecRepository with dir={dir}")

    def _parse(self, file: Path) -> Dict[str, Any]:
        """
        Parse the given specification file.

        Args:
            file (Path): The specification file to parse.

        Returns:
            Dict[str, Any]: The parsed specification data.
        """
        self.logger.debug(f"Parse file={file}")
        with file.open("r") as f:
            lines = f.readlines()
        first_line = next((i for i, line in enumerate(lines) if len(line.split()) == 2), None)
        if first_line is None:
            raise InvalidValue(
                "Spec-File must contain 2 numbers in the first line with defines the number of machines and jobs.",
                "\n".join(lines),
            )

        return {
            "specification": "\n".join(
                lines[first_line + 1 :]
            ),  # adding line separator to the beginning of every line. using lines[first_line:] to skip the lines before the first line with 2 numbers
            "description": f"Specs from Spec-File {lines[first_line]}",
        }

    def map_to_instance_dsl_format(self, raw_str: str) -> str:
        """
        Map the raw string to the instance DSL format.

        Args:
            raw_str (str): The raw string to map.

        Returns:
            str: The mapped string in instance DSL format.
        """
        lines = raw_str.split("\n")
        num_machines = int(len(lines[0].split(" ")) / 2)
        dsl_str = (
            "|".join([f"(m{i},t)" for i in range(num_machines)]) + "\n"
        )  # building header of the dsl string
        for line_num, line in enumerate(lines):
            numbers_list = [int(number) for number in line.split()]
            dsl_line = f"j{line_num}|" + " ".join(
                [
                    f"({numbers_list[i]}, {numbers_list[i + 1]})"
                    for i in range(0, len(numbers_list), 2)
                ]
            )
            dsl_str += f"{dsl_line}\n"
        self.logger.debug(f"Mapped raw string to instance DSL format")

        return dsl_str

    def load_as_dict(self) -> Dict[str, Any]:
        """
        Load the repository data as a dictionary.

        Returns:
            Dict[str, Any]: The repository data as a dictionary.
        """
        _dict = self._parse(self.dir)
        _dict["specification"] = self.map_to_instance_dsl_format(_dict["specification"])

        self.logger.debug(f"Loaded as dict")
        _dict = {
            "title": "InstanceConfig",
            "instance_config": {"description": "Minimal Spec-File Instance", "instance": _dict},
        }
        return _dict

    def __repr__(self) -> str:
        """
        Return a string representation of the SpecRepository.

        Returns:
            str: The string representation of the SpecRepository.
        """
        return f"SpecRepository(dir={self.dir})"


class ApiRepo(Repository):
    """
    Repository for API data.
    """

    def __init__(self, _: Any, loglevel: int | str, config: Config, *args, **kwargs):
        """
        Initialize the ApiRepo.

        Args:
            _ (Any): Placeholder argument.
            loglevel (int): The log level.
            config (Config): The configuration object.
        """
        super().__init__(loglevel, config)
        self.logger.debug(f"Init ApiRepo with dir={dir}")

    def _parse(self, file: Path) -> Dict[str, Any]:
        """
        Parse the given file.

        Args:
            file (Path): The file to parse.

        Returns:
            Dict[str, Any]: The parsed data.
        """
        self.logger.debug(f"Parse file={file}")
        raise NotImplementedError

    def load_as_dict(self) -> Dict[str, Any]:
        """
        Load the repository data as a dictionary.

        Returns:
            Dict[str, Any]: The repository data as a dictionary.
        """
        self.logger.debug(f"Loaded as dict")
        raise NotImplementedError

    def __repr__(self) -> str:
        """
        Return a string representation of the ApiRepo.

        Returns:
            str: The string representation of the ApiRepo.
        """
        return f"ApiRepo()"
