import pytest

from jobshoplab.compiler.validators import SimpleDSLValidator as InstanceDSLValidator
from jobshoplab.utils.exceptions import (
    InstanceSchemaError,
    InvalidFieldValueError,
    JobSpecificationSyntaxError,
    MissingRequiredFieldError,
)


def test_validator_init(test_config):
    validator = InstanceDSLValidator("debug", test_config)
    assert str(validator) == "SimpleDSLValidator()"


def test_valid_minimal_instance(minimal_instance_dict, test_config):
    validator = InstanceDSLValidator("debug", test_config)
    # Should not raise any exceptions
    validator.validate(minimal_instance_dict)


def test_missing_instance_config(test_config):
    validator = InstanceDSLValidator("debug", test_config)
    invalid_dict = {"title": "InstanceConfig"}

    with pytest.raises(MissingRequiredFieldError) as excinfo:
        validator.validate(invalid_dict)
    assert "instance_config" in str(excinfo.value)


def test_missing_description(minimal_instance_dict, test_config):
    validator = InstanceDSLValidator("debug", test_config)

    # Remove description from instance_config
    del minimal_instance_dict["instance_config"]["description"]

    with pytest.raises(MissingRequiredFieldError) as excinfo:
        validator.validate(minimal_instance_dict)
    assert "description" in str(excinfo.value)


def test_invalid_job_specification(minimal_instance_dict, test_config):
    validator = InstanceDSLValidator("debug", test_config)

    # Invalid job specification syntax
    minimal_instance_dict["instance_config"]["instance"][
        "specification"
    ] = """
    (m0,t)|(m1,t)|(m2,t)
    j0|(0,3) (1,2) # Missing one operation
    j1|(0,2) (2,1) (1,4)
    j2|(1,4) (2,3) (0,3)
    """

    with pytest.raises(JobSpecificationSyntaxError) as excinfo:
        validator.validate(minimal_instance_dict)
    assert "Invalid job specification format" in str(excinfo.value)


def test_machine_index_out_of_bounds(minimal_instance_dict, test_config):
    validator = InstanceDSLValidator("debug", test_config)

    # Machine index out of bounds
    minimal_instance_dict["instance_config"]["instance"][
        "specification"
    ] = """
    (m0,t)|(m1,t)|(m2,t)
    j0|(0,3) (1,2) (5,2) # Machine index 5 is out of bounds
    j1|(0,2) (2,1) (1,4)
    j2|(1,4) (2,3) (0,3)
    """

    with pytest.raises(JobSpecificationSyntaxError) as excinfo:
        validator.validate(minimal_instance_dict)
    assert "Machine index 5 is out of bounds" in str(excinfo.value)


def test_invalid_logistics_agv_missing_amount(minimal_instance_dict, test_config):
    validator = InstanceDSLValidator("debug", test_config)

    # Missing 'amount' field for AGV type
    minimal_instance_dict["instance_config"]["logistics"] = {
        "type": "agv",
        "specification": """
        m-0|m-1|m-2|in-buf|out-buf
        m-0|0 5 4 0 0
        m-1|5 0 2 0 0
        m-2|4 2 0 0 0
        in-buf|0 0 0 0 0
        out-buf|0 0 0 0 0
        """,
    }

    with pytest.raises(MissingRequiredFieldError) as excinfo:
        validator.validate(minimal_instance_dict)
    assert "amount" in str(excinfo.value)


def test_invalid_travel_times_specification(minimal_instance_dict, test_config):
    validator = InstanceDSLValidator("debug", test_config)

    # Invalid travel times (non-integer value)
    minimal_instance_dict["instance_config"]["logistics"] = {
        "type": "agv",
        "amount": 3,
        "specification": """
        m-0|m-1|m-2|in-buf|out-buf
        m-0|0 5 4 0 abc
        m-1|5 0 2 0 0
        m-2|4 2 0 0 0
        in-buf|0 0 0 0 0
        out-buf|0 0 0 0 0
        """,
    }

    with pytest.raises(InstanceSchemaError) as excinfo:
        validator.validate(minimal_instance_dict)
    assert "Travel time 'abc'" in str(excinfo.value)
    assert "not a valid integer" in str(excinfo.value)


def test_setup_times_validation(minimal_instance_dict, test_config):
    validator = InstanceDSLValidator("debug", test_config)

    # Invalid setup times (missing machine field)
    minimal_instance_dict["instance_config"]["setup_times"] = [
        {"specification": "tl-0|tl-1|tl-2\ntl-0|0 2 5\ntl-1|2 0 8\ntl-2|5 2 0"}
    ]

    with pytest.raises(MissingRequiredFieldError) as excinfo:
        validator.validate(minimal_instance_dict)
    assert "machine" in str(excinfo.value)


def test_outages_validation(minimal_instance_dict, test_config):
    validator = InstanceDSLValidator("debug", test_config)

    # Valid outage
    minimal_instance_dict["instance_config"]["outages"] = [
        {
            "component": "m-1",
            "type": "maintenance",
            "duration": 5,
            "frequency": {"type": "gamma", "shape": 2, "scale": 5, "base": 10},
        }
    ]

    # Should not raise an exception
    validator.validate(minimal_instance_dict)

    # Invalid outage type
    minimal_instance_dict["instance_config"]["outages"] = [
        {"component": "m-1", "type": "invalid_type", "duration": 5, "frequency": 10}
    ]

    with pytest.raises(InvalidFieldValueError) as excinfo:
        validator.validate(minimal_instance_dict)
    assert "type" in str(excinfo.value)
    assert "invalid_type" in str(excinfo.value)


def test_stochastic_time_validation(minimal_instance_dict, test_config):
    validator = InstanceDSLValidator("debug", test_config)

    # Missing required parameter for Gaussian distribution
    minimal_instance_dict["instance_config"]["outages"] = [
        {
            "component": "m-1",
            "type": "maintenance",
            "duration": {"type": "gaussian"},  # Missing 'std'
            "frequency": 10,
        }
    ]

    with pytest.raises(MissingRequiredFieldError) as excinfo:
        validator.validate(minimal_instance_dict)
    assert "std" in str(excinfo.value)


def test_init_state_validation(minimal_instance_dict_with_intralogistics, test_config):
    validator = InstanceDSLValidator("debug", test_config)

    # Valid init_state
    validator.validate(minimal_instance_dict_with_intralogistics)

    # Invalid init_state (missing location for transport)
    invalid_dict = minimal_instance_dict_with_intralogistics.copy()
    invalid_dict["init_state"]["t-0"] = {}

    with pytest.raises(MissingRequiredFieldError) as excinfo:
        validator.validate(invalid_dict)
    assert "location" in str(excinfo.value)


def test_init_state_transport_validation(minimal_instance_dict, test_config):
    validator = InstanceDSLValidator("debug", test_config)

    # Valid transport specification
    test_dict = minimal_instance_dict.copy()
    test_dict["init_state"] = {
        "t-0": {"location": "m-1"},
        "t-1": {"location": "b-0"},
    }
    validator.validate(test_dict)

    # Invalid transport location (wrong format)
    test_dict["init_state"]["t-0"]["location"] = "invalid-location"
    with pytest.raises(InvalidFieldValueError) as excinfo:
        validator.validate(test_dict)
    assert "Machine ID (m-*) or buffer ID (b-*)" in str(excinfo.value)

    # Invalid transport job reference
    test_dict["init_state"]["t-0"] = {
        "location": "m-1",
        "transport_job": "invalid-job"
    }
    with pytest.raises(InvalidFieldValueError) as excinfo:
        validator.validate(test_dict)
    assert "Job ID (j-*)" in str(excinfo.value)


def test_init_state_job_validation(minimal_instance_dict, test_config):
    validator = InstanceDSLValidator("debug", test_config)

    # Valid job specification
    test_dict = minimal_instance_dict.copy()
    test_dict["init_state"] = {
        "j-0": {"location": "b-0"},
        "j-1": {"location": "m-1"},
    }
    validator.validate(test_dict)

    # Invalid job location
    test_dict["init_state"]["j-0"]["location"] = "invalid-location"
    with pytest.raises(InvalidFieldValueError) as excinfo:
        validator.validate(test_dict)
    assert "Machine ID (m-*), buffer ID (b-*), or transport ID (t-*)" in str(excinfo.value)


def test_init_state_buffer_validation(minimal_instance_dict, test_config):
    validator = InstanceDSLValidator("debug", test_config)

    # Valid buffer specification
    test_dict = minimal_instance_dict.copy()
    test_dict["init_state"] = {
        "b-0": {"store": ["j-0", "j-1"]},
        "b-1": {"store": []},
    }
    validator.validate(test_dict)

    # Invalid buffer store (not a list)
    test_dict["init_state"]["b-0"]["store"] = "j-0"
    with pytest.raises(InvalidFieldValueError) as excinfo:
        validator.validate(test_dict)
    assert "List of job IDs" in str(excinfo.value)

    # Invalid job ID in store
    test_dict["init_state"]["b-0"]["store"] = ["j-0", "invalid-job"]
    with pytest.raises(InvalidFieldValueError) as excinfo:
        validator.validate(test_dict)
    assert "Job ID (j-*)" in str(excinfo.value)


def test_init_state_machine_validation(minimal_instance_dict, test_config):
    validator = InstanceDSLValidator("debug", test_config)

    # Valid machine specification
    test_dict = minimal_instance_dict.copy()
    test_dict["init_state"] = {
        "m-0": {"occupied_till": 10, "mounted_tool": "tl-0"},
        "m-1": {"occupied_till": 5.5},
    }
    validator.validate(test_dict)

    # Invalid occupied_till type
    test_dict["init_state"]["m-0"]["occupied_till"] = "invalid"
    with pytest.raises(InvalidFieldValueError) as excinfo:
        validator.validate(test_dict)
    assert "Integer or float representing time" in str(excinfo.value)

    # Invalid mounted_tool type
    test_dict["init_state"]["m-0"] = {"mounted_tool": 123}
    with pytest.raises(InvalidFieldValueError) as excinfo:
        validator.validate(test_dict)
    assert "String representing tool ID" in str(excinfo.value)


def test_init_state_invalid_component_id(minimal_instance_dict, test_config):
    validator = InstanceDSLValidator("debug", test_config)

    # Invalid component ID format
    test_dict = minimal_instance_dict.copy()
    test_dict["init_state"] = {
        "invalid-id": {"location": "m-1"}
    }

    with pytest.raises(InstanceSchemaError) as excinfo:
        validator.validate(test_dict)
    assert "Unknown component ID format" in str(excinfo.value)


def test_init_state_special_fields(minimal_instance_dict, test_config):
    validator = InstanceDSLValidator("debug", test_config)

    # Valid start_time
    test_dict = minimal_instance_dict.copy()
    test_dict["init_state"] = {
        "start_time": 10
    }
    validator.validate(test_dict)

    # Invalid start_time type
    test_dict["init_state"]["start_time"] = "invalid"
    with pytest.raises(InvalidFieldValueError) as excinfo:
        validator.validate(test_dict)
    assert "Integer or float representing time" in str(excinfo.value)
