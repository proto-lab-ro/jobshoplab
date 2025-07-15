from abc import ABC, abstractmethod
from collections import OrderedDict
from functools import partial
from logging import Logger
from typing import Callable
import torch
from torch_geometric.data import Data
import networkx as nx
import matplotlib.pyplot as plt
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


# class TasselObservationBinaryActionFactory(TasselObservation):
#     def __init__(
#         self,
#         loglevel: int,
#         config: Config,
#         instance: InstanceConfig,
#         event_generator: PossibleEventGenerator,
#         *args,
#         **kwargs,
#     ):
#         """
#         Initialize the SimpleJsspObservationFactory.

#         Args:
#             loglevel (int): The log level.
#             config (Config): The configuration object.
#             instance (InstanceConfig): The instance configuration object.
#         """
#         super().__init__(loglevel, config, instance)
#         self.spaces["current_job"] = gym.spaces.Discrete(self.num_jobs + 1, start=0)
#         self.spaces.move_to_end("current_job")
#         self.observation_space: gym.spaces.Dict = gym.spaces.Dict(self.spaces)
#         self.event_generator = event_generator

#     def make(
#         self,
#         state: State,
#         done: bool,
#     ) -> dict:
#         """
#         Create an observation.

#         Args:
#             state (State): The state to create the observation from.

#         Returns:
#             dict: The observation.
#         """
#         obs = super().make(state, done)
#         if not done:
#             next_job = self.event_generator.next(state)
#             if next_job is None:
#                 raise InvalidKey(next_job)
#             obs["current_job"] = get_id_int(next_job.id)
#         else:
#             obs["current_job"] = len(
#                 state.jobs
#             )  # setting to biggest job id +1 to prevent RuntimeError in model.learn
#         return obs

#     def __repr__(self) -> str:
#         """
#         Return a string representation of the SimpleJsspObservationFactory.

#         Returns:
#             str: The string representation of the SimpleJsspObservationFactory.
#         """
#         return f"SimpleJsspObservationFactory with observation_space {self.observation_space}"


class GNNObservationFactory(ObservationFactory):
    def __init__(self, loglevel: int, config: Config, instance: InstanceConfig, *args, **kwargs):
        """
        Initialize the GNNObservationFactory.

        Args:
            loglevel (int): The log level.
            config (Config): The configuration object.
            instance (InstanceConfig): The instance configuration object.
        """
        # TODO: Implement the GNNObservationFactory
        self.max_nodes: int = 60
        self.num_node_features: int = 5  # Example feature size, adjust as needed
        self.max_edges: int = 100
        self.show_graph = True
        super().__init__(loglevel, config, instance)
        self.observation_space = gym.spaces.Dict(
            {
                "node_feats": gym.spaces.Box(
                    low=-np.inf,
                    high=np.inf,
                    shape=(self.max_nodes, self.num_node_features),
                    dtype=np.float32,
                ),
                "edge_index": gym.spaces.Box(
                    low=0,
                    high=self.max_nodes,
                    shape=(2, self.max_edges),
                    dtype=np.int64,
                ),
                "num_nodes": gym.spaces.Box(0, 1, (1,), dtype=np.int64),
                "num_edges": gym.spaces.Box(0, 1, (1,), dtype=np.int64),
            }
        )



    def make(self, state_result: StateMachineResult, *args, **kwargs) -> dict:
        """
        Create an observation for the GNN.

        Args:
            state_result (StateMachineResult): The state result to create the observation from.

        Returns:
            dict: The observation containing node features and edge indices.
        """
        # TODO: Implement
        state: State = state_result.state
        # Example implementation, adjust according to your state structure

        max_edge_index, num_ops_nodes, ops_num_edges = self.__graph_feats__(state)


        ops_node_feats = self.__ops_node_feats(num_ops_nodes)
        ops_edge_index_forward = self.__ops_edge_index_forward(state)
        #ops_node_feats = np.random.rand(num_ops_nodes, self.num_node_features).astype(np.float32)
        #edge_index = np.random.randint(0, max_edge_index, (2, self.max_edges)).astype(np.int64)
        
        if self.show_graph:
            data = Data(x = torch.tensor(ops_node_feats),edge_index=torch.tensor(ops_edge_index_forward,dtype=torch.int64))
            G = nx.Graph()
            edges = data.edge_index.t().tolist()
            G.add_edges_from(edges)

            # Draw the graph
            nx.draw(G, with_labels=True)
            plt.show()


        num_nodes = np.array([self.max_nodes], dtype=np.int64)#TODO
        num_edges = np.array([self.max_edges], dtype=np.int64)#TODO

        return {
            "node_feats": ops_node_feats,
            "edge_index": ops_edge_index_forward,
            "num_nodes": num_nodes,
            "num_edges": num_edges,
        }
    

    def __ops_edge_index_forward(self, state):
        jobs = state.jobs
        edge_list = []
        op_offset = 0  # Offset for global op index across jobs

        for job in jobs:
            num_ops = len(job.operations)
            # For each pair of subsequent operations in the job, create an edge
            for i in range(num_ops - 1):
                src = op_offset + i
                dst = op_offset + i + 1
                edge_list.append([src, dst])
            op_offset += num_ops

        if len(edge_list) == 0:
            # No edges, return empty array with correct shape
            return np.zeros((2, 0), dtype=np.int64)



        edge_index = np.array(edge_list, dtype=np.int64).T
        num_edges = edge_index.shape[1]
        if num_edges < self.max_edges:
            pad_width = self.max_edges - num_edges
            padding = np.zeros((2, pad_width), dtype=np.int64)
            edge_index = np.hstack([edge_index, padding])

        return edge_index
    def __ops_node_feats(self,num_ops_nodes):
        ops_node_feats = np.random.rand(num_ops_nodes, self.num_node_features).astype(np.float32)
        #Check For padding
        if ops_node_feats.shape[0] < self.max_nodes:
            pad_rows = self.max_nodes - ops_node_feats.shape[0]
            padding = np.zeros((pad_rows, self.num_node_features), dtype=np.float32)
            ops_node_feats = np.vstack([ops_node_feats, padding])
        
        return ops_node_feats

    def __graph_feats__(self, state):
        ### Ops
        jobs = state.jobs
        ops = [op for job in jobs for op in job.operations]
        num_ops_nodes = len(ops) 
        num_jobs = len(jobs)
        ### Edges between ops
        ops_num_edges = 0
        max_edge_index = -1
        for job in jobs:
            # Each job has (number of operations - 1) edges between consecutive operations
            ops_num_edges += max(0, len(job.operations) - 1)
            max_edge_index += 1


        ### 
        return max_edge_index, num_ops_nodes, ops_num_edges

    def __repr__(self) -> str:
        """
        Return a string representation of the GNNObservationFactory.

        Returns:
            str: The string representation of the GNNObservationFactory.
        """
        return "GNNObservationFactory"


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
        self.spaces["current_job"] = gym.spaces.Discrete(self.num_jobs + 1, start=0)
        self.spaces["current_component_id"] = gym.spaces.Discrete(self.num_components + 1, start=0)
        self.spaces["current_component_type"] = gym.spaces.Discrete(
            3, start=0
        )  # 0: machine, 1: transport, 2: placeholder results in a total of 3 possible values
        self.spaces.move_to_end("current_job")
        self.spaces.move_to_end("current_component_id")
        self.spaces.move_to_end("current_component_type")
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
            obs["current_job"] = (
                get_id_int(transition.job_id) if transition.job_id else len(state.state.jobs)
            )
            obs["current_component_id"] = self.get_component_id(transition.component_id)
            obs["current_component_type"] = get_component_type_int(transition.component_id)
        else:
            obs["current_job"] = len(
                state.state.jobs
            )  # setting to biggest job id +1 to prevent RuntimeError in model.learn
            obs["current_component_id"] = self.num_components
            obs["current_component_type"] = 3
        return obs

    def __repr__(self) -> str:
        """
        Return a string representation of the SimpleJsspObservationFactory.

        Returns:
            str: The string representation of the SimpleJsspObservationFactory.
        """
        return f"SimpleJsspObservationFactory with observation_space {self.observation_space}"


# class MultidiscreteActionObservationFactory(SimpleJsspObservationFactory):
#     def __init__(
#         self,
#         loglevel: int,
#         config: Config,
#         instance: InstanceConfig,
#         event_generator: PossibleEventGenerator,
#         *args,
#         **kwargs,
#     ):
#         """
#         Initialize the SimpleJsspObservationFactory.

#         Args:
#             loglevel (int): The log level.
#             config (Config): The configuration object.
#             instance (InstanceConfig): The instance configuration object.
#         """
#         super().__init__(loglevel, config, instance)
#         self.spaces["jobs_queue"] = gym.spaces.Box(
#             low=0, high=1, shape=(self.num_jobs,), dtype=np.int8
#         )
#         self.spaces["machine_queue"] = gym.spaces.Box(
#             low=0, high=1, shape=(self.num_machines,), dtype=np.int8
#         )
#         self.spaces.move_to_end("jobs_queue")
#         self.spaces.move_to_end("machine_queue")
#         self.observation_space: gym.spaces.Dict = gym.spaces.Dict(self.spaces)
#         self.event_generator = event_generator

#     def make(
#         self,
#         state: State,
#         done: bool,
#     ) -> dict:
#         """
#         Create an observation.

#         Args:
#             state (State): The state to create the observation from.

#         Returns:
#             dict: The observation.
#         """
#         obs = super().make(state)

#         obs["jobs_queue"] = np.zeros(self.num_jobs, dtype=np.int8)
#         obs["machine_queue"] = np.zeros(self.num_machines, dtype=np.int8)
#         for el in self.event_generator.event_queue:
#             if isinstance(el, JobState):
#                 job_id = get_id_int(el.id)
#                 obs["jobs_queue"][job_id] = 1
#                 op = job_type_utils.get_next_not_done_operation(el)
#                 machine_id = get_id_int(op.machine_id)
#                 obs["machine_queue"][machine_id] = 1

#         return obs

#     def __repr__(self) -> str:
#         """
#         Return a string representation of the SimpleJsspObservationFactory.

#         Returns:
#             str: The string representation of the SimpleJsspObservationFactory.
#         """
#         return f"SimpleJsspObservationFactory with observation_space {self.observation_space}"


class OperationArrayObservation(ObservationFactory):
    def __init__(self, loglevel: int, config: Config, instance: InstanceConfig, *args, **kwargs):
        num_operations = sum(len(job.operations) for job in instance.instance.specification)
        num_jobs = len(instance.instance.specification)

        super().__init__(loglevel, config, instance)
        #! todo unsafe code get max from all buffers
        max_buffer_id = int(instance.buffers[-1].id.split("-")[1])
        self.spaces = OrderedDict(
            {
                "operation_state": gym.spaces.Box(
                    low=0, high=1, shape=(1, num_operations), dtype=np.float32
                ),
                "current_time": gym.spaces.Box(low=0, high=1.0, shape=(1,), dtype=np.float32),
                "job_locations": gym.spaces.Box(
                    low=0, high=max_buffer_id, shape=(1, num_jobs), dtype=np.int32
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
                        duration = operation.end_time.time - operation.start_time.time
                        progress = (
                            state_result.state.time.time - operation.start_time.time
                        ) / duration
                        operation_state.append(progress)
                    case OperationStateState.DONE:
                        operation_state.append(1)
                    case _:
                        raise NotImplementedError
        job_locations = [job.location for job in state_result.state.jobs]
        if any(not j.startswith("b") for j in job_locations):
            raise InvalidValue("Job location must be a buffer", job_locations)
        job_ints = [int(j.split("-")[1]) for j in job_locations]
        return {
            "operation_state": np.array([operation_state]),
            "current_time": np.array(
                [np.float32(state_result.state.time.time / self.max_allowed_time)]
            ),
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
        self.spaces["current_job"] = gym.spaces.Discrete(self.num_jobs + 1, start=0)
        self.spaces["current_component_id"] = gym.spaces.Discrete(self.num_components + 1, start=0)
        self.spaces["current_component_type"] = gym.spaces.Discrete(
            3, start=0
        )  # 0: machine, 1: transport, 2: placeholder results in a total of 3 possible values
        self.spaces.move_to_end("current_job")
        self.spaces.move_to_end("current_component_id")
        self.spaces.move_to_end("current_component_type")
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
            obs["current_job"] = (
                get_id_int(transition.job_id) if transition.job_id else len(state.state.jobs)
            )
            obs["current_component_id"] = self.get_component_id(transition.component_id)
            obs["current_component_type"] = get_component_type_int(transition.component_id)
        else:
            obs["current_job"] = len(
                state.state.jobs
            )  # setting to biggest job id +1 to prevent RuntimeError in model.learn
            obs["current_component_id"] = self.num_components
            obs["current_component_type"] = 3
        return obs

    def __repr__(self) -> str:
        """
        Return a string representation of the BinaryOperationArrayObservation.

        Returns:
            str: The string representation of the BinaryOperationArrayObservation.
        """
        return f"BinaryOperationArrayObservation with observation_space {self.observation_space}"
