from jobshoplab.types.instance_config_types import TransportConfig
from jobshoplab.types.state_types import TransportState, TransportStateState
from jobshoplab.utils.state_machine_utils.component_type_utils import \
    get_obj_by_id


def get_transport_state_by_id(
    transports: tuple[TransportState, ...], transport_id: str
) -> TransportState:
    """
    Get a transport by its ID from a tuple of TransportState objects.

    Args:
        transports (tuple[TransportState, ...]): A tuple of TransportState objects.
        transport_id (str): The ID of the desired transport.

    Returns:
        TransportState: The TransportState object with the specified ID.

    Raises:
        InvalidValue: If the desired transport is not found in the given tuple of transports.
    """
    return get_obj_by_id(transports, transport_id)


def get_transport_config_by_id(
    transports: tuple[TransportConfig, ...], transport_id: str
) -> TransportConfig:
    """
    Get a transport by its ID from a tuple of TransportConfig objects.

    Args:
        transports (tuple[TransportConfig, ...]): A tuple of TransportConfig objects.
        transport_id (str): The ID of the desired transport.

    Returns:
        TransportConfig: The TransportConfig object with the specified ID.

    Raises:
        InvalidValue: If the desired transport is not found in the given tuple of transports.
    """
    return get_obj_by_id(transports, transport_id)


def group_transports_by_state(
    transports: tuple[TransportState, ...],
) -> dict[TransportStateState, tuple[TransportState, ...]]:
    """
    Group all transports by their state.

    Args:
        transports (tuple[TransportState, ...]): A tuple of TransportState objects.

    Returns:
        dict[str, tuple[TransportState, ...]]: A dictionary with the transport state as the key and a tuple of transports as the value.
    """
    grouped_transports = {}
    for transport in transports:
        if transport.state not in grouped_transports:
            grouped_transports[transport.state] = []
        grouped_transports[transport.state].append(transport)
    return grouped_transports
