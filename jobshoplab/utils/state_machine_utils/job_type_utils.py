from typing import Iterable

from jobshoplab.types import (JobConfig, JobState, OperationConfig,
                              OperationState)
from jobshoplab.types.state_types import MachineState, OperationStateState
from jobshoplab.utils.exceptions import InvalidValue


def job_at_machine(job: JobState, machine: MachineState) -> bool:
    """
    Check if a job is at a machine.

    Args:
        job (JobState): The job to check.
        machine (MachineState): The machine to check.

    Returns:
        bool: True if the job is at the machine, False otherwise.
    """

    return job.location == machine.id


def get_job_state_by_id(jobs: tuple[JobState, ...], job_id: str) -> JobState:
    """
    Get a job by its ID from a tuple of JobState objects.

    Args:
        jobs (tuple[JobState, ...]): A tuple of JobState objects.
        job_id (str): The ID of the desired job.

    Returns:
        JobState: The JobState object with the specified ID.

    Raises:
        InvalidValue: If the desired job is not found in the given tuple of jobs.
    """
    job = next(filter(lambda job: job.id == job_id, jobs), None)
    if job is None:
        raise InvalidValue(id, jobs, "desired job not found")
    return job


def get_job_config_by_id(jobs: tuple[JobConfig, ...], job_id: str) -> JobConfig:
    """
    Get a job config by its ID from a tuple of JobConfig objects.

    Args:
        jobs (tuple[JobConfig, ...]): A tuple of JobConfig objects.
        job_id (str): The ID of the desired job.

    Returns:
        JobConfig: The JobConfig object with the specified ID.

    Raises:
        InvalidValue: If the desired job is not found in the given tuple of jobs.
    """
    job = next(filter(lambda job: job.id == job_id, jobs), None)
    if job is None:
        raise InvalidValue(job_id, jobs, "desired job not found")
    return job


def get_operation_state_by_id(jobs: tuple[JobState, ...], operation_id: str) -> OperationState:
    """
    Get an operation by its ID from a tuple of JobState objects.

    Args:
        jobs (tuple[JobState, ...]): A tuple of JobState objects.
        operation_id (str): The ID of the desired operation.

    Returns:
        JobState: The JobState object with the specified ID.

    Raises:
        InvalidValue: If the desired operation is not found in the given tuple of jobs.
    """
    operations = (operation for job in jobs for operation in job.operations)
    operation = next(filter(lambda op: op.id == operation_id, operations), None)
    if operation is None:
        raise InvalidValue(operation_id, jobs, "desired operation not found")
    return operation


def get_operation_config_by_id(jobs: tuple[JobConfig, ...], operation_id: str) -> OperationConfig:
    """
    Get an operation config by its ID from a tuple of JobConfig objects.

    Args:
        jobs (tuple[JobConfig, ...]): A tuple of JobConfig objects.
        operation_id (str): The ID of the desired operation.

    Returns:
        JobConfig: The JobConfig object with the specified ID.

    Raises:
        InvalidValue: If the desired operation is not found in the given tuple of jobs.
    """
    operations = (operation for job in jobs for operation in job.operations)
    operation = next(filter(lambda op: op.id == operation_id, operations), None)
    if operation is None:
        raise InvalidValue(operation_id, jobs, "desired operation not found")
    return operation


def is_last_operation_running(job: JobState) -> bool:
    """
    Check if the last operation of a job is running.

    Args:
        job (JobState): The job to check.

    Returns:
        bool: True if the last operation of the job is running, False otherwise.
    """
    return job.operations[-1].operation_state_state == OperationStateState.PROCESSING


def is_job_running(job: JobState) -> bool:
    """
    Check if a job is running.

    Args:
        job (JobState): The job to check.

    Returns:
        bool: True if the job is running, False otherwise.
    """
    return any(
        operation.operation_state_state == OperationStateState.PROCESSING
        for operation in job.operations
    )


def get_next_not_done_operation(job: JobState) -> OperationState:
    """
    Get the next operation from a job.

    Args:
        job (JobState): The job to get the next operation from.

    Returns:
        OperationState: The next operation from the job.

    Raises:
        InvalidValue: If the job has no more operations.
    """
    operations = job.operations
    next_operation = next(
        filter(lambda op: op.operation_state_state != OperationStateState.DONE, operations), None
    )
    if next_operation is None:
        raise InvalidValue(job, "job has no more operations. all operations are done.")
    return next_operation


def get_next_idle_operation(job: JobState) -> OperationState:
    """
    Get the next operation from a job.

    Args:
        job (JobState): The job to get the next operation from.

    Returns:
        OperationState: The next operation from the job.

    Raises:
        InvalidValue: If the job has no more operations.
    """
    operations = job.operations
    next_operation = next(
        filter(lambda op: op.operation_state_state == OperationStateState.IDLE, operations), None
    )
    if next_operation is None:
        raise InvalidValue(job, "job has no more operations. all operations are done.")
    return next_operation


def get_next_operation_for_machine(machine_id, jobs: JobState) -> OperationState:
    raise NotImplementedError


def get_processing_operation(job: JobState) -> OperationState | None:
    """
    Get the active operation from a job.

    Args:
        job (JobState): The job to get the active operation from.

    Returns:
        OperationState: The active operation from the job.

    Raises:
        InvalidValue: If the job has no active operations.
    """
    operations = job.operations
    active_operation = next(
        filter(lambda op: op.operation_state_state == OperationStateState.PROCESSING, operations),
        None,
    )
    if active_operation is None:
        return None
    return active_operation


# group all operations from jobstates by thier operationstatestate
def group_operations_by_state(
    job_states: Iterable[JobState] | JobState,
) -> dict[OperationStateState, list[OperationState]]:
    """
    Group all operations from job states by their operation state state.

    Args:
        job_states (Iterable[JobState]): An iterable of JobState objects.

    Returns:
        dict[OperationStateState, list[OperationState]]: A dictionary with the operation state state as the key and a list of operations as the value.
    """
    if isinstance(job_states, JobState):
        job_states = [job_states]

    operations = (operation for job in job_states for operation in job.operations)
    grouped_operations = {}
    for operation in operations:
        if operation.operation_state_state not in grouped_operations:
            grouped_operations[operation.operation_state_state] = []
        grouped_operations[operation.operation_state_state].append(operation)
    return grouped_operations


def is_done(job: JobState) -> bool:
    """
    Check if a job is done.

    Args:
        job (JobState): The job to check.

    Returns:
        bool: True if the job is done, False otherwise.
    """
    return all(
        operation.operation_state_state == OperationStateState.DONE for operation in job.operations
    )
