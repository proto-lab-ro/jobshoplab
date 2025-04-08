from jobshoplab.types.instance_config_types import InstanceConfig
from jobshoplab.types.state_types import (
    DeterministicTimeConfig,
    StochasticTimeConfig,
)


def _get_travel_time_from_spec(
    instance: InstanceConfig, transport_source: str, transport_destination: str
) -> int:
    if transport_source.startswith("m") or transport_destination.startswith("m"):
        travel_time = instance.logistics.travel_times.get((transport_source, transport_destination))
        match travel_time:
            case DeterministicTimeConfig():  # @ FELIX ADD STOCHASTIC TIME and Breakdown
                return travel_time.time
            case StochasticTimeConfig():
                travel_time.update()
                return travel_time.time
            case None:
                raise ValueError(
                    "No travel time found between", transport_source, transport_destination
                )
            case _:
                raise NotImplementedError()
    else:
        raise NotImplementedError()
