from dataclasses import dataclass
from enum import Enum
from typing import Callable, Literal, Mapping, TypeAlias

from jobshoplab.types.stochasticy_models import StochasticTimeConfig
from jobshoplab.utils.utils import hash

ResourceConfig = Literal["EnergyConsumption", "Waste", "C02Emission", "FinancialCost"]
EnergyConsumptionConfig = "Consumption"
WasteConfig = "Consumption"
C02EmissionConfig = "Consumption"
FinancialCostConfig = "Consumption"
FailConfig = "OutageConfig"
MaintenanceConfig = "OutageConfig"
RechargeConfig = "OutageConfig"
Tool: TypeAlias = str


class TransportTypeConfig(Enum):
    """Enumeration for transport type configuration."""

    AGV = "agv"
    CONVEYOR = "conveyor"
    TELEPORTER = "teleporter"  #! TEMPORARY

    def asdict(self) -> str:
        return self.value


class BufferTypeConfig(Enum):
    """Enumeration for buffer type configuration."""

    FIFO = "fifo"
    LIFO = "lifo"
    DUMMY = "dummy"
    FLEX_BUFFER = "flex_buffer"

    def asdict(self) -> str:
        return self.value


class ProblemInstanceTypeConfig(Enum):
    """
    Enum class representing the problem instance types for job shop, flow shop, and open shop.
    """

    JOB_SHOP = "job_shop"
    FLOW_SHOP = "flow_shop"
    OPEN_SHOP = "open_shop"

    def asdict(self) -> str:
        return self.value


@dataclass(frozen=True)
class Product:
    """
    Data class representing a product.

    Attributes:
        id (str): The ID of the product.
        name (str): The name of the product.
    """

    id: str
    name: str

    def asdict(self) -> dict:
        return {"id": self.id, "name": self.name}


@dataclass(frozen=True)
class ConsumptionConfig:
    """
    Data class representing the configuration for consumption.
    """

    idle: float
    active: float
    outage: float
    setup: float

    def asdict(self) -> dict:
        return {
            "idle": self.idle,
            "active": self.active,
            "outage": self.outage,
            "setup": self.setup,
        }


@dataclass(frozen=True)
class DeterministicTimeConfig:
    """
    Data class representing the configuration for deterministic time.

    Attributes:
        time (int): The time value.
    """

    time: int

    def asdict(self) -> dict:
        return {"deterministic_time": self.time}


class OutageTypeConfig(Enum):
    """
    Enumeration for outage configuration types.
    Attributes:
        FAIL (str): The fail type.
        MAINTENANCE (str): The maintenance type.
        RECHARGE (str): The recharge type.
    """

    FAIL = "fail"
    MAINTENANCE = "maintenance"
    RECHARGE = "recharge"

    def asdict(self) -> str:
        return self.value


@dataclass(frozen=True)
class OutageConfig:
    """
    Data class representing an outage.

    Attributes:
        frequency (DeterministicTimeConfig | StochasticFrequency): The frequency of the outage.
        duration (DeterministicTimeConfig | StochasticTimeConfig): The duration of the outage.
    """

    id: str
    frequency: DeterministicTimeConfig | StochasticTimeConfig
    duration: DeterministicTimeConfig | StochasticTimeConfig
    type: OutageTypeConfig

    def asdict(self) -> dict:
        return {
            "id": self.id,
            "frequency": self.frequency.asdict(),
            "duration": self.duration.asdict(),
        }


@dataclass(frozen=True)
class BufferConfig:
    """
    Data class representing the configuration for a buffer.

    Attributes:
        id (str): The ID of the buffer.
        type (BufferTypeConfig): The type of the buffer.
        capacity (int): The capacity of the buffer.
        resources (tuple[ResourceConfig]): The resources required by the buffer.
    """

    id: str
    type: BufferTypeConfig
    capacity: int
    resources: tuple[ResourceConfig, ...]
    description: str | None = None
    parent: str | None = None

    def asdict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.asdict(),
            "capacity": self.capacity,
            "resources": tuple(r.asdict() for r in self.resources),
            "description": self.description,
            "parent": self.parent,
        }


@dataclass(frozen=True)
class TransportConfig:
    """
    Data class representing the configuration for a transport.

    Attributes:
        id (str): The ID of the transport.
        type (TransportTypeConfig): The type of the transport.
        outages (tuple[OutageConfig]): The outages of the transport.
        resources (tuple[ResourceConfig]): The resources required by the transport.
    """

    id: str
    type: TransportTypeConfig
    outages: tuple[OutageConfig, ...]
    resources: tuple[ResourceConfig, ...]
    buffer: BufferConfig
    description: str | None = None

    def asdict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.asdict(),
            "outages": tuple(o.asdict() for o in self.outages),
            "resources": tuple(r.asdict() for r in self.resources),
            "buffer": self.buffer.asdict(),
            "description": self.description,
        }


@dataclass(frozen=True)
class MachineConfig:
    """
    Data class representing the configuration for a machine.

    Attributes:
        id (str): The ID of the machine.
        outages (tuple[OutageConfig]): The outages of the machine.
        setup_times (dict[tuple[Product, Product], DeterministicTimeConfig | StochasticTimeConfig]): The setup times for different product pairs.
        prebuffer (BufferConfig): The prebuffer configuration.
        postbuffer (BufferConfig): The postbuffer configuration.
        batches (int): The number of batches the machine can process.
        resources (tuple[ResourceConfig]): The resources required by the machine.
    """

    id: str
    outages: tuple[OutageConfig, ...]
    setup_times: Mapping[tuple[Tool, Tool], DeterministicTimeConfig | StochasticTimeConfig]
    prebuffer: BufferConfig
    postbuffer: BufferConfig
    batches: int
    resources: tuple[ResourceConfig, ...]
    buffer: BufferConfig
    description: str | None = None

    def asdict(self) -> dict:
        return {
            "id": self.id,
            "outages": tuple(o.asdict() for o in self.outages),
            "setup_times": {
                f"{p1.id}_{p2.id}": st.asdict() for (p1, p2), st in self.setup_times.items()
            },
            "prebuffer": self.prebuffer.asdict(),
            "postbuffer": self.postbuffer.asdict(),
            "batches": self.batches,
            "resources": tuple(r.asdict() for r in self.resources),
            "buffer": self.buffer.asdict(),
            "description": self.description,
        }

    def __hash__(self) -> int:
        return hash("m{}".format(self.id))

    def __eq__(self, value: object) -> bool:
        return isinstance(value, MachineConfig) and value.id == self.id


@dataclass(frozen=True)
class TwinMachineConfig:
    """
    Data class representing the configuration for twin machines.

    Attributes:
        id (str): The ID of the twin machines.
        machines (tuple[MachineConfig]): The twin machines.
    """

    id: str
    machines: tuple[MachineConfig, ...]

    def asdict(self) -> dict:
        return {
            "id": self.id,
            "machines": tuple(m.asdict() for m in self.machines),
        }


@dataclass(frozen=True)
class OperationConfig:
    """
    Data class representing the configuration for an operation.

    Attributes:
        id (str): The ID of the operation.
        machine (MachineConfig | TwinMachineConfig): The machine configuration for the operation.
        duration (DeterministicTimeConfig | StochasticTimeConfig): The duration configuration for the operation.
    """

    id: str
    machine: str
    duration: DeterministicTimeConfig | StochasticTimeConfig
    tool: Tool

    def asdict(self) -> dict:
        return {
            "id": self.id,
            "machine": self.machine,
            "duration": self.duration.asdict(),
        }


@dataclass(frozen=True)
class JobConfig:
    """
    Data class representing the configuration for a job.

    Attributes:
        id (str): The ID of the job.
        product (Product): The product associated with the job.
        operations (tuple[OperationConfig]): The operations that make up the job.
        priority (float): The priority of the job, ranging from zero to one.
    """

    id: str
    product: Product
    operations: tuple[OperationConfig, ...]
    priority: float  # from zero to one

    def asdict(self) -> dict:
        return {
            "id": self.id,
            "product": self.product.asdict(),
            "operations": tuple(o.asdict() for o in self.operations),
            "priority": self.priority,
        }

    def __hash__(self) -> int:
        return hash("j{}".format(self.id))

    def __eq__(self, value: object) -> bool:
        return isinstance(value, JobConfig) and value.id == self.id


@dataclass(frozen=True)
class ProblemInstanceConfig:
    """
    Data class representing the configuration for a problem instance.

    Attributes:
        type (ProblemInstanceTypeConfig): The type of the problem instance.
        specification (tuple[JobConfig]): The specification of the problem instance.
    """

    type: ProblemInstanceTypeConfig
    specification: tuple[JobConfig, ...]

    def asdict(self) -> dict:
        return {
            "type": self.type.asdict(),
            "specification": tuple(j.asdict() for j in self.specification),
        }


# @dataclass(frozen=True)
# class LogisticsConfig:
#     capacity: int
#     travel_times: Mapping[
#         tuple[MachineConfig | BufferConfig, MachineConfig | BufferConfig],
#         DeterministicTimeConfig | StochasticTimeConfig,
#     ]

#     def __repr__(self) -> str:
#         trv_str = ", ".join(
#             f"({type(key[0]).__name__}_{key[0].id}, {type(key[1]).__name__}_{key[1].id}): {value}"
#             for key, value in self.travel_times.items()
#         )
#         return f"LogisticsConfig(capacity={self.capacity}, travel_times={trv_str})"

#     def __str__(self) -> str:
#         return self.__repr__()


@dataclass(frozen=True)
class LogisticsConfig:
    capacity: int
    travel_times: Mapping[
        tuple[str, str],  # Use strings for ids
        DeterministicTimeConfig | StochasticTimeConfig,
    ]

    def asdict(self) -> dict:
        return {
            "capacity": self.capacity,
            "travel_times": {
                f"{key[0]}_{key[1]}": value.asdict() for key, value in self.travel_times.items()
            },
        }

    def __repr__(self) -> str:
        trv_str = ", ".join(
            f"({key[0]}, {key[1]}): {value}"  # Only referencing the ids
            for key, value in self.travel_times.items()
        )
        return f"LogisticsConfig(capacity={self.capacity}, travel_times={trv_str})"

    def __str__(self) -> str:
        return self.__repr__()


@dataclass(frozen=True)
class InstanceConfig:
    """
    Data class representing the configuration for an instance.

    Attributes:
        description (str): The description of the instance.
        components (tuple[ComponentConfig]): The components of the instance.
        instance (ProblemInstanceConfig): The problem instance configuration.
    """

    description: str
    instance: ProblemInstanceConfig
    logistics: LogisticsConfig
    machines: tuple[MachineConfig, ...]
    buffers: tuple[BufferConfig, ...]
    transports: tuple[TransportConfig, ...]

    def asdict(self) -> dict:
        return {
            "description": self.description,
            "instance": self.instance.asdict(),
            "logistics": self.logistics.asdict(),
            "machines": tuple(m.asdict() for m in self.machines),
            "buffers": tuple(b.asdict() for b in self.buffers),
            "transports": tuple(t.asdict() for t in self.transports),
        }
