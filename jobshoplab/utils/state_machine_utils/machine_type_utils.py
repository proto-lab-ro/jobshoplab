from dataclasses import replace

from jobshoplab.types.instance_config_types import MachineConfig
from jobshoplab.types.state_types import BufferState, MachineState
from jobshoplab.utils.exceptions import InvalidValue
from jobshoplab.utils.state_machine_utils.component_type_utils import get_obj_by_id


def get_machine_state_by_id(machines: tuple[MachineState, ...], machine_id: str) -> MachineState:
    """
    Get a machine by its ID from a tuple of MachineState objects.

    Args:
        machines (tuple[MachineState, ...]): A tuple of MachineState objects.
        machine_id (str): The ID of the desired machine.

    Returns:
        MachineState: The MachineState object with the specified ID.

    Raises:
        InvalidValue: If the desired machine is not found in the given tuple of machines.
    """
    return get_obj_by_id(machines, machine_id)


def get_machine_config_by_id(
    machine_configs: tuple[MachineConfig, ...], machine_id: str
) -> MachineConfig:
    """
    Get a machine config by its ID from a tuple of MachineConfig objects.

    Args:
        machine_configs (tuple[MachineConfig, ...]): A tuple of MachineConfig objects.
        machine_id (str): The ID of the desired machine.

    Returns:
        MachineConfig: The MachineConfig object with the specified ID.

    Raises:
        InvalidValue: If the desired machine config is not found in the given tuple of machine configs.
    """
    return get_obj_by_id(machine_configs, machine_id)


def get_machine_id_from_buffer(
    machine_configs: tuple[MachineConfig, ...], buffer_id: str
) -> str | None:
    """
    Get the Machine where the buffer is located.

    Checks if buffer is prebuffer, postbuffer or buffer and returns the corresponding machine id.
    """
    for machine in machine_configs:
        if buffer_id == machine.prebuffer.id:
            return machine.id
        if buffer_id == machine.buffer.id:
            return machine.id
        if buffer_id == machine.postbuffer.id:
            return machine.id
    # return None
    # raise InvalidValue(buffer_id, machine_configs, "buffer not found in any machine")


def get_buffer_state_from_machine(machine_state: MachineState, buffer_id: str) -> BufferState:
    """
    Get the buffer state from a machine state.
    """
    if buffer_id == machine_state.prebuffer.id:
        return machine_state.prebuffer
    if buffer_id == machine_state.buffer.id:
        return machine_state.buffer
    if buffer_id == machine_state.postbuffer.id:
        return machine_state.postbuffer
    raise InvalidValue(buffer_id, machine_state, "buffer not found in machine")


def replace_buffer_state_in_machine(
    machine_state: MachineState, buffer_state: BufferState
) -> MachineState:
    """
    Update the buffer state in a machine state.
    """
    if buffer_state.id == machine_state.prebuffer.id:
        return replace(machine_state, prebuffer=buffer_state)
    if buffer_state.id == machine_state.buffer.id:
        return replace(machine_state, buffer=buffer_state)
    if buffer_state.id == machine_state.postbuffer.id:
        return replace(machine_state, postbuffer=buffer_state)
    raise InvalidValue(buffer_state.id, machine_state, "buffer not found in machine")
