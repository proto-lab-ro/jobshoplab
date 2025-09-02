from abc import ABC, abstractmethod
from collections import OrderedDict
from functools import partial
from logging import Logger
from typing import Callable

import gymnasium as gym
import numpy as np

from jobshoplab.types import ComponentTransition, Config, InstanceConfig, State
from jobshoplab.types.state_types import (
    JobState,
    MachineState,
    MachineStateState,
    OperationState,
    OperationStateState,
    StateMachineResult,
)
from jobshoplab.utils.exceptions import InvalidValue
from jobshoplab.utils.logger import get_logger
from jobshoplab.utils.utils import (
    get_component_id_int,
    get_component_type_int,
    get_id_int,
    get_max_allowed_time,
)

Observation = type("Observation", (object,), {})


class ObservationFactory(ABC):
    """
    Abstract base class for observation factories.
    Args:
        loglevel (int): The log level.
        config (Config): The configuration object.
        instance (InstanceConfig): The instance configuration object.
    """

    @abstractmethod
    def __init__(
        self, loglevel: int | str, config: Config, instance: InstanceConfig, *args, **kwargs
    ):
        """
        Initialize the ObservationFactory.

        Args:
            loglevel (int): The log level.
            config (Config): The configuration object.
        """
        self.logger: Logger = get_logger(__name__, loglevel)
        self.config: Config = config
        self.instance: InstanceConfig = instance

    @abstractmethod
    def make(self, state_result: StateMachineResult, *args, **kwargs) -> Observation:
        """
        Create an observation based on the given state.

        Args:
            state (State): The state to create the observation from.

        Returns:
            Observation: The created observation.
        """

    @abstractmethod
    def __repr__(self) -> str:
        """
        Return a string representation of the ObservationFactory.

        Returns:
            str: The string representation of the ObservationFactory.
        """
        return ""


class DummyObservationFactory(ObservationFactory):
    """
    A dummy observation factory for testing purposes.
    Args:

    """

    def __init__(self, loglevel: int, config: Config, instance: InstanceConfig, *args, **kwargs):
        """
        Initialize the DummyObservationFactory.
        """
        super().__init__(loglevel, config, instance)
        self.observation_space = gym.spaces.Box(low=0, high=1, shape=(1,), dtype=np.int64)
        for name, val in kwargs.items():
            setattr(self, name, val)

    def make(
        self,
        state_result: StateMachineResult,
        *args,
        **kwargs,
    ) -> np.ndarray:
        """
        Create a dummy observation.
        Args:
            state (State): The state to create the observation from.
        Returns:
            Observation: The dummy observation.
        """
        return self.observation_space.sample()

    def __repr__(self) -> str:
        """
        Return a string representation of the DummyObservationFactory.

        Returns:
            str: The string representation of the DummyObservationFactory.
        """
        return "DummyObservationFactory"


class PassTroughObservation(ObservationFactory):
    """
    Pass through observation factory the whole state
    Args:

    """

    def __init__(self, loglevel: int, config: Config, instance: InstanceConfig, *args, **kwargs):
        """
        Initialize the PassTroughObservation.
        """
        super().__init__(loglevel, config, instance)
        self.observation_space = None

    def make(
        self,
        state_result: StateMachineResult,
        *args,
        **kwargs,
    ):
        return state_result

    def __repr__(self) -> str:
        """
        Return a string representation of the PassTroughObservation.

        Returns:
            str: The string representation of the PassTroughObservation.
        """
        return "PassTroughObservation"


# class TasselObservation(ObservationFactory):
#     def __init__(self, loglevel: int, config: Config, instance: InstanceConfig, *args, **kwargs):
#         self.num_jobs: int = len(instance.instance.specification)
#         machines = instance.machines
#         self.num_machines: int = len(machines)
#         super().__init__(loglevel, config, instance)
#         # num_job_operations = len(instance.instance.specification[0].operations)
#         self.lower_bound = calculate_lower_bound(instance)
#         self.spaces = OrderedDict(
#             {
#                 "left_over_time": gym.spaces.Box(
#                     low=0, high=1, shape=(self.num_jobs,), dtype=np.int8
#                 ),  # left-over time for the currently performed operation on the job
#                 "percent_finished": gym.spaces.Box(
#                     low=0, high=1, shape=(self.num_jobs,), dtype=np.int8
#                 ),  # percentage of operations finished for a job
#                 "total_completion": gym.spaces.Box(
#                     low=0, high=1, shape=(self.num_jobs,), dtype=np.int8
#                 ),  # left-over time until total completion of the job, scaled by the longest job total completion time
#                 "time_until_next_machine_is_free": gym.spaces.Box(
#                     low=0, high=1, shape=(self.num_jobs,), dtype=np.int8
#                 ),  # time until the machine needed to perform the next job’s operation is free, scaled by the longest job total completion time
#                 "idle_since_last_op": gym.spaces.Box(
#                     low=0, high=1, shape=(self.num_jobs,), dtype=np.int8
#                 ),  # IDLE time since last job’s performed operation, scaled by the sum of durations of all operations
#                 "cum_idle_time": gym.spaces.Box(
#                     low=0, high=1, shape=(self.num_jobs,), dtype=np.int8
#                 ),  # cumulative job’s IDLE time in the schedule
#             }
#         )  # TODO: Add spaces
#         self.observation_space: gym.spaces.Dict = gym.spaces.Dict(self.spaces)  # type: ignore

#     def make(self, state: State) -> dict:
#         left_over_times = self._calculate_left_over_times(state)
#         percent_finished = self._calculate_percent_finished(state)
#         time_until_next_machine_is_free = self._calculate_time_until_next_machine_is_free(state)
#         total_completion = self._calculate_total_completion(state)
#         idle_since_last_op = self._calculate_idle_since_last_op(state)
#         cum_idle_time = self._calculate_cum_idle_time(state)

#         return {
#             "left_over_time": left_over_times,
#             "percent_finished": percent_finished,
#             "total_completion": total_completion,
#             "time_until_next_machine_is_free": time_until_next_machine_is_free,
#             "idle_since_last_op": idle_since_last_op,
#             "cum_idle_time": cum_idle_time,
#         }

#     def _calculate_cum_idle_time(self, state: State) -> list:
#         cum_idle_time = []

#         for jobState in state.jobs:
#             total_idle_time = 0

#             # Calculate idle time for the first operation
#             if jobState.operations:  # Check if there are any operations
#                 first_op = jobState.operations[0]
#                 if isinstance(first_op.start_time, Time):
#                     idle_time_first_op = first_op.start_time.time
#                     total_idle_time += idle_time_first_op
#                 else:
#                     idle_time_first_op = state.time.time
#                     total_idle_time += idle_time_first_op

#             # Loop through operations in pairs
#             for i in range(len(jobState.operations) - 1):
#                 current_op = jobState.operations[i]
#                 next_op = jobState.operations[i + 1]

#                 if (
#                     current_op.operation_state_state == OperationStateState.DONE
#                     and next_op.operation_state_state != OperationStateState.IDLE
#                 ):
#                     # Calculate idle time only if the current operation is done
#                     idle_duration = next_op.start_time.time - current_op.end_time.time
#                     total_idle_time += idle_duration

#                 elif (
#                     current_op.operation_state_state == OperationStateState.DONE
#                     and next_op.operation_state_state == OperationStateState.IDLE
#                 ):
#                     idle_duration = state.time.time - current_op.end_time.time
#                     total_idle_time += idle_duration

#             cum_idle_time.append(total_idle_time)

#         # Scale total idle time by an appropriate factor if necessary
#         max_idle_time = self.lower_bound * 2
#         cum_idle_time_scaled = [min(1, total_idle / max_idle_time) for total_idle in cum_idle_time]

#         return cum_idle_time_scaled

#     def _calculate_idle_since_last_op(self, state: State) -> list:
#         idle_since_last_op = []
#         for jobState in state.jobs:
#             # check if there is an processing operation
#             processing_op = job_type_utils.get_processing_operation(jobState)
#             if processing_op:
#                 idle_since_last_op.append(0)
#                 continue

#             # Find the most recent completed operation
#             for op in reversed(jobState.operations):  # Reverse to find the last completed operation
#                 last_op_end_time = None
#                 if op.operation_state_state == OperationStateState.DONE:
#                     last_op_end_time = op.end_time.time
#                     break

#             # Calculate idle time since last operation
#             if last_op_end_time:
#                 idle_time = state.time.time - last_op_end_time
#             else:
#                 # If no operation has been completed yet, idle time is 0
#                 idle_time = 0

#             idle_since_last_op.append(idle_time)
#         return idle_since_last_op

#     def _calculate_left_over_times(self, state: State) -> list:
#         left_over_times = []
#         for jobState in state.jobs:
#             processing_op = job_type_utils.get_processing_operation(jobState)
#             left_over_time = (processing_op.end_time.time - state.time.time) if processing_op else 0
#             left_over_times.append(left_over_time)
#         return left_over_times

#     def _calculate_percent_finished(self, state: State) -> list:
#         percent_finished = []
#         for jobState in state.jobs:
#             job_config = job_type_utils.get_job_config_by_id(
#                 self.instance.instance.specification, jobState.id
#             )
#             total_duration = sum(
#                 op.duration.time
#                 for op in job_config.operations
#                 if isinstance(op.duration, DeterministicTimeConfig)
#             )

#             completed_duration = sum(
#                 job_type_utils.get_operation_config_by_id(
#                     self.instance.instance.specification, op.id
#                 ).duration.time
#                 for op in jobState.operations
#                 if op.operation_state_state == OperationStateState.DONE
#             )

#             percent_finished.append(completed_duration / total_duration)
#         return percent_finished

#     def _calculate_time_until_next_machine_is_free(self, state: State) -> list:
#         time_until_next_machine_is_free = []
#         for jobState in state.jobs:
#             last_op = jobState.operations[-1]
#             if last_op.operation_state_state != OperationStateState.IDLE:
#                 machien_free_time = 0
#             else:
#                 next_idle_op = job_type_utils.get_next_idle_operation(jobState)
#                 next_machine = next_idle_op.machine_id
#                 next_machine_state = next(filter(lambda x: x.id == next_machine, state.machines))
#                 machien_free_time = (
#                     next_machine_state.occupied_till.time
#                     if isinstance(next_machine_state.occupied_till, Time)
#                     else 0
#                 )

#             time_until_next_machine_is_free.append(machien_free_time)
#         return time_until_next_machine_is_free

#     def _calculate_total_completion(self, state: State) -> list:
#         total_completion = []
#         for jobState in state.jobs:
#             job_config = job_type_utils.get_job_config_by_id(
#                 self.instance.instance.specification, jobState.id
#             )

#             idle_ops = filter(
#                 lambda x: x.operation_state_state == OperationStateState.IDLE, jobState.operations
#             )
#             idle_ops_config = [
#                 job_type_utils.get_operation_config_by_id((job_config,), op.id) for op in idle_ops
#             ]
#             sum_idle_durations = sum(idle_op.duration.time for idle_op in idle_ops_config)

#             processing_ops = filter(
#                 lambda x: x.operation_state_state == OperationStateState.PROCESSING,
#                 jobState.operations,
#             )
#             remaining_processing_times = [
#                 op.end_time.time - state.time.time for op in processing_ops
#             ]
#             max_remaining_processing_time = (
#                 max(remaining_processing_times) if remaining_processing_times else 0
#             )

#             job_total_completion = (
#                 sum_idle_durations + max_remaining_processing_time
#             ) / self.lower_bound
#             total_completion.append(job_total_completion)

#         return total_completion

#     def __repr__(self) -> str:
#         """
#         Return a string representation of the TasselObservationFactory.

#         Returns:
#             str: The string representation of the TasselObservationFactory.
#         """
#         return f"TasselObservationFactory with observation_space {self.observation_space}"


class SimpleJsspObservationFactory(ObservationFactory):
    def __init__(
        self,
        loglevel: int,
        config: Config,
        instance: InstanceConfig,
        *args,
        **kwargs,
    ):
        """
        Initialize the SimpleJsspObservationFactory.

        Args:
            loglevel (int): The log level.
            config (Config): The configuration object.
            instance (InstanceConfig): The instance configuration object.
        """
        self.num_jobs: int = len(instance.instance.specification)
        self.get_component_id: Callable[[str], int] = partial(
            get_component_id_int, (instance.machines + instance.transports)
        )
        self.num_machines: int = len(instance.machines)
        self.num_components: int = len(instance.machines + instance.transports)
        super().__init__(loglevel, config, instance)
        self.max_allowed_time = get_max_allowed_time(instance)
        self.spaces = OrderedDict(
            {
                "job_running": gym.spaces.Box(low=0, high=1, shape=(self.num_jobs,), dtype=np.int8),
                "job_executed_on_machine": gym.spaces.Box(
                    low=0, high=1, shape=(self.num_jobs, self.num_machines), dtype=np.int8
                ),
                "job_progression": gym.spaces.Box(
                    low=0, high=self.num_jobs, shape=(self.num_jobs,), dtype=np.int32
                ),
                "machine_running": gym.spaces.Box(
                    low=0, high=1, shape=(self.num_machines,), dtype=np.int8
                ),
                "machine_progression": gym.spaces.Box(
                    low=0, high=self.num_jobs, shape=(self.num_machines,), dtype=np.int32
                ),
                "available_jobs": gym.spaces.Box(
                    low=0, high=1, shape=(self.num_jobs,), dtype=np.int8
                ),
                "current_time": gym.spaces.Box(low=0, high=1.0, shape=(1,), dtype=np.float32),
            }
        )
        self.observation_space: gym.spaces.Dict = gym.spaces.Dict(self.spaces)  # type: ignore

    def _get_finished_operations_for_machine(
        self, machine: MachineState, jobs: tuple[JobState, ...]
    ) -> tuple[OperationState, ...]:
        operations = (op for job in jobs for op in job.operations if op.machine_id == machine.id)
        return tuple(
            filter(lambda x: x.operation_state_state == OperationStateState.DONE, operations)
        )

    def make(self, state_result: StateMachineResult, done: bool = None) -> dict:
        """
        Create an observation.

        Args:
            state (State): The state to create the observation from.

        Returns:
            dict: The observation.
        """
        state: State = state_result.state
        jobs: list[JobState] = sorted(state.jobs, key=lambda x: x.id)
        job_running: tuple[bool, ...] = tuple(
            any(op.operation_state_state == OperationStateState.PROCESSING for op in job.operations)
            for job in jobs
        )

        available_jobs: tuple[bool, ...] = tuple(
            any(op.operation_state_state == OperationStateState.IDLE for op in job.operations)
            and not job_running[get_id_int(job.id)] > 0
            for job in jobs
        )
        job_executed_on_machine: tuple[tuple[bool, ...], ...] = tuple()
        job_progression: list[int] = list(0 for job in jobs)
        for job in jobs:
            e_tuple: list[bool] = [False for _ in range(self.num_machines)]
            finished_operations = tuple(
                filter(
                    lambda x: x.operation_state_state == OperationStateState.DONE,
                    job.operations,
                )
            )
            for op in finished_operations:
                e_tuple[get_id_int(op.machine_id)] = True
            job_executed_on_machine += (tuple(e_tuple),)
            job_progression[get_id_int(job.id)] = len(finished_operations)

        machines: tuple[MachineState, ...] = tuple(
            sorted(
                state.machines,
                key=lambda x: x.id,
            )
        )
        machine_running: tuple[bool, ...] = tuple(
            machine.state == MachineStateState.WORKING for machine in machines
        )
        machine_progression: tuple[int, ...] = tuple(
            len(self._get_finished_operations_for_machine(machine, tuple(jobs)))
            for machine in machines
        )
        current_time = np.array([np.float32(state.time.time / self.max_allowed_time)])

        return {
            "job_running": job_running,
            "job_executed_on_machine": job_executed_on_machine,
            "job_progression": tuple(job_progression),
            "machine_running": machine_running,
            "machine_progression": machine_progression,
            "available_jobs": available_jobs,
            "current_time": current_time,
        }

    def __repr__(self) -> str:
        """
        Return a string representation of the SimpleJsspObservationFactory.

        Returns:
            str: The string representation of the SimpleJsspObservationFactory.
        """
        return f"SimpleJsspObservationFactory with observation_space {self.observation_space}"


class BinaryActionObservationFactory(SimpleJsspObservationFactory):
    def __init__(
        self,
        loglevel: int,
        config: Config,
        instance: InstanceConfig,
        *args,
        **kwargs,
    ):
        """
        Initialize the SimpleJsspObservationFactory.

        Args:
            loglevel (int): The log level.
            config (Config): The configuration object.
            instance (InstanceConfig): The instance configuration object.
        """
        super().__init__(loglevel, config, instance)
        self.spaces["current_transition"] = gym.spaces.Box(
            low=0, high=1, shape=(3,), dtype=np.float32
        )
        self.spaces.move_to_end("current_transition")
        self.observation_space: gym.spaces.Dict = gym.spaces.Dict(self.spaces)

    def make(
        self,
        state_result: StateMachineResult,
        done: bool,
    ) -> dict:
        """
        Create an observation.

        Args:
            state (State): The state to create the observation from.

        Returns:
            dict: The observation.
        """
        state = state_result
        obs = super().make(state)
        if not done:
            if len(state.possible_transitions) == 0:
                raise InvalidValue("No possible transitions", state)
            transition: ComponentTransition = state.possible_transitions[0]
            current_job = np.float32(
                (get_id_int(transition.job_id) if transition.job_id else len(state.state.jobs))
                / len(state.state.jobs)
            )
            _current_component_id, total_components = self.get_component_id(transition.component_id)
            current_component_id = np.float32(_current_component_id / total_components)
            current_component_type = np.float32(get_component_type_int(transition.component_id))
        else:
            current_job = np.float32(1)
            current_component_id = np.float32(1)
            current_component_type = np.float32(1)

        arr = np.array([current_component_id, current_job, current_component_type]).astype(
            np.float32
        )
        obs["current_transition"] = arr
        return obs

    def __repr__(self) -> str:
        """
        Return a string representation of the SimpleJsspObservationFactory.

        Returns:
            str: The string representation of the SimpleJsspObservationFactory.
        """
        return f"SimpleJsspObservationFactory with observation_space {self.observation_space}"


class OperationArrayObservation(ObservationFactory):
    def __init__(self, loglevel: int, config: Config, instance: InstanceConfig, *args, **kwargs):
        num_operations = sum(len(job.operations) for job in instance.instance.specification)
        num_jobs = len(instance.instance.specification)

        super().__init__(loglevel, config, instance)
        #! todo unsafe code get max from all buffers
        self.max_buffer_id = (
            len(instance.buffers) + len(instance.machines) * 3 + len(instance.transports)
        ) - 1  # all buffers, 3 buffers per machine and 1 buffer per transport (-1 because buffers start at 0)
        self.spaces = OrderedDict(
            {
                "operation_state": gym.spaces.Box(
                    low=0, high=1, shape=(1, num_operations), dtype=np.float32
                ),
                "job_locations": gym.spaces.Box(
                    low=0, high=1.0, shape=(1, num_jobs), dtype=np.float32
                ),
            }
        )

        self.num_jobs: int = len(instance.instance.specification)
        self.get_component_id: Callable[[str], int] = partial(
            get_component_id_int, (instance.machines + instance.transports)
        )
        self.num_machines: int = len(instance.machines)
        self.num_components: int = len(instance.machines + instance.transports)
        self.max_allowed_time = get_max_allowed_time(instance)
        self.observation_space: gym.spaces.Dict = gym.spaces.Dict(self.spaces)

    def make(self, state_result: StateMachineResult) -> dict:
        operation_state = []
        for job in state_result.state.jobs:
            for operation in job.operations:
                match operation.operation_state_state:
                    case OperationStateState.IDLE:
                        operation_state.append(0)
                    case OperationStateState.PROCESSING:
                        if operation.start_time is None or operation.end_time is None:
                            raise InvalidValue("Operation start or end time is None", operation)
                        duration = operation.end_time.time - operation.start_time.time  # type: ignore
                        progress = (
                            state_result.state.time.time - operation.start_time.time
                        ) / duration  # type: ignore
                        operation_state.append(progress)
                    case OperationStateState.DONE:
                        operation_state.append(1)
                    case _:
                        raise NotImplementedError
        job_locations = [job.location for job in state_result.state.jobs]
        if any(not j.startswith("b") for j in job_locations):
            raise InvalidValue("Job location must be a buffer", job_locations)
        job_ints = [np.float32(int(j.split("-")[1]) / self.max_buffer_id) for j in job_locations]
        return {
            "operation_state": np.array([operation_state]).astype(np.float32),
            "job_locations": np.array([job_ints], dtype=np.float32),
        }

    def __repr__(self) -> str:
        """
        Return a string representation of the OperationArrayObservation.

        Returns:
            str: The string representation of the OperationArrayObservation.
        """
        return f"OperationArrayObservation with observation_space {self.observation_space}"


class BinaryOperationArrayObservation(OperationArrayObservation):
    def __init__(
        self,
        loglevel: int,
        config: Config,
        instance: InstanceConfig,
        *args,
        **kwargs,
    ):
        super().__init__(loglevel, config, instance)
        self.num_jobs: int = len(instance.instance.specification)
        self.spaces["current_transition"] = gym.spaces.Box(
            low=0, high=1, shape=(3,), dtype=np.float32
        )
        self.spaces.move_to_end("current_transition")
        self.observation_space: gym.spaces.Dict = gym.spaces.Dict(self.spaces)

    def make(
        self,
        state_result: StateMachineResult,
        done: bool,
    ) -> dict:
        """
        Create an observation.

        Args:
            state (State): The state to create the observation from.

        Returns:
            dict: The observation.
        """
        state = state_result
        obs = super().make(state)
        if not done:
            if len(state.possible_transitions) == 0:
                raise InvalidValue("No possible transitions", state)
            transition: ComponentTransition = state.possible_transitions[0]
            current_job = np.float32(
                (get_id_int(transition.job_id) if transition.job_id else len(self.num_jobs))
                / self.num_jobs
            )
            _current_component_id, total_components = self.get_component_id(transition.component_id)
            current_component_id = np.float32(_current_component_id / total_components)
            current_component_type = np.float32(get_component_type_int(transition.component_id))
        else:
            current_job = np.float32(1)
            current_component_id = np.float32(1)
            current_component_type = np.float32(1)

        arr = np.array([current_component_id, current_job, current_component_type]).astype(
            np.float32
        )
        obs["current_transition"] = arr
        return obs

    def __repr__(self) -> str:
        """
        Return a string representation of the BinaryOperationArrayObservation.

        Returns:
            str: The string representation of the BinaryOperationArrayObservation.
        """
        return f"BinaryOperationArrayObservation with observation_space {self.observation_space}"






class TasselJsspObservation(ObservationFactory):
    def __init__(self, loglevel: int, config: Config, instance: InstanceConfig, *args, **kwargs):
        super().__init__(loglevel, config, instance)

        self.num_jobs: int = len(instance.instance.specification)
        self.get_component_id: Callable[[str], int] = partial(
            get_component_id_int, (instance.machines + instance.transports)
        )
        self.num_machines: int = len(instance.machines)
        self.num_components: int = len(instance.machines + instance.transports)
        self.max_allowed_time = get_max_allowed_time(instance)


        self.spaces = OrderedDict(
            {    "allocatable": gym.spaces.MultiBinary(
                    self.num_jobs
                    #A Boolean to represent if the job can be allocated
                ),
                "left_over_time": gym.spaces.Box(
                    low=0, high=1, shape=(self.num_jobs,), dtype=np.int8
                ),  # left-over time for the currently performed operation on the job
                "percent_finished": gym.spaces.Box(
                    low=0, high=1, shape=(self.num_jobs,), dtype=np.int8
                ),  # percentage of operations finished for a job
                "total_completion": gym.spaces.Box(
                    low=0, high=1, shape=(self.num_jobs,), dtype=np.int8
                ),  # left-over time until total completion of the job, scaled by the longest job total completion time
                "time_until_next_machine_is_free": gym.spaces.Box(
                    low=0, high=1, shape=(self.num_jobs,), dtype=np.int8
                ),  # time until the machine needed to perform the next job’s operation is free, scaled by the longest job total completion time
                "idle_since_last_op": gym.spaces.Box(
                    low=0, high=1, shape=(self.num_jobs,), dtype=np.int8
                ),  # IDLE time since last job’s performed operation, scaled by the sum of durations of all operations
                "cum_idle_time": gym.spaces.Box(
                    low=0, high=1, shape=(self.num_jobs,), dtype=np.int8
                ),  # cumulative job’s IDLE time in the schedule
            }
        )
        self.observation_space: gym.spaces.Dict = gym.spaces.Dict(self.spaces)




    def make(self, state_result: StateMachineResult, done: bool) -> dict:
        state = state_result
        allocatable = self._calculate_allocatable(state)
        left_over_times = self._calculate_left_over_times(state)
        percent_finished = self._calculate_percent_finished(state)
        time_until_next_machine_is_free = self._calculate_time_until_next_machine_is_free(state)
        total_completion = self._calculate_total_completion(state)
        idle_since_last_op = self._calculate_idle_since_last_op(state)
        cum_idle_time = self._calculate_cum_idle_time(state)

        observation_dict = {
            "allocatable": allocatable,
            "left_over_time": left_over_times,
            "percent_finished": percent_finished,
            "total_completion": total_completion,
            "time_until_next_machine_is_free": time_until_next_machine_is_free,
            "idle_since_last_op": idle_since_last_op,
            "cum_idle_time": cum_idle_time,
        }
        self.logger.debug(f"Observation: {observation_dict}")
        return observation_dict
    

    def _calculate_allocatable(self, state: State) -> list:
        """Calculate if jobs can be allocated to machines."""
        allocatable = []
        for job in state.state.jobs:
            # A job is allocatable if it has any IDLE operations and no PROCESSING operations
            has_idle = any(op.operation_state_state == OperationStateState.IDLE for op in job.operations)
            has_processing = any(op.operation_state_state == OperationStateState.PROCESSING for op in job.operations)
            allocatable.append(1 if has_idle and not has_processing else 0)
        return allocatable

    def _calculate_left_over_times(self, state: State) -> list:
        """Calculate remaining processing time for current operations."""
        left_over_times = []
        for job in state.state.jobs:
            processing_ops = [op for op in job.operations 
                            if op.operation_state_state == OperationStateState.PROCESSING]
            if processing_ops:
                # If operation is processing, calculate remaining time
                op = processing_ops[0]
                left_over_time = (op.end_time.time - state.state.time.time)
            else:
                left_over_time = 0
            left_over_times.append(left_over_time)
        return left_over_times

    def _calculate_percent_finished(self, state: State) -> list:
        """Calculate percentage of completed operations for each job."""
        percent_finished = []
        for job in state.state.jobs:
            total_ops = len(job.operations)
            completed_ops = sum(1 for op in job.operations 
                            if op.operation_state_state == OperationStateState.DONE)
            percent = completed_ops / total_ops if total_ops > 0 else 0
            percent_finished.append(percent)
        return percent_finished

    def _calculate_time_until_next_machine_is_free(self, state: State) -> list:
        """Calculate time until next required machine becomes available."""
        wait_times = []
        for job in state.state.jobs:
            # Find next idle operation
            next_idle_op = next((op for op in job.operations 
                            if op.operation_state_state == OperationStateState.IDLE), None)
            if next_idle_op:
                # Find the machine needed for next operation
                machine = next(m for m in state.state.machines if m.id == next_idle_op.machine_id)
                if machine.state == MachineStateState.WORKING:
                    wait_time = machine.occupied_till.time - state.state.time.time
                    wait_times.append(wait_time)
                else:
                    wait_times.append(0)
            else:
                wait_times.append(0)
        return wait_times

    def _calculate_total_completion(self, state: State) -> list:
        """Calculate estimated total completion time remaining for each job."""
        total_completion = []
        for job in state.state.jobs:
            # Sum remaining processing times and idle operation durations
            remaining_time = 0
            
            # Add remaining time of processing operations
            processing_ops = [op for op in job.operations 
                            if op.operation_state_state == OperationStateState.PROCESSING]
            for op in processing_ops:
                remaining_time += op.end_time.time - state.state.time.time
                
            # Add duration of idle operations
            idle_ops = [op for op in job.operations 
                    if op.operation_state_state == OperationStateState.IDLE]
            for op in idle_ops:
                op_config = next(o for o in self.instance.instance.specification[get_id_int(job.id)].operations 
                            if o.id == op.id)
                remaining_time += op_config.duration.time
                
            total_completion.append(remaining_time / self.max_allowed_time)
        return total_completion

    def _calculate_idle_since_last_op(self, state: State) -> list:
        """Calculate idle time since last completed operation for each job."""
        idle_times = []
        for job in state.state.jobs:
            # Find last completed operation
            last_completed = next((op for op in reversed(job.operations)
                                if op.operation_state_state == OperationStateState.DONE), None)
            if last_completed and not any(op.operation_state_state == OperationStateState.PROCESSING 
                                        for op in job.operations):
                idle_time = (state.state.time.time - last_completed.end_time.time) / self.max_allowed_time
                idle_times.append(idle_time)
            else:
                idle_times.append(0)
        return idle_times

    def _calculate_cum_idle_time(self, state: State) -> list:
        """Calculate cumulative idle time for each job."""
        cum_idle_times = []
        for job in state.state.jobs:
            total_idle_time = 0
            
            # Add initial waiting time before first operation
            first_op = job.operations[0] if job.operations else None
            if first_op is not None and first_op.start_time.time is not None:
                total_idle_time += first_op.start_time.time
                
            # Add idle time between operations
            for i in range(len(job.operations) - 1):
                current_op = job.operations[i]
                next_op = job.operations[i + 1]
                
                if (current_op.operation_state_state == OperationStateState.DONE and 
                    next_op.operation_state_state != OperationStateState.IDLE and 
                    next_op.start_time):
                    total_idle_time += next_op.start_time.time - current_op.end_time.time
                    
            # Add final idle time if job is not complete or processing
            last_op = job.operations[-1] if job.operations else None
            if (last_op and 
                last_op.operation_state_state == OperationStateState.DONE and
                not any(op.operation_state_state == OperationStateState.PROCESSING 
                    for op in job.operations)):
                total_idle_time += state.state.time.time - last_op.end_time.time
                
            cum_idle_times.append(total_idle_time / self.max_allowed_time)
        return cum_idle_times
    def __repr__(self) -> str:
        """
        Return a string representation of the OperationArrayObservation.

        Returns:
            str: The string representation of the OperationArrayObservation.
        """
        return f"OperationArrayObservation with observation_space {self.observation_space}"
    



