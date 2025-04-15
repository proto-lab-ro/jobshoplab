import logging
import random
from dataclasses import asdict
from functools import partial
from typing import Callable

import gymnasium as gym
import numpy as np
import torch
from heracless.utils.cfg_tree import as_lowercase

from jobshoplab.compiler import Compiler
from jobshoplab.env import rendering
from jobshoplab.env.factories import observations, rewards, actions
from jobshoplab.state_machine.core.state_machine import is_done
from jobshoplab.state_machine.middleware import middleware as middleware_collection
from jobshoplab.types import Config, InstanceConfig, StateMachineResult
from jobshoplab.utils import calculate_lower_bound, get_max_allowed_time
from jobshoplab.utils.exceptions import EnvDone
from jobshoplab.utils.load_config import load_config
from jobshoplab.utils.logger import get_logger
from jobshoplab.utils.rich_cli import render


class DependencyBuilder:
    """
    A builder class for managing dependencies in the JobShopLab environment.

    This class handles initialization and configuration of various components needed for
    the JobShopLab environment, including logging, random seeds, and factory objects
    for observations, rewards, rendering, and state simulation.

    Attributes:
        _config: Configuration object containing environment settings
        _logger: Logger instance for this class


        loglevel(loglevel: int | str | None) -> int | str:
            Gets loglevel from config or arguments

        logger(loglevel: int | str) -> tuple[any, int | str]:
            Creates and returns a logger instance

        seed(seed: int | None) -> int | None:
            Sets random seeds for reproducibility

        compiler(compiler: Compiler | None) -> Compiler:
            Returns compiler instance, creates new one if None provided

        lower_bound(instance_config: InstanceConfig) -> int:
            Calculates lower bound for given instance

        max_allowed_time(instance_config: InstanceConfig) -> int:
            Gets maximum allowed time for instance

        num_operations(instance_config: InstanceConfig) -> int:
            Returns total number of operations in instance

        observation_factory(observation_factory: any, log_level: int | str, instance: InstanceConfig) -> any:
            Builds observation factory instance

        reward_factory(reward_factory: any, log_level: int | str, instance: InstanceConfig, max_allowed_time: int) -> any:
            Builds reward factory instance

        render_backend(render_backend: any, log_level: int | str, instance: InstanceConfig) -> any:
            Builds render backend instance

        action_factory(action_factory: any, log_level: int | str, instance: InstanceConfig) -> any:
            Builds action_factory instance

        state_simulator(middleware: any, log_level: int | str, instance: InstanceConfig, action_factory: any, observation_factory: any) -> any:
            Builds state simulator instance

    Private Methods:
        _to_lowercase(string: str) -> str:
            Converts string to lowercase

        _config_args_getter(kwd_list: list[str]) -> dict:
            Gets configuration arguments from keyword list

        _get_args(log_level: str | int | None, instance: InstanceConfig, additional_args_kwd: list[str], additional_args: dict) -> dict:
            Builds arguments dictionary for factory creation

        _get_instance_from_config(conf_obj: str) -> str:
            Gets instance name from configuration

        _build_factory(module: any, env_arg: any, config_name: str, additional_args: dict, log_level: int | str, instance: InstanceConfig) -> any:
            Generic factory builder method
    """

    def __init__(self, config: Config | None, loglevel: int | str | None = None) -> None:
        self._config: Config = self.config(config)
        self._logger = get_logger(self.__str__(), "warning")

    def config(self, _config: Config | None) -> Config:
        if _config is None:
            _config: Config = load_config()
        return _config

    def loglevel(self, loglevel: int | str | None) -> int | str:
        # getting loglevel from config or setting it to default
        _loglevel = (
            self._config.env.loglevel
            if hasattr(self._config.env, "loglevel")
            else self._config.default_loglevel
        )
        # getting loglevel from arguments or setting it to default
        l_level = _loglevel if loglevel is None else loglevel
        return l_level

    def logger(self, loglevel: int | str) -> logging.Logger:
        return get_logger("JobShopLabEnv(gym.Env)", loglevel)

    def seed(self, seed: int | None) -> int | None:
        if hasattr(self._config.env, "seed"):
            config_seed: int = self._config.env.seed
        else:
            config_seed = None
        _seed = config_seed if seed is None else seed

        if _seed is not None:
            random.seed(seed)
            np.random.seed(seed)
            torch.manual_seed(seed)
        return seed

    def compiler(self, compiler: Compiler | None) -> Compiler:
        complier_loglevel = (
            self._config.compiler.loglevel
            if hasattr(self._config.compiler, "loglevel")
            else config.default_loglevel
        )

        if compiler is None:
            compiler = Compiler(
                config=self._config,
                loglevel=complier_loglevel,
            )
        return compiler

    def lower_bound(self, instance_config: InstanceConfig) -> int:
        return calculate_lower_bound(instance_config)

    def max_allowed_time(self, instance_config: InstanceConfig) -> int:
        return get_max_allowed_time(instance_config)

    def num_operations(self, instance_config: InstanceConfig) -> int:
        return len([o for j in instance_config.instance.specification for o in j.operations])

    def _to_lowercase(self, string: str) -> str:
        return as_lowercase(string)

    def _config_args_getter(self, kwd_list: list[str]) -> dict:
        conf_obj = self._config
        for kwd in kwd_list:
            _kwd = self._to_lowercase(kwd)
            if not hasattr(conf_obj, _kwd):
                self._logger.warning(f"No {_kwd} defined in config")
                return {}
            else:
                conf_obj = getattr(conf_obj, _kwd)
        return asdict(conf_obj)

    def _get_args(
        self,
        log_level: str | int | None,
        instance: InstanceConfig,
        additional_args_kwd: list[str],
        additional_args: dict,
    ) -> dict:
        args = self._config_args_getter(additional_args_kwd)
        additional_args.update(
            {"loglevel": log_level, "instance": instance, "config": self._config}
        )
        additional_args.update(**args)
        return additional_args

    def _get_instance_from_config(self, conf_obj: str) -> str:
        if not hasattr(self._config.env, conf_obj):
            raise ValueError(f"No {conf_obj} defined in config")
        return getattr(self._config.env, conf_obj)

    def _build_factory(
        self,
        module: any,
        env_arg: any,
        config_name: str,
        additional_args: dict,
        log_level: int | str,
        instance: InstanceConfig,
    ) -> any:
        # building args
        _factory_name = self._get_instance_from_config(config_name)
        additional_args_kwd = [config_name, _factory_name]
        args = self._get_args(log_level, instance, additional_args_kwd, additional_args)

        # if a instance is passed as argument we initialize it
        if not env_arg == None:
            if isinstance(env_arg, type(lambda: None)):  # checks if its a function
                return partial(env_arg, **args)
            return env_arg(**args)

        if not isinstance(env_arg, object):
            raise ValueError(f"Invalid {config_name} argument")

        _obj = getattr(module, _factory_name)
        if isinstance(_obj, type(lambda: None)):  # checks if its a function
            return partial(_obj, **args)
        return _obj(**args)

    def observation_factory(
        self, observation_factory: any, log_level: int | str, instance: InstanceConfig
    ) -> any:
        return self._build_factory(
            observations,
            observation_factory,
            "observation_factory",
            {},
            log_level,
            instance,
        )

    def reward_factory(
        self,
        reward_factory: any,
        log_level: int | str,
        instance: InstanceConfig,
        max_allowed_time: int,
    ) -> any:
        return self._build_factory(
            rewards,
            reward_factory,
            "reward_factory",
            {"max_allowed_time": max_allowed_time},
            log_level,
            instance,
        )

    def render_backend(
        self, render_backend: any, log_level: int | str, instance: InstanceConfig
    ) -> any:
        return self._build_factory(
            rendering,
            render_backend,
            "render_backend",
            {},
            log_level,
            instance,
        )

    def action_factory(
        self, action_factory: any, log_level: int | str, instance: InstanceConfig
    ) -> any:
        return self._build_factory(
            actions,
            action_factory,
            "action_factory",
            {},
            log_level,
            instance,
        )

    def state_simulator(
        self,
        middleware: any,
        log_level: int | str,
        instance: InstanceConfig,
        action_factory: any,
        observation_factory: any,
    ) -> any:
        return self._build_factory(
            middleware_collection,
            middleware,
            "middleware",
            {"action_factory": action_factory, "observation_factory": observation_factory},
            log_level,
            instance,
        )


class JobShopLabEnv(gym.Env):
    """
    JobShopLabEnv is an environment for job shop scheduling problems using the OpenAI Gym interface.

    The environment simulates a job shop scheduling problem where jobs need to be processed on machines
    in a specific order. The goal is to minimize the makespan (total completion time) while respecting
    all constraints.

        config (Config | None): Configuration object containing environment parameters. Defaults to None.
        seed (int | None): Random seed for reproducibility. Defaults to None.
        compiler (Compiler | None): Instance compiler to parse problem instances. Defaults to None.
        observation_factory (observations.ObservationFactory | None): ActionFactory for creating observations. Defaults to None.
        reward_factory (rewards.RewardFactory | None): ActionFactory for calculating rewards. Defaults to None.
        middleware (middleware_collection.Middleware | None): Middleware for state transitions. Defaults to None.
        action_factory (action_factory_collection.ActionFactory | None): ActionFactory for actions. Defaults to None.
        render_backend (Callable | None): Function for rendering the environment. Defaults to None.
        loglevel (int | str | None): Logging level. Defaults to None.

        logger (Logger): Logger instance for the environment
        config (Config): Configuration object
        loglevel (int|str): Current logging level
        seed (int): Random seed used
        instance (InstanceConfig): Problem instance configuration
        lower_bound (int): Lower bound on makespan
        max_allowed_time (int): Maximum allowed timesteps
        num_operations (int): Total number of operations
        reward_factory (rewards.RewardFactory): ActionFactory for calculating rewards
        render_backend (Callable): Function for rendering
        state_simulator (middleware_collection.Middleware): Middleware for state transitions
        init_state (StateMachineResult): Initial state
        observation_space (gym.Space): Space of possible observations
        action_space (gym.Space): Space of possible actions
        state (StateMachineResult): Current state
        history (tuple[StateMachineResult]): History of states
        truncated (bool): Whether episode was truncated
        terminated (bool): Whether episode terminated naturally
        done (bool): Whether episode is done (terminated or truncated)
        current_observation (dict): Current observation

        step(action): Takes an action and returns next observation, reward, done flags and info
        reset(seed): Resets environment to initial state with optional new seed
        render(): Renders current state of environment
        _is_done(): Checks if episode should terminate naturally
        _is_truncated(): Checks if episode should be truncated
        _get_info(): Returns info dict about current state
        _gen_render_metadata(): Generates metadata for rendering

        observation (dict): Current observation of environment state
        reward (float): Reward from last action
        terminated (bool): Whether episode terminated naturally
        truncated (bool): Whether episode was truncated
        info (dict): Additional information about current state
    """

    def __init__(
        self,
        config: Config | None = None,
        seed: int | None = None,
        compiler: Compiler | None = None,
        observation_factory: observations.ObservationFactory | None = None,
        reward_factory: rewards.RewardFactory | None = None,
        middleware: middleware_collection.Middleware | None = None,
        action_factory: actions.ActionFactory | None = None,
        render_backend: Callable | None = None,
        loglevel: int | str | None = None,
    ):
        """Initialize JobShopLabEnv environment.

        This class represents a Job Shop scheduling environment for reinforcement learning.
        It inherits from the base environment class and sets up the required components
        for simulation, observation generation, reward calculation and visualization.

        Args:
            config (Config, optional): Configuration object containing environment parameters.
                Defaults to None.
            seed (int, optional): Random seed for reproducibility. Defaults to None.
            compiler (Compiler, optional): Compiler instance for processing job shop problems.
                Defaults to None.
            observation_factory (ObservationFactory, optional): ActionFactory class for creating
                observations. Defaults to None.
            reward_factory (RewardFactory, optional): ActionFactory class for calculating rewards.
                Defaults to None.
            middleware (Middleware, optional): Middleware component for pre/post processing.
                Defaults to None.
            action_factory (ActionFactory, optional): ActionFactory component for action processing.
                Defaults to None.
            render_backend (Callable, optional): Backend function for visualization.
                Defaults to None.
            loglevel (int | str, optional): Logging level for the environment.
                Defaults to None.

        Attributes:
            init_args (dict): Dictionary storing initialization arguments
            current_observation (object): Latest observation from the environment
        """
        super(JobShopLabEnv, self).__init__()

        self.init_args = {
            "config": config,
            "seed": seed,
            "compiler": compiler,
            "observation_factory": observation_factory,
            "reward_factory": reward_factory,
            "middleware": middleware,
            "action_factory": action_factory,
            "render_backend": render_backend,
            "loglevel": loglevel,
        }
        self.current_observation = self.reset(seed)

    def _get_info(self):
        return {
            "no_op": len(self.history[-1].action.transitions) == 0,
            "terminated": self.terminated,
            "truncated": self.truncated,
            "makespan": self.state.state.time.time if self.terminated else None,
            "no_op_count": sum([int(len(h.action.transitions) == 0) for h in self.history]),
        }

    def _is_done(self):
        """
        Check if the episode is done.

        Returns:
            terminated (bool): True if the episode is terminated, False otherwise.
            truncated (bool): True if the episode is truncated, False otherwise.
        """
        return is_done(self.state)

    def _is_truncated(self):
        trunc = self.state_simulator.is_truncated()
        return trunc

    def step(self, action):
        """
        Take a step in the environment.

        Args:
            action: The action to take.

        Returns:
            observation: The observation after taking the action.
            reward: The reward after taking the action.
            terminated (bool): True if the episode is terminated, False otherwise.
            truncated (bool): True if the episode is truncated, False otherwise.
            info: Additional information.
        """
        if self.done:
            raise EnvDone()
        state_result, observation = self.state_simulator.step(self.state, action)
        if state_result.success:
            self.state = state_result
            self.history += (state_result,)
            self.terminated = self._is_done()
            self.truncated = self._is_truncated()
        else:
            self.truncated = True
            self.terminated = False
        self.done = self.terminated or self.truncated
        reward = self.reward_factory.make(self.state, self.terminated, self.truncated)
        return observation, reward, self.terminated, self.truncated, self._get_info()

    def reset(
        self,
        seed: int | None = None,
    ) -> tuple[dict, dict]:
        """Reset the environment to its initial state.

        This method initializes or reinitializes all the environment components including:
        - Configuration and logging setup
        - Instance compilation
        - Static instance-based values
        - Observation and reward factories
        - State machine and action_factory
        - Initial state and observation

        Args:
            seed (int | None): Random seed to use for this reset. Defaults to None.

        Returns:
            tuple[np.ndarray, dict]: A tuple containing:
                - Initial observation [dict space]
                - Empty info dictionary
        """
        builder = DependencyBuilder(self.init_args["config"], self.init_args["loglevel"])
        self.config: Config = builder.config(self.init_args["config"])
        self.loglevel: int | str = builder.loglevel(self.init_args["loglevel"])
        self.logger = builder.logger(self.loglevel)
        self.seed: int | None = builder.seed(seed)
        compiler: Compiler = builder.compiler(self.init_args["compiler"])

        # getting instance config and init state for further initialization
        self.instance: InstanceConfig
        _init_state: any
        self.instance, _init_state = compiler.compile()

        ### instance based static values
        self.lower_bound: int = builder.lower_bound(self.instance)
        self.max_allowed_time: int = builder.max_allowed_time(self.instance)
        self.num_operations: int = builder.num_operations(self.instance)

        # getting factories
        observation_factory: observations.ObservationFactory = builder.observation_factory(
            self.init_args["observation_factory"], self.loglevel, self.instance
        )

        self.reward_factory: rewards.RewardFactory = builder.reward_factory(
            self.init_args["reward_factory"], self.loglevel, self.instance, self.max_allowed_time
        )
        self.render_backend: Callable = builder.render_backend(
            self.init_args["render_backend"], self.loglevel, self.instance
        )

        # build state machine and action_factory
        action_factory: action_factory_collection.ActionFactory = builder.action_factory(
            self.init_args["action_factory"], self.loglevel, self.instance
        )

        self.state_simulator: middleware_collection.Middleware = builder.state_simulator(
            self.init_args["middleware"],
            self.loglevel,
            self.instance,
            action_factory,
            observation_factory,
        )

        self.init_state: StateMachineResult
        current_observation: np.ndarray
        self.init_state, current_observation = self.state_simulator.reset(_init_state)

        # setting init state history and flags
        self.observation_space: gym.Space = observation_factory.observation_space
        self.action_space: gym.Space = action_factory.action_space
        self.state: StateMachineResult = self.init_state
        self.history: tuple[StateMachineResult, ...] = tuple()
        self.truncated: bool = False
        self.terminated: bool = False
        self.done = False
        return current_observation, {}

    def _gen_render_metadata(self) -> dict:
        """
        Generate metadata dictionary for rendering.

        Creates a dictionary containing important state information about the
        current environment that can be used for rendering purposes.

        Returns:
            dict: Dictionary with metadata about the current environment state
        """
        return {
            "instance": self.instance.description,
            "env_hash": str(self.__hash__()),
            "step": len(self.history),
            "terminated": self.terminated,
            "truncated": self.truncated,
        }

    def get_config(self) -> Config:
        """
        Get the current environment configuration.

        Returns:
            Config: The configuration object for this environment
        """
        return self.config

    def render(
        self,
        mode: str = "normal",
    ) -> None:
        """
        Render the current state of the environment.

        Visualizes the current state using one of several available rendering backends.

        Args:
            mode: The rendering mode to use
                - "normal": Default rendering to console/terminal
                - "dashboard": Web-based dashboard visualization
                - "simulation": (Not implemented) Simulation-based visualization

        Returns:
            None: The rendering is displayed but not returned
        """
        match mode:
            case "normal":
                self.render_backend(history=self.history, instance=self.instance)
            case "dashboard":
                return rendering.render_in_dashboard(
                    loglevel=self.config.render_backend.render_in_dashboard.loglevel,
                    history=self.history,
                    instance=self.instance,
                    debug=self.config.render_backend.render_in_dashboard.debug,
                    port=self.config.render_backend.render_in_dashboard.port,
                )
            case "simulation":
                self.logger.error("Simulation mode is not implemented yet.")

            #     simulate(
            #         loglevel=self.config.render_backend.simulation.loglevel,
            #         instance=self.instance,
            #         state_hist=self.history,
            #         port=self.config.render_backend.simulation.port,
            #         bind_all=self.config.render_backend.simulation.bind_all,
            #     )
            case "debug":

                render(history=self.history, instance=self.instance)

            case _:
                raise ValueError(mode)


if __name__ == "__main__":
    # from jobshopsimulation.utils.utils import make_json_dump

    config = load_config()
    env = JobShopLabEnv(config)
    obs, info = env.reset()
    print(obs)
    print(10 * "-")
    done = False
    while not done:
        obs, reward, termianted, truncated, inf = env.step(1)
        done = termianted or truncated
    # env.render()
