from dataclasses import asdict
from logging import Logger
from typing import Any, Dict, Tuple

from jobshoplab.compiler import manipulators, mapper, repos, validators
from jobshoplab.types import Config, InstanceConfig, State
from jobshoplab.utils import get_args, get_logger


class Compiler:

    def __init__(
        self,
        config: Config,
        loglevel: int | str | str = "INFO",
        repo: None | repos.Repository = None,
        *args,
        **kwargs,
    ):
        """
        Initializes the Compiler object.

        Args:
            config (Config): The configuration object.
            loglevel (int | str, optional): The log level. Defaults to "INFO".
        """
        self.logger: Logger = get_logger(__name__, loglevel=loglevel)
        self.logger.debug("Compiler initialized")
        self.loglevel = loglevel
        # getting dependencies
        self.config = config

        self.repo: repos.Repository = (
            getattr(repos, self.config.compiler.repo)(
                **get_args(
                    self.logger,
                    {"loglevel": loglevel, "config": self.config},
                    config,
                    ["compiler", "repo"],
                )
            )
            if repo is None
            else repo
        )

        self.manipulators: tuple[manipulators.Manipulator, ...] = tuple(
            getattr(manipulators, manipulator)(**self._build_obj_args(manipulator))
            for manipulator in config.compiler.manipulators
        )

        self.validator: validators.AbstractValidator = getattr(
            validators, config.compiler.validator
        )(**self._build_obj_args(config.compiler.validator))

        self.init_state_mapper: mapper.DictToInitStateMapper = mapper.DictToInitStateMapper(
            **self._build_obj_args("DictToInitStateMapper")
        )
        self.instance_mapper: mapper.DictToInstanceMapper = mapper.DictToInstanceMapper(
            **self._build_obj_args("DictToInstanceMapper")
        )
        self.logger.debug("Dependencies loaded")

    def _build_obj_args(self, obj_name: str) -> Dict[str, Any]:
        """
        Builds the arguments for the specified object.

        Args:
            obj_name (str): The name of the object.

        Returns:
            Dict[str, Any]: The arguments for the object.
        """
        if hasattr(self.config, obj_name):
            obj_args = asdict(getattr(self.config, obj_name))
        else:
            obj_args = {}
        obj_args["loglevel"] = self.loglevel
        obj_args["config"] = self.config
        return obj_args

    def compile(self) -> Tuple[InstanceConfig, State]:
        """
        Compiles the provided input source to a instance and init_state dto.

        Returns:
            Tuple[InstanceConfig, State]: A tuple containing the compiled instance and initial state.
        """
        self.logger.info("Starting compilation")
        spec_dict: dict = self.repo.load_as_dict()

        self.logger.debug("Loaded spec_dict")
        self.validator.validate(spec_dict)  # raises if something is wrong

        instance = self.instance_mapper.map(spec_dict)
        init_state = self.init_state_mapper.map(spec_dict, instance)
        self.logger.debug("Mapped spec_dict")

        for manipulator in self.manipulators:
            instance, init_state = manipulator.manipulate(instance, init_state)

        self.logger.debug("Manipulated instance")
        self.logger.info("Compilation complete")
        return instance, init_state


if __name__ == "__main__":
    # Example usage
    pass

    config = load_config()
    compiler = Compiler(config, "debug", manipulators=[manipulators.InstanceRandomizer])
    # instance, init_state = compiler.compile()
    instance = compiler.compile()
    # print(instance)
    # print(init_state)
