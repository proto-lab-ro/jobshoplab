from dataclasses import replace

import pytest

from jobshoplab.types import NoTime, State, Time
from jobshoplab.types.action_types import ComponentTransition
from jobshoplab.types.instance_config_types import (
    BufferConfig,
    BufferTypeConfig,
    DeterministicTimeConfig,
    InstanceConfig,
    Product,
    TransportTypeConfig,
)
from jobshoplab.types.state_types import (
    BufferState,
    BufferStateState,
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


@pytest.fixture
def create_buffer_state():
    def create_state(
        id: str = "b-999", state: BufferStateState = BufferStateState.EMPTY, store: tuple = ()
    ) -> BufferState:
        return BufferState(id=id, state=state, store=store)

    return create_state


@pytest.fixture
def operation_done():
    return OperationState(
        id="o-1",
        operation_state_state=OperationStateState.DONE,
        start_time=NoTime(),
        end_time=NoTime(),
        machine_id="m-1",
    )


@pytest.fixture
def operation_processing():
    return OperationState(
        id="o-1",
        operation_state_state=OperationStateState.PROCESSING,
        start_time=NoTime(),
        end_time=NoTime(),
        machine_id="m-1",
    )


@pytest.fixture
def operation_idle():
    return OperationState(
        id="o-1",
        operation_state_state=OperationStateState.IDLE,
        start_time=NoTime(),
        end_time=NoTime(),
        machine_id="m-1",
    )


@pytest.fixture
def job_state_done(operation_done):
    return JobState(id="j-1", operations=(operation_done,), location="m-1")


@pytest.fixture
def job_state_processing(operation_processing):
    return JobState(id="j-1", operations=(operation_processing,), location="m-1")


@pytest.fixture
def machine_state_idle_empty(create_buffer_state):
    return MachineState(
        id="m-1",
        buffer=create_buffer_state("b-2"),
        occupied_till=NoTime(),
        prebuffer=create_buffer_state("b-1"),
        postbuffer=create_buffer_state("b-3"),
        state=MachineStateState.IDLE,
        resources=(),
        outages=(),
        mounted_tool="tl-0",
    )


@pytest.fixture
def machine_state_idle(create_buffer_state):
    return MachineState(
        id="m-1",
        buffer=create_buffer_state("b-2"),
        occupied_till=NoTime(),
        prebuffer=create_buffer_state("b-1", BufferStateState.NOT_EMPTY, ("j-1",)),
        postbuffer=create_buffer_state("b-3"),
        state=MachineStateState.IDLE,
        resources=(),
        outages=(),
        mounted_tool="tl-0",
    )


@pytest.fixture
def machine_state_working(create_buffer_state):
    return MachineState(
        id="m-1",
        buffer=create_buffer_state("b-6", BufferStateState.FULL, ("j-2",)),
        occupied_till=NoTime(),
        prebuffer=create_buffer_state("b-4"),
        postbuffer=create_buffer_state("b-5", BufferStateState.NOT_EMPTY, ("j-1",)),
        state=MachineStateState.WORKING,
        resources=(),
        outages=(),
        mounted_tool="tl-0",
    )


@pytest.fixture
def machine_state_working_on_j1(create_buffer_state):
    return MachineState(
        id="m-1",
        buffer=create_buffer_state("b-6", BufferStateState.FULL, ("j-1",)),
        occupied_till=NoTime(),
        prebuffer=create_buffer_state("b-4"),
        postbuffer=create_buffer_state("b-5"),
        state=MachineStateState.WORKING,
        resources=(),
        outages=(),
        mounted_tool="tl-0",
    )


@pytest.fixture
def transport_state_idle(create_buffer_state):
    return TransportState(
        id="t-1",
        state=TransportStateState.IDLE,
        occupied_till=NoTime(),
        buffer=create_buffer_state("b-11"),
        location=TransportLocation(progress=0.0, location="m-1"),
        transport_job=None,
        outages=(),
    )


@pytest.fixture
def transport_state_working(create_buffer_state):
    return TransportState(
        id="t-1",
        state=TransportStateState.WORKING,
        occupied_till=NoTime(),
        buffer=create_buffer_state("b-11", BufferStateState.NOT_EMPTY, ("j-1",)),
        location=TransportLocation(progress=0.0, location=("m-1",)),
        transport_job=None,
        outages=(),
    )


@pytest.fixture
def machine_transition_idle_to_working():
    return ComponentTransition(
        component_id="m-1", new_state=MachineStateState.WORKING, job_id="j-1"
    )


@pytest.fixture
def machine_transition_working_to_idle():
    return ComponentTransition(component_id="m-1", new_state=MachineStateState.IDLE, job_id="j-1")


@pytest.fixture
def transport_state_pickup(create_buffer_state):
    return TransportState(
        id="t-1",
        state=TransportStateState.PICKUP,
        occupied_till=NoTime(),
        buffer=create_buffer_state("b-11"),
        location=TransportLocation(progress=0.0, location=("m-1")),
        transport_job="j-1",
        outages=(),
    )


@pytest.fixture
def transport_state_waitingpickup(create_buffer_state):
    return TransportState(
        id="t-1",
        state=TransportStateState.WAITINGPICKUP,
        occupied_till=NoTime(),
        buffer=create_buffer_state(),
        location=TransportLocation(progress=0.0, location=("m-1")),
        transport_job=None,
        outages=(),
    )


@pytest.fixture
def transport_state_transit(create_buffer_state):
    return TransportState(
        id="t-1",
        state=TransportStateState.TRANSIT,
        occupied_till=NoTime(),
        buffer=create_buffer_state("b-11", BufferStateState.NOT_EMPTY, ("j-1",)),
        location=TransportLocation(progress=0.5, location=("m-1", "m-2", "m-1")),
        transport_job=None,
        outages=(),
    )


@pytest.fixture
def transport_transition_pickup_to_transit():
    return ComponentTransition(
        component_id="t-1",
        new_state=TransportStateState.TRANSIT,
        job_id="j-1",
    )


@pytest.fixture
def transport_transition_pickup_to_waitingpickup():
    return ComponentTransition(
        component_id="t-1",
        new_state=TransportStateState.WAITINGPICKUP,
        job_id="j-1",
    )


@pytest.fixture
def transport_transition_waitingpickup_to_transit():
    return ComponentTransition(
        component_id="t-1",
        new_state=TransportStateState.TRANSIT,
        job_id="j-1",
    )


@pytest.fixture
def transport_transition_idle():
    return ComponentTransition(
        component_id="t-1",
        new_state=TransportStateState.IDLE,
        job_id="j-1",
    )


@pytest.fixture
def job_state_done_end_time_10():
    return JobState(
        id="j-1",
        operations=(
            OperationState(
                id="o-1",
                operation_state_state=OperationStateState.DONE,
                start_time=NoTime(),
                end_time=Time(10),
                machine_id="m-1",
            ),
        ),
        location="m-1",
    )


@pytest.fixture
def job_state_done_end_time_5():
    return JobState(
        id="j-2",
        operations=(
            OperationState(
                id="o-2",
                operation_state_state=OperationStateState.DONE,
                start_time=NoTime(),
                end_time=Time(5),
                machine_id="m-2",
            ),
        ),
        location="m-2",
    )


@pytest.fixture
def machine_transition_working():
    return ComponentTransition(component_id="m-1", new_state=MachineStateState.SETUP, job_id="j-1")


@pytest.fixture
def transport_transition_working():
    return ComponentTransition(
        component_id="t-1", new_state=TransportStateState.WORKING, job_id="j-1"
    )


# Fixtures for machines with occupied_till time
@pytest.fixture
def default_state_with_machine_occupied(machine_state_working):
    state = State(
        time=Time(10),
        machines=(replace(machine_state_working, occupied_till=Time(10)),),
        transports=(),
        jobs=(
            JobState(
                id="j-1",
                operations=(
                    OperationState(
                        id="op-1",
                        operation_state_state=OperationStateState.PROCESSING,
                        start_time=Time(0),
                        end_time=Time(10),
                        machine_id="m-1",
                    ),
                ),
                location="m-1",
            ),
        ),
        buffers=(),
    )
    return state


# Fixtures for transports in specific states
@pytest.fixture
def default_state_transport_transit(transport_state_transit):
    state = State(
        time=Time(10),
        machines=(),
        transports=(replace(transport_state_transit, occupied_till=Time(10)),),
        jobs=(
            JobState(
                id="j-1",
                operations=(),
                location="t-1",
            ),
        ),
        buffers=(),
    )
    return state


@pytest.fixture
def default_state_transport_pickup(transport_state_pickup):
    state = State(
        time=Time(10),
        machines=(),
        transports=(replace(transport_state_pickup, occupied_till=Time(10)),),
        jobs=(
            JobState(
                id="j-1",
                operations=(
                    OperationState(
                        id="o-1",
                        operation_state_state=OperationStateState.PROCESSING,
                        start_time=Time(0),
                        end_time=Time(10),
                        machine_id="m-1",
                    ),
                    OperationState(
                        id="o-2",
                        operation_state_state=OperationStateState.IDLE,
                        start_time=NoTime(),
                        end_time=NoTime(),
                        machine_id="m-2",
                    ),
                ),
                location="b-1",
            ),
        ),
        buffers=(),
    )
    return state


@pytest.fixture
def default_state_transport_pickup_ready(default_state_transport_pickup, machine_state_working):
    # Modify job to be ready for pickup
    job = replace(
        default_state_transport_pickup.jobs[0],
        operations=(
            OperationState(
                id="o-1",
                operation_state_state=OperationStateState.DONE,
                start_time=Time(0),
                end_time=Time(10),
                machine_id="m-1",
            ),
            OperationState(
                id="o-2",
                operation_state_state=OperationStateState.IDLE,
                start_time=NoTime(),
                end_time=NoTime(),
                machine_id="m-2",
            ),
        ),
    )
    state = replace(
        default_state_transport_pickup, jobs=(job,), machines=(machine_state_working,), buffers=()
    )
    return state


@pytest.fixture
def default_state_transport_teleporter(transport_state_idle):
    transport = replace(
        transport_state_idle,
        state=TransportStateState.IDLE,
        transport_job="j-1",
    )
    transport_config = TransportTypeConfig.TELEPORTER
    state = State(
        time=Time(10),
        machines=(),
        transports=(transport,),
        jobs=(JobState(id="j-1", operations=(), location="source_location"),),
        buffers=(),
    )
    return state


@pytest.fixture
def component_transition_transport_teleport():
    return ComponentTransition(
        component_id="t-1",
        new_state=TransportStateState.IDLE,
        job_id="j-1",
    )


@pytest.fixture
def default_state_transport_idle(transport_state_idle):
    state = State(
        time=Time(0),
        machines=(),
        transports=(transport_state_idle,),
        jobs=(
            JobState(
                id="j-1",
                operations=(
                    OperationState(
                        id="o-0-0",
                        operation_state_state=OperationStateState.IDLE,
                        start_time=NoTime(),
                        end_time=NoTime(),
                        machine_id="m-1",
                    ),
                ),
                location="b-3",
            ),
        ),
        buffers=(),
    )
    return state


@pytest.fixture
def component_transition_transport_idle_to_working():
    return ComponentTransition(
        component_id="t-1",
        new_state=TransportStateState.WORKING,
        job_id="j-1",
    )


@pytest.fixture
def default_state_with_transport_occupied(transport_state_transit):
    state = State(
        time=Time(10),
        machines=(),
        transports=(replace(transport_state_transit, occupied_till=Time(10)),),
        jobs=(
            JobState(
                id="j-1",
                operations=(),
                location="t-1",
            ),
        ),
        buffers=(),
    )
    return state


@pytest.fixture
def default_state_with_machine_and_transport_occupied(
    default_state_with_machine_occupied, default_state_with_transport_occupied
):
    state = replace(
        default_state_with_machine_occupied,
        transports=default_state_with_transport_occupied.transports,
    )
    return state


@pytest.fixture
def default_state_machine_idle_empty(machine_state_idle_empty):
    state = State(
        time=Time(0),
        machines=(machine_state_idle_empty,),
        transports=(),
        jobs=(
            JobState(
                id="j-1",
                operations=(
                    OperationState(
                        id="o-0-0",
                        operation_state_state=OperationStateState.IDLE,
                        start_time=NoTime(),
                        end_time=NoTime(),
                        machine_id="m-1",
                    ),
                ),
                location="b-1",
            ),
        ),
        buffers=(),
    )
    return state


@pytest.fixture
def default_state_machine_idle(machine_state_idle):
    state = State(
        time=Time(0),
        machines=(machine_state_idle,),
        transports=(),
        jobs=(
            JobState(
                id="j-1",
                operations=(
                    OperationState(
                        id="o-0-0",
                        operation_state_state=OperationStateState.IDLE,
                        start_time=NoTime(),
                        end_time=NoTime(),
                        machine_id="m-1",
                    ),
                ),
                location="b-1",
            ),
        ),
        buffers=(),
    )
    return state


@pytest.fixture
def default_state_machine_working(machine_state_working):
    state = State(
        time=Time(10),
        machines=(machine_state_working,),
        transports=(),
        jobs=(
            JobState(
                id="j-1",
                operations=(
                    OperationState(
                        id="o-1",
                        operation_state_state=OperationStateState.PROCESSING,
                        start_time=Time(0),
                        end_time=Time(10),
                        machine_id="m-1",
                    ),
                ),
                location="m-1",
            ),
        ),
        buffers=(),
    )
    return state


@pytest.fixture
def default_state_machine_setup(machine_state_working):
    state = State(
        time=Time(0),
        machines=(machine_state_working,),
        transports=(),
        jobs=(
            JobState(
                id="j-1",
                operations=(
                    OperationState(
                        id="o-1",
                        operation_state_state=OperationStateState.PROCESSING,
                        start_time=Time(0),
                        end_time=Time(0),
                        machine_id="m-1",
                    ),
                ),
                location="b-3",
            ),
        ),
        buffers=(),
    )
    return state


@pytest.fixture
def simple_job_config():
    from jobshoplab.types.instance_config_types import JobConfig, OperationConfig

    return JobConfig(
        id="j-1",
        operations=(
            OperationConfig(
                id="op-1",
                machine="m-1",
                duration=DeterministicTimeConfig(time=10),
                tool="tl-0",  # Changed from machine_id to machine
            ),
        ),
        product=Product(id="p-1", name="product-1"),
        priority=1,
    )


@pytest.fixture
def simple_machine_config():
    from jobshoplab.types.instance_config_types import BufferConfig, MachineConfig

    return MachineConfig(
        id="m-1",
        buffer=BufferConfig(id="b-22", resources=(), capacity=1, type=BufferTypeConfig.FIFO),
        prebuffer=BufferConfig(id="b-23", resources=(), capacity=1, type=BufferTypeConfig.FIFO),
        postbuffer=BufferConfig(id="b-24", resources=(), capacity=1, type=BufferTypeConfig.FIFO),
        outages=(),
        resources=(),
        setup_times=(),
        batches=1,
    )
