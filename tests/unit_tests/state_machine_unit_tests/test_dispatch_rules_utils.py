from jobshoplab.utils.state_machine_utils.dispatch_rules_uitls import (
    find_job_config_from_operation,
    find_job_state_from_operation,
    get_all_outbuffer_jobs,
    get_inbuffer_jobs_for_machine,
    get_job_by_operation_count,
    get_job_with_most_remaining_processing_time,
    get_machine_jobs_by_remaining_processing_time,
    get_machine_prebuffer_jobs_by_processing_time,
    get_prebuffer_operations_for_machine,
)


def test_get_inbuffer_jobs_for_machine(default_instance, default_state_machine_idle):

    jobs = get_inbuffer_jobs_for_machine(default_instance, default_state_machine_idle, "m-1")
    assert len(jobs) == 1
    assert jobs[0].id == "j-1"


def test_get_prebuffer_operations_for_machine(default_instance, default_state_machine_idle):
    operations = get_prebuffer_operations_for_machine(
        default_instance, default_state_machine_idle, "m-1"
    )
    assert len(operations) == 1
    assert operations[0].id == "o-0-0"


def test_find_job_state_from_operation(default_state_machine_idle):
    job = find_job_state_from_operation(default_state_machine_idle, "o-0-0")
    assert job.id == "j-1"


def test_find_job_config_from_operation(default_instance):
    job = find_job_config_from_operation(default_instance, "o-0-0")
    assert job is not None


# TODO
