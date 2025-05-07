from dataclasses import replace

import pytest

from jobshoplab.state_machine.core.state_machine.manipulate import (
    begin_next_job_on_machine, complete_active_operation_on_machine,
    complete_transport_task)
from jobshoplab.types.state_types import (MachineStateState, NoTime,
                                          OperationStateState, Time,
                                          TransportStateState)
from jobshoplab.utils.exceptions import InvalidValue, NotImplementedError


def test_finish_transport_job(
    default_instance, transport_state_transit, default_state_machine_idle_empty, job_state_done
):
    # Setup
    time = Time(10)
    job_state = replace(job_state_done, location="t-1")
    transport_state = replace(
        transport_state_transit,
        transport_job=job_state.id,
        buffer=replace(transport_state_transit.buffer, store=(job_state.id,)),  # Add job to buffer
        location=replace(transport_state_transit.location, location=("source", "path", "dest")),
    )

    machine = default_state_machine_idle_empty.machines[0]

    # Execute
    updated_job, updated_transport, updated_machine = complete_transport_task(
        default_instance, job_state, transport_state, machine, time
    )

    # Assert
    assert updated_job.location == "b-1"
    assert updated_transport.state == TransportStateState.OUTAGE
    assert updated_transport.transport_job is None
    assert updated_transport.occupied_till == Time(10)


def test_finish_transport_job_no_time(
    default_instance, job_state_done, transport_state_transit, default_state_machine_idle_empty
):
    with pytest.raises(NotImplementedError):
        complete_transport_task(
            default_instance,
            job_state_done,
            transport_state_transit,
            default_state_machine_idle_empty.machines[0],
            NoTime(),
        )


def test_finish_active_operation(default_instance, default_state_machine_working):
    # Setup
    time = Time(10)
    machine = replace(
        default_state_machine_working.machines[0],
        buffer=replace(
            default_state_machine_working.machines[0].buffer, store=("j-1",)  # Add job to buffer
        ),
    )
    state = replace(default_state_machine_working, machines=(machine,))

    # Execute
    updated_job, updated_machine = complete_active_operation_on_machine(
        default_instance, state.jobs, machine, time
    )

    # Assert
    assert updated_machine.state == MachineStateState.IDLE
    assert updated_machine.occupied_till == NoTime()
    active_op = [
        op for op in updated_job.operations if op.operation_state_state == OperationStateState.DONE
    ][0]
    assert active_op.end_time == time


def test_finish_active_operation_no_job_in_buffer(
    default_instance, machine_state_working, default_state_machine_working
):
    # Setup
    time = Time(10)
    with pytest.raises(InvalidValue):
        complete_active_operation_on_machine(
            default_instance, default_state_machine_working.jobs, machine_state_working, time
        )


def test_finish_active_operation_no_time(default_instance, default_state_machine_working):
    # Setup
    machine = default_state_machine_working.machines[0]
    with pytest.raises(NotImplementedError):
        complete_active_operation_on_machine(
            default_instance, default_state_machine_working.jobs, machine, NoTime()
        )


def test_start_next_operation(default_instance, job_state_done, machine_state_idle):
    # Setup
    time = Time(10)
    job = replace(job_state_done, location="m-1")
    operation = replace(
        job.operations[0],
        id="o-0-0",  # Make sure ID matches config
        operation_state_state=OperationStateState.IDLE,
        machine_id="m-1",  # Make sure machine ID matches
        start_time=NoTime(),
        end_time=NoTime(),
    )
    job = replace(job, operations=(operation,))
    machine = replace(
        machine_state_idle,
        buffer=replace(machine_state_idle.buffer, store=("j-1",)),  # Ensure job in buffer
        prebuffer=replace(machine_state_idle.prebuffer, store=()),  # Ensure prebuffer is empty
        state=MachineStateState.SETUP,
    )

    # Execute
    updated_job, updated_machine = begin_next_job_on_machine(default_instance, job, machine, time)

    # Assert
    assert updated_machine.state == MachineStateState.WORKING
    assert updated_machine.occupied_till == Time(13)  # time + duration
    active_op = [
        op
        for op in updated_job.operations
        if op.operation_state_state == OperationStateState.PROCESSING
    ][0]
    assert active_op.start_time == time
    assert active_op.end_time == Time(13)

    # Additional assertions
    assert job.id in updated_machine.buffer.store  # Check job is in buffer
    assert len(updated_machine.buffer.store) == 1  # Should only have one job


def test_start_next_operation_no_time(default_instance, job_state_done, machine_state_idle):
    with pytest.raises(Exception):
        begin_next_job_on_machine(default_instance, job_state_done, machine_state_idle, NoTime())
