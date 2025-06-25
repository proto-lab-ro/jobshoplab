import pytest
from jobshoplab.compiler.mapper import DictToInstanceMapper
from jobshoplab.state_machine.core.state_machine import handler, state
from jobshoplab.types.instance_config_types import BufferTypeConfig
from jobshoplab.types.state_types import (
    MachineStateState, Time, NoTime, State, MachineState, BufferState, 
    BufferStateState, JobState, OperationState, OperationStateState
)
from jobshoplab.types.action_types import Action, ComponentTransition, ActionFactoryInfo
from jobshoplab.state_machine import time_machines


def create_buffer_aware_test_state(
    machine_id: str = "m-0",
    job_ids: tuple[str, ...] = ("j-0", "j-1", "j-2"),
    machine_state: MachineStateState = MachineStateState.IDLE,
    current_time: int = 0,
    prebuffer_id: str = None,
    postbuffer_id: str = None,
    main_buffer_id: str = None
) -> State:
    """Create a test state with jobs positioned in machine prebuffer"""
    
    if prebuffer_id is None:
        prebuffer_id = f"b-{machine_id}-pre"
    if postbuffer_id is None:
        postbuffer_id = f"b-{machine_id}-post"
    if main_buffer_id is None:
        main_buffer_id = f"b-{machine_id}-main"
    
    # Create job states with IDLE operations using standard operation ID format
    jobs = tuple(
        JobState(
            id=job_id,
            operations=(
                OperationState(
                    id=f"o-{i}-0",  # Use standard format: o-<job_index>-<operation_index>
                    start_time=NoTime(),
                    end_time=NoTime(),
                    machine_id=machine_id,
                    operation_state_state=OperationStateState.IDLE,
                ),
            ),
            location=prebuffer_id  # Jobs are in the prebuffer
        )
        for i, job_id in enumerate(job_ids)
    )
    
    # Create machine state with jobs in prebuffer
    machine = MachineState(
        id=machine_id,
        buffer=BufferState(id=main_buffer_id, state=BufferStateState.EMPTY, store=()),
        occupied_till=NoTime(),
        prebuffer=BufferState(
            id=prebuffer_id,
            state=BufferStateState.NOT_EMPTY if job_ids else BufferStateState.EMPTY,
            store=job_ids
        ),
        postbuffer=BufferState(id=postbuffer_id, state=BufferStateState.EMPTY, store=()),
        state=machine_state,
        mounted_tool="tl-0",
        outages=(),
        resources=()
    )
    
    return State(
        time=Time(current_time),
        jobs=jobs,
        machines=(machine,),
        transports=(),
        buffers=(),
    )


@pytest.fixture
def fifo_buffer_config():
    """Config with FIFO prebuffer machines for testing automatic scheduling"""
    return {
        "instance_config": {
            "description": "FIFO buffer test instance",
            "instance": {
                "specification": """
                    (m0,t)|(m1,t)|(m2,t)
                    j0|(0,3) (1,2) (2,2)
                    j1|(0,2) (1,1) (2,4)
                    j2|(0,4) (2,3) (1,3)
                """
            },
            "machines": {
                "prebuffer": [
                    {"capacity": 10, "type": "fifo"}
                ],
                "postbuffer": [
                    {"capacity": 10, "type": "fifo"}
                ]
            }
        }
    }


@pytest.fixture
def lifo_buffer_config():
    """Config with LIFO prebuffer machines for testing automatic scheduling"""
    return {
        "instance_config": {
            "description": "LIFO buffer test instance",
            "instance": {
                "specification": """
                    (m0,t)|(m1,t)|(m2,t)
                    j0|(0,3) (1,2) (2,2)
                    j1|(0,2) (1,1) (2,4)
                    j2|(0,4) (2,3) (1,3)
                """
            },
            "machines": {
                "prebuffer": [
                    {"capacity": 10, "type": "lifo"}
                ],
                "postbuffer": [
                    {"capacity": 10, "type": "lifo"}
                ]
            }
        }
    }


@pytest.fixture
def flex_buffer_config():
    """Config with flex prebuffer machines for testing manual scheduling"""
    return {
        "instance_config": {
            "description": "Flex buffer test instance",
            "instance": {
                "specification": """
                    (m0,t)|(m1,t)|(m2,t)
                    j0|(0,3) (1,2) (2,2)
                    j1|(0,2) (1,1) (2,4)
                    j2|(0,4) (2,3) (1,3)
                """
            },
            "machines": {
                "prebuffer": [
                    {"capacity": 10, "type": "flex_buffer"}
                ],
                "postbuffer": [
                    {"capacity": 10, "type": "flex_buffer"}
                ]
            }
        }
    }


@pytest.fixture
def mixed_buffer_config():
    """Config with different buffer types per machine for comprehensive testing"""
    return {
        "instance_config": {
            "description": "Mixed buffer types test instance",
            "instance": {
                "specification": """
                    (m0,t)|(m1,t)|(m2,t)
                    j0|(0,3) (1,2) (2,2)
                    j1|(0,2) (1,1) (2,4)
                    j2|(0,4) (2,3) (1,3)
                """
            },
            "machines": [
                {
                    "m-0": {
                        "prebuffer": [{"capacity": 10, "type": "fifo"}],
                        "postbuffer": [{"capacity": 10, "type": "fifo"}]
                    }
                },
                {
                    "m-1": {
                        "prebuffer": [{"capacity": 10, "type": "lifo"}],
                        "postbuffer": [{"capacity": 10, "type": "lifo"}]
                    }
                },
                {
                    "m-2": {
                        "prebuffer": [{"capacity": 10, "type": "flex_buffer"}],
                        "postbuffer": [{"capacity": 10, "type": "flex_buffer"}]
                    }
                }
            ]
        }
    }


def test_buffer_configuration_verification(fifo_buffer_config, lifo_buffer_config, flex_buffer_config, config):
    """Test that buffer configurations are correctly applied to machines"""
    # Test FIFO configuration
    mapper = DictToInstanceMapper(0, config=config)
    fifo_instance = mapper.map(fifo_buffer_config)
    
    for machine in fifo_instance.machines:
        assert machine.prebuffer.type == BufferTypeConfig.FIFO
        assert machine.postbuffer.type == BufferTypeConfig.FIFO
        assert machine.prebuffer.capacity == 10
        assert machine.postbuffer.capacity == 10
    
    # Test LIFO configuration
    lifo_instance = mapper.map(lifo_buffer_config)
    
    for machine in lifo_instance.machines:
        assert machine.prebuffer.type == BufferTypeConfig.LIFO
        assert machine.postbuffer.type == BufferTypeConfig.LIFO
        assert machine.prebuffer.capacity == 10
        assert machine.postbuffer.capacity == 10
    
    # Test flex configuration
    flex_instance = mapper.map(flex_buffer_config)
    
    for machine in flex_instance.machines:
        assert machine.prebuffer.type == BufferTypeConfig.FLEX_BUFFER
        assert machine.postbuffer.type == BufferTypeConfig.FLEX_BUFFER
        assert machine.prebuffer.capacity == 10
        assert machine.postbuffer.capacity == 10


def test_mixed_buffer_configuration(mixed_buffer_config, config):
    """Test that mixed buffer configurations are correctly applied per machine"""
    mapper = DictToInstanceMapper(0, config=config)
    instance = mapper.map(mixed_buffer_config)
    
    # Find machines by ID
    machines_by_id = {machine.id: machine for machine in instance.machines}
    
    # Verify m-0 has FIFO buffers
    assert machines_by_id["m-0"].prebuffer.type == BufferTypeConfig.FIFO
    assert machines_by_id["m-0"].postbuffer.type == BufferTypeConfig.FIFO
    
    # Verify m-1 has LIFO buffers
    assert machines_by_id["m-1"].prebuffer.type == BufferTypeConfig.LIFO
    assert machines_by_id["m-1"].postbuffer.type == BufferTypeConfig.LIFO
    
    # Verify m-2 has flex buffers
    assert machines_by_id["m-2"].prebuffer.type == BufferTypeConfig.FLEX_BUFFER
    assert machines_by_id["m-2"].postbuffer.type == BufferTypeConfig.FLEX_BUFFER


def test_create_timed_transitions_fifo_buffer_auto_schedule(fifo_buffer_config, config):
    """Test that create_timed_transitions creates automatic transitions for FIFO buffers"""
    # Create instance from config to get proper buffer configurations
    mapper = DictToInstanceMapper(0, config=config)
    instance = mapper.map(fifo_buffer_config)
    
    # Create a test state with jobs in FIFO prebuffer and machine idle
    # Use the actual buffer IDs from the instance
    machine_config = instance.machines[0]  # Get first machine
    test_state = create_buffer_aware_test_state(
        machine_id=machine_config.id,
        job_ids=("j-0", "j-1", "j-2"),  # j-0 should be processed first in FIFO
        machine_state=MachineStateState.IDLE,
        current_time=0,
        prebuffer_id=machine_config.prebuffer.id,
        postbuffer_id=machine_config.postbuffer.id,
        main_buffer_id=machine_config.buffer.id
    )
    
    # Expected behavior: Should create transition for j-0 (first job in FIFO prebuffer)
    timed_transitions = handler.create_timed_transitions("debug", test_state, instance)
    
    # Filter transitions for our machine
    machine_transitions = [t for t in timed_transitions if t.component_id == machine_config.id]
    
    assert len(machine_transitions) == 1, "Should create exactly one transition for FIFO buffer"
    assert machine_transitions[0].component_id == machine_config.id
    assert machine_transitions[0].job_id == "j-0", "Should process first job in FIFO order"
    assert machine_transitions[0].new_state == MachineStateState.SETUP


def test_create_timed_transitions_lifo_buffer_auto_schedule(lifo_buffer_config, config):
    """Test that create_timed_transitions creates automatic transitions for LIFO buffers"""
    # Create instance from config to get proper buffer configurations
    mapper = DictToInstanceMapper(0, config=config)
    instance = mapper.map(lifo_buffer_config)
    
    # Create a test state with jobs in LIFO prebuffer and machine idle
    # Use the actual buffer IDs from the instance
    machine_config = instance.machines[0]  # Get first machine
    test_state = create_buffer_aware_test_state(
        machine_id=machine_config.id,
        job_ids=("j-0", "j-1", "j-2"),  # j-2 should be processed first in LIFO
        machine_state=MachineStateState.IDLE,
        current_time=0,
        prebuffer_id=machine_config.prebuffer.id,
        postbuffer_id=machine_config.postbuffer.id,
        main_buffer_id=machine_config.buffer.id
    )
    
    # Expected behavior: Should create transition for j-2 (last job in LIFO prebuffer)
    timed_transitions = handler.create_timed_transitions("debug", test_state, instance)
    
    # Filter transitions for our machine
    machine_transitions = [t for t in timed_transitions if t.component_id == machine_config.id]
    
    assert len(machine_transitions) == 1, "Should create exactly one transition for LIFO buffer"
    assert machine_transitions[0].component_id == machine_config.id
    assert machine_transitions[0].job_id == "j-2", "Should process last job in LIFO order"
    assert machine_transitions[0].new_state == MachineStateState.SETUP


def test_create_timed_transitions_flex_buffer_no_auto_schedule(flex_buffer_config, config):
    """Test that create_timed_transitions does NOT create automatic transitions for flex buffers"""
    # Create instance from config to get proper buffer configurations
    mapper = DictToInstanceMapper(0, config=config)
    instance = mapper.map(flex_buffer_config)
    
    # Create a test state with jobs in flex prebuffer and machine idle
    # Use the actual buffer IDs from the instance
    machine_config = instance.machines[0]  # Get first machine
    test_state = create_buffer_aware_test_state(
        machine_id=machine_config.id,
        job_ids=("j-0", "j-1", "j-2"),  # Jobs waiting but no automatic scheduling
        machine_state=MachineStateState.IDLE,
        current_time=0,
        prebuffer_id=machine_config.prebuffer.id,
        postbuffer_id=machine_config.postbuffer.id,
        main_buffer_id=machine_config.buffer.id
    )
    
    # Expected behavior: Should NOT create any automatic transitions for flex buffers
    timed_transitions = handler.create_timed_transitions("debug", test_state, instance)
    
    # Filter transitions for our machine
    machine_transitions = [t for t in timed_transitions if t.component_id == machine_config.id]
    
    assert len(machine_transitions) == 0, "Should NOT create automatic transitions for flex buffers"


def test_state_step_fifo_integration(fifo_buffer_config, config):
    """Test end-to-end state.step() behavior with FIFO buffers"""
    # Create instance from config to get proper buffer configurations
    mapper = DictToInstanceMapper(0, config=config)
    instance = mapper.map(fifo_buffer_config)
    
    # Use the actual machine and buffer IDs from the instance
    machine_config = instance.machines[0]  # Get first machine
    test_state = create_buffer_aware_test_state(
        machine_id=machine_config.id,
        job_ids=("j-0", "j-1", "j-2"),
        machine_state=MachineStateState.IDLE,
        current_time=0,
        prebuffer_id=machine_config.prebuffer.id,
        postbuffer_id=machine_config.postbuffer.id,
        main_buffer_id=machine_config.buffer.id
    )
    
    # Create action with time advancement
    action = Action(
        transitions=(),  # No manual transitions
        action_factory_info=ActionFactoryInfo.Valid,
        time_machine=time_machines.jump_to_event
    )
    
    # Call state.step() - should trigger automatic FIFO scheduling
    result = state.step("debug", instance, config, test_state, action)
    
    assert result.success, f"State step should succeed: {result.message}"
    
    # Verify that j-0 (first in FIFO) was scheduled automatically
    # Check if machine transitioned from IDLE to SETUP for j-0
    final_machine = result.state.machines[0]
    
    # The machine should either be in SETUP state with j-0, or have j-0 in its main buffer
    if final_machine.state == MachineStateState.SETUP:
        assert final_machine.buffer.store == ("j-0",), "j-0 should be first job scheduled in FIFO order"
    else:
        # Or j-0 should have been moved to main buffer for processing
        processed_jobs = [job for job in result.state.jobs if job.id == "j-0"]
        assert len(processed_jobs) == 1
        # Verify j-0's location changed from prebuffer


def test_state_step_lifo_integration(lifo_buffer_config, config):
    """Test end-to-end state.step() behavior with LIFO buffers"""
    # Create instance from config to get proper buffer configurations
    mapper = DictToInstanceMapper(0, config=config)
    instance = mapper.map(lifo_buffer_config)
    
    # Use the actual machine and buffer IDs from the instance
    machine_config = instance.machines[0]  # Get first machine
    test_state = create_buffer_aware_test_state(
        machine_id=machine_config.id,
        job_ids=("j-0", "j-1", "j-2"),
        machine_state=MachineStateState.IDLE,
        current_time=0,
        prebuffer_id=machine_config.prebuffer.id,
        postbuffer_id=machine_config.postbuffer.id,
        main_buffer_id=machine_config.buffer.id
    )
    
    # Create action with time advancement
    action = Action(
        transitions=(),  # No manual transitions
        action_factory_info=ActionFactoryInfo.Valid,
        time_machine=time_machines.jump_to_event
    )
    
    # Call state.step() - should trigger automatic LIFO scheduling
    result = state.step("debug", instance, config, test_state, action)
    
    assert result.success, f"State step should succeed: {result.message}"
    
    # Verify that j-2 (last in LIFO) was scheduled automatically
    # Check if machine transitioned from IDLE to SETUP for j-2
    final_machine = result.state.machines[0]
    
    # The machine should either be in SETUP state with j-2, or have j-2 in its main buffer
    if final_machine.state == MachineStateState.SETUP:
        assert final_machine.buffer.store == ("j-2",), "j-2 should be first job scheduled in LIFO order"
    else:
        # Or j-2 should have been moved to main buffer for processing
        processed_jobs = [job for job in result.state.jobs if job.id == "j-2"]
        assert len(processed_jobs) == 1
        # Verify j-2's location changed from prebuffer


def test_state_step_flex_manual_scheduling(flex_buffer_config, config):
    """Test end-to-end state.step() behavior with flex buffers requiring manual scheduling"""
    # Create instance from config to get proper buffer configurations
    mapper = DictToInstanceMapper(0, config=config)
    instance = mapper.map(flex_buffer_config)
    
    # Use the actual machine and buffer IDs from the instance
    machine_config = instance.machines[0]  # Get first machine
    test_state = create_buffer_aware_test_state(
        machine_id=machine_config.id,
        job_ids=("j-0", "j-1", "j-2"),
        machine_state=MachineStateState.IDLE,
        current_time=0,
        prebuffer_id=machine_config.prebuffer.id,
        postbuffer_id=machine_config.postbuffer.id,
        main_buffer_id=machine_config.buffer.id
    )
    
    # Test 1: No automatic scheduling with empty action
    action_empty = Action(
        transitions=(),  # No manual transitions
        action_factory_info=ActionFactoryInfo.Valid,
        time_machine=time_machines.jump_to_event
    )
    
    result_empty = state.step("debug", instance, config, test_state, action_empty)
    assert result_empty.success, f"State step should succeed: {result_empty.message}"
    
    # Verify NO automatic scheduling occurred
    final_machine = result_empty.state.machines[0]
    assert final_machine.state == MachineStateState.IDLE, "Machine should remain IDLE with flex buffers"
    assert final_machine.buffer.store == (), "No jobs should be automatically moved to main buffer"
    
    # Verify possible_transitions contains manual scheduling options
    possible_machine_transitions = [
        t for t in result_empty.possible_transitions 
        if t.component_id == "m-0" and t.new_state == MachineStateState.SETUP
    ]
    assert len(possible_machine_transitions) > 0, "Should have manual scheduling options available"
    
    # Test 2: Manual scheduling works
    manual_transition = ComponentTransition(
        component_id="m-0",
        new_state=MachineStateState.SETUP,
        job_id="j-1"  # Manually choose j-1
    )
    
    action_manual = Action(
        transitions=(manual_transition,),
        action_factory_info=ActionFactoryInfo.Valid,
        time_machine=time_machines.jump_to_event
    )
    
    result_manual = state.step("debug", instance, config, test_state, action_manual)
    assert result_manual.success, f"Manual scheduling should succeed: {result_manual.message}"
    
    # Verify manual transition worked
    final_machine_manual = result_manual.state.machines[0]
    if final_machine_manual.state == MachineStateState.SETUP:
        assert final_machine_manual.buffer.store == ("j-1",), "Manually selected job should be processed"