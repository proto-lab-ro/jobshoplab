from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from jobshoplab.types.state_types import (BufferStateState, MachineStateState,
                                          TransportStateState)

ComponentState = TransportStateState | MachineStateState | BufferStateState


@dataclass(frozen=True)
class ComponentTransition:
    component_id: str
    new_state: ComponentState
    job_id: Optional[str]  # eg. Transtition from Working to Idle does not require a job
    # TODO: Wie stellen wir einen Fahrauftrag dar? -> Job von A nach B?

    def asdict(self) -> dict:
        return {
            "component_id": self.component_id,
            "new_state": self.new_state.asdict(),
            "job_id": self.job_id,
        }


class ActionFactoryInfo(Enum):
    Valid = "Valid"
    NoMoreOperations = "NoMoreOperations"
    NoOperation = "NoOperation"
    Dummy = "Dummy"

    def asdict(self) -> str:
        return self.value


@dataclass(frozen=True)
class Action:
    transitions: tuple[ComponentTransition, ...]
    action_factory_info: ActionFactoryInfo
    time_machine: Callable

    def asdict(self) -> dict:
        return {
            "transitions": tuple(t.asdict() for t in self.transitions),
            "action_factory_info": self.action_factory_info.asdict(),
            "time_machine": self.time_machine.__name__,
        }
