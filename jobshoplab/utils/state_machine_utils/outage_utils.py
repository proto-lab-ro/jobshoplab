from jobshoplab.types.instance_config_types import InstanceConfig, OutageConfig
from jobshoplab.types.state_types import (
    TransportState,
    DeterministicTimeConfig,
    StochasticTimeConfig,
    MachineState,
    State,
    Time,
    NoTime,
    OutageActive,
    OutageInactive,
    OutageState,
)
from jobshoplab.utils.state_machine_utils.transport_type_utils import get_transport_config_by_id
from jobshoplab.utils.state_machine_utils.machine_type_utils import get_machine_config_by_id
from jobshoplab.utils.exceptions import InvalidType
from typing import Iterable


def _get_duration(current_time, outage_state):
    match outage_state.active:
        case OutageActive():
            raise ValueError("Outage is active")
        case OutageInactive():
            if isinstance(outage_state.last_time_active, NoTime):
                last_time_active = 0
            else:
                last_time_active = outage_state.last_time_active.time
            return current_time.time - last_time_active
        case _:
            raise ValueError("Outage state is not active or inactive")


def _sample_frq(frequency: StochasticTimeConfig, duration: int) -> bool:
    """
    Sample a time from the frequency object.
    """
    applies = duration > frequency.time
    if applies:
        frequency.update()
        return True
    return False


def _should_apply_based_on_frequency(outage, duration):
    match outage.frequency:
        case DeterministicTimeConfig():
            return outage.frequency.time >= duration
        case StochasticTimeConfig():
            return _sample_frq(outage.frequency, duration)
        case _:
            raise NotImplementedError()


def _sample_from_outage_obj(
    outage: OutageConfig, component: MachineState | TransportState, current_time: Time | NoTime
) -> OutageState:
    """
    Sample a time from the outage object.
    """
    outage_state = next(filter(lambda x: x.id == outage.id, component.outages), None)
    if outage_state is None:
        raise ValueError("Outage state not found in component")
    duration_since_last_occ = _get_duration(current_time, outage_state)
    should_apply = _should_apply_based_on_frequency(outage, duration_since_last_occ)
    if not should_apply:
        return outage_state
    # its time for a outage now.. lets get the duration
    match outage.duration:
        case DeterministicTimeConfig():
            return OutageState(
                id=outage.id,
                active=OutageActive(
                    start_time=current_time,
                    end_time=Time(current_time.time + outage.duration.time),
                ),
            )
        case StochasticTimeConfig():
            outage.duration.update()
            return OutageState(
                id=outage.id,
                active=OutageActive(
                    start_time=current_time,
                    end_time=Time(current_time.time + outage.duration.time),
                ),
            )
        case _:
            raise ValueError("Outage duration is not deterministic or stochastic")


def get_new_outage_states(
    component: TransportState | MachineState, instance: InstanceConfig, current_time: Time | NoTime
) -> tuple[OutageState, ...]:
    """
    Get the time until the transport is available again.
    """
    match component:
        case TransportState():
            conf_obj = get_transport_config_by_id(instance.transports, component.id)
        case MachineState():
            conf_obj = get_machine_config_by_id(instance.machines, component.id)
        case _:
            raise InvalidType("component", component, "TransportState or MachineState")
    return tuple(
        (_sample_from_outage_obj(outage, component, current_time) for outage in conf_obj.outages)
    )


def get_occupied_time_from_outage_iterator(outage_states: Iterable) -> int:
    """
    Get the occupied time from the outage iterator.
    """
    active_outages = filter(lambda x: isinstance(x.active, OutageActive), outage_states)
    if not active_outages:
        return 0
    return max(map(lambda x: x.active.end_time.time, active_outages))


def release_outage(outage):
    """
    Release the outage.
    """
    if isinstance(outage.active, OutageActive):
        return OutageState(
            id=outage.id,
            active=OutageInactive(last_time_active=outage.active.end_time),
        )
    return outage
