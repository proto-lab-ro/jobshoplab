from dataclasses import replace
from typing import Tuple

from jobshoplab.types import InstanceConfig
from jobshoplab.types.state_types import (
    JobState,
    MachineState,
    MachineStateState,
    NoTime,
    OperationState,
    OperationStateState,
    Time,
    TransportLocation,
    TransportState,
    TransportStateState,
)
from jobshoplab.utils.exceptions import InvalidValue, NotImplementedError
from jobshoplab.utils.state_machine_utils import (
    buffer_type_utils,
    job_type_utils,
    machine_type_utils,
    possible_transition_utils,
)


def complete_transport_task(
    instance: InstanceConfig,
    job_state: JobState,
    transport: TransportState,
    machine: MachineState,
    time: Time | NoTime,
) -> Tuple[JobState, TransportState, MachineState]:
    """
    Transport puts job at input buffer of machine and goes back to idle.
    -> moves the job from the transport buffer to the machine prebuffer
    """
    if isinstance(time, Time):
        transport_buffer, machine_prebuffer, job_state = buffer_type_utils.switch_buffer(
            instance=instance,
            buffer_from_state=transport.buffer,
            buffer_to_state=machine.prebuffer,
            job_state=job_state,
        )

        # remove job from transport
        transport = replace(
            transport,
            buffer=transport_buffer,
            state=TransportStateState.IDLE,
            occupied_till=NoTime(),
            location=TransportLocation(0, transport.location.location[2]),
            transport_job=None,
        )

        machine = replace(machine, prebuffer=machine_prebuffer)

        return job_state, transport, machine

    else:
        raise NotImplementedError()


def complete_active_operation_on_machine(
    instance: InstanceConfig,
    jobs: tuple[JobState, ...],
    machine_state: MachineState,
    time: Time | NoTime,
) -> Tuple[JobState, MachineState]:
    """
    Completes the active operation on the machine
    -> moves the job to the postbuffer
    -> sets the machine state to idle
    -> sets the operation state to done
    """
    match time:
        case NoTime():
            raise NotImplementedError()

    try:
        job_id = machine_state.buffer.store[0]
    except IndexError:
        raise InvalidValue("No job in buffer", machine_state.buffer)

    job_state = job_type_utils.get_job_state_by_id(jobs, job_id)
    active_op = job_type_utils.get_processing_operation(job_state)

    if not active_op:
        raise InvalidValue("No active operation", active_op)
    active_op = replace(active_op, end_time=time, operation_state_state=OperationStateState.DONE)

    # update job
    job_state = possible_transition_utils.replace_job_operation_state(job_state, active_op)
    buffer = buffer_type_utils.remove_from_buffer(machine_state.buffer, job_state.id)

    machine_config = machine_type_utils.get_machine_config_by_id(
        instance.machines, machine_state.id
    )

    postbuffer, job_state = buffer_type_utils.put_in_buffer(
        machine_state.postbuffer, machine_config.postbuffer, job_state
    )

    machine_state = replace(
        machine_state,
        buffer=buffer,
        postbuffer=postbuffer,
        state=MachineStateState.IDLE,
        occupied_till=NoTime(),
    )

    return job_state, machine_state


def begin_next_job_on_machine(
    instance: InstanceConfig,
    job_state: JobState,
    machine_state: MachineState,
    time: Time | NoTime,
) -> Tuple[JobState, MachineState]:
    """
    Starts the next operation on the machine.
    -> puts the job from the prebuffer to the buffer
    -> sets the operation state to processing
    -> sets the machine state to working
    """
    if isinstance(time, Time):
        # set next operation as active
        job_configs = instance.instance.specification
        op_state = job_type_utils.get_next_not_done_operation(job_state)
        op_config = job_type_utils.get_operation_config_by_id(job_configs, op_state.id)

        occupied_time = Time(time.time + possible_transition_utils.get_duration(op_config.duration))

        op_state = OperationState(
            id=op_config.id,
            start_time=time,
            end_time=occupied_time,
            machine_id=machine_state.id,
            operation_state_state=OperationStateState.PROCESSING,
        )

        job_state = possible_transition_utils.replace_job_operation_state(job_state, op_state)

        machine_config = machine_type_utils.get_machine_config_by_id(
            instance.machines, machine_state.id
        )

        # put job from prebuffer to machine buffer
        prebuffer = buffer_type_utils.remove_from_buffer(machine_state.prebuffer, job_state.id)
        buffer, job_state = buffer_type_utils.put_in_buffer(
            machine_state.buffer, machine_config.buffer, job_state
        )

        machine_state = replace(
            machine_state,
            prebuffer=prebuffer,
            buffer=buffer,
            state=MachineStateState.WORKING,
            occupied_till=occupied_time,
        )

        return job_state, machine_state

    else:
        raise NotImplementedError()
