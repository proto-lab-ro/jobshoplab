import pytest

from jobshoplab.types.state_types import (
    BufferState,
    BufferStateState,
    NoTime,
    State,
    TransportLocation,
    TransportState,
    TransportStateState,
)
from jobshoplab.utils.state_machine_utils.transport_type_utils import (
    get_transport_id_by_job_id,
    get_transport_state_by_job_id,
)


@pytest.fixture
def transport_with_job():
    """Create a transport assigned to a job."""
    return TransportState(
        id="t-1",
        state=TransportStateState.WORKING,
        location=TransportLocation(progress=0.5, location=("m-1", "m-2", "m-3")),
        occupied_till=NoTime(),
        outages=(),
        buffer=BufferState(id="t-1-buffer", state=BufferStateState.EMPTY, store=()),
        transport_job="job-1",
    )


@pytest.fixture
def transport_without_job():
    """Create a transport not assigned to any job."""
    return TransportState(
        id="t-2",
        state=TransportStateState.IDLE,
        location=TransportLocation(progress=0.0, location=("depot", "depot", "depot")),
        occupied_till=NoTime(),
        outages=(),
        buffer=BufferState(id="t-2-buffer", state=BufferStateState.EMPTY, store=()),
        transport_job=None,
    )


@pytest.fixture
def state_with_transports(transport_with_job, transport_without_job):
    """Create a state with multiple transports."""
    return State(
        jobs=(),
        machines=(),
        transports=(transport_with_job, transport_without_job),
        buffers=(),
        time=NoTime(),
    )


class TestGetTransportIdByJobId:
    """Test get_transport_id_by_job_id function."""

    def test_finds_transport_assigned_to_job(self, state_with_transports):
        """Test that function finds transport assigned to a specific job."""
        transport_id = get_transport_id_by_job_id(state_with_transports, "job-1")
        assert transport_id == "t-1"

    def test_returns_none_for_unassigned_job(self, state_with_transports):
        """Test that function returns None for job not assigned to any transport."""
        transport_id = get_transport_id_by_job_id(state_with_transports, "job-2")
        assert transport_id is None

    def test_returns_none_for_empty_state(self):
        """Test that function returns None when no transports exist."""
        empty_state = State(
            jobs=(),
            machines=(),
            transports=(),
            buffers=(),
            time=NoTime(),
        )
        transport_id = get_transport_id_by_job_id(empty_state, "job-1")
        assert transport_id is None

    def test_finds_correct_transport_with_multiple_assignments(self):
        """Test that function finds correct transport when multiple transports have jobs."""
        transport1 = TransportState(
            id="t-1",
            state=TransportStateState.WORKING,
            location=TransportLocation(progress=0.5, location=("m-1", "m-2", "m-3")),
            occupied_till=NoTime(),
            outages=(),
            buffer=BufferState(id="t-1-buffer", state=BufferStateState.EMPTY, store=()),
            transport_job="job-1",
        )

        transport2 = TransportState(
            id="t-2",
            state=TransportStateState.WORKING,
            location=TransportLocation(progress=0.3, location=("m-2", "m-3", "m-4")),
            occupied_till=NoTime(),
            outages=(),
            buffer=BufferState(id="t-2-buffer", state=BufferStateState.EMPTY, store=()),
            transport_job="job-2",
        )

        state = State(
            jobs=(),
            machines=(),
            transports=(transport1, transport2),
            buffers=(),
            time=NoTime(),
        )

        # Test finding first transport
        transport_id = get_transport_id_by_job_id(state, "job-1")
        assert transport_id == "t-1"

        # Test finding second transport
        transport_id = get_transport_id_by_job_id(state, "job-2")
        assert transport_id == "t-2"


class TestGetTransportStateByJobId:
    """Test get_transport_state_by_job_id function."""

    def test_finds_transport_state_assigned_to_job(self, state_with_transports):
        """Test that function finds transport state assigned to a specific job."""
        transport_state = get_transport_state_by_job_id(state_with_transports, "job-1")
        assert transport_state is not None
        assert transport_state.id == "t-1"
        assert transport_state.transport_job == "job-1"

    def test_returns_none_for_unassigned_job(self, state_with_transports):
        """Test that function returns None for job not assigned to any transport."""
        transport_state = get_transport_state_by_job_id(state_with_transports, "job-2")
        assert transport_state is None

    def test_returns_none_for_empty_state(self):
        """Test that function returns None when no transports exist."""
        empty_state = State(
            jobs=(),
            machines=(),
            transports=(),
            buffers=(),
            time=NoTime(),
        )
        transport_state = get_transport_state_by_job_id(empty_state, "job-1")
        assert transport_state is None

    def test_finds_correct_transport_state_with_multiple_assignments(self):
        """Test that function finds correct transport state when multiple transports have jobs."""
        transport1 = TransportState(
            id="t-1",
            state=TransportStateState.WORKING,
            location=TransportLocation(progress=0.5, location=("m-1", "m-2", "m-3")),
            occupied_till=NoTime(),
            outages=(),
            buffer=BufferState(id="t-1-buffer", state=BufferStateState.EMPTY, store=()),
            transport_job="job-1",
        )

        transport2 = TransportState(
            id="t-2",
            state=TransportStateState.WORKING,
            location=TransportLocation(progress=0.3, location=("m-2", "m-3", "m-4")),
            occupied_till=NoTime(),
            outages=(),
            buffer=BufferState(id="t-2-buffer", state=BufferStateState.EMPTY, store=()),
            transport_job="job-2",
        )

        state = State(
            jobs=(),
            machines=(),
            transports=(transport1, transport2),
            buffers=(),
            time=NoTime(),
        )

        # Test finding first transport state
        transport_state = get_transport_state_by_job_id(state, "job-1")
        assert transport_state is not None
        assert transport_state.id == "t-1"
        assert transport_state.transport_job == "job-1"
        assert transport_state.state == TransportStateState.WORKING

        # Test finding second transport state
        transport_state = get_transport_state_by_job_id(state, "job-2")
        assert transport_state is not None
        assert transport_state.id == "t-2"
        assert transport_state.transport_job == "job-2"
        assert transport_state.state == TransportStateState.WORKING
