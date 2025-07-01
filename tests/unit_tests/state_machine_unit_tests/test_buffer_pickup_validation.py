"""
Unit tests for buffer pickup validation functionality.

This module tests the buffer-type-aware job transport pickup validation logic.
Tests are written using TDD approach - tests first, implementation follows.
"""

import pytest

from jobshoplab.types.instance_config_types import BufferConfig, BufferTypeConfig
from jobshoplab.types.state_types import BufferState, BufferStateState
from jobshoplab.utils.state_machine_utils.buffer_type_utils import (
    get_job_position_in_postbuffer,
    is_correct_position_for_buffer_type,
    is_job_ready_for_pickup_from_postbuffer,
)


class TestGetJobPositionInPostbuffer:
    """Test getting job position within a postbuffer."""

    def test_job_found_at_index_0(self, create_buffer_state):
        """Test job found at first position returns index 0."""
        buffer = create_buffer_state("postbuffer-1", BufferStateState.NOT_EMPTY, ("job-1", "job-2", "job-3"))
        
        position = get_job_position_in_postbuffer("job-1", buffer)
        
        assert position == 0

    def test_job_found_at_index_1(self, create_buffer_state):
        """Test job found at second position returns index 1."""
        buffer = create_buffer_state("postbuffer-1", BufferStateState.NOT_EMPTY, ("job-1", "job-2", "job-3"))
        
        position = get_job_position_in_postbuffer("job-2", buffer)
        
        assert position == 1

    def test_job_found_at_last_index(self, create_buffer_state):
        """Test job found at last position returns correct index."""
        buffer = create_buffer_state("postbuffer-1", BufferStateState.NOT_EMPTY, ("job-1", "job-2", "job-3"))
        
        position = get_job_position_in_postbuffer("job-3", buffer)
        
        assert position == 2

    def test_job_not_found_returns_none(self, create_buffer_state):
        """Test job not in buffer returns None."""
        buffer = create_buffer_state("postbuffer-1", BufferStateState.NOT_EMPTY, ("job-1", "job-2"))
        
        position = get_job_position_in_postbuffer("job-999", buffer)
        
        assert position is None

    def test_empty_buffer_returns_none(self, create_buffer_state):
        """Test empty buffer returns None for any job."""
        buffer = create_buffer_state("postbuffer-1", BufferStateState.EMPTY, ())
        
        position = get_job_position_in_postbuffer("job-1", buffer)
        
        assert position is None


class TestIsCorrectPositionForBufferType:
    """Test buffer type position validation logic."""

    @pytest.mark.parametrize("buffer_type,job_position,buffer_length,expected", [
        # FIFO tests - only index 0 is valid
        (BufferTypeConfig.FIFO, 0, 3, True),   # First position in FIFO
        (BufferTypeConfig.FIFO, 1, 3, False),  # Not first position in FIFO
        (BufferTypeConfig.FIFO, 2, 3, False),  # Not first position in FIFO
        (BufferTypeConfig.FIFO, 0, 1, True),   # Single job at first position
        
        # LIFO tests - only last index is valid
        (BufferTypeConfig.LIFO, 2, 3, True),   # Last position in LIFO (index 2 of 3)
        (BufferTypeConfig.LIFO, 0, 3, False),  # Not last position in LIFO
        (BufferTypeConfig.LIFO, 1, 3, False),  # Not last position in LIFO
        (BufferTypeConfig.LIFO, 0, 1, True),   # Single job is at last position
        
        # FLEX tests - any position is valid
        (BufferTypeConfig.FLEX_BUFFER, 0, 3, True),  # Any position in FLEX
        (BufferTypeConfig.FLEX_BUFFER, 1, 3, True),  # Any position in FLEX
        (BufferTypeConfig.FLEX_BUFFER, 2, 3, True),  # Any position in FLEX
        (BufferTypeConfig.FLEX_BUFFER, 0, 1, True),  # Single job in FLEX
        
        # DUMMY tests - treated like FIFO
        (BufferTypeConfig.DUMMY, 0, 3, True),   # First position in DUMMY
        (BufferTypeConfig.DUMMY, 1, 3, False),  # Not first position in DUMMY
    ])
    def test_position_validation_for_buffer_types(self, buffer_type, job_position, buffer_length, expected):
        """Test position validation for all buffer types."""
        result = is_correct_position_for_buffer_type(job_position, buffer_length, buffer_type)
        
        assert result == expected

    def test_empty_buffer_always_invalid(self):
        """Test that empty buffer (length 0) is always invalid."""
        for buffer_type in BufferTypeConfig:
            result = is_correct_position_for_buffer_type(0, 0, buffer_type)
            assert result is False


class TestIsJobReadyForPickupFromPostbuffer:
    """Test high-level job pickup readiness validation."""

    @pytest.mark.skip(reason="Need proper InstanceConfig fixture - will implement in integration tests")
    def test_job_ready_fifo_first_position(self, minimal_instance_dict, default_init_state_result):
        """Test job ready for pickup from FIFO buffer at first position."""
        # This test requires proper InstanceConfig object, not dict
        # Will be properly implemented in integration test phase
        pass

    @pytest.mark.skip(reason="Need proper InstanceConfig fixture - will implement in integration tests")
    def test_job_not_ready_fifo_second_position(self, minimal_instance_dict, default_init_state_result):
        """Test job not ready for pickup from FIFO buffer at second position."""
        # Will be properly implemented in integration test phase
        pass

    @pytest.mark.skip(reason="Need proper InstanceConfig fixture - will implement in integration tests")
    def test_job_ready_lifo_last_position(self, minimal_instance_dict, default_init_state_result):
        """Test job ready for pickup from LIFO buffer at last position."""
        # Will be properly implemented in integration test phase
        pass

    @pytest.mark.skip(reason="Need proper InstanceConfig fixture - will implement in integration tests")
    def test_job_ready_flex_any_position(self, minimal_instance_dict, default_init_state_result):
        """Test job ready for pickup from FLEX buffer at any position."""
        # Will be properly implemented in integration test phase
        pass

    @pytest.mark.skip(reason="Need proper InstanceConfig fixture - will implement in integration tests")
    def test_job_not_in_any_postbuffer(self, minimal_instance_dict, default_init_state_result):
        """Test job not in any postbuffer returns False."""
        # Will be properly implemented in integration test phase
        pass


class TestBufferPickupIntegration:
    """Integration tests for buffer pickup validation with real buffer configurations."""

    @pytest.fixture
    def fifo_buffer_config(self):
        """Create a FIFO buffer configuration."""
        return BufferConfig(
            id="fifo-postbuffer",
            type=BufferTypeConfig.FIFO,
            capacity=5,
            resources=()
        )

    @pytest.fixture
    def lifo_buffer_config(self):
        """Create a LIFO buffer configuration."""
        return BufferConfig(
            id="lifo-postbuffer", 
            type=BufferTypeConfig.LIFO,
            capacity=5,
            resources=()
        )

    @pytest.fixture
    def flex_buffer_config(self):
        """Create a FLEX buffer configuration."""
        return BufferConfig(
            id="flex-postbuffer",
            type=BufferTypeConfig.FLEX_BUFFER,
            capacity=5,
            resources=()
        )

    def test_fifo_buffer_pickup_validation(self, fifo_buffer_config, create_buffer_state):
        """Test FIFO buffer allows pickup only from first position."""
        # Multiple jobs in FIFO buffer
        buffer_state = create_buffer_state(
            "fifo-postbuffer", 
            BufferStateState.NOT_EMPTY, 
            ("job-1", "job-2", "job-3")
        )
        
        # Job at index 0 should be ready
        assert is_correct_position_for_buffer_type(0, 3, fifo_buffer_config.type) is True
        
        # Jobs at other positions should not be ready
        assert is_correct_position_for_buffer_type(1, 3, fifo_buffer_config.type) is False
        assert is_correct_position_for_buffer_type(2, 3, fifo_buffer_config.type) is False

    def test_lifo_buffer_pickup_validation(self, lifo_buffer_config, create_buffer_state):
        """Test LIFO buffer allows pickup only from last position."""
        # Multiple jobs in LIFO buffer
        buffer_state = create_buffer_state(
            "lifo-postbuffer",
            BufferStateState.NOT_EMPTY,
            ("job-1", "job-2", "job-3")
        )
        
        # Job at last index should be ready
        assert is_correct_position_for_buffer_type(2, 3, lifo_buffer_config.type) is True
        
        # Jobs at other positions should not be ready
        assert is_correct_position_for_buffer_type(0, 3, lifo_buffer_config.type) is False
        assert is_correct_position_for_buffer_type(1, 3, lifo_buffer_config.type) is False

    def test_flex_buffer_pickup_validation(self, flex_buffer_config, create_buffer_state):
        """Test FLEX buffer allows pickup from any position."""
        # Multiple jobs in FLEX buffer
        buffer_state = create_buffer_state(
            "flex-postbuffer",
            BufferStateState.NOT_EMPTY,
            ("job-1", "job-2", "job-3")
        )
        
        # All positions should be ready in FLEX buffer
        assert is_correct_position_for_buffer_type(0, 3, flex_buffer_config.type) is True
        assert is_correct_position_for_buffer_type(1, 3, flex_buffer_config.type) is True
        assert is_correct_position_for_buffer_type(2, 3, flex_buffer_config.type) is True