from dataclasses import replace

import pytest

from jobshoplab.types import NoTime, State, Time
from jobshoplab.types.action_types import ComponentTransition
from jobshoplab.types.instance_config_types import (
    BufferConfig,
    BufferTypeConfig,
    DeterministicTimeConfig,
    JobConfig,
    MachineConfig,
    OperationConfig,
    OutageConfig,
    OutageTypeConfig,
    Product,
    TransportConfig,
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
    OutageActive,
    OutageInactive,
    OutageState,
    Time,
    TransportLocation,
    TransportState,
    TransportStateState,
)
from jobshoplab.types.stochasticy_models import GaussianFunction


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
def machine_state_setup(create_buffer_state):
    return MachineState(
        id="m-1",
        buffer=create_buffer_state("b-2", BufferStateState.FULL, ("j-1",)),
        occupied_till=NoTime(),
        prebuffer=create_buffer_state("b-1"),
        postbuffer=create_buffer_state("b-3"),
        state=MachineStateState.SETUP,
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
def machine_state_outage(create_buffer_state):
    return MachineState(
        id="m-1",
        buffer=create_buffer_state("b-6", BufferStateState.FULL, ("j-1",)),
        occupied_till=NoTime(),
        prebuffer=create_buffer_state("b-4"),
        postbuffer=create_buffer_state("b-5"),
        state=MachineStateState.OUTAGE,
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


# @pytest.fixture
# def machine_transition_working_to_idle():
#     return ComponentTransition(component_id="m-1", new_state=MachineStateState.IDLE, job_id="j-1")


@pytest.fixture
def machine_transition_outage_to_idle():
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
    return ComponentTransition(
        component_id="m-1", new_state=MachineStateState.WORKING, job_id="j-1"
    )


@pytest.fixture
def machine_transition_outage():
    return ComponentTransition(component_id="m-1", new_state=MachineStateState.OUTAGE, job_id="j-1")


@pytest.fixture
def machine_transition_setup():
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
def default_state_transport_pickup(transport_state_pickup, default_machines, default_buffer):
    machine0, machine1, machine2 = default_machines
    machine_states = tuple()
    for machine in default_machines:
        machine_state = MachineState(
            id=machine.id,
            buffer=BufferState(id=machine.buffer.id, state=BufferStateState.EMPTY, store=()),
            occupied_till=NoTime(),
            prebuffer=BufferState(
                id=machine.prebuffer.id,
                state=BufferStateState.EMPTY,
                store=(),
            ),
            mounted_tool="tl-0",
            outages=(),
            postbuffer=BufferState(
                id=machine.postbuffer.id,
                state=BufferStateState.EMPTY,
                store=(),
            ),
            state=MachineStateState.IDLE,
            resources=(),
        )
        machine_states += (machine_state,)
    
    default_buffer_states = (
        BufferState(
            id=default_buffer[0].id,
            state=BufferStateState.EMPTY,
            store=(),
        ),
        BufferState(id=default_buffer[1].id, state=BufferStateState.EMPTY, store=()),
    )
    
    state = State(
        time=Time(10),
        machines=machine_states,
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
        buffers=default_buffer_states,
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
                        id="o-0-1",
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


#
@pytest.fixture
def default_state_machine_setup(machine_state_setup):
    state = State(
        time=Time(0),
        machines=(machine_state_setup,),
        transports=(),
        jobs=(
            JobState(
                id="j-1",
                operations=(
                    OperationState(
                        id="o-0-1",
                        operation_state_state=OperationStateState.PROCESSING,
                        start_time=Time(0),
                        end_time=Time(0),
                        machine_id="m-1",
                    ),
                ),
                location="b-2",
            ),
        ),
        buffers=(),
    )
    return state


@pytest.fixture
def default_state_machine_outage(machine_state_outage):
    state = State(
        time=Time(0),
        machines=(machine_state_outage,),
        transports=(),
        jobs=(
            JobState(
                id="j-1",
                operations=(
                    OperationState(
                        id="o-0-1",
                        operation_state_state=OperationStateState.PROCESSING,
                        start_time=Time(2),
                        end_time=Time(2),
                        machine_id="m-1",
                    ),
                ),
                location="b-6",
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
                id="o-0-1",
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


@pytest.fixture
def deterministic_setup_times():
    """
    Creates a dictionary of deterministic setup times between different tools.
    The setup time when changing from tool_i to tool_j is i*j
    """
    tool0, tool1, tool2 = "tl-0", "tl-1", "tl-2"
    return {
        (tool0, tool0): DeterministicTimeConfig(0),  # No setup time when using same tool
        (tool0, tool1): DeterministicTimeConfig(1),  # Setup time from tool0 to tool1 is 1
        (tool0, tool2): DeterministicTimeConfig(2),  # Setup time from tool0 to tool2 is 2
        (tool1, tool0): DeterministicTimeConfig(1),  # Setup time from tool1 to tool0 is 1
        (tool1, tool1): DeterministicTimeConfig(0),  # No setup time when using same tool
        (tool1, tool2): DeterministicTimeConfig(3),  # Setup time from tool1 to tool2 is 3
        (tool2, tool0): DeterministicTimeConfig(2),  # Setup time from tool2 to tool0 is 2
        (tool2, tool1): DeterministicTimeConfig(3),  # Setup time from tool2 to tool1 is 3
        (tool2, tool2): DeterministicTimeConfig(0),  # No setup time when using same tool
    }


@pytest.fixture
def stochastic_setup_times():
    """
    Creates a dictionary of stochastic setup times between different tools.
    """
    tool0, tool1, tool2 = "tl-0", "tl-1", "tl-2"
    return {
        (tool0, tool0): GaussianFunction(base_time=0, std=0.1),
        (tool0, tool1): GaussianFunction(base_time=1, std=1),
        (tool0, tool2): GaussianFunction(base_time=2, std=1),
        (tool1, tool0): GaussianFunction(base_time=1, std=1),
        (tool1, tool1): GaussianFunction(base_time=0, std=0.1),
        (tool1, tool2): GaussianFunction(base_time=3, std=2),
        (tool2, tool0): GaussianFunction(base_time=2, std=1),
        (tool2, tool1): GaussianFunction(base_time=3, std=2),
        (tool2, tool2): GaussianFunction(base_time=0, std=0.1),
    }


@pytest.fixture
def machine_with_deterministic_setup_times(deterministic_setup_times):
    """
    Creates a machine configuration with deterministic setup times.
    """
    _inf = 999999
    return MachineConfig(
        id="m-setup",
        outages=(),
        setup_times=deterministic_setup_times,
        prebuffer=BufferConfig(
            id="b-setup-1",
            type=BufferTypeConfig.FLEX_BUFFER,
            capacity=_inf,
            resources=(),
            parent="m-setup",
        ),
        postbuffer=BufferConfig(
            id="b-setup-2",
            type=BufferTypeConfig.FLEX_BUFFER,
            capacity=_inf,
            resources=(),
            parent="m-setup",
        ),
        batches=1,
        resources=(),
        buffer=BufferConfig(
            id="b-setup-3",
            type=BufferTypeConfig.FLEX_BUFFER,
            capacity=1,
            resources=(),
            parent="m-setup",
        ),
    )


@pytest.fixture
def machine_with_stochastic_setup_times(stochastic_setup_times):
    """
    Creates a machine configuration with stochastic setup times.
    """
    _inf = 999999
    return MachineConfig(
        id="m-stoch-setup",
        outages=(),
        setup_times=stochastic_setup_times,
        prebuffer=BufferConfig(
            id="b-stoch-1",
            type=BufferTypeConfig.FLEX_BUFFER,
            capacity=_inf,
            resources=(),
            parent="m-stoch-setup",
        ),
        postbuffer=BufferConfig(
            id="b-stoch-2",
            type=BufferTypeConfig.FLEX_BUFFER,
            capacity=_inf,
            resources=(),
            parent="m-stoch-setup",
        ),
        batches=1,
        resources=(),
        buffer=BufferConfig(
            id="b-stoch-3",
            type=BufferTypeConfig.FLEX_BUFFER,
            capacity=1,
            resources=(),
            parent="m-stoch-setup",
        ),
    )


@pytest.fixture
def machine_state_with_tool0(create_buffer_state):
    """
    Creates a machine state with tool0 mounted.
    """
    return MachineState(
        id="m-setup",
        buffer=create_buffer_state("b-setup-3"),
        occupied_till=NoTime(),
        prebuffer=create_buffer_state("b-setup-1", BufferStateState.NOT_EMPTY, ("j-setup",)),
        postbuffer=create_buffer_state("b-setup-2"),
        state=MachineStateState.IDLE,
        resources=(),
        outages=(),
        mounted_tool="tl-0",  # Tool0 is mounted
    )


@pytest.fixture
def machine_state_with_tool1(create_buffer_state):
    """
    Creates a machine state with tool1 mounted.
    """
    return MachineState(
        id="m-setup",
        buffer=create_buffer_state("b-setup-3"),
        occupied_till=NoTime(),
        prebuffer=create_buffer_state("b-setup-1", BufferStateState.NOT_EMPTY, ("j-setup",)),
        postbuffer=create_buffer_state("b-setup-2"),
        state=MachineStateState.IDLE,
        resources=(),
        outages=(),
        mounted_tool="tl-1",  # Tool1 is mounted
    )


@pytest.fixture
def operation_with_tool0():
    """
    Creates an operation that requires tool0.
    """
    return OperationState(
        id="o-setup-0",
        operation_state_state=OperationStateState.IDLE,
        start_time=NoTime(),
        end_time=NoTime(),
        machine_id="m-setup",
    )


@pytest.fixture
def operation_with_tool1():
    """
    Creates an operation that requires tool1.
    """
    return OperationState(
        id="o-setup-1",
        operation_state_state=OperationStateState.IDLE,
        start_time=NoTime(),
        end_time=NoTime(),
        machine_id="m-setup",
    )


@pytest.fixture
def operation_with_tool2():
    """
    Creates an operation that requires tool2.
    """
    return OperationState(
        id="o-setup-2",
        operation_state_state=OperationStateState.IDLE,
        start_time=NoTime(),
        end_time=NoTime(),
        machine_id="m-setup",
    )


@pytest.fixture
def job_with_tool0_operation(operation_with_tool0):
    """
    Creates a job that requires tool0 for its next operation.
    """
    return JobState(id="j-setup", operations=(operation_with_tool0,), location="b-setup-1")


@pytest.fixture
def job_with_tool1_operation(operation_with_tool1):
    """
    Creates a job that requires tool1 for its next operation.
    """
    return JobState(id="j-setup", operations=(operation_with_tool1,), location="b-setup-1")


@pytest.fixture
def job_with_tool2_operation(operation_with_tool2):
    """
    Creates a job that requires tool2 for its next operation.
    """
    return JobState(id="j-setup", operations=(operation_with_tool2,), location="b-setup-1")


@pytest.fixture
def simple_op_config_with_tool0():
    """
    Creates a simple operation config that requires tool0.
    """
    return OperationConfig(
        id="o-setup-0",
        machine="m-setup",
        duration=DeterministicTimeConfig(time=10),
        tool="tl-0",
    )


@pytest.fixture
def simple_op_config_with_tool1():
    """
    Creates a simple operation config that requires tool1.
    """
    return OperationConfig(
        id="o-setup-1",
        machine="m-setup",
        duration=DeterministicTimeConfig(time=10),
        tool="tl-1",
    )


@pytest.fixture
def simple_op_config_with_tool2():
    """
    Creates a simple operation config that requires tool2.
    """
    return OperationConfig(
        id="o-setup-2",
        machine="m-setup",
        duration=DeterministicTimeConfig(time=10),
        tool="tl-2",
    )


@pytest.fixture
def job_config_with_tool_operations(
    simple_op_config_with_tool0, simple_op_config_with_tool1, simple_op_config_with_tool2
):
    """
    Creates a job config with operations requiring different tools.
    """
    return JobConfig(
        id="j-setup",
        operations=(
            simple_op_config_with_tool0,
            simple_op_config_with_tool1,
            simple_op_config_with_tool2,
        ),
        product=Product(id="p-setup", name="product-setup"),
        priority=1,
    )


# Outage related fixtures


@pytest.fixture
def deterministic_outage_config_fail():
    """
    Creates a deterministic outage configuration for a machine failure (FAIL type).
    """
    return OutageConfig(
        id="o-fail-1",
        frequency=DeterministicTimeConfig(time=100),  # Occurs every 100 time units
        duration=DeterministicTimeConfig(time=20),  # Lasts for 20 time units
        type=OutageTypeConfig.FAIL,
    )


@pytest.fixture
def deterministic_outage_config_maintenance():
    """
    Creates a deterministic outage configuration for scheduled maintenance (MAINTENANCE type).
    """
    return OutageConfig(
        id="o-maint-1",
        frequency=DeterministicTimeConfig(time=200),  # Occurs every 200 time units
        duration=DeterministicTimeConfig(time=30),  # Lasts for 30 time units
        type=OutageTypeConfig.MAINTENANCE,
    )


@pytest.fixture
def deterministic_outage_config_recharge():
    """
    Creates a deterministic outage configuration for recharging (RECHARGE type).
    """
    return OutageConfig(
        id="o-recharge-1",
        frequency=DeterministicTimeConfig(time=150),  # Occurs every 150 time units
        duration=DeterministicTimeConfig(time=15),  # Lasts for 15 time units
        type=OutageTypeConfig.RECHARGE,
    )


@pytest.fixture
def stochastic_outage_config_fail():
    """
    Creates a stochastic outage configuration for a machine failure (FAIL type).
    """
    return OutageConfig(
        id="o-fail-stoch-1",
        frequency=GaussianFunction(base_time=100, std=10),  # Around every 100 time units
        duration=GaussianFunction(base_time=20, std=5),  # Around 20 time units
        type=OutageTypeConfig.FAIL,
    )


@pytest.fixture
def stochastic_outage_config_maintenance():
    """
    Creates a stochastic outage configuration for scheduled maintenance (MAINTENANCE type).
    """
    return OutageConfig(
        id="o-maint-stoch-1",
        frequency=GaussianFunction(base_time=200, std=20),  # Around every 200 time units
        duration=GaussianFunction(base_time=30, std=5),  # Around 30 time units
        type=OutageTypeConfig.MAINTENANCE,
    )


@pytest.fixture
def stochastic_outage_config_recharge():
    """
    Creates a stochastic outage configuration for recharging (RECHARGE type).
    """
    return OutageConfig(
        id="o-recharge-stoch-1",
        frequency=GaussianFunction(base_time=150, std=15),  # Around every 150 time units
        duration=GaussianFunction(base_time=15, std=3),  # Around 15 time units
        type=OutageTypeConfig.RECHARGE,
    )


@pytest.fixture
def outage_state_active():
    """
    Creates an active outage state.
    """
    return OutageState(id="o-fail-1", active=OutageActive(start_time=Time(10), end_time=Time(30)))


@pytest.fixture
def outage_state_inactive():
    """
    Creates an inactive outage state.
    """
    return OutageState(id="o-fail-1", active=OutageInactive(last_time_active=Time(5)))


@pytest.fixture
def machine_config_with_deterministic_outages(
    deterministic_outage_config_fail, deterministic_outage_config_maintenance
):
    """
    Creates a machine configuration with deterministic outages.
    """
    _inf = 999999
    return MachineConfig(
        id="m-outage",
        outages=(deterministic_outage_config_fail, deterministic_outage_config_maintenance),
        setup_times={},
        prebuffer=BufferConfig(
            id="b-outage-1",
            type=BufferTypeConfig.FLEX_BUFFER,
            capacity=_inf,
            resources=(),
            parent="m-outage",
        ),
        postbuffer=BufferConfig(
            id="b-outage-2",
            type=BufferTypeConfig.FLEX_BUFFER,
            capacity=_inf,
            resources=(),
            parent="m-outage",
        ),
        batches=1,
        resources=(),
        buffer=BufferConfig(
            id="b-outage-3",
            type=BufferTypeConfig.FLEX_BUFFER,
            capacity=1,
            resources=(),
            parent="m-outage",
        ),
    )


@pytest.fixture
def machine_state_with_deterministic_outages(
    create_buffer_state, deterministic_outage_config_fail, deterministic_outage_config_maintenance
):
    """
    Creates a machine state with deterministic outages.
    """
    return MachineState(
        id="m-outage",
        buffer=create_buffer_state("b-outage-3"),
        occupied_till=NoTime(),
        prebuffer=create_buffer_state("b-outage-1", BufferStateState.NOT_EMPTY, ("j-outage",)),
        postbuffer=create_buffer_state("b-outage-2"),
        state=MachineStateState.IDLE,
        resources=(),
        outages=(
            OutageState(
                id=deterministic_outage_config_fail.id,
                active=OutageInactive(last_time_active=NoTime()),
            ),
            OutageState(
                id=deterministic_outage_config_maintenance.id,
                active=OutageInactive(last_time_active=NoTime()),
            ),
        ),
        mounted_tool="tl-0",
    )


@pytest.fixture
def machine_with_stochastic_outages(
    stochastic_outage_config_fail, stochastic_outage_config_maintenance
):
    """
    Creates a machine configuration with stochastic outages.
    """
    _inf = 999999
    return MachineConfig(
        id="m-stoch-outage",
        outages=(stochastic_outage_config_fail, stochastic_outage_config_maintenance),
        setup_times={},
        prebuffer=BufferConfig(
            id="b-stoch-outage-1",
            type=BufferTypeConfig.FLEX_BUFFER,
            capacity=_inf,
            resources=(),
            parent="m-stoch-outage",
        ),
        postbuffer=BufferConfig(
            id="b-stoch-outage-2",
            type=BufferTypeConfig.FLEX_BUFFER,
            capacity=_inf,
            resources=(),
            parent="m-stoch-outage",
        ),
        batches=1,
        resources=(),
        buffer=BufferConfig(
            id="b-stoch-outage-3",
            type=BufferTypeConfig.FLEX_BUFFER,
            capacity=1,
            resources=(),
            parent="m-stoch-outage",
        ),
    )


@pytest.fixture
def transport_with_deterministic_outages(
    deterministic_outage_config_fail, deterministic_outage_config_recharge
):
    """
    Creates a transport configuration with deterministic outages.
    """
    return TransportConfig(
        id="t-outage",
        type=TransportTypeConfig.AGV,
        outages=(deterministic_outage_config_fail, deterministic_outage_config_recharge),
        resources=(),
        buffer=BufferConfig(
            id="b-t-outage", type=BufferTypeConfig.FLEX_BUFFER, capacity=1, resources=()
        ),
    )


@pytest.fixture
def transport_with_stochastic_outages(
    stochastic_outage_config_fail, stochastic_outage_config_recharge
):
    """
    Creates a transport configuration with stochastic outages.
    """
    return TransportConfig(
        id="t-stoch-outage",
        type=TransportTypeConfig.AGV,
        outages=(stochastic_outage_config_fail, stochastic_outage_config_recharge),
        resources=(),
        buffer=BufferConfig(
            id="b-t-stoch-outage", type=BufferTypeConfig.FLEX_BUFFER, capacity=1, resources=()
        ),
    )


@pytest.fixture
def machine_state_with_active_outage(create_buffer_state, outage_state_active):
    """
    Creates a machine state with an active outage.
    """
    return MachineState(
        id="m-outage",
        buffer=create_buffer_state("b-outage-3", BufferStateState.FULL, ("j-outage",)),
        occupied_till=Time(30),  # Occupied until outage ends
        prebuffer=create_buffer_state("b-outage-1"),
        postbuffer=create_buffer_state("b-outage-2"),
        state=MachineStateState.OUTAGE,
        resources=(),
        outages=(outage_state_active,),
        mounted_tool="tl-0",
    )


@pytest.fixture
def machine_state_with_inactive_outage(create_buffer_state, outage_state_inactive):
    """
    Creates a machine state with an inactive outage.
    """
    return MachineState(
        id="m-outage",
        buffer=create_buffer_state("b-outage-3"),
        occupied_till=NoTime(),
        prebuffer=create_buffer_state("b-outage-1", BufferStateState.NOT_EMPTY, ("j-outage",)),
        postbuffer=create_buffer_state("b-outage-2"),
        state=MachineStateState.IDLE,
        resources=(),
        outages=(outage_state_inactive,),
        mounted_tool="tl-0",
    )


@pytest.fixture
def transport_state_with_active_outage(create_buffer_state, outage_state_active):
    """
    Creates a transport state with an active outage.
    """
    return TransportState(
        id="t-outage",
        state=TransportStateState.OUTAGE,
        occupied_till=Time(30),  # Occupied until outage ends
        buffer=create_buffer_state("b-t-outage"),
        location=TransportLocation(progress=0.0, location="m-1"),
        transport_job=None,
        outages=(outage_state_active,),
    )


@pytest.fixture
def transport_state_with_inactive_outage(create_buffer_state, outage_state_inactive):
    """
    Creates a transport state with an inactive outage.
    """
    return TransportState(
        id="t-outage",
        state=TransportStateState.IDLE,
        occupied_till=NoTime(),
        buffer=create_buffer_state("b-t-outage"),
        location=TransportLocation(progress=0.0, location="m-1"),
        transport_job=None,
        outages=(outage_state_inactive,),
    )


@pytest.fixture
def default_state_machine_with_active_outage(machine_state_with_active_outage):
    """
    Creates a state with a machine that has an active outage.
    """
    return State(
        time=Time(15),  # During outage
        machines=(machine_state_with_active_outage,),
        transports=(),
        jobs=(
            JobState(
                id="j-outage",
                operations=(
                    OperationState(
                        id="o-outage-1",
                        operation_state_state=OperationStateState.PROCESSING,
                        start_time=Time(5),
                        end_time=Time(40),  # Would end after outage
                        machine_id="m-outage",
                    ),
                ),
                location="b-outage-3",
            ),
        ),
        buffers=(),
    )


@pytest.fixture
def default_state_transport_with_active_outage(transport_state_with_active_outage):
    """
    Creates a state with a transport that has an active outage.
    """
    return State(
        time=Time(15),  # During outage
        machines=(),
        transports=(transport_state_with_active_outage,),
        jobs=(
            JobState(
                id="j-transport-outage",
                operations=(),
                location="t-outage",
            ),
        ),
        buffers=(),
    )
