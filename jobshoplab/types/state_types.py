from dataclasses import dataclass
from enum import Enum
from typing import Protocol, TypeVar, Union

from jobshoplab.types.instance_config_types import (
    DeterministicTimeConfig,
)

EnergyConsumption = TypeVar("EnergyConsumption")
Waste = TypeVar("Waste")
C02Emission = TypeVar("C02Emission")
FinancialCost = TypeVar("FinancialCost")
# Define more specific types using Union instead of TypeVar where appropriate
ComponentState = Union["TransportStateState", "MachineStateState", "BufferStateState"]
Component = Union["MachineState", "TransportState", "BufferState"]


# These should be proper classes rather than TypeVars
class EnergyConsumptionType(Protocol):
    def asdict(self) -> dict: ...


class WasteType(Protocol):
    def asdict(self) -> dict: ...


class C02EmissionType(Protocol):
    def asdict(self) -> dict: ...


class FinancialCostType(Protocol):
    def asdict(self) -> dict: ...


Resources = Union[EnergyConsumptionType, WasteType, C02EmissionType, FinancialCostType]


# This should be defined based on the actual action structure
class ActionProtocol(Protocol):
    def asdict(self) -> dict: ...


Action = ActionProtocol


@dataclass(frozen=True)
class Time:
    time: int

    def __add__(self, other: Union["Time", "DeterministicTimeConfig"]) -> "Time":
        if isinstance(other, Time):
            return Time(self.time + other.time)
        raise TypeError(
            "Unsupported operand type(s) for +: 'Time' and '{}'".format(type(other).__name__)
        )

    def asdict(self) -> dict:
        return {"time": self.time}


@dataclass(frozen=True)
class NoTime:
    time = None

    def asdict(self) -> dict:
        return {"no_time": None}


@dataclass(frozen=True)
class FailTime:
    reason: str
    time = None

    def asdict(self) -> dict:
        return {"fail_time": {"reason": self.reason, "time": self.time}}


class BufferStateState(Enum):
    EMPTY = "Empty"
    NOT_EMPTY = "NotEmpty"
    FULL = "Full"

    def asdict(self) -> str:
        return self.value


class OperationStateState(Enum):
    IDLE = "Idle"
    SETUP = "Setup"  #!FELIX state here
    PROCESSING = "Processing"
    DONE = "Done"
    TRANSPORT = "Transport"

    def asdict(self) -> str:
        return self.value


@dataclass(frozen=True)
class OperationState:
    id: str
    start_time: Time | NoTime
    end_time: Time | NoTime
    machine_id: str
    operation_state_state: OperationStateState

    def asdict(self) -> dict:
        return {
            "id": self.id,
            "start_time": self.start_time.asdict(),
            "end_time": self.end_time.asdict(),
            "machine_id": self.machine_id,
            "operation_state_state": self.operation_state_state.asdict(),
        }


@dataclass(frozen=True)
class JobState:
    id: str
    operations: tuple[OperationState, ...]
    location: str

    def asdict(self) -> dict:
        return {
            "id": self.id,
            "operations": tuple(o.asdict() for o in self.operations),
            "location": self.location,
        }


@dataclass(frozen=True)
class BufferState:
    id: str
    state: BufferStateState
    store: tuple[str, ...]  # Job IDs

    def asdict(self) -> dict:
        return {"id": self.id, "state": self.state.asdict(), "store": self.store}


@dataclass(frozen=True)
class Consumption:
    value: float

    def asdict(self) -> int:
        return self.value


class MachineStateState(Enum):
    IDLE = "Idle"
    SETUP = "Setup"
    WORKING = "Working"

    def asdict(self) -> str:
        return self.value


class TransportStateState(Enum):
    IDLE = "Idle"
    WORKING = "Working"
    PICKUP = "Pickup"
    TRANSIT = "Transit"
    OUTAGE = "Outage"
    WAITINGPICKUP = "WaitingPickup"

    def asdict(self) -> str:
        return self.value


@dataclass(frozen=True)
class MachineState:
    id: str
    buffer: BufferState
    occupied_till: Time | NoTime
    prebuffer: BufferState
    postbuffer: BufferState
    state: MachineStateState
    resources: tuple[Resources, ...]

    def asdict(self) -> dict:
        return {
            "id": self.id,
            "buffer": self.buffer.asdict(),
            "occupied_till": self.occupied_till.asdict(),
            "prebuffer": self.prebuffer.asdict(),
            "postbuffer": self.postbuffer.asdict(),
            "state": self.state.asdict(),
            "resources": tuple(r.asdict() for r in self.resources),
        }


@dataclass
class TransportLocation:
    progress: float  # TODO: Implement in state machine
    location: str | tuple[str, str, str]

    def asdict(self) -> dict:
        return {"progress": self.progress, "location": self.location}


@dataclass(frozen=True)
class TransportState:
    state: TransportStateState
    id: str
    occupied_till: Time | NoTime
    buffer: BufferState
    location: TransportLocation
    transport_job: str | None

    def asdict(self) -> dict:
        return {
            "state": self.state.asdict(),
            "id": self.id,
            "occupied_till": self.occupied_till.asdict(),
            "buffer": self.buffer.asdict(),
            "location": self.location.asdict(),
            "transport_job": self.transport_job,
        }


@dataclass(frozen=True)
class State:
    jobs: tuple[JobState, ...]
    time: Time | NoTime
    machines: tuple[MachineState, ...]
    transports: tuple[TransportState, ...]
    buffers: tuple[BufferState, ...]

    def asdict(self) -> dict:
        return {
            "jobs": tuple(j.asdict() for j in self.jobs),
            "time": self.time.asdict(),
            "machines": tuple(m.asdict() for m in self.machines),
            "transports": tuple(t.asdict() for t in self.transports),
            "buffers": tuple(b.asdict() for b in self.buffers),
        }


ComponentTransition = TypeVar("ComponentTransition")


@dataclass(frozen=True)
class StateMachineResult:
    state: State
    sub_states: tuple[
        State, ...
    ]  #! USE ONLY FOR VIZ DEBUG OR LOGGING. sub_states are possibly semantically incorrect
    action: Action  # type: ignore #
    success: bool
    message: str
    possible_transitions: tuple[ComponentTransition, ...]  # type: ignore #

    def asdict(self) -> dict:
        return {
            "state": self.state.asdict(),
            "sub_states": tuple(s.asdict() for s in self.sub_states),
            "action": self.action.asdict(),
            "success": self.success,
            "message": self.message,
        }


class TransitionResult:
    """Result of a transition operation"""

    def __init__(self, state: State, errors: list[str]):
        self.state = state
        self.errors = errors

    def asdict(self) -> dict:
        """Convert to dictionary representation"""
        return {"state": self.state.asdict(), "errors": self.errors}
