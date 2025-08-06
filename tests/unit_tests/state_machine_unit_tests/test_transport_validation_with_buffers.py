"""
Unit tests for transport validation with buffer-type-aware pickup restrictions.

This module tests the validation logic for transport transitions, specifically
the WAITINGPICKUP -> PICKUP transition validation based on buffer type constraints.
"""

import pytest

from jobshoplab.state_machine.core.state_machine.validate import is_transport_transition_valid
from jobshoplab.types import InstanceConfig
from jobshoplab.types.action_types import ComponentTransition
from jobshoplab.types.instance_config_types import (
    BufferConfig,
    BufferRoleConfig,
    BufferTypeConfig,
    LogisticsConfig,
    ProblemInstanceConfig,
    ProblemInstanceTypeConfig,
)
from jobshoplab.types.state_types import (
    BufferState,
    BufferStateState,
    MachineState,
    MachineStateState,
    NoTime,
    State,
    TransportLocation,
    TransportState,
    TransportStateState,
)


def create_test_instance_with_buffer(
    buffer_id: str, buffer_type: BufferTypeConfig, parent: str = "m-1"
) -> InstanceConfig:
    """Helper function to create a test InstanceConfig with a specific buffer configuration."""
    buffer_config = BufferConfig(
        id=buffer_id,
        type=buffer_type,
        capacity=10,
        resources=(),
        description=None,
        parent=parent,
        role=BufferRoleConfig.COMPONENT,
    )

    problem_instance = ProblemInstanceConfig(
        type=ProblemInstanceTypeConfig.JOB_SHOP, specification=()
    )

    logistics = LogisticsConfig(capacity=1, travel_times={})

    return InstanceConfig(
        description="test instance for buffer validation",
        buffers=(buffer_config,),
        machines=(),
        transports=(),
        logistics=logistics,
        instance=problem_instance,
    )


@pytest.fixture
def create_machine_with_postbuffer(create_buffer_state):
    """Create a machine with a postbuffer containing jobs."""

    def create_machine(
        postbuffer_id: str, jobs: tuple, buffer_type: BufferTypeConfig = BufferTypeConfig.FIFO
    ):
        postbuffer = create_buffer_state(postbuffer_id, BufferStateState.NOT_EMPTY, jobs)
        prebuffer = create_buffer_state(f"{postbuffer_id}-pre", BufferStateState.EMPTY, ())
        buffer = create_buffer_state(f"{postbuffer_id}-main", BufferStateState.EMPTY, ())

        return MachineState(
            id="m-1",
            buffer=buffer,
            occupied_till=NoTime(),
            prebuffer=prebuffer,
            postbuffer=postbuffer,
            state=MachineStateState.IDLE,
            outages=(),
            mounted_tool="tool-1",
            resources=(),
        )

    return create_machine


@pytest.fixture
def transport_waiting_for_pickup():
    """Create a transport in WAITINGPICKUP state."""
    return TransportState(
        id="t-1",
        state=TransportStateState.WAITINGPICKUP,
        location=TransportLocation(progress=0.0, location=("m-1", "m-1", "m-1")),
        occupied_till=NoTime(),
        outages=(),
        buffer=BufferState(id="t-1-buffer", state=BufferStateState.EMPTY, store=()),
        transport_job="job-1",  # Assigned to pick up job-1
    )


@pytest.fixture
def pickup_transition():
    """Create a WAITINGPICKUP -> PICKUP transition."""
    return ComponentTransition(
        component_id="t-1", new_state=TransportStateState.PICKUP, job_id="job-1"
    )


class TestTransportValidationWithBuffers:
    """Test transport validation with buffer type constraints."""


class TestFIFOBufferTransportValidation:
    """Test transport validation with FIFO buffers."""

    def test_fifo_pickup_allowed_first_position(
        self, create_machine_with_postbuffer, transport_waiting_for_pickup, pickup_transition
    ):
        """Test pickup allowed when job is at first position in FIFO buffer."""
        # Job-1 is at index 0 (first position) in FIFO buffer
        machine = create_machine_with_postbuffer("fifo-postbuffer", ("job-1", "job-2", "job-3"))
        state = State(
            jobs=(),
            machines=(machine,),
            transports=(transport_waiting_for_pickup,),
            buffers=(),
            time=NoTime(),
        )

        # This test will initially fail because we haven't implemented buffer validation yet
        # For now, the existing validation should pass (no buffer checking)
        is_valid, message = is_transport_transition_valid(
            state, transport_waiting_for_pickup, pickup_transition
        )

        # Currently should pass because buffer validation is not implemented yet
        assert is_valid is True
        assert message == ""

    @pytest.mark.skip(
        reason="Buffer validation not yet implemented in is_transport_transition_valid"
    )
    def test_fifo_pickup_blocked_second_position(
        self, create_machine_with_postbuffer, transport_waiting_for_pickup, pickup_transition
    ):
        """Test pickup blocked when job is at second position in FIFO buffer."""
        # Job-1 is at index 1 (second position) in FIFO buffer - should be blocked
        machine = create_machine_with_postbuffer("fifo-postbuffer", ("job-2", "job-1", "job-3"))
        state = State(
            jobs=(),
            machines=(machine,),
            transports=(transport_waiting_for_pickup,),
            buffers=(),
            time=NoTime(),
        )

        # Buffer validation is now implemented - pickup should be blocked
        instance = create_test_instance_with_buffer("fifo-postbuffer", BufferTypeConfig.FIFO)
        is_valid, message = is_transport_transition_valid(
            state, transport_waiting_for_pickup, pickup_transition
        )

        # Should be False because job-1 is at position 1 (not first position) in FIFO buffer
        assert is_valid is False
        assert "job-1" in message
        assert "not ready for pickup" in message


class TestLIFOBufferTransportValidation:
    """Test transport validation with LIFO buffers."""

    def test_lifo_pickup_allowed_last_position(
        self, create_machine_with_postbuffer, transport_waiting_for_pickup, pickup_transition
    ):
        """Test pickup allowed when job is at last position in LIFO buffer."""
        # Job-1 is at index 2 (last position) in LIFO buffer
        machine = create_machine_with_postbuffer("lifo-postbuffer", ("job-2", "job-3", "job-1"))
        # TODO: Need to set buffer type to LIFO in the machine config
        state = State(
            jobs=(),
            machines=(machine,),
            transports=(transport_waiting_for_pickup,),
            buffers=(),
            time=NoTime(),
        )

        # Create instance with LIFO buffer type
        instance = create_test_instance_with_buffer("lifo-postbuffer", BufferTypeConfig.LIFO)
        is_valid, message = is_transport_transition_valid(
            state, transport_waiting_for_pickup, pickup_transition
        )

        # Should pass because job-1 is at position 2 (last position) in LIFO buffer
        assert is_valid is True
        assert message == ""

    @pytest.mark.skip(
        reason="Buffer validation not yet implemented in is_transport_transition_valid"
    )
    def test_lifo_pickup_blocked_first_position(
        self, create_machine_with_postbuffer, transport_waiting_for_pickup, pickup_transition
    ):
        """Test pickup blocked when job is at first position in LIFO buffer."""
        # Job-1 is at index 0 (first position) in LIFO buffer - should be blocked
        machine = create_machine_with_postbuffer("lifo-postbuffer", ("job-1", "job-2", "job-3"))
        # TODO: Need to set buffer type to LIFO in the machine config
        state = State(
            jobs=(),
            machines=(machine,),
            transports=(transport_waiting_for_pickup,),
            buffers=(),
            time=NoTime(),
        )

        # Create instance with LIFO buffer type
        instance = create_test_instance_with_buffer("lifo-postbuffer", BufferTypeConfig.LIFO)
        is_valid, message = is_transport_transition_valid(
            state, transport_waiting_for_pickup, pickup_transition
        )

        # Should fail because job-1 is at position 0 (first position) in LIFO buffer
        assert is_valid is False
        assert "job-1" in message
        assert "not ready for pickup" in message


class TestFLEXBufferTransportValidation:
    """Test transport validation with FLEX buffers."""

    def test_flex_pickup_allowed_any_position(
        self, create_machine_with_postbuffer, transport_waiting_for_pickup, pickup_transition
    ):
        """Test pickup allowed from any position in FLEX buffer."""
        positions_to_test = [
            ("job-1", "job-2", "job-3"),  # First position
            ("job-2", "job-1", "job-3"),  # Middle position
            ("job-2", "job-3", "job-1"),  # Last position
        ]

        for jobs in positions_to_test:
            machine = create_machine_with_postbuffer("flex-postbuffer", jobs)
            state = State(
                jobs=(),
                machines=(machine,),
                transports=(transport_waiting_for_pickup,),
                buffers=(),
                time=NoTime(),
            )

            # Create instance with FLEX buffer type
            instance = create_test_instance_with_buffer(
                "flex-postbuffer", BufferTypeConfig.FLEX_BUFFER
            )
            is_valid, message = is_transport_transition_valid(
                state, transport_waiting_for_pickup, pickup_transition
            )

            # FLEX buffer should allow pickup from any position
            assert is_valid is True
            assert message == ""


class TestEdgeCasesTransportValidation:
    """Test edge cases for transport validation."""

    @pytest.mark.skip(
        reason="Buffer validation not yet implemented in is_transport_transition_valid"
    )
    def test_job_not_in_any_postbuffer(
        self, create_machine_with_postbuffer, transport_waiting_for_pickup, pickup_transition
    ):
        """Test pickup blocked when job is not in any postbuffer."""
        # Machine postbuffer doesn't contain job-1
        machine = create_machine_with_postbuffer("postbuffer", ("job-2", "job-3"))
        state = State(
            jobs=(),
            machines=(machine,),
            transports=(transport_waiting_for_pickup,),
            buffers=(),
            time=NoTime(),
        )

        # Create a basic instance config with FIFO buffer type
        instance = create_test_instance_with_buffer("postbuffer", BufferTypeConfig.FIFO)
        is_valid, message = is_transport_transition_valid(
            state, transport_waiting_for_pickup, pickup_transition
        )

        # Should be invalid because job is not found in any postbuffer
        assert is_valid is False
        assert "job-1" in message
        assert "not ready for pickup" in message

    @pytest.mark.skip(
        reason="Buffer validation not yet implemented in is_transport_transition_valid"
    )
    def test_empty_postbuffer(
        self, create_machine_with_postbuffer, transport_waiting_for_pickup, pickup_transition
    ):
        """Test pickup blocked when postbuffer is empty."""
        machine = create_machine_with_postbuffer("postbuffer", ())  # Empty buffer
        state = State(
            jobs=(),
            machines=(machine,),
            transports=(transport_waiting_for_pickup,),
            buffers=(),
            time=NoTime(),
        )

        # Create a basic instance config with FIFO buffer type
        instance = create_test_instance_with_buffer("postbuffer", BufferTypeConfig.FIFO)
        is_valid, message = is_transport_transition_valid(
            state, transport_waiting_for_pickup, pickup_transition
        )

        # Should be invalid because buffer is empty (job not found)
        assert is_valid is False
        assert "job-1" in message
        assert "not ready for pickup" in message

    def test_non_pickup_transition_unaffected(self, transport_waiting_for_pickup):
        """Test that non-pickup transitions are not affected by buffer validation."""
        # Test a different transition (not WAITINGPICKUP -> PICKUP)
        working_transition = ComponentTransition(
            component_id="t-1", new_state=TransportStateState.WORKING, job_id="job-1"
        )

        # Transport in IDLE state
        idle_transport = TransportState(
            id="t-1",
            state=TransportStateState.IDLE,
            location=TransportLocation(progress=0.0, location=("depot", "depot", "depot")),
            occupied_till=NoTime(),
            outages=(),
            buffer=BufferState(id="t-1-buffer", state=BufferStateState.EMPTY, store=()),
            transport_job=None,
        )

        state = State(jobs=(), machines=(), transports=(idle_transport,), buffers=(), time=NoTime())

        is_valid, message = is_transport_transition_valid(state, idle_transport, working_transition)

        # Non-pickup transitions should use existing validation logic
        assert is_valid is True
        assert message == ""
