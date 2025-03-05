from abc import ABC, abstractmethod
from dataclasses import replace
from functools import partial
from logging import Logger
from typing import Any, Callable, Protocol, TypeAlias, Union


from jobshoplab.env.factories.actions import BinaryJobActionFactory, ActionFactory
from jobshoplab.env.factories.observations import *
from jobshoplab.state_machine.core.state_machine import step
from jobshoplab.state_machine.time_machines import force_jump_to_event, jump_to_event
from jobshoplab.types import Config, InstanceConfig, State, StateMachineResult
from jobshoplab.types.action_types import Action, ActionFactoryInfo
from jobshoplab.utils import get_logger
from jobshoplab.utils.exceptions import (
    InvalidValue,
    UnsuccessfulStateMachineResult,
)


class StableBaselines3ActionProtocol(Protocol):
    """Protocol for StableBaselines3 actions"""

    def __getitem__(self, key: Union[int, str]) -> Any: ...


StableBaselines3Action: TypeAlias = Union[StableBaselines3ActionProtocol, int, float, np.ndarray]
StableBaselines3Observation: TypeAlias = Union[np.ndarray, dict]


class SubTimeStepper:
    """A class to track and manage operation counts during time steps.

    This class keeps track of the number of no-operations and actual actions
    performed during simulation time steps, providing functionality to determine
    if the current step should be truncated.

    Attributes:
        no_op_counter (int): Counter for no-operation actions
        action_counter (int): Counter for actual actions/operations

    Methods:
        add_operation(action): Increments appropriate counter based on action type
        should_truncate(): Determines if current time step should be truncated
        __len__(): Returns total count of all operations
        reset(action): Resets counters and adds initial action
    """

    def __init__(self, truncation_active: bool = True) -> None:
        """
        Initialize a new SubTimeStepper instance.

        Args:
            truncation_active: Whether truncation is enabled
        """
        self.no_op_counter: int = 0
        self.action_counter: int = 0
        self.trunction_active: bool = truncation_active

    def add_operation(self, action: Action) -> None:
        """
        Add an operation to the counter based on its type.

        Args:
            action: The action to count
        """
        if action.action_factory_info == ActionFactoryInfo.NoOperation:
            self.no_op_counter += 1
        else:
            self.action_counter += 1

    def should_truncate(self) -> bool:
        """
        Determine if the episode should be truncated.

        Returns:
            bool: True if the episode should be truncated, False otherwise
        """
        if not self.trunction_active:
            return False
        if self.action_counter == 0:
            return True
        return False

    def __len__(self) -> int:
        """
        Get the total number of operations.

        Returns:
            int: Total number of operations
        """
        return self.no_op_counter + self.action_counter

    def reset(self, action: Action) -> None:
        """
        Reset counters and add an initial action.

        Args:
            action: The initial action
        """
        self.no_op_counter = 0
        self.action_counter = 0
        self.add_operation(action)


class Middleware(ABC):

    def __init__(
        self,
        loglevel: int | str,
        config: Config,
        instance: InstanceConfig,
        action_factory: ActionFactory,
        observation_factory: ObservationFactory,
        state_machine_step: Callable = step,
        *args,
        **kwargs,
    ):
        """
        Initialize the Middleware.

        Args:
            loglevel (int): The log level.
            config (Config): The configuration object.
        """
        self.logger: Logger = get_logger(__name__, loglevel)
        self.config: Config = config
        self.instance: InstanceConfig = instance
        self.action_factory: ActionFactory = action_factory
        self.action_space = self.action_factory.action_space
        self.state_machine_step = partial(
            state_machine_step,
            loglevel=config.state_machine.loglevel,
            instance=instance,
            config=config,
        )
        self.observation_factory = observation_factory

    @abstractmethod
    def step(
        self,
        state: StateMachineResult,
        action: StableBaselines3Action,
    ) -> tuple[StateMachineResult, StableBaselines3Observation]:
        pass

    @abstractmethod
    def reset(self, init_state) -> tuple[StateMachineResult, StableBaselines3Observation]:
        pass


class EventBasedBinaryActionMiddleware(Middleware):
    """Event-based middleware for handling binary actions in a state machine environment.

    This middleware class processes binary actions and manages state transitions based on events. It handles
    both regular operations and no-operation (NO-OP) cases, with support for truncation through a joker system.

    Args:
        loglevel (int | str): Logging level for the middleware.
        config (Config): Configuration settings for the middleware.
        instance (InstanceConfig): Instance-specific configuration settings.
        truncation_joker (int): Number of allowed truncations before episode termination.
        action_factory (BinaryJobActionFactory): ActionFactory for converting actions to binary format.
        observation_factory (ObservationFactory): ActionFactory for creating observations from state results.
        state_machine_step (Callable, optional): Function for executing state machine steps. Defaults to step.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.

    Attributes:
        truncation_joker (int): Current number of remaining truncation attempts.
        _init_truncation_joker (int): Initial number of truncation attempts.
        stepper (SubTimeStepper): Helper class for managing time steps.

    Methods:
        reset(init_state: State) -> tuple[StateMachineResult, StableBaselines3Observation]:
            Resets the middleware to its initial state.

        step(state: StateMachineResult, action: StableBaselines3Action) -> tuple[StateMachineResult, StableBaselines3Observation]:
            Executes one step in the environment with the given action.

        is_truncated() -> bool:
            Checks if the episode should be truncated based on the joker count.

    Raises:
        InvalidValue: When the state parameter is not of type StateMachineResult.
        UnsuccessfulStateMachineResult: When no valid transitions are available.
    """

    def __init__(
        self,
        loglevel: int | str,
        config: Config,
        instance: InstanceConfig,
        truncation_joker: int,
        truncation_active: bool,
        action_factory: BinaryJobActionFactory,
        observation_factory: ObservationFactory,
        state_machine_step: Callable = step,
        *args,
        **kwargs,
    ):
        super().__init__(
            loglevel=loglevel,
            config=config,
            instance=instance,
            action_factory=action_factory,
            observation_factory=observation_factory,
            state_machine_step=state_machine_step,
        )
        self.truncation_joker = truncation_joker
        self._init_truncation_joker = truncation_joker
        self.stepper = SubTimeStepper(truncation_active)

    def reset(self, init_state: State) -> tuple[StateMachineResult, StableBaselines3Observation]:
        """Reset the middleware with an initial state.

        This method resets the state machine to an initial state and generates the corresponding observation.
        It uses a dummy action to perform the first state machine step.

        Args:
            init_state (State): The initial state to reset the state machine to.

        Returns:
            tuple[StateMachineResult, StableBaselines3Observation]: A tuple containing:
                - StateMachineResult: The result of the state machine step after reset
                - StableBaselines3Observation: The observation generated from the state machine result

        Example:
            >>> middleware = Middleware()
            >>> init_state = State()
            >>> result, obs = middleware.reset(init_state)

        Notes:
            - The method uses a dummy action from the action_factory for the initial state machine step
            - Resets the truncation joker to its initial value
            - The 'done' flag in the observation is set to False during reset
        """

        state_result = self.state_machine_step(
            state=init_state, action=self.action_factory.get_dummy_action()
        )
        observation = self.observation_factory.make(state_result=state_result, done=False)
        self.truncation_joker = self._init_truncation_joker
        return state_result, observation

    def _is_no_op(self, action: Action):
        return action.action_factory_info == ActionFactoryInfo.NoOperation

    def _get_no_op_result(self, action: Action, state: StateMachineResult):

        match len(state.possible_transitions):
            case 0:
                raise UnsuccessfulStateMachineResult("No possible transitions")
            case 1:
                action = replace(action, time_machine=force_jump_to_event)
                state = self.state_machine_step(state=state.state, action=action)
                if len(state.possible_transitions) == 0:
                    raise UnsuccessfulStateMachineResult("No possible transitions")
                if self.stepper.should_truncate():
                    self.truncation_joker -= 1
                self.stepper.reset(action)
                return state

            case _:
                return StateMachineResult(
                    state=state.state,
                    sub_states=state.sub_states,
                    action=Action(
                        tuple(),
                        action_factory_info=ActionFactoryInfo.NoOperation,
                        time_machine=jump_to_event,
                    ),
                    success=True,
                    message="NO OPERATION",
                    possible_transitions=state.possible_transitions[1:],
                )

    def _is_state_machine_done(self, state: StateMachineResult):
        return len(state.possible_transitions) == 0

    def step(
        self, state: StateMachineResult, action: StableBaselines3Action
    ) -> tuple[StateMachineResult, StableBaselines3Observation]:
        """
        Executes one step in the state machine based on the given state and action.

        This method processes an action through the state machine, updates the state accordingly,
        and generates a corresponding observation.

        Args:
            state (StateMachineResult): The current state of the state machine. Must be a valid
                StateMachineResult object containing the state information.
            action (StableBaselines3Action): The action to be executed, in the format expected
                by StableBaselines3.

        Returns:
            tuple[StateMachineResult, StableBaselines3Observation]: A tuple containing:
                - StateMachineResult: The new state after executing the action
                - StableBaselines3Observation: The observation generated from the new state

        Raises:
            InvalidValue: If the provided state is not of type StateMachineResult

        Example:
            >>> new_state, observation = middleware.step(current_state, action)
            >>> print(observation)  # View the resulting observation

        Notes:
            - The action is first interpreted using the middleware's action_factory
            - If the action is a no-op, it's handled differently from regular actions
            - The method checks if the state machine has reached a terminal state
            - An observation is generated based on the new state and completion status
        """
        if not isinstance(state, StateMachineResult):
            raise InvalidValue("State must be of type StateMachineResult")
        action = self.action_factory.interpret(action, state)
        self.stepper.add_operation(action)
        if self._is_no_op(action):
            state = self._get_no_op_result(action, state)
        else:
            state = self.state_machine_step(state=state.state, action=action)

        done = self._is_state_machine_done(state)
        observation = self.observation_factory.make(state, done)
        return state, observation

    def is_truncated(self):
        return self.truncation_joker < 0
