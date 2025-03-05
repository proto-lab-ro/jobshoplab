import jobshoplab.utils.state_machine_utils.job_type_utils as job_type_utils
import jobshoplab.utils.state_machine_utils.machine_type_utils as machine_type_utils
from jobshoplab.types import InstanceConfig, State
from jobshoplab.types.state_types import JobState, OperationStateState

# TODO: Validate and test the functions in this file


def get_inbuffer_jobs_for_machine(instance: InstanceConfig, state: State, machine_id: str):
    machine_state = machine_type_utils.get_machine_state_by_id(state.machines, machine_id)
    return [
        job_type_utils.get_job_state_by_id(state.jobs, job_id)
        for job_id in machine_state.prebuffer.store
    ]


def get_prebuffer_operations_for_machine(instance: InstanceConfig, state: State, machine_id: str):
    machine_state = machine_type_utils.get_machine_state_by_id(state.machines, machine_id)

    operations = []
    for job_id in machine_state.prebuffer.store:
        job_state = job_type_utils.get_job_state_by_id(state.jobs, job_id)
        next_operation = job_type_utils.get_next_not_done_operation(job_state)

        if next_operation.machine_id != machine_id:
            raise ValueError(
                f"Bug: Next operation (ID: {next_operation.id}) is not at machine {machine_id}, but it is in the prebuffer."
            )

        operations.append(
            job_type_utils.get_operation_config_by_id(
                instance.instance.specification, next_operation.id
            )
        )

    return operations


def find_job_state_from_operation(state: State, operation_id: str) -> JobState | None:
    return next(
        (job for job in state.jobs if any(op.id == operation_id for op in job.operations)), None
    )


def find_job_config_from_operation(instance: InstanceConfig, operation_id: str):
    return next(
        (
            job
            for job in instance.instance.specification
            if any(op.id == operation_id for op in job.operations)
        ),
        None,
    )


def get_machine_prebuffer_jobs_by_processing_time(
    instance: InstanceConfig, state: State, mode="SPT"
):
    """Gets jobs for machines based on the processing time of their next operation."""

    if mode not in {"SPT", "LPT"}:
        raise ValueError(f"Invalid mode: {mode}")

    sorting_func = min if mode == "SPT" else max
    machine_jobs = {}

    for machine in instance.machines:
        operations = get_prebuffer_operations_for_machine(instance, state, machine.id)
        if not operations:
            continue

        selected_operation = sorting_func(operations, key=lambda op: op.duration.duration)
        job = find_job_state_from_operation(state, selected_operation.id)

        if job:
            machine_jobs[machine.id] = job.id

    return machine_jobs


def get_machine_jobs_by_remaining_processing_time(
    instance: InstanceConfig, state: State, mode="srpt"
):
    """Assigns jobs to machines based on Shortest/Longest Remaining Processing Time."""

    if mode not in {"srpt", "lrpt"}:
        raise ValueError(f"Invalid mode: {mode}")

    sorting_func = min if mode == "srpt" else max
    machine_jobs = {}

    for machine in instance.machines:
        operations = get_prebuffer_operations_for_machine(instance, state, machine.id)
        if not operations:
            continue

        selected_operation = sorting_func(
            operations,
            key=lambda op: sum(
                op.duration.duration
                for op in find_job_config_from_operation(instance, op.id).operations
            ),
        )

        job = find_job_state_from_operation(state, selected_operation.id)

        if job:
            machine_jobs[machine.id] = job.id

    return machine_jobs


def get_all_outbuffer_jobs(instance: InstanceConfig, state: State):
    """Retrieves all jobs in outbuffer and postbuffer across machines."""

    jobs = [
        job_type_utils.get_job_state_by_id(state.jobs, job_id) for job_id in state.buffers[0].store
    ]

    for machine in state.machines:
        jobs.extend(
            job_type_utils.get_job_state_by_id(state.jobs, job_id)
            for job_id in machine.postbuffer.store
        )

    return tuple(jobs)


def get_job_with_most_remaining_processing_time(
    instance: InstanceConfig, job_states: tuple[JobState, ...]
):
    """Returns the job with the most remaining processing time."""

    best_job = None
    best_remaining_time = float("-inf")

    for job in job_states:
        job_config = job_type_utils.get_job_config_by_id(instance.instance.specification, job.id)
        remaining_time = sum(
            op.duration.duration
            for op in job_config.operations
            if op.id
            in {
                op.id
                for op in job.operations
                if op.operation_state_state == OperationStateState.IDLE
            }
        )

        if remaining_time > best_remaining_time:
            best_job, best_remaining_time = job, remaining_time

    return best_job


def get_job_by_operation_count(job_states, find_max=True):
    """Returns the job with the most or least remaining operations."""

    best_job = None
    best_idle_count = float("-inf") if find_max else float("inf")

    for job in job_states:
        idle_count = sum(
            1 for op in job.operations if op.operation_state_state == OperationStateState.IDLE
        )
        if idle_count == 0:
            continue  # Job is fully processed

        if (find_max and idle_count > best_idle_count) or (
            not find_max and idle_count < best_idle_count
        ):
            best_job, best_idle_count = job, idle_count

    return best_job
