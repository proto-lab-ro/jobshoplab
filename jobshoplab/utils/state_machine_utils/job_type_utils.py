from typing import Iterable, Optional

from jobshoplab.types import InstanceConfig, JobConfig, JobState, OperationConfig, OperationState
from jobshoplab.types.instance_config_types import BufferRoleConfig
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


def get_next_idle_operation(job: JobState) -> Optional[OperationState]:
    """
    Get the next idle operation from a job that needs to be executed.

    This function searches for the first operation in the job that is in IDLE state,
    meaning it's ready to be processed. Unlike get_next_not_done_operation, this
    function returns None if no idle operations exist, allowing graceful handling
    of jobs where all operations are complete or in progress.

    Args:
        job (JobState): The job to get the next idle operation from.

    Returns:
        Optional[OperationState]: The next idle operation from the job, or None
            if no idle operations remain. This allows proper handling of completed
            jobs without raising exceptions.
    """
    operations = job.operations
    # Find the first operation that is ready to be executed (IDLE state)
    next_operation = next(
        filter(lambda op: op.operation_state_state == OperationStateState.IDLE, operations), None
    )
    return next_operation


def get_next_operation_for_machine(machine_id, jobs: JobState) -> OperationState:
    raise NotImplementedError


def get_prior_executed_operation(job: JobState) -> Optional[OperationState]:
    """Get the last operation from a job that is in the DONE state.
    Args:
        job (JobState): The job to get the last operation from.
    Returns:
        OperationState: The last operation from the job that is in the DONE state.
    Raises:
        InvalidValue: If the job has no operations in the DONE state.
    """
    done_operations = tuple(
        filter(lambda op: op.operation_state_state == OperationStateState.DONE, job.operations)
    )
    if not done_operations:
        return None
    return done_operations[-1]


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


def is_done(job: JobState, instance: InstanceConfig) -> bool:
    """
    Check if a job is completely done in the job shop system.

    A job is considered done when two conditions are met:
    1. All operations are completed (DONE state)
    2. The job has been transported to an output buffer

    This dual-condition approach ensures that job completion includes both
    processing completion and proper material flow to the final destination.

    Args:
        job (JobState): The job to check for completion.
        instance (InstanceConfig): The instance configuration containing buffer definitions.

    Returns:
        bool: True if the job is completely done (operations complete AND in output buffer),
            False otherwise. This indicates full job shop process completion for the job.
    """
    # Get all output buffer IDs - final destinations for completed jobs
    output_buffer_ids = [b.id for b in instance.buffers if b.role == BufferRoleConfig.OUTPUT]
    # Job is done only if operations are complete AND it's in an output buffer
    return all_operations_done(job) and job.location in output_buffer_ids


def all_operations_done(job: JobState) -> bool:
    """
    Check if all operations in a single job are in DONE state.

    This function verifies that every operation within a job has been completed
    by checking their state. It's used as a prerequisite for job completion
    but doesn't guarantee the job is fully done (transportation to output buffer
    is also required).

    Args:
        job (JobState): The job to check for operation completion.

    Returns:
        bool: True if all operations in the job are in DONE state, False otherwise.
            This indicates processing completion but not necessarily full job completion.
    """
    # Check that every operation in this job has been completed
    return all(
        operation.operation_state_state == OperationStateState.DONE for operation in job.operations
    )


def no_operation_idle(job: JobState) -> bool:
    """
    Check if no operations in a job are in IDLE state.

    This function determines if a job has any remaining operations that need to be
    executed. When this returns True, it means all operations are either in progress
    (PROCESSING) or completed (DONE), indicating the job may need transportation
    to the output buffer rather than to another machine for processing.

    Args:
        job (JobState): The job to check for idle operations.

    Returns:
        bool: True if no operations are in IDLE state (all are PROCESSING or DONE),
            False if at least one operation is still waiting to be processed.
            Used to determine if job needs transport to output vs. next operation.
    """
    # Check that no operation is waiting to be processed (all are beyond IDLE state)
    return all(
        operation.operation_state_state != OperationStateState.IDLE for operation in job.operations
    )
