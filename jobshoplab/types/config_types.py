from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DslRepositoryConfig:
    dir: str = "data/jssp_instances/dsl/default_instance.yaml"


@dataclass
class SpecRepositoryConfig:
    dir: str = "data/jssp_instances/spec_files/ft06"


@dataclass
class CompilerConfig:
    loglevel: str = "warning"
    repo: str = "DslRepository"
    validator: str = "SimpleDSLValidator"
    manipulators: List[str] = field(default_factory=lambda: ["DummyManipulator"])
    dsl_repository: DslRepositoryConfig = field(default_factory=DslRepositoryConfig)
    spec_repository: SpecRepositoryConfig = field(default_factory=SpecRepositoryConfig)


@dataclass
class EnvConfig:
    loglevel: str = "warning"
    observation_factory: str = "BinaryActionObservationFactory"
    reward_factory: str = "BinaryActionJsspReward"
    action_factory: str = "BinaryJobActionFactory"
    render_backend: str = "render_in_dashboard"
    middleware: str = "EventBasedBinaryActionMiddleware"
    max_time_fct: int = 2
    max_action_fct: int = 3


@dataclass
class StateMachineConfig:
    loglevel: str = "warning"
    allow_early_transport: bool = True
    middleware: Optional[str] = None
    action_factory: Optional[str] = None


@dataclass
class EventBasedBinaryActionMiddlewareConfig:
    loglevel: str = "warning"
    truncation_joker: int = 5
    truncation_active: bool = False


@dataclass
class MiddlewareConfig:
    event_based_binary_action_middleware: EventBasedBinaryActionMiddlewareConfig = field(
        default_factory=EventBasedBinaryActionMiddlewareConfig
    )


@dataclass
class BinaryJobActionFactoryConfig:
    loglevel: str = "warning"


@dataclass
class ActionFactoryConfig:
    binary_job_action_factory: BinaryJobActionFactoryConfig = field(
        default_factory=BinaryJobActionFactoryConfig
    )


@dataclass
class BinaryActionObservationFactoryConfig:
    loglevel: str = "warning"


@dataclass
class TasselJsspObservationConfig:
    loglevel: str = "warning"



@dataclass
class ObservationFactoryConfig:
    binary_action_observation_factory: BinaryActionObservationFactoryConfig = field(
        default_factory=BinaryActionObservationFactoryConfig
    )
    tassel_jsp_observation: TasselJsspObservationConfig = field(
        default_factory=TasselJsspObservationConfig
    )


@dataclass
class BinaryActionJsspRewardConfig:
    loglevel: str = "warning"
    sparse_bias: float = 1.0
    dense_bias: float = 0.001
    truncation_bias: float = -1.0


@dataclass
class RewardFactoryConfig:
    binary_action_jssp_reward: BinaryActionJsspRewardConfig = field(
        default_factory=BinaryActionJsspRewardConfig
    )


@dataclass
class RenderInDashboardConfig:
    loglevel: str = "warning"
    port: int = 8050
    debug: bool = False


@dataclass
class SimulationConfig:
    json_dump_dir: str = "data/tmp/simulation_interface.json"
    port: int = 8051
    loglevel: str = "warning"
    bind_all: bool = False


@dataclass
class CliTableConfig:
    loglevel: str = "warning"


@dataclass
class RenderBackendConfig:
    render_in_dashboard: RenderInDashboardConfig = field(default_factory=RenderInDashboardConfig)
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    cli_table: CliTableConfig = field(default_factory=CliTableConfig)


@dataclass
class Config:
    title: str = "Dev Environment"
    default_loglevel: str = "warning"
    compiler: CompilerConfig = field(default_factory=CompilerConfig)
    env: EnvConfig = field(default_factory=EnvConfig)
    state_machine: StateMachineConfig = field(default_factory=StateMachineConfig)
    middleware: MiddlewareConfig = field(default_factory=MiddlewareConfig)
    action_factory: ActionFactoryConfig = field(default_factory=ActionFactoryConfig)
    observation_factory: ObservationFactoryConfig = field(default_factory=ObservationFactoryConfig)
    reward_factory: RewardFactoryConfig = field(default_factory=RewardFactoryConfig)
    render_backend: RenderBackendConfig = field(default_factory=RenderBackendConfig)
