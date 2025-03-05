from typing import Tuple, TypeVar

from jobshoplab.types.state_types import State
from jobshoplab.utils.exceptions import InvalidValue

T = TypeVar("T", bound=object)


def get_obj_by_id(obj: Tuple[T, ...], id: str) -> T:
    """
    Get an object by its ID from a tuple of objects.

    Args:
        obj (Tuple[T, ...]): A tuple of objects.
        id (str): The ID of the desired object.

    Returns:
        T: The object with the specified ID.

    Raises:
        InvalidValue: If the desired object is not found in the given tuple of objects.
    """
    object = next(filter(lambda obj: obj.id == id, obj), None)  # type: ignore
    if object is None:
        raise InvalidValue(id, obj, "desired object not found")
    return object


def get_comp_by_id(state: State, id: str):
    comp = (*state.machines, *state.buffers, *state.transports)
    return get_obj_by_id(comp, id)
