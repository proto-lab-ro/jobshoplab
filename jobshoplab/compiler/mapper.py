import re
import sys
from abc import ABC, abstractmethod
from functools import partial
from logging import Logger
from dataclasses import replace
from typing import Dict, Generator, Iterator, List, Union

from jobshoplab.types import Config, InstanceConfig, State
from jobshoplab.types.instance_config_types import *
from jobshoplab.types.state_types import *
from jobshoplab.utils import get_logger
from jobshoplab.utils.exceptions import NotImplementedError
from jobshoplab.utils.utils import get_id_int
from jobshoplab.utils.stochasticy_models import (
    PoissonFunction,
    GammaFunction,
    BetaFunction,
    GaussianFunction,
)


class ID_Counter:
    def __init__(self):
        self.machine_counter = -1
        self.buffer_counter = 0  # start with 1 to have a buffer_0 reserved for the input
        self.transport_counter = -1

    def get_machine_id(self):
        self.machine_counter += 1
        return f"m-{self.machine_counter}"

    def get_buffer_id(self):
        self.buffer_counter += 1
        return f"b-{self.buffer_counter}"

    def get_transport_id(self):
        self.transport_counter += 1
        return f"t-{self.transport_counter}"


class DefaultInstanceLookUpFactory:
    def __init__(
        self,
        loglevel: int | str,
        config: Config,
        num_jobs: int,
        num_machines: int,
    ):
        """
        Initialize the DefaultLookUpFactory.

        Args:
            loglevel (int | str): The log level.
            config (Config): The configuration object.
            num_jobs (int): The number of jobs.
            num_machines (int): The number of machines.
        """
        self.logger: Logger = get_logger(__name__, loglevel)
        self.config: Config = config
        self.num_jobs = num_jobs
        self.num_machines = num_machines
        self.job_priority: float = 0.5
        self.instance_type: str = "job_shop"

    def get_default_tool(self):
        return "tl-0"

    def _get_setup_times(
        self, products: List[Product]
    ) -> Dict[tuple[Product, Product], DeterministicTimeConfig]:
        """
        Get the setup times between products.

        Args:
            products (List[Product]): The list of products.

        Returns:
            Dict[tuple[Product, Product], DeterministicTimeConfig]: The setup times.
        """
        setup_times = {}
        for product in products:
            for other_product in products:
                setup_times[(product, other_product)] = DeterministicTimeConfig(0)
        return setup_times

    def get_default_products(self) -> List[Product]:
        """
        Get the default list of products.

        Returns:
            List[Product]: The default products.
        """
        return [
            Product(id=f"p-{product_id}", name=f"product_{product_id}")
            for product_id in range(self.num_jobs)
        ]

    def get_default_machine(
        self,
        machine_id: str,
        prebuffer: BufferConfig,
        postbuffer: BufferConfig,
        machine_buffer_id: str,
    ) -> MachineConfig:
        """
        Get the default machine configuration with standard settings.

        Args:
            machine_id: The machine ID string (format: m-[number])
            prebuffer: The prebuffer configuration for the machine
            postbuffer: The postbuffer configuration for the machine
            machine_buffer_id: The ID for the machine's internal buffer

        Returns:
            MachineConfig: The default machine configuration
        """
        products = self.get_default_products()
        setup_times = self._get_setup_times(products)
        return MachineConfig(
            id=machine_id,
            outages=tuple(),
            setup_times=setup_times,
            prebuffer=prebuffer,
            postbuffer=postbuffer,
            batches=1,
            resources=tuple(),
            buffer=BufferConfig(
                machine_buffer_id,
                BufferTypeConfig.FLEX_BUFFER,
                1,
                tuple(),
                "Machine buffer",
                machine_id,
            ),
        )

    def get_default_buffer(
        self, buffer_id: str, parent: str, description: str | None = None
    ) -> BufferConfig:
        """
        Get the default buffer configuration.

        Args:
            buffer_id (int): The buffer ID.

        Returns:
            BufferConfig: The default buffer configuration.
        """
        return BufferConfig(
            id=buffer_id,
            type=BufferTypeConfig.FLEX_BUFFER,
            capacity=sys.maxsize,
            resources=tuple(),
            parent=parent,
            description=description,
        )

    def get_default_transport(self, transport_id: str, buffer_id: str) -> TransportConfig:
        """
        Get the default transport configuration.

        Args:
            transport_id (int): The transport ID.

        Returns:
            TransportConfig: The default transport configuration.
        """
        return TransportConfig(
            id=transport_id,
            type=TransportTypeConfig.AGV,
            outages=tuple(),
            resources=tuple(),
            buffer=BufferConfig(
                id=buffer_id,
                type=BufferTypeConfig.FLEX_BUFFER,
                capacity=1,
                resources=tuple(),
                parent=transport_id,
                description="AGV buffer",
            ),
        )

    def get_default_logistics(
        self, machines: tuple[MachineConfig, ...], buffers: tuple[BufferConfig, ...]
    ) -> LogisticsConfig:
        """
        Get the default logistics configuration.

        Args:
            machines (tuple[MachineConfig, ...]): The machines.
            buffers (tuple[BufferConfig, ...]): The buffers.


        Returns:
            LogisticsConfig: The default logistics configuration.
        """
        machines_and_buffer = machines + buffers
        return LogisticsConfig(
            capacity=sys.maxsize,  # max int
            travel_times={
                (c0.id, c1.id): DeterministicTimeConfig(0)
                for c0 in machines_and_buffer
                for c1 in machines_and_buffer
            },
        )

    @classmethod
    def partial(
        cls,
        loglevel: Union[int, str],
        config: Config,
    ):
        return lambda num_jobs, num_machines: cls(loglevel, config, num_jobs, num_machines)


class DefaultStateLookUpFactory:
    def __init__(
        self,
        loglevel: Union[int, str],
        config: Config,
        instance: InstanceConfig,
    ):
        """
        Initialize the DefaultLookUpFactory.

        Args:
            loglevel (int | str): The log level.
            config (Config): The configuration object.
            num_jobs (int): The number of jobs.
            num_machines (int): The number of machines.
        """
        self.logger: Logger = get_logger(__name__, loglevel)
        self.config: Config = config
        self._instance: InstanceConfig = instance
        self.time = Time(0)
        self.finished_operations: tuple[OperationConfig, ...] = tuple()
        self.active_operation: Optional[OperationConfig] = None

    def get_operations(self, job: JobConfig) -> Generator[OperationState, None, None]:
        """
        Get the open operations for the given job.

        Args:
            job (JobConfig): The job to get the open operations for.

        Yields:
            OperationState: The open operations.
        """

        for operation in job.operations:
            yield OperationState(
                id=operation.id,
                start_time=NoTime(),
                end_time=NoTime(),
                machine_id=operation.machine,
                operation_state_state=OperationStateState.IDLE,
            )

    def get_default_machine(self, machine: MachineConfig) -> MachineState:

        return MachineState(
            id=machine.id,
            buffer=BufferState(id=machine.buffer.id, state=BufferStateState.EMPTY, store=tuple()),
            occupied_till=NoTime(),
            prebuffer=BufferState(
                id=machine.prebuffer.id,
                state=BufferStateState.EMPTY,
                store=tuple(),
            ),
            postbuffer=BufferState(
                id=machine.postbuffer.id,
                state=BufferStateState.EMPTY,
                store=tuple(),
            ),
            state=MachineStateState.IDLE,
            resources=tuple(),
        )

    def get_default_transport(
        self, transport: TransportConfig, machines: tuple[MachineState, ...]
    ) -> TransportState:
        # putting one transport to each machine resolving over the ids
        transport_id = get_id_int(transport.id)
        machine_index = transport_id % len(
            machines
        )  # make sure the transport is associated with a machine even if there are more transports than machines

        location_gen = filter(lambda x: get_id_int(x.id) == machine_index, machines)
        location_gen = map(lambda x: x.id, location_gen)
        location = next(location_gen, None)
        if location is None:
            raise ValueError(f"Transport with id={transport.id} can not associate with a machine")
        return TransportState(
            id=transport.id,
            state=TransportStateState.IDLE,
            buffer=BufferState(id=transport.buffer.id, state=BufferStateState.EMPTY, store=tuple()),
            occupied_till=NoTime(),
            location=TransportLocation(
                progress=1.0,
                location=location,
            ),
            transport_job=None,
        )

    @classmethod
    def partial(
        cls,
        loglevel: Union[int, str],
        config: Config,
    ):
        return lambda instance: cls(loglevel, config, instance)


class AbstractDictMapper(ABC):
    """Abstract base class for dictionary mappers."""

    @abstractmethod
    def __init__(
        self,
        loglevel: Union[int, str],
        config: Config,
        default_factory: DefaultInstanceLookUpFactory | DefaultStateLookUpFactory,
        *args,
        **kwargs,
    ):
        """
        Initialize the AbstractDictMapper.

        Args:
            loglevel (int): The log level.
            config (Config): The configuration object.
        """
        self.logger: Logger = get_logger(__name__, loglevel)
        self.config: Config = config
        self.default_factory: Callable = default_factory.partial(loglevel, config)
        self.counter = ID_Counter()

    @abstractmethod
    def map(self, spec_dict: Dict) -> Union[InstanceConfig, State]:
        """
        Map the given dictionary to an InstanceConfig or State object.

        Args:
            spec_dict (Dict): The dictionary to be mapped.

        Returns:
            Union[InstanceConfig, State]: The mapped object.
        """
        raise NotImplementedError

    @abstractmethod
    def __repr__(self) -> str:
        """
        Return a string representation of the object.

        Returns:
            str: The string representation.
        """
        raise NotImplementedError

    def has_key(self, keys: tuple[str, ...], spec_dict: Dict) -> bool:
        """
        Check if the given key is in the dictionary.

        Args:
            key (List[str]): The key to check.
            spec_dict (Dict): The dictionary to check.

        Returns:
            bool: True if the key is in the dictionary, False otherwise.
        """
        self.logger.debug(f"Check if keys={keys} is in spec_dict")
        for key in keys:
            if key not in spec_dict:
                return False
            spec_dict = spec_dict[key]
        return True


class DictToInstanceMapper(AbstractDictMapper):
    """
    Dictionary to InstanceConfig mapper.

    This class is responsible for mapping a dictionary representation of an instance configuration
    to an InstanceConfig object. It provides methods for parsing and mapping the specification,
    components, and logistics of the instance.

    Args:
        loglevel (int | str): The log level.
        config (Config): The configuration object.
    """

    def __init__(self, loglevel: Union[int, str], config: Config, *args, **kwargs):
        """
        Initialize the DictToInstanceMapper.

        Args:
            loglevel (int): The log level.
            config (Config): The configuration object.
        """
        super().__init__(loglevel, config, DefaultInstanceLookUpFactory)
        self.logger.debug("Init DictToInstanceMapper")
        self.default_factory = partial(DefaultInstanceLookUpFactory, loglevel, config)

    def make_defaults(
        self,
        spec_dict: Dict,
    ) -> None:
        """
        Perform a lookup based on the given key.

        Args:
            key (List[str]): The lookup key.

        Returns:
            Dict: The lookup result.
        """
        self.logger.debug(f"creating defaults")
        spec_string = spec_dict["instance_config"]["instance"]["specification"]
        spec_list = spec_string.split("\n")
        spec_list = (line.replace(" ", "") for line in spec_list)  # remove whitespace
        spec_list = tuple(
            filter(lambda x: self._check_pattern(x), spec_list)
        )  # remove lines with do not follow a certain pattern
        self.num_jobs = len(spec_list)
        self.num_machines = len(spec_list[1].split(",")) - 1
        self.defaults = self.default_factory(num_jobs=self.num_jobs, num_machines=self.num_machines)
        self.logger.debug(f"successfully created defaults")

    def _get_job_params(self, operation_string: str) -> Iterator[tuple[int, int]]:
        """
        Get the job parameters from the given operation string.

        Args:
            operation_string (str): The operation string.

        Returns:
            tuple[int, int]: The job parameters.
        """
        # using regex to extract the job parameters
        return map(
            lambda arg: (int(arg[0]), int(arg[1])), re.findall(r"\((\d+),(\d+)\)", operation_string)
        )

    def _check_pattern(self, s: str) -> bool:
        pattern = r"j\d+\|\(\d+,\d+\)+"
        return bool(re.match(pattern, s))

    def _parse_travel_times(
        self, spec_dict: Dict, input_buffer_id: str, output_buffer_id: str
    ) -> Mapping[tuple[str, str], DeterministicTimeConfig | StochasticTimeConfig]:
        """
        Parse the given logistics specification string.

        Args:
            spec_dict (Dict): The specification dictionary.

        Returns:
            LogisticsConfig: The parsed LogisticsConfig object.
        """
        self.logger.debug("Parse logistics specification")
        if not self.has_key(("instance_config", "logistics", "specification"), spec_dict):
            raise ValueError("Logistics specification must be provided.")

        if self.has_key(("instance_config", "logistics", "time_behavior"), spec_dict):
            time_behavior = spec_dict["instance_config"]["logistics"]["time_behavior"]
        else:
            time_behavior = "static"
        logistics_spec_str = spec_dict["instance_config"]["logistics"]["specification"]
        lines = [line.strip() for line in logistics_spec_str.strip().split("\n")]
        headers = lines[0].split("|")  # Get machine names from the header row

        # Create a dictionary to map each (machine1, machine2) tuple to its value
        mapper = {}

        for line in lines[1:]:
            parts = line.split("|")
            row_machine = parts[0]
            values = map(int, parts[1].split())

            for col_machine, value in zip(headers, values):
                row_name = self._map_travel_times_names(
                    row_machine, input_buffer_id, output_buffer_id
                )
                col_name = self._map_travel_times_names(
                    col_machine, input_buffer_id, output_buffer_id
                )
                mapper[(row_name, col_name)] = self._get_time(value, time_behavior)

        return mapper

    def _map_travel_times_names(
        self, name: str, input_buffer_id: str, output_buffer_id: str
    ) -> str:
        """
        Map location names to their corresponding IDs in the travel times configuration.

        This converts human-readable location names (like 'input', 'output') to the
        actual component IDs used in the system.

        Args:
            name: The location name to map
            input_buffer_id: The ID of the input buffer
            output_buffer_id: The ID of the output buffer

        Returns:
            str: The mapped component ID

        Raises:
            ValueError: If the name doesn't match any known location
        """
        if name.startswith("m-"):
            return name
        if name.lower() in [
            "input",
            "input-buffer",
            "inputbuffer",
            "input buffer",
            "input_buffer",
            "in-buf",
            "inbuf",
            "in buf",
            "in_buffer",
        ]:
            return input_buffer_id
        if name.lower() in [
            "output",
            "output-buffer",
            "outputbuffer",
            "output buffer",
            "output_buffer",
            "out-buf",
        ]:
            return output_buffer_id
        raise ValueError(f"Unknown location name: {name}")

    def _get_time(
        self, duration: int | None, time_behavior: Union[str, dict[str, Union[str, int]], int]
    ) -> DeterministicTimeConfig | StochasticTimeConfig:
        if duration is None:
            if isinstance(time_behavior, int):
                return DeterministicTimeConfig(time=time_behavior)
            elif isinstance(time_behavior, dict) and "base" in time_behavior:
                duration = int(time_behavior["base"])

        if not isinstance(duration, int):
            raise ValueError("Duration must be an integer")

        if time_behavior == "static":
            return DeterministicTimeConfig(time=duration)

        if isinstance(time_behavior, dict):
            if "type" not in time_behavior:
                raise ValueError("Distribution type must be specified")

            dist_type = str(time_behavior["type"])
            match dist_type:
                case "poisson":
                    mean = float(time_behavior["mean"])
                    func = PoissonFunction(duration, mean)
                case "gamma":
                    shape = float(time_behavior["shape"])
                    scale = float(time_behavior["scale"])
                    func = GammaFunction(duration, shape, scale)
                case "beta":
                    alpha = float(time_behavior["alpha"])
                    beta = float(time_behavior["beta"])
                    func = BetaFunction(duration, alpha, beta)
                case "gaussian":
                    mean = float(time_behavior["mean"])
                    std = float(time_behavior["std"])
                    func = GaussianFunction(duration, mean, std)
                case _:
                    raise ValueError(f"Unknown distribution function: {dist_type}")
            return StochasticTimeConfig(time=func)
        raise ValueError(f"Unknown time behavior: {time_behavior}")

    def _parse_specification(
        self, spec_dict: dict, time_behavior: str | dict
    ) -> Generator[JobConfig, None, None]:
        """
        Parse the given specification string.

        Args:
            spec_str (str): The specification string.

        Yields:
            JobConfig: The parsed JobConfig object.
        """
        spec_str = spec_dict["instance_config"]["instance"]["specification"]
        lines = spec_str.split("\n")  # remove first line description only
        self.logger.debug("Parse specification")
        lines = (line.replace(" ", "") for line in lines)  # remove whitespace
        lines = filter(
            lambda x: self._check_pattern(x), lines
        )  # remove lines with do not follow a certain pattern

        entries = tuple((line.split("|")[1] for line in lines))  # remove line description

        job_param_tuple = (
            (job_id, self._get_job_params(operation_string))
            for job_id, operation_string in enumerate(entries)
        )
        priority = self.defaults.job_priority

        # Map job_param_tuple to JobConfig
        for job_id, operation_tuple in job_param_tuple:
            operations: tuple[OperationConfig, ...] = tuple()
            operation_tuple = tuple(operation_tuple)
            if self.has_key(("instance_config", "instance", "tool_usage"), spec_dict):
                tools_per_operation = next(
                    filter(
                        lambda i: i["job"] == f"j{job_id}",
                        spec_dict["instance_config"]["instance"]["tool_usage"],
                    ),
                    None,
                )
                if tools_per_operation is None:
                    raise ValueError(f"No tool usage found for job {job_id}")
                tools_per_operation = tools_per_operation["operation_tools"]
            else:
                tools_per_operation = [self.defaults.get_default_tool()] * len(operation_tuple)
            for operation_id, operation_params in enumerate(operation_tuple):
                machine_id, duration = operation_params
                tool = tools_per_operation[operation_id]
                operations += (
                    OperationConfig(
                        id=f"o-{job_id}-{operation_id}",
                        machine=f"m-{machine_id}",
                        duration=self._get_time(duration, time_behavior),
                        tool=tool,
                    ),
                )
            yield JobConfig(
                id=f"j-{job_id}",
                product=Product(id=f"j-{job_id}", name=f"product_{job_id}"),
                priority=priority,
                operations=operations,
            )  # yielding directly to keep it readable
        self.logger.debug("Successfully parsed specification")

    def _map_specification(self, spec_dict: Dict) -> ProblemInstanceConfig:
        """
        Map the given specification string to a JobConfig object.

        Args:
            spec_dict (Dict): The specification string.

        Returns:
            JobConfig: The mapped JobConfig object.
        """
        self.logger.debug("Map specification")

        if self.has_key(("instance_config", "instance", "type"), spec_dict):
            spec_type = spec_dict["instance_config"]["instance"]["type"]
        else:
            spec_type = self.defaults.instance_type

        spec_type = ProblemInstanceTypeConfig(spec_type)
        if self.has_key(
            ("instance_config", "instance", "specification", "time_behavior"), spec_dict
        ):
            time_behavior = spec_dict["instance_config"]["instance"]["specification"][
                "time_behavior"
            ]
        else:
            time_behavior = "static"
        specification = tuple(self._parse_specification(spec_dict, time_behavior))
        self.logger.debug("Successfully mapped specification")
        return ProblemInstanceConfig(
            specification=specification,
            type=spec_type,
        )

    def _parse_setup_times(
        self, setup_times_str: str, time_behavior: str | dict
    ) -> Mapping[tuple[str, str], DeterministicTimeConfig | StochasticTimeConfig]:

        # self.logger.debug("Parse logistics specification")
        # if not self.has_key(("instance_config", "logistics", "specification"), spec_dict):
        #     raise ValueError("Logistics specification must be provided.")

        # if self.has_key(("instance_config", "logistics", "time_behavior"), spec_dict):
        #     time_behavior = spec_dict["instance_config"]["logistics"]["time_behavior"]
        # else:
        #     time_behavior = "static"
        lines = [line.strip() for line in setup_times_str.strip().split("\n")]
        headers = lines[0].split("|")  # Get machine names from the header row

        # Create a dictionary to map each (machine1, machine2) tuple to its value
        mapper = {}

        for line in lines[1:]:
            parts = line.split("|")
            row_name = parts[0]
            values = map(int, parts[1].split())
            for col_name, value in zip(headers, values):
                mapper[(row_name, col_name)] = self._get_time(value, time_behavior)

        return mapper

    def _add_machine_spec(self, default: MachineConfig, spec_dict: Dict) -> MachineConfig:
        machine = default
        if self.has_key(("instance_config", "outages"), spec_dict):
            component_list = ["m", "machine", "Machine", "MACHINE", machine.id]
            outages = self._map_spec_dict_to_outage(spec_dict, component_list, default.outages)
            machine = replace(machine, outages=outages)
        if self.has_key(("instance_config", "setup_times"), spec_dict):

            setup_times_str = spec_dict["instance_config"]["setup_times"]
            setup_times_str = next(
                filter(lambda i: i["machine"] == machine.id, setup_times_str), None
            )
            if setup_times_str is None:
                raise ValueError(f"No setup times found for machine {machine.id}")
            if "time_behavior" in setup_times_str.keys():
                _time_behavior = setup_times_str["time_behavior"]
            else:
                _time_behavior = "static"
            setup_times = self._parse_setup_times(setup_times_str["specification"], _time_behavior)
            machine = replace(machine, setup_times=setup_times)
        return machine

    def _match_outage_type(self, type: str) -> OutageTypeConfig:
        match type:
            case "maintenance" | "repair":
                return OutageTypeConfig.MAINTENANCE
            case "breakdown" | "fail":
                return OutageTypeConfig.FAIL
            case "recharge" | "recharging":
                return OutageTypeConfig.RECHARGE
            case _:
                raise ValueError(f"Unknown outage type: {type}")

    def _map_spec_dict_to_outage(self, spec_dict, component_list, outages):
        if not self.has_key(("instance_config", "outages"), spec_dict):
            return outages
        for maintance_spec in spec_dict["instance_config"]["outages"]:
            if maintance_spec["component"] in component_list:
                duration_behavior = maintance_spec["duration"]
                frequency_behavior = maintance_spec["frequency"]
                _type = self._match_outage_type(maintance_spec["type"])
                outages += (
                    OutageConfig(
                        duration=self._get_time(None, duration_behavior),
                        frequency=self._get_time(None, frequency_behavior),
                        type=_type,
                    ),
                )
        return outages

    def _add_buffer_spec(self, default: BufferConfig, spec_dict: Dict) -> BufferConfig:
        raise NotImplementedError

    def _add_transport_spec(self, spec_dict: Dict) -> tuple[TransportConfig, ...]:
        transport = spec_dict["instance_config"]["logistics"]

        if "amount" not in transport:
            raise ValueError("Transport configuration must include 'amount' key.")

        type = transport.get("type", TransportTypeConfig.AGV)

        match transport.get("type", "").lower():
            case "agv":
                type = TransportTypeConfig.AGV
            case _:
                raise ValueError(f"Unknown transport type: {transport.get('type')}")

        transports: tuple[TransportConfig, ...] = tuple()
        outages = self._map_spec_dict_to_outage(
            spec_dict, ["t", "transport", "Transport", "TRANSPORT"], tuple()
        )
        for i in range(transport["amount"]):
            transport_id = self.counter.get_transport_id()
            transports += (
                TransportConfig(
                    id=transport_id,
                    type=type,
                    outages=outages,
                    resources=tuple(),
                    buffer=BufferConfig(
                        id=self.counter.get_buffer_id(),
                        type=BufferTypeConfig.FLEX_BUFFER,
                        capacity=1,
                        resources=tuple(),
                        parent=transport_id,
                        description="AGV buffer",
                    ),
                ),
            )

        return transports

    def _map_components(
        self, spec_dict: Dict
    ) -> tuple[tuple[MachineConfig, ...], tuple[TransportConfig, ...], tuple[BufferConfig, ...]]:
        """
        Map the given dictionary to a JobConfig object.

        Args:
            spec_dict (Dict): The dictionary to be mapped.

        Returns:
            JobConfig: The mapped JobConfig object.
        """
        self.logger.debug("Map components")
        machines = tuple()
        # mapping machines
        for _ in range(self.num_machines):
            machine_id = self.counter.get_machine_id()
            machine = self.defaults.get_default_machine(
                machine_id,
                self.defaults.get_default_buffer(self.counter.get_buffer_id(), machine_id),
                self.defaults.get_default_buffer(self.counter.get_buffer_id(), machine_id),
                self.counter.get_buffer_id(),
            )
            machine = self._add_machine_spec(machine, spec_dict)
            machines += (machine,)

        # mapping transport
        if self.has_key(("instance_config", "logistics", "type"), spec_dict):
            transport = self._add_transport_spec(spec_dict)

        else:
            transport = tuple(
                self.defaults.get_default_transport(
                    self.counter.get_transport_id(), self.counter.get_buffer_id()
                )
                for _ in range(self.num_jobs)
            )

        # mapping buffer

        buffer = (
            self.defaults.get_default_buffer("b-0", None, "input buffer"),
            self.defaults.get_default_buffer(self.counter.get_buffer_id(), None, "output buffer"),
        )

        if self.has_key(("instance_config", "components", "buffer"), spec_dict):
            for _ in spec_dict["instance_config"]["components"]["buffer"]:
                default_buffer = self.defaults.get_default_buffer(self.counter.get_buffer_id())
                _buffer = self._add_buffer_spec(default_buffer, spec_dict)
                buffer += (_buffer,)
        self.logger.debug("Successfully mapped components")
        return machines, transport, buffer

    def _map_logistics(self, spec_dict: Dict, input_buffer_id, output_buffer_id) -> LogisticsConfig:
        """
        Map the given dictionary to a JobConfig object.

        Args:
            spec_dict (Dict): The dictionary to be mapped.

        Returns:
            JobConfig: The mapped JobConfig object.
        """
        self.logger.debug("Map logistics")
        if self.has_key(("instance_config", "logistics"), spec_dict):
            travel_times = self._parse_travel_times(spec_dict, input_buffer_id, output_buffer_id)
            return LogisticsConfig(
                capacity=sys.maxsize,  # max int
                travel_times=travel_times,
            )
        self.logger.debug("Successfully mapped logistics")
        return self.defaults.get_default_logistics(self.machines, self.buffer)

    def map(self, spec_dict: Dict) -> InstanceConfig:
        """
        Map a specification dictionary to an InstanceConfig object.

        Takes a dictionary representation of the instance specification and
        converts it into a structured InstanceConfig object with typed components,
        including machines, transports, buffers, and logistics.

        Args:
            spec_dict: The specification dictionary containing the configuration

        Returns:
            InstanceConfig: The complete instance configuration object

        Raises:
            ValueError: If required configuration elements are missing or invalid
        """

        self.logger.debug("Mapping InstanceConfig")
        # RESET COUNTER FOR EACH MAPPING
        self.counter = ID_Counter()

        self.make_defaults(spec_dict)
        self.machines, self.transports, self.buffer = self._map_components(spec_dict)
        self.instance = self._map_specification(spec_dict)
        self.logistics = self._map_logistics(spec_dict, self.buffer[0].id, self.buffer[1].id)

        self.logger.debug("Successfully mapped InstanceConfig")

        return InstanceConfig(
            description=spec_dict["instance_config"]["description"],
            logistics=self.logistics,
            instance=self.instance,
            machines=self.machines,
            buffers=self.buffer,
            transports=self.transports,
        )

    def __repr__(self) -> str:
        """
        Return a string representation of the object.

        Returns:
            str: The string representation.
        """
        return f"DictToInstanceMapper()"


class DictToInitStateMapper(AbstractDictMapper):
    """Dictionary to State mapper"""

    def __init__(self, loglevel: int | str, config: Config):
        """
        Initialize the DictToInitStateMapper.

        Args:
            loglevel (int): The log level.
            config (Config): The configuration object.
        """
        super().__init__(loglevel, config, DefaultStateLookUpFactory)
        self.logger.debug("Init DictToInitStateMapper")

    def _map_jobs(self, spec_dict: Dict, instance: InstanceConfig) -> Iterator[JobState]:
        input_buffer_id = instance.buffers[0].id
        for job in instance.instance.specification:
            if self.has_key(("init_state", "components", "machines"), spec_dict):
                raise NotImplementedError
            operations = tuple(self.defaults.get_operations(job))
            _id = job.id
            if self.has_key(("init_state", "jobs", str(job.id), "location"), spec_dict):
                raise NotImplementedError

            yield JobState(_id, operations, location=input_buffer_id)

    def _map_time(self, spec_dict: Dict) -> Time:
        if self.has_key(("init_state", "start_time"), spec_dict):
            time = spec_dict["init_state"]["start_time"]
            return Time(time)
        return self.defaults.time

    def _get_transport_state(self, transport: TransportConfig, spec_dict: Dict) -> TransportState:
        transport_spec = spec_dict["init_state"]["transport"]
        int_id = get_id_int(transport.id)
        if len(transport_spec) < int_id:
            raise ValueError(f"Transport with id={transport.id} not found in transport_spec")

        return TransportState(
            id=transport.id,
            state=TransportStateState.IDLE,
            buffer=BufferState(id=transport.buffer.id, state=BufferStateState.EMPTY, store=tuple()),
            occupied_till=NoTime(),
            location=TransportLocation(
                progress=1.0,
                location=transport_spec[int_id]["location"],
            ),
            transport_job=None,
        )

    def _map_components(
        self, spec_dict: Dict, instance: InstanceConfig, jobs: tuple[JobState, ...]
    ) -> tuple[tuple[MachineState, ...], tuple[TransportState, ...], tuple[BufferState, ...]]:
        if self.has_key(("init_state", "components", "machines"), spec_dict):
            raise NotImplementedError
        if self.has_key(("init_state", "components", "buffer"), spec_dict):
            raise NotImplementedError
        if self.has_key(("init_state", "components", "transport"), spec_dict):
            raise NotImplementedError
        machine_states = tuple(
            map((lambda m: self.defaults.get_default_machine(m)), instance.machines)
        )

        if self.has_key(("init_state", "transport"), spec_dict):
            transport_states = tuple(
                map(
                    (lambda t: self._get_transport_state(t, spec_dict)),
                    instance.transports,
                )
            )
        else:
            transport_states = tuple(
                map(
                    (lambda t: self.defaults.get_default_transport(t, machine_states)),
                    instance.transports,
                )
            )
        job_ids = tuple(j.id for j in jobs)
        buffer_states = (
            BufferState(id=instance.buffers[0].id, state=BufferStateState.NOT_EMPTY, store=job_ids),
            BufferState(id=instance.buffers[1].id, state=BufferStateState.EMPTY, store=tuple()),
        )
        return (machine_states, transport_states, buffer_states)

    def map(self, spec_dict: Dict, instance: InstanceConfig) -> State:
        """
        Map the given dictionary to a State object.

        Args:
            spec_dict (Dict): The dictionary to be mapped.

        Returns:
            State: The mapped State object.
        """

        self.logger.debug("Mapping Init State")

        # RESET COUNTER FOR EACH MAPPING
        self.counter = ID_Counter()

        self.defaults: DefaultStateLookUpFactory = self.default_factory(instance)
        jobs = tuple(self._map_jobs(spec_dict, instance))
        time = self._map_time(spec_dict)
        machines, transports, buffer = self._map_components(spec_dict, instance, jobs)
        return State(jobs=jobs, time=time, machines=machines, transports=transports, buffers=buffer)

    def __repr__(self) -> str:
        """
        Return a string representation of the object.

        Returns:
            str: The string representation.
        """
        return f"DictToInitStateMapper()"
