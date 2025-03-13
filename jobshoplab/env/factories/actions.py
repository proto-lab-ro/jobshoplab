from abc import ABC, abstractmethod
from logging import Logger

from gymnasium import spaces

from jobshoplab.state_machine.time_machines import jump_to_event
from jobshoplab.types import Config, InstanceConfig, State
from jobshoplab.types.action_types import Action, ComponentTransition, ActionFactoryInfo
from jobshoplab.types.state_types import (
    JobState,
    MachineStateState,
    StateMachineResult,
    TransportState,
    TransportStateState,
)
from jobshoplab.utils import get_logger
from jobshoplab.utils.exceptions import ActionOutOfActionSpace, InvalidValue
from jobshoplab.utils.state_machine_utils import job_type_utils
from jobshoplab.utils.utils import get_id_int


class MinimalActionFactory(ABC):
    def __init__(self) -> None:
        pass

    def interpret(self, action: Action) -> Action:
        return action


class ActionFactory(ABC):
    """
    Abstract base class for action_factorys.
    """

    @abstractmethod
    def __init__(
        self,
        loglevel: int | str,
        config: Config,
        instance: InstanceConfig,
        action_space: spaces.Space,
        *args,
        **kwargs,
    ):
        """
        Initialize the ActionFactory.

        Args:
            loglevel (int): The log level.
            config (Config): The configuration object.
        """
        self.logger: Logger = get_logger(__name__, loglevel)
        self.config: Config = config
        self.instance: InstanceConfig = instance
        self.action_space: spaces.Space = action_space

    def get_dummy_action(self) -> Action:
        return Action(
            transitions=tuple(),
            action_factory_info=ActionFactoryInfo.NoOperation,
            time_machine=jump_to_event,
        )

    @abstractmethod
    def interpret(self, action: spaces.Space, *args, **kwargs) -> Action:
        """
        Interpret the given state.

        Args:
            state (State): The state to interpret.

        Returns:
            StateMachineResult: The result of the interpretation.
        """

    @abstractmethod
    def __repr__(self) -> str:
        """
        Return a string representation of the ActionFactory.

        Returns:
            str: The string representation of the ActionFactory.
        """
        return ""


class DummyActionFactory(ActionFactory):
    """
    A dummy action_factory for testing purposes.
    """

    def __init__(
        self, loglevel: int | str, config: Config, instance: InstanceConfig, *args, **kwargs
    ):
        """
        Initialize the DummyFactory.
        """
        action_space = spaces.Discrete(1)
        super().__init__(loglevel, config, instance, action_space)
        self.logger.info("DummyFactory initialized.")

    def interpret(self, action: spaces.Space) -> Action:
        """
        Interpret the given state.
        """
        self.logger.debug("DummyFactory.interpret() called.")
        return int(action)

    def __repr__(self) -> str:
        """
        Return a string representation of the DummyFactory.
        """
        return f"DummyFactory with action space:{self.action_space}"


class BinaryJobActionFactory(ActionFactory):
    def __init__(
        self,
        loglevel: int | str,
        config: Config,
        instance: InstanceConfig,
        *args,
        **kwargs,
    ):
        self.num_jobs = len(instance.instance.specification)
        action_space = spaces.Discrete(2, start=0)
        super().__init__(loglevel, config, instance, action_space, *args, **kwargs)
        self.dummy_action = Action(
            transitions=tuple(),
            action_factory_info=ActionFactoryInfo.NoOperation,
            time_machine=jump_to_event,
        )

    def interpret(
        self,
        action: int,
        state: StateMachineResult,
        *args,
        **kwargs,
    ) -> Action:
        if len(state.possible_transitions) == 0:
            raise InvalidValue(
                "state.possible_transitions", state.possible_transitions, "No possible transitions"
            )
        transition = state.possible_transitions[0]
        state: State = state.state

        if not self.action_space.contains(action):
            raise ActionOutOfActionSpace(action, self.action_space)
        int_action = int(action)

        if int_action == 0:
            # No Operation Schedule
            self.logger.info("No Operation Schedule")
            return Action(
                transitions=tuple(),
                action_factory_info=ActionFactoryInfo.NoOperation,
                time_machine=jump_to_event,
            )

        return Action(
            transitions=(transition,),
            action_factory_info=ActionFactoryInfo.Valid,
            time_machine=jump_to_event,
        )

    def __repr__(self) -> str:
        return f"SimpleJsspActionFactory with action space:{self.action_space}"


class MultiDiscreteActionSpaceFactory(ActionFactory):
    def __init__(
        self,
        loglevel: int | str,
        config: Config,
        instance: InstanceConfig,
        *args,
        **kwargs,
    ):
        self.num_jobs = len(instance.instance.specification)
        # action_space = spaces.Discrete(2, start=0)
        action_space = spaces.MultiDiscrete([2] * self.num_jobs)
        super().__init__(loglevel, config, instance, action_space, *args, **kwargs)

    def interpret(
        self,
        action: tuple[int],
        state: State,
        *args,
        **kwargs,
    ) -> Action:
        raise NotImplementedError
        if not self.action_space.contains(action):
            raise ActionOutOfActionSpace(action, self.action_space)

        # Map actions to jobs
        # action 0 is no operation schedule
        # action 1 is job 0, action 2 is job 1, etc.

        transitions = []
        for job_id_int, action in enumerate(action):
            if action == 0:
                continue

            elif action == 1:
                job: JobState = next(
                    filter(lambda j: get_id_int(j.id) == job_id_int, state.jobs), None
                )
                if job is None:
                    raise InvalidValue("job", job_id_int, "Job not found in state.")

                # TODO: Fails if there are no open operations
                next_op = job_type_utils.get_next_not_done_operation(job)

                # getting transporter
                transports = state.transports
                transporter = filter(
                    lambda x: get_id_int(x.id) == get_id_int(job.id),
                    transports,
                )

                transporter: TransportState | None = next(transporter, None)
                if transporter is None:
                    raise InvalidValue(
                        "transporter", next_op.id, "No Transporter found. this is a bug"
                    )
                # make transitions
                component_teleporter = ComponentTransition(
                    component_id=transporter.id,
                    new_state=TransportStateState.WORKING,
                    job_id=job.id,
                )

                component_transition = ComponentTransition(
                    component_id=next_op.machine_id,
                    new_state=MachineStateState.WORKING,
                    job_id=job.id,
                )

                transitions.append(component_teleporter)
                transitions.append(component_transition)

        return Action(
            transitions=tuple(transitions),
            action_factory_info=ActionFactoryInfo.Valid,
        )

    def __repr__(self) -> str:
        return f"SimpleJsspActionFactory with action space:{self.action_space}"
