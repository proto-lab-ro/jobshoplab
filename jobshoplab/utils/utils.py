import hashlib
import logging
import re
from dataclasses import asdict
from typing import (
    Any,
    Hashable,
    Protocol,
)

import numpy as np
from heracless.utils.cfg_tree import as_lowercase

from jobshoplab.utils.exceptions import InvalidValue


# Define a more specific Config type
class ConfigProtocol(Protocol):
    """Protocol defining the interface expected for config objects"""

    def __getattr__(self, name: str) -> Any: ...


Config = ConfigProtocol


def get_args(
    logger: logging.Logger, std_args: dict, config: Config, cfg_instance: list[str]
) -> dict:
    """
    Get the arguments by merging the standard arguments with the attributes of the config object.

    Args:
        std_args (dict): The standard arguments. can be empty. if no standard arguments are needed.
        config (Config): The config object.
        cfg_instance (list[str]): The list of attribute names to access the desired config instance.

    Returns:
        dict: The merged arguments. to be used in the constructor of the object.

    Raises:
            InvalidValue: If the config object is None or if it doesn't have the required attribute.

    """
    args = std_args
    if config is None:
        raise InvalidValue("config must be a Config object not None", config)
    # checking if the parent folders exist in the config object if not thise is an error
    _config = config
    for instance in cfg_instance[:-1]:
        if not hasattr(config, instance):
            raise InvalidValue(
                f"config object doesn't have the attribute {instance} make sure there is not a typo in code or config file.",
                instance,
            )
        _config = getattr(config, instance)

    # the warning can now be only raised if the last instance is not found witch can be intedded if no additional arguments are needed.
    current_instance = config
    for instance in cfg_instance:
        instance = as_lowercase(instance)
        if not hasattr(current_instance, instance):
            logger.debug(
                f"config object doesn't have the attribute {instance} is thise intended? returning no additional arguments."
            )
            return args
        current_instance = getattr(current_instance, instance)
    # current_instance = as_lowercase(current_instance)
    match current_instance:
        case str():
            current_instance = as_lowercase(current_instance)
            cfg_dict = asdict(getattr(_config, current_instance))
        case _:
            cfg_dict = asdict(current_instance)

    return {**args, **cfg_dict}


def hash(obj: Hashable) -> int:
    """
    Hash the given object.

    Args:
        obj (Hashable): The object to hash. preferably a string.

    Returns:
        int: The hash value.
    """
    # Convert the id to a string and encode it to bytes, then hash it using SHA-256
    id_str = str(obj).encode("utf-8")
    hash_digest = hashlib.sha256(id_str).hexdigest()
    # Convert the hexadecimal digest to an integer and return it
    return int(hash_digest, 16)


def get_id_int(id: str) -> int:
    """
    Extracts the integer part from an ID string.

    Args:
        id (str): The ID string in the format [a-z]-[0-999]+.

    Returns:
        str: The extracted integer part of the ID.

    Raises:
        InvalidValue: If the ID format is invalid.

    Example:
        >>> get_id_int('a-123')
        '123'
    # TODO: How to handle Operation -> o-1-2
    """
    pattern = r"^[a-z]-\d+$"
    match = re.match(pattern, id)
    if not match:
        raise InvalidValue(f"Invalid id format {id} expected format is [a-z]-[0-999]+", id)
    return int(id.split("-")[1])


def get_component_type_int(id: str) -> int:
    """
    Get the integer representation of a component type from its ID.

    Args:
        id: The component ID string (format: [a-z]-[number])

    Returns:
        int: Integer code for the component type (0 for machine, 1 for transport, 2 for buffer)

    Raises:
        InvalidValue: If the component type is invalid
    """
    component_str = id.split("-")[0]
    match component_str:
        case "m":
            return 0
        case "t":
            return 1
        case "b":
            return 2
        case _:
            raise InvalidValue(f"Invalid component id {id}", id)


def get_component_id_int(all_components: list[Any], id: str) -> int:
    """
    Get the integer index of a component in a list of components.

    Args:
        all_components: List of component objects with 'id' attribute
        id: The component ID to find

    Returns:
        int: The index of the component in the list

    Raises:
        InvalidValue: If the component ID is not found
    """
    component_mapping = {component.id: i for i, component in enumerate(all_components)}
    if id not in component_mapping:
        raise InvalidValue(f"Invalid component id {id}", id)
    return component_mapping[id]


## calc_lower_bound
#####
def calculate_bi(schedule: np.ndarray) -> np.ndarray:
    """
    Calculate the bi values for Taillard's lower bound calculation.

    Args:
        schedule: A 3D numpy array representing the job schedule
                 [job_index][operation_index][machine, duration]

    Returns:
        np.ndarray: Array of bi values for each machine
    """
    num_machines = schedule.shape[1]
    num_jobs = schedule.shape[0]
    b: list[float] = []
    for machine in range(num_machines):
        b_m = np.inf
        for job in range(num_jobs):
            sum_val = 0
            for operation in range(num_machines):
                if schedule[job][operation][0] == machine:
                    break
                sum_val += schedule[job][operation][1]
            if sum_val < b_m:
                b_m = sum_val
        b.append(b_m)
    return np.array(b)


def calculate_ai(schedule: np.ndarray) -> np.ndarray:
    """
    Calculate the ai values for Taillard's lower bound calculation.

    Args:
        schedule: A 3D numpy array representing the job schedule
                 [job_index][operation_index][machine, duration]

    Returns:
        np.ndarray: Array of ai values for each machine
    """
    num_machines = schedule.shape[1]
    num_jobs = schedule.shape[0]
    a: list[float] = []
    for machine in range(num_machines):
        a_m = np.inf
        for job in range(num_jobs):
            sum_val = 0
            op_id = 0
            for operation in range(num_machines):
                op_id = operation
                if schedule[job][operation][0] == machine:
                    break
            sum_val += np.sum(schedule[job][op_id + 1 :, 1])
            if sum_val < a_m:
                a_m = sum_val
        a.append(a_m)
    return np.array(a)


def total_processing_time(schedule: np.ndarray) -> np.ndarray:
    """
    Calculate the total processing time for each machine.

    Args:
        schedule: A 3D numpy array representing the job schedule
                 [job_index][operation_index][machine, duration]

    Returns:
        np.ndarray: Array of total processing times for each machine
    """
    num_jobs = schedule.shape[0]
    num_machines = schedule.shape[1]
    total_processing_times = np.zeros(num_machines)
    for job in range(num_jobs):
        for operation in range(num_machines):
            machine = int(schedule[job][operation][0])
            duration = schedule[job][operation][1]
            total_processing_times[machine] += duration
    return total_processing_times


def max_job_duration(schedule: np.ndarray) -> int:
    """
    Calculate the maximum total duration of any job.

    Args:
        schedule: A 3D numpy array representing the job schedule
                 [job_index][operation_index][machine, duration]

    Returns:
        int: Maximum duration of any job
    """
    job_durations = np.zeros(schedule.shape[0], dtype=np.int32)
    for job in range(schedule.shape[0]):
        job_durations[job] = sum(schedule[job][:, 1])
    return int(max(job_durations))


def max_machine_duration(schedule: np.ndarray) -> int:
    """
    Calculate the maximum total duration of operations on any machine.

    Args:
        schedule: A 3D numpy array representing the job schedule
                 [job_index][operation_index][machine, duration]

    Returns:
        int: Maximum duration of any machine
    """
    machine_durations = np.zeros(schedule.shape[1], dtype=np.int32)
    for machine in range(schedule.shape[1]):
        machine_durations[machine] = sum(schedule[schedule[:, :, 0] == machine][:, 1])
    return int(max(machine_durations))


def calculate_lower_bound2(schedule: np.ndarray) -> int:
    """
    Calculate a simple lower bound for the makespan as the maximum of:
    1. The maximum total duration of any job
    2. The maximum total duration of operations on any machine

    Args:
        schedule: A 3D numpy array representing the job schedule
                 [job_index][operation_index][machine, duration]

    Returns:
        int: A lower bound for the makespan
    """
    max_jd = max_job_duration(schedule=schedule)
    max_md = max_machine_duration(schedule=schedule)

    return max(max_jd, max_md)


def calculate_lower_bound(instance):
    """
    lowerbound calculation implementation after taillard 1989 Benchmarks for basic scheduling problems.
    gives a rought estimate of the lower bound of the makespan of the instance. the estimate is allways less than the actual makespan.
    Args:
        instance (object): The instance object.

    Returns:
        int: The lower bound of the makespan of the instance

    """

    schedule = np.array(
        [
            [(int(o.machine.split("-")[1]), o.duration.duration) for o in job.operations]
            for job in instance.instance.specification
        ]
    )
    bi = calculate_bi(schedule)
    ai = calculate_ai(schedule)
    Ti = total_processing_time(schedule)
    return int(max(max(bi + Ti + ai), max_job_duration(schedule)))


def get_max_allowed_time(instance_config):
    """
    Calculate the maximum allowed time for a given instance configuration.

    This function computes the sum of the durations of all operations in the
    instance configuration. This sum represents the worst-case scenario for
    scheduling without any obvious mistakes.

    Args:
        instance_config (object): The configuration of the instance, which
        includes job specifications and their respective operations.

    Returns:
        int: The total duration of all operations, representing the maximum
        allowed time.
    """
    return sum(
        [
            o.duration.duration
            for job in instance_config.instance.specification
            for o in job.operations
        ]
    )  # max allowed time is the sum of all operation durations, witch can be seen a the worst scheduling stragety without obviors mistakes
