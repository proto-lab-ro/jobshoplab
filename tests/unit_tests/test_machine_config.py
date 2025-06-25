import pytest
from jobshoplab.compiler.mapper import DictToInstanceMapper
from jobshoplab.types.instance_config_types import BufferTypeConfig


@pytest.fixture
def global_machine_buffer_config():
    """Config with global machine buffer settings applied to all machines"""
    return {
        "instance_config": {
            "description": "test instance with global machine buffer config",
            "instance": {
                "specification": """
                    (m0,t)|(m1,t)|(m2,t)
                    j0|(0,3) (1,2) (2,2)
                    j1|(0,2) (2,1) (1,4)
                    j2|(1,4) (2,3) (0,3)
                """
            },
            "machines": {
                "prebuffer": [
                    {"capacity": 5, "type": "fifo"}
                ],
                "postbuffer": [
                    {"capacity": 5, "type": "fifo"}
                ]
            }
        }
    }


@pytest.fixture
def specific_machine_buffer_config():
    """Config with machine-specific buffer settings for m-0 only"""
    return {
        "instance_config": {
            "description": "test instance with specific machine buffer config",
            "instance": {
                "specification": """
                    (m0,t)|(m1,t)|(m2,t)
                    j0|(0,3) (1,2) (2,2)
                    j1|(0,2) (2,1) (1,4)
                    j2|(1,4) (2,3) (0,3)
                """
            },
            "machines": [
                {
                    "m-0": {
                        "prebuffer": [
                            {"capacity": 5, "type": "fifo"}
                        ],
                        "postbuffer": [
                            {"capacity": 5, "type": "fifo"}
                        ]
                    }
                }
            ]
        }
    }


def test_global_machine_buffer_configuration(global_machine_buffer_config, config):
    """Test that global machine buffer configuration applies to all machines"""
    mapper = DictToInstanceMapper(0, config=config)
    instance = mapper.map(global_machine_buffer_config)
    
    # Verify all machines have the configured buffer properties
    for machine in instance.machines:
        # Check prebuffer configuration
        assert machine.prebuffer.capacity == 5
        assert machine.prebuffer.type == BufferTypeConfig.FIFO
        
        # Check postbuffer configuration  
        assert machine.postbuffer.capacity == 5
        assert machine.postbuffer.type == BufferTypeConfig.FIFO


def test_specific_machine_buffer_configuration(specific_machine_buffer_config, config):
    """Test that machine-specific buffer configuration only applies to specified machine"""
    mapper = DictToInstanceMapper(0, config=config)
    instance = mapper.map(specific_machine_buffer_config)
    
    # Find machine m-0 and other machines
    machine_m0 = None
    other_machines = []
    
    for machine in instance.machines:
        if machine.id == "m-0":
            machine_m0 = machine
        else:
            other_machines.append(machine)
    
    # Verify machine m-0 has the configured buffer properties
    assert machine_m0 is not None
    assert machine_m0.prebuffer.capacity == 5
    assert machine_m0.prebuffer.type == BufferTypeConfig.FIFO
    assert machine_m0.postbuffer.capacity == 5
    assert machine_m0.postbuffer.type == BufferTypeConfig.FIFO
    
    # Verify other machines have default buffer properties (not the specific config)
    for machine in other_machines:
        # Default buffer configuration should be different from the specific config
        # (assuming defaults are not capacity=5 and type=FIFO)
        assert machine.prebuffer.capacity != 5 or machine.prebuffer.type != BufferTypeConfig.FIFO
        assert machine.postbuffer.capacity != 5 or machine.postbuffer.type != BufferTypeConfig.FIFO


def test_machine_config_buffer_property_setting(config):
    """Test that buffer properties can be set through machine configuration"""
    # Test with both global and specific configurations
    global_config = {
        "instance_config": {
            "description": "test buffer properties",
            "instance": {
                "specification": """
                    (m0,t)|(m1,t)
                    j0|(0,3) (1,2)
                    j1|(0,2) (1,4)
                """
            },
            "machines": {
                "prebuffer": [
                    {"capacity": 10, "type": "lifo"}
                ],
                "postbuffer": [
                    {"capacity": 8, "type": "fifo"}
                ]
            }
        }
    }
    
    mapper = DictToInstanceMapper(0, config=config)
    instance = mapper.map(global_config)
    
    # Should have two machines (m-0 and m-1)
    assert len(instance.machines) == 2
    
    # Check that both machines have the same buffer configuration (global setting)
    for machine in instance.machines:
        # Verify buffer properties are correctly set
        assert machine.prebuffer.capacity == 10
        assert machine.prebuffer.type == BufferTypeConfig.LIFO
        assert machine.postbuffer.capacity == 8
        assert machine.postbuffer.type == BufferTypeConfig.FIFO