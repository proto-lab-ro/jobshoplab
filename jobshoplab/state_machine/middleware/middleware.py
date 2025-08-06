"""
Middleware components for connecting the state machine to reinforcement learning environments.

This module provides middleware classes that serve as an interface between the JobShopLab
state machine and reinforcement learning environments, particularly those compatible with
StableBaselines3. It translates RL actions to state machine transitions and converts
state machine results into observations for the learning algorithms.
"""

from abc import ABC, abstractmethod
from dataclasses import replace
from functools import partial
from logging import Logger
from typing import Any, Callable, Protocol, TypeAlias, Union

import numpy as np

from jobshoplab.env.factories.actions import ActionFactory, BinaryJobActionFactory
from jobshoplab.env.factories.observations import ObservationFactory
from jobshoplab.state_machine.core.state_machine import step
from jobshoplab.state_machine.time_machines import force_jump_to_event, jump_to_event
from jobshoplab.types import Config, InstanceConfig, State, StateMachineResult
from jobshoplab.types.action_types import Action, ActionFactoryInfo
from jobshoplab.utils import get_logger
from jobshoplab.utils.exceptions import InvalidValue, UnsuccessfulStateMachineResult
from jobshoplab.utils.state_machine_utils import core_utils


class StableBaselines3ActionProtocol(Protocol):
    """
    Protocol defining the expected interface for StableBaselines3 actions.

    This protocol ensures that actions can be accessed via indexing,
    which is required for handling various action formats from StableBaselines3.
    """

    def __getitem__(self, key: Union[int, str]) -> Any: ...


# Type aliases for StableBaselines3 compatible actions and observations
StableBaselines3Action: TypeAlias = Union[StableBaselines3ActionProtocol, int, float, np.ndarray]
StableBaselines3Observation: TypeAlias = Union[np.ndarray, dict]


class SubTimeStepper:
    """
    Tracks and manages operation counts during simulation time steps.

    This class monitors the number of no-operations and actual actions
    performed during simulation time steps, and determines if the current
    step should be truncated based on predefined rules.

    Attributes:
        no_op_counter (int): Counter for no-operation actions
        action_counter (int): Counter for actual actions/operations
        truncation_active (bool): Whether truncation is enabled
    """

    def __init__(self, truncation_active: bool = True) -> None:
        """
        Initialize a new SubTimeStepper instance.

        Args:
            truncation_active: Flag to enable/disable truncation functionality
        """
        self.no_op_counter: int = 0
        self.action_counter: int = 0
        self.trunction_active: bool = truncation_active

    def add_operation(self, action: Action) -> None:
        """
        Increment the appropriate counter based on action type.

        This method categorizes actions as either no-operations or actual actions
        and increments the corresponding counter.

        Args:
            action: The action to categorize and count
        """
        if action.action_factory_info == ActionFactoryInfo.NoOperation:
            self.no_op_counter += 1
        else:
            self.action_counter += 1

    def should_truncate(self) -> bool:
        """
        Determine if the current episode should be truncated.

        This method evaluates whether to truncate the episode based on the
        pattern of actions taken. The episode should be truncated if:
        1. Truncation is enabled, and
        2. No actual actions have been taken (only no-operations)

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
        Get the total number of operations recorded.

        Returns:
            int: Sum of no-operations and actual actions
        """
        return self.no_op_counter + self.action_counter

    def reset(self, action: Action) -> None:
        """
        Reset all counters and add an initial action.

        This method clears all operation counters and registers the provided
        action as the first operation in the new sequence.

        Args:
            action: The initial action to register after resetting
        """
        self.no_op_counter = 0
        self.action_counter = 0
        self.add_operation(action)


class Middleware(ABC):
    """
    Abstract base class for state machine middleware components.

    Middleware components provide the interface between the state machine
    and reinforcement learning environments. They translate RL actions into
    state machine transitions and convert state machine results into
    observations suitable for RL algorithms.

    This abstract class defines the required interface for all middleware
    implementations in the system.
    """

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
        Initialize the middleware component.

        Args:
            loglevel: Logging level for middleware operations
            config: Global configuration settings
            instance: Problem instance configuration
            action_factory: Factory for creating/interpreting actions
            observation_factory: Factory for creating observations from states
            state_machine_step: Function to execute state machine steps (defaults to step)
            *args: Additional positional arguments for extensions
            **kwargs: Additional keyword arguments for extensions
        """
        self.logger: Logger = get_logger(__name__, loglevel)
        self.config: Config = config
        self.instance: InstanceConfig = instance
        self.action_factory: ActionFactory = action_factory
        self.action_space = self.action_factory.action_space

        # Create a partially applied state_machine_step function with fixed parameters
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
        """
        Execute one step in the environment with the given action.

        Args:
            state: Current state of the state machine
            action: Action from the RL agent to execute

        Returns:
            tuple: New state and corresponding observation
        """
        pass

    @abstractmethod
    def reset(self, init_state: State) -> tuple[StateMachineResult, StableBaselines3Observation]:
        """
        Reset the environment to an initial state.

        Args:
            init_state: The initial state to reset to

        Returns:
            tuple: Initial state and corresponding observation
        """
        pass


class EventBasedBinaryActionMiddleware(Middleware):
    """
    Event-based middleware for handling binary actions in a state machine environment.

    This middleware processes binary actions and manages state transitions based on events.
    It handles both regular operations and no-operation (NO-OP) cases, with support for
    truncation through a joker system that limits consecutive no-op actions.

    The middleware provides an interface between RL algorithms (particularly StableBaselines3)
    and the JobShopLab state machine, translating actions and observations between them.
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
        """
        Initialize the event-based binary action middleware.

        Args:
            loglevel: Logging level for middleware operations
            config: Global configuration settings
            instance: Problem instance configuration
            truncation_joker: Number of allowed truncations before episode termination
            truncation_active: Whether to enable truncation
            action_factory: Factory for creating/interpreting binary actions
            observation_factory: Factory for creating observations from states
            state_machine_step: Function to execute state machine steps
            *args: Additional positional arguments for extensions
            **kwargs: Additional keyword arguments for extensions
        """
        super().__init__(
            loglevel=loglevel,
            config=config,
            instance=instance,
            action_factory=action_factory,
            observation_factory=observation_factory,
            state_machine_step=state_machine_step,
        )
        # Initialize truncation system
        self.truncation_joker = truncation_joker
        self._init_truncation_joker = truncation_joker
        self.stepper = SubTimeStepper(truncation_active)

    def reset(self, init_state: State) -> tuple[StateMachineResult, StableBaselines3Observation]:
        """
        Reset the middleware to an initial state.

        This method initializes the state machine with the given initial state,
        performs a dummy action to set up the initial state machine result, and
        generates an initial observation. It also resets the truncation joker
        to its initial value.

        Args:
            init_state: The initial state to reset the state machine to

        Returns:
            tuple: Initial state result and corresponding observation
        """
        # Perform initial state machine step with a dummy action
        state_result = self.state_machine_step(
            state=init_state, action=self.action_factory.get_dummy_action()
        )

        # Create observation from the initial state
        observation = self.observation_factory.make(state_result=state_result, done=False)

        # Reset truncation joker counter
        self.truncation_joker = self._init_truncation_joker

        return state_result, observation

    def _is_no_op(self, action: Action) -> bool:
        """
        Check if an action is a no-operation.

        Args:
            action: The action to check

        Returns:
            bool: True if the action is a no-operation, False otherwise
        """
        return action.action_factory_info == ActionFactoryInfo.NoOperation

    def _get_no_op_result(self, action: Action, state: StateMachineResult) -> StateMachineResult:
        """
        Process a no-operation action based on the current state.

        This method handles no-operation actions differently depending on the
        number of possible transitions in the current state:

        - If no transitions are possible: Raise an exception
        - If one transition is possible: Force a jump to the next event
        - If multiple transitions are possible: Return a modified state with the first
          transition removed (this simulates choosing to do nothing when multiple
          options are available)

        Args:
            action: The no-operation action
            state: The current state machine result

        Returns:
            StateMachineResult: The result after processing the no-operation

        Raises:
            UnsuccessfulStateMachineResult: If no valid transitions are available
        """
        match len(state.possible_transitions):
            # No transitions available - nothing can be done
            case 0:
                raise UnsuccessfulStateMachineResult()

            # Exactly one transition available - force jump to next event
            case 1:
                # Use force_jump_to_event time machine
                action = replace(action, time_machine=force_jump_to_event)
                state = self.state_machine_step(state=state.state, action=action)
                # If there are still no possible transitions, the state machine is stuck
                if len(state.possible_transitions) == 0:
                    # Try one final step to resolve any remaining time dependencies before giving up
                    if core_utils.is_done(
                        state.state, self.instance
                    ):  # edge case where the state machine is done
                        return state
                    raise UnsuccessfulStateMachineResult()

                # Check for truncation (too many no-ops)
                if self.stepper.should_truncate():
                    self.truncation_joker -= 1

                # Reset stepper with this action
                self.stepper.reset(action)
                return state

            # Multiple transitions available - return modified state
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
                    # Remove the first possible transition (simulates skipping it)
                    possible_transitions=state.possible_transitions[1:],
                )

    def _is_state_machine_done(self, state: StateMachineResult) -> bool:
        """
        Check if the state machine has completed execution.

        A state machine is considered done when no more transitions are possible.

        Args:
            state: The current state machine result

        Returns:
            bool: True if the state machine is done, False otherwise
        """
        return len(state.possible_transitions) == 0

    def step(
        self, state: StateMachineResult, action: StableBaselines3Action
    ) -> tuple[StateMachineResult, StableBaselines3Observation]:
        """
        Execute one step in the state machine based on the given action.

        This method processes an action through the state machine, updates the
        state accordingly, and generates a corresponding observation for the
        RL algorithm.

        The method handles regular actions and no-operations differently:
        - Regular actions: Applied directly to the state machine
        - No-operations: Processed through special handling based on context

        Args:
            state: Current state of the state machine
            action: Action from the RL agent to execute

        Returns:
            tuple: New state and corresponding observation

        Raises:
            InvalidValue: If the provided state is not a valid StateMachineResult
        """
        # Validate input state
        if not isinstance(state, StateMachineResult):
            raise InvalidValue("State must be of type StateMachineResult")

        # Convert RL action to state machine action
        action = self.action_factory.interpret(action, state)

        # Record this operation
        self.stepper.add_operation(action)

        # Handle action based on its type
        if self._is_no_op(action):
            # Special handling for no-operations
            state = self._get_no_op_result(action, state)
        else:
            # Regular action processing
            state = self.state_machine_step(state=state.state, action=action)

        # Check if the state machine is done
        done = self._is_state_machine_done(state)

        # Create observation from the new state
        observation = self.observation_factory.make(state, done)
        return state, observation

    def is_truncated(self) -> bool:
        """
        Check if the current episode should be truncated.

        An episode is truncated when the truncation joker count goes negative,
        which happens after too many consecutive no-operation steps.

        Returns:
            bool: True if the episode should be truncated, False otherwise
        """
        return self.truncation_joker < 0
