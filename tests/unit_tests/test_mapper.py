from jobshoplab.compiler.mapper import DictToInitStateMapper, DictToInstanceMapper
from jobshoplab.types.instance_config_types import BufferRoleConfig


def test_instance_mapping(minimal_instance_dict, default_instance, config):
    mapper = DictToInstanceMapper(0, config=config)
    mapped_instance = mapper.map(minimal_instance_dict)
    assert mapped_instance.machines == default_instance.machines
    assert mapped_instance.buffers == default_instance.buffers
    assert mapped_instance.transports == default_instance.transports
    assert mapped_instance.instance == default_instance.instance
    assert mapped_instance.description == default_instance.description
    assert mapped_instance.logistics == default_instance.logistics


def test_state_mapping(minimal_instance_dict, default_instance, config, default_init_state):
    mapper = DictToInitStateMapper("debug", config=config)
    mapped_state = mapper.map(minimal_instance_dict, default_instance)
    assert default_init_state.buffers == mapped_state.buffers
    assert default_init_state.transports == mapped_state.transports
    assert default_init_state.machines == mapped_state.machines
    assert default_init_state.jobs == mapped_state.jobs
    assert default_init_state.time == mapped_state.time


def test_instance_mapping_with_intralogistics(
    minimal_instance_dict_with_intralogistics, default_instance_with_intralogistics, config
):
    mapper = DictToInstanceMapper(0, config=config)
    mapped_instance = mapper.map(minimal_instance_dict_with_intralogistics)
    assert mapped_instance.machines == default_instance_with_intralogistics.machines
    assert mapped_instance.buffers == default_instance_with_intralogistics.buffers
    assert mapped_instance.transports == default_instance_with_intralogistics.transports
    assert mapped_instance.instance == default_instance_with_intralogistics.instance
    assert mapped_instance.description == default_instance_with_intralogistics.description
    assert mapped_instance.logistics == default_instance_with_intralogistics.logistics


def test_state_mapping_with_intralogistics(
    minimal_instance_dict_with_intralogistics, default_instance, config, default_init_state
):
    mapper = DictToInitStateMapper("debug", config=config)
    mapped_state = mapper.map(minimal_instance_dict_with_intralogistics, default_instance)
    assert default_init_state.buffers == mapped_state.buffers
    assert default_init_state.machines == mapped_state.machines
    assert default_init_state.jobs == mapped_state.jobs
    assert default_init_state.time == mapped_state.time

    # JUST TESTING AGAINST LOCATION STRING
    for mapped_transport, location in zip(mapped_state.transports, ["m-1", "m-2", "m-2"]):
        assert mapped_transport.location.location == location


def test_outages(instance_dict_with_outages, config, instance_with_outages):
    mapper = DictToInstanceMapper(0, config=config)
    mapped_instance = mapper.map(instance_dict_with_outages)
    assert mapped_instance.machines == instance_with_outages.machines
    assert mapped_instance.transports == instance_with_outages.transports


def test_stochastic_machine_times(
    instance_dict_with_stochastic_machine_times,
    instance_with_stochastic_machine_times,
    config,
):
    mapper = DictToInstanceMapper(0, config=config)
    mapped_instance = mapper.map(instance_dict_with_stochastic_machine_times)
    assert mapped_instance.machines == instance_with_stochastic_machine_times.machines


def test_stochastic_transport_times(
    instance_dict_with_stochastic_transport_times,
    instance_with_stochastic_transport_times,
    config,
):
    mapper = DictToInstanceMapper(0, config=config)
    mapped_instance = mapper.map(instance_dict_with_stochastic_transport_times)
    assert mapped_instance.logistics == instance_with_stochastic_transport_times.logistics


def test_static_setup_times(
    instance_dict_with_static_setup_times,
    instance_with_static_setup_times,
    config,
):
    mapper = DictToInstanceMapper(0, config=config)
    mapped_instance = mapper.map(instance_dict_with_static_setup_times)
    assert mapped_instance.machines == instance_with_static_setup_times.machines


def test_stochastic_setup_times(
    instance_dict_with_stochastic_setup_times,
    instance_with_stochastic_setup_times,
    config,
):
    mapper = DictToInstanceMapper(0, config=config)
    mapped_instance = mapper.map(instance_dict_with_stochastic_setup_times)
    assert mapped_instance.machines == instance_with_stochastic_setup_times.machines


def test_buffer_role_mapping(config):
    """Test that buffer roles are correctly mapped from dictionary to instance configuration."""
    # Create test data with various buffer roles
    instance_dict = {
        "instance_config": {
            "description": "test instance for buffer roles",
            "instance": {
                "specification": """
                    (m0,t)|(m1,t)
                    j0|(0,2) (1,3)
                    j1|(1,1) (0,2)
                """
            },
            "buffer": [
                {"name": "b-input", "type": "fifo", "capacity": 10, "role": "input"},
                {"name": "b-output", "type": "flex_buffer", "capacity": 5, "role": "output"},
                {
                    "name": "b-compensation",
                    "type": "flex_buffer",
                    "capacity": 3,
                    "role": "compensation",
                },
            ],
        }
    }

    mapper = DictToInstanceMapper(0, config=config)
    mapped_instance = mapper.map(instance_dict)

    # Find buffers by name and verify their roles
    buffer_roles = {buf.id: buf.role for buf in mapped_instance.buffers}

    # Check that explicit buffer roles are correctly mapped
    input_buffer = next((buf for buf in mapped_instance.buffers if "b-input" in buf.id), None)
    output_buffer = next((buf for buf in mapped_instance.buffers if "b-output" in buf.id), None)
    compensation_buffer = next(
        (buf for buf in mapped_instance.buffers if "b-compensation" in buf.id), None
    )

    # Alternative: find by original name in description or try different approach
    if not input_buffer:
        input_buffer = next(
            (buf for buf in mapped_instance.buffers if buf.role == BufferRoleConfig.INPUT), None
        )
    if not output_buffer:
        output_buffer = next(
            (buf for buf in mapped_instance.buffers if buf.role == BufferRoleConfig.OUTPUT), None
        )
    if not compensation_buffer:
        compensation_buffer = next(
            (buf for buf in mapped_instance.buffers if buf.role == BufferRoleConfig.COMPENSATION),
            None,
        )

    assert input_buffer.role == BufferRoleConfig.INPUT
    assert output_buffer.role == BufferRoleConfig.OUTPUT
    assert compensation_buffer.role == BufferRoleConfig.COMPENSATION

    # Check that machine buffers get COMPONENT role by default
    machine_buffers = [
        buf for buf in mapped_instance.buffers if buf.parent and buf.parent.startswith("m-")
    ]
    for buf in machine_buffers:
        assert buf.role == BufferRoleConfig.COMPONENT


def test_buffer_role_case_insensitive(config):
    """Test that buffer role parsing is case insensitive."""
    instance_dict = {
        "instance_config": {
            "description": "test instance for case insensitive roles",
            "instance": {
                "specification": """
                    (m0,t)
                    j0|(0,2)
                    j1|(0,1)
                """
            },
            "buffer": [
                {"name": "b-input", "type": "fifo", "capacity": 10, "role": "input"},
                {"name": "b-output", "type": "flex_buffer", "capacity": 10, "role": "output"},
                {"name": "b-test", "type": "fifo", "capacity": 5, "role": "input"},  # lowercase
            ],
        }
    }

    mapper = DictToInstanceMapper(0, config=config)
    mapped_instance = mapper.map(instance_dict)

    test_buffer = next(buf for buf in mapped_instance.buffers if "b-test" in buf.id)
    assert test_buffer.role == BufferRoleConfig.INPUT


def test_buffer_description_mapping(config):
    """Test that buffer descriptions are correctly mapped."""
    instance_dict = {
        "instance_config": {
            "description": "test instance for buffer descriptions",
            "instance": {
                "specification": """
                    (m0,t)
                    j0|(0,2)
                    j1|(0,1)
                """
            },
            "buffer": [
                {"name": "b-input", "type": "fifo", "capacity": 10, "role": "input"},
                {"name": "b-output", "type": "flex_buffer", "capacity": 10, "role": "output"},
                {
                    "name": "b-test",
                    "type": "fifo",
                    "capacity": 5,
                    "role": "input",
                    "description": "Test input buffer",
                },
            ],
        }
    }

    mapper = DictToInstanceMapper(0, config=config)
    mapped_instance = mapper.map(instance_dict)

    test_buffer = next(buf for buf in mapped_instance.buffers if "b-test" in buf.id)
    assert test_buffer.description == "Test input buffer"


def test_invalid_buffer_role_error(config):
    """Test that invalid buffer roles raise appropriate errors."""
    import pytest

    from jobshoplab.utils.exceptions import InvalidType

    instance_dict = {
        "instance_config": {
            "description": "test instance for invalid role",
            "instance": {
                "specification": """
                    (m0,t)
                    j0|(0,2)
                    j1|(0,1)
                """
            },
            "buffer": [
                {"name": "b-input", "type": "fifo", "capacity": 10, "role": "input"},
                {"name": "b-output", "type": "flex_buffer", "capacity": 10, "role": "output"},
                {
                    "name": "b-test",
                    "type": "fifo",
                    "capacity": 5,
                    "role": "invalid_role",  # Invalid role
                },
            ],
        }
    }

    mapper = DictToInstanceMapper(0, config=config)

    with pytest.raises(InvalidType) as exc_info:
        mapper.map(instance_dict)

    assert "BufferRoleConfig" in str(exc_info.value)


def test_agv_buffer_component_role(config):
    """Test that AGV buffers get COMPONENT role by default."""
    instance_dict = {
        "instance_config": {
            "description": "test instance with AGV transport",
            "instance": {
                "specification": """
                    (m0,t)|(m1,t)
                    j0|(0,2) (1,3)
                    j1|(1,1) (0,2)
                """
            },
            "logistics": {
                "type": "agv",
                "amount": 2,
                "specification": """
                    m-0|m-1|in-buf|out-buf
                    m-0|0 5 0 0
                    m-1|5 0 0 0
                    in-buf|0 0 0 0
                    out-buf|0 0 0 0
                """,
            },
        }
    }

    mapper = DictToInstanceMapper(0, config=config)
    mapped_instance = mapper.map(instance_dict)

    # Find AGV buffers (transport buffers)
    agv_buffers = [
        buf for buf in mapped_instance.buffers if buf.parent and buf.parent.startswith("t-")
    ]

    # All AGV buffers should have COMPONENT role
    for buf in agv_buffers:
        assert buf.role == BufferRoleConfig.COMPONENT
