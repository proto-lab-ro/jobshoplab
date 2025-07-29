from jobshoplab.types.instance_config_types import TransportConfig
from jobshoplab.types.state_types import State, TransportState, TransportStateState
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


def get_transport_id_by_job_id(state: State, job_id: str) -> str | None:
    """
    Find which transport is currently assigned to handle a specific job.

    Args:
        state (State): Current state of the system.
        job_id (str): ID of the job to find transport for.

    Returns:
        str | None: Transport ID if found, None if no transport is assigned to this job.
    """
    for transport in state.transports:
        if transport.transport_job == job_id:
            return transport.id
    return None


def get_transport_state_by_job_id(state: State, job_id: str) -> TransportState | None:
    """
    Find which transport state is currently assigned to handle a specific job.

    Args:
        state (State): Current state of the system.
        job_id (str): ID of the job to find transport for.

    Returns:
        TransportState | None: TransportState object if found, None if no transport is assigned to this job.
    """
    for transport in state.transports:
        if transport.transport_job == job_id:
            return transport
    return None
