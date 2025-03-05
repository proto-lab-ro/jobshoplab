from dataclasses import dataclass
from datetime import datetime
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class RenderBackend:
    render_in_dashboard: "RenderInDashboard"
    simulation: "Simulation"


@dataclass(frozen=True)
class EventBasedBinaryActionMiddleware:
    loglevel: str
    truncation_joker: int
    truncation_active: bool


@dataclass(frozen=True)
class Env:
    loglevel: str
    observation_factory: str
    reward_factory: str
    action_factory: str
    render_backend: str
    middleware: str
    max_time_fct: int
    max_action_fct: int


@dataclass(frozen=True)
class BinaryActionJsspReward:
    loglevel: str
    sparse_bias: int
    dense_bias: float
    truncation_bias: int


@dataclass(frozen=True)
class Compiler:
    loglevel: str
    repo: str
    validator: str
    manipulators: tuple[str]
    dsl_repository: "DslRepository"
    spec_repository: "SpecRepository"


@dataclass(frozen=True)
class RenderInDashboard:
    loglevel: str
    port: int
    debug: bool


@dataclass(frozen=True)
class RewardFactory:
    binary_action_jssp_reward: "BinaryActionJsspReward"


@dataclass(frozen=True)
class BinaryJobActionActionFactory:
    loglevel: str


@dataclass(frozen=True)
class BinaryActionObservationFactory:
    loglevel: str


@dataclass(frozen=True)
class Simulation:
    json_dump_dir: str
    port: int
    loglevel: str
    bind_all: bool


@dataclass(frozen=True)
class ActionFactory:
    binary_job_action_action_factory: "BinaryJobActionActionFactory"


@dataclass(frozen=True)
class StateMachine:
    loglevel: str


@dataclass(frozen=True)
class Config:
    title: str
    default_loglevel: str
    compiler: "Compiler"
    env: "Env"
    state_machine: "StateMachine"
    middleware: "Middleware"
    action_factory: "ActionFactory"
    observation_factory: "ObservationFactory"
    reward_factory: "RewardFactory"
    render_backend: "RenderBackend"


@dataclass(frozen=True)
class SpecRepository:
    dir: str


@dataclass(frozen=True)
class Middleware:
    event_based_binary_action_middleware: "EventBasedBinaryActionMiddleware"


@dataclass(frozen=True)
class DslRepository:
    dir: str


@dataclass(frozen=True)
class ObservationFactory:
    binary_action_observation_factory: "BinaryActionObservationFactory"


def load_config(config_path: str) -> Config: ...
