import re
from abc import ABC, abstractmethod
from logging import Logger
from typing import Any

from jobshoplab.types import Config
from jobshoplab.utils import get_logger
from jobshoplab.utils.exceptions import (
    InstanceSchemaError,
    InvalidFieldValueError,
    JobSpecificationSyntaxError,
    MissingRequiredFieldError,
    NotImplementedError,
)


class AbstractValidator(ABC):
    """
    Abstract base class for validators.
    """

    @abstractmethod
    def __init__(self, loglevel: int | str, config: Config, *args, **kwargs):
        """
        Initializes the AbstractValidator.

        Args:
            loglevel (int): The log level for the logger.
            config (Config): The configuration object.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        self.logger: Logger = get_logger(__name__, loglevel)
        self.config: Config = config

    @abstractmethod
    def validate(self, spec_dict: dict) -> None:
        """
        Validates the given spec_dict.

        Args:
            spec_dict (dict): The dictionary to be validated.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        raise NotImplementedError

    @abstractmethod
    def __repr__(self) -> str:
        """
        Returns a string representation of the validator.

        Returns:
            str: The string representation of the validator.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        raise NotImplementedError


class DummyValidator(AbstractValidator):
    """
    A dummy validator for testing purposes.
    """

    def __init__(self, loglevel: int | str, config: Config, *args, **kwargs):
        """
        Initializes the DummyValidator.

        Args:
            loglevel (int): The log level for the logger.
            config (Config): The configuration object.
        """
        super().__init__(loglevel, config)
        self.logger.debug(f"Init DummyValidator")

    def validate(self, spec_dict: dict) -> None:
        """
        Validates the given spec_dict.

        Args:
            spec_dict (dict): The dictionary to be validated.

        Returns:
            None

        """
        self.logger.debug(f"Validate")

    def __repr__(self) -> str:
        """
        Returns a string representation of the DummyValidator.

        Returns:
            str: The string representation of the DummyValidator.
        """
        return f"DummyValidator()"


class SimpleDSLValidator(AbstractValidator):
    """
    Validator for Instance DSL syntax in YAML configurations.

    This validator checks the structure and syntax of instance configuration files,
    ensuring they adhere to the expected format before they are processed by the mapper.
    """

    def __init__(self, loglevel: int | str, config: Config, *args, **kwargs):
        """
        Initializes the InstanceDSLValidator.

        Args:
            loglevel (int | str): The log level for the logger.
            config (Config): The configuration object.
        """
        super().__init__(loglevel, config)
        self.logger.debug("Initializing InstanceDSLValidator")

    def validate(self, spec_dict: dict) -> None:
        """
        Validates the given instance specification dictionary.

        Args:
            spec_dict (dict): The dictionary representation of an instance configuration.

        Raises:
            MissingRequiredFieldError: If a required field is missing.
            InvalidFieldValueError: If a field has an invalid value.
            JobSpecificationSyntaxError: If the job specification syntax is invalid.
            InstanceSchemaError: For other schema-related errors.
        """
        self.logger.debug("Validating instance specification")

        # 1. Check top-level structure
        self._validate_top_level_structure(spec_dict)

        # 2. Validate instance_config section
        instance_config = spec_dict.get("instance_config", {})
        self._validate_instance_config(instance_config)

        # 3. Validate job specification DSL syntax
        if "instance" in instance_config and "specification" in instance_config["instance"]:
            self._validate_job_specification(instance_config["instance"]["specification"])

        # 4. Validate logistics section if present
        if "logistics" in instance_config:
            self._validate_logistics_section(instance_config["logistics"])

        # 5. Validate setup times if present
        if "setup_times" in instance_config:
            self._validate_setup_times(instance_config["setup_times"])

        # 6. Validate outages if present
        if "outages" in instance_config:
            self._validate_outages(instance_config["outages"])

        # 7. Validate init_state if present
        if "init_state" in spec_dict:
            self._validate_init_state(spec_dict["init_state"])

        self.logger.debug("Instance specification validation completed successfully")

    def _validate_top_level_structure(self, spec_dict: dict) -> None:
        """
        Validates the top-level structure of the specification dictionary.

        Args:
            spec_dict (dict): The specification dictionary to validate.

        Raises:
            MissingRequiredFieldError: If instance_config is missing.
        """
        if "instance_config" not in spec_dict:
            raise MissingRequiredFieldError("instance_config")

    def _validate_instance_config(self, instance_config: dict) -> None:
        """
        Validates the instance_config section of the specification.

        Args:
            instance_config (dict): The instance_config section to validate.

        Raises:
            MissingRequiredFieldError: If required fields are missing.
            InvalidFieldValueError: If fields have invalid values.
        """
        # Check for required fields
        if "description" not in instance_config:
            raise MissingRequiredFieldError("description", "instance_config")

        if "instance" not in instance_config:
            raise MissingRequiredFieldError("instance", "instance_config")

        # Validate instance section
        instance = instance_config["instance"]
        if "specification" not in instance:
            raise MissingRequiredFieldError("specification", "instance_config.instance")

    def _validate_job_specification(self, specification: str) -> None:
        """
        Validates the job specification DSL syntax.

        Args:
            specification (str): The job specification string.

        Raises:
            JobSpecificationSyntaxError: If the job specification syntax is invalid.
        """
        # Split the specification into lines and remove leading/trailing whitespace
        lines = [line.strip() for line in specification.strip().split("\n")]

        # Skip empty lines
        lines = [line for line in lines if line]

        if not lines:
            raise JobSpecificationSyntaxError(1, "", "Empty job specification")

        # First line should be the machine header
        header_pattern = r"^(\(m\d+,\w+\)\|)+(\(m\d+,\w+\))$"
        if not re.match(header_pattern, lines[0].replace(" ", "")):
            raise JobSpecificationSyntaxError(1, lines[0], "Invalid machine header format")

        # Extract number of machines from header
        num_machines = len(lines[0].replace(" ", "").split("|"))

        # Job lines pattern
        job_line_pattern = r"^j\d+\|(\(\d+,\d+\)\s*)+$"

        # Check each job line
        for i, line in enumerate(lines[1:], 1):
            line_without_spaces = line.replace(" ", "")
            if not re.match(job_line_pattern, line_without_spaces):
                raise JobSpecificationSyntaxError(i + 1, line, "Invalid job specification format")

            # Check that the job has the correct number of operations
            operations = re.findall(r"\(\d+,\d+\)", line_without_spaces)
            if len(operations) != num_machines:
                raise JobSpecificationSyntaxError(
                    i + 1,
                    line,
                    f"Job has {len(operations)} operations, but there are {num_machines} machines",
                )

            # Check that machine indices are within bounds
            for op in operations:
                machine_idx = int(op.split(",")[0].replace("(", ""))
                if machine_idx >= num_machines:
                    raise JobSpecificationSyntaxError(
                        i + 1,
                        line,
                        f"Machine index {machine_idx} is out of bounds (max index: {num_machines-1})",
                    )

    def _validate_logistics_section(self, logistics: dict) -> None:
        """
        Validates the logistics section if present.

        Args:
            logistics (dict): The logistics section to validate.

        Raises:
            MissingRequiredFieldError: If required fields are missing.
            InvalidFieldValueError: If fields have invalid values.
            InstanceSchemaError: For other schema-related errors.
        """
        # Check for required fields for AGVs
        if "type" in logistics and logistics["type"] == "agv":
            if "amount" not in logistics:
                raise MissingRequiredFieldError("amount", "instance_config.logistics")

        # Validate travel times specification if present
        if "specification" in logistics:
            self._validate_travel_times_specification(logistics["specification"])

    def _validate_travel_times_specification(self, specification: str) -> None:
        """
        Validates the travel times specification syntax.

        Args:
            specification (str): The travel times specification string.

        Raises:
            InstanceSchemaError: For schema-related errors.
        """
        # Split the specification into lines and remove leading/trailing whitespace
        lines = [line.strip() for line in specification.strip().split("\n")]

        # Skip empty lines
        lines = [line for line in lines if line]

        if not lines:
            raise InstanceSchemaError("Empty travel times specification", "logistics.specification")

        # First line should be the location header
        header = lines[0].split("|")
        if len(header) < 2:
            raise InstanceSchemaError(
                "Invalid location header format - must contain at least two locations separated by '|'",
                "logistics.specification",
            )

        num_locations = len(header)

        # Check each travel time line
        for i, line in enumerate(lines[1:], 1):
            parts = line.split("|")
            if len(parts) != 2:
                raise InstanceSchemaError(
                    f"Invalid travel time line format at line {i+1}: '{line}'",
                    "logistics.specification",
                )

            location = parts[0]
            if location not in header:
                raise InstanceSchemaError(
                    f"Unknown location '{location}' at line {i+1}", "logistics.specification"
                )

            times = parts[1].split()
            if len(times) != num_locations:
                raise InstanceSchemaError(
                    f"Travel time line {i+1} has {len(times)} times, but there are {num_locations-1} destination locations",
                    "logistics.specification",
                )

            # Check that times are integers
            for time in times:
                try:
                    int(time)
                except ValueError:
                    raise InstanceSchemaError(
                        f"Travel time '{time}' at line {i+1} is not a valid integer",
                        "logistics.specification",
                    )

    def _validate_setup_times(self, setup_times: list) -> None:
        """
        Validates the setup times specification.

        Args:
            setup_times (list): The setup times configuration.

        Raises:
            InstanceSchemaError: For schema-related errors.
        """
        # If it's a list, each item should have a 'machine' and 'specification' field
        if isinstance(setup_times, list):
            for i, setup in enumerate(setup_times):
                if not isinstance(setup, dict):
                    raise InstanceSchemaError(
                        f"Setup time entry {i+1} must be a dictionary", "setup_times"
                    )

                if "machine" not in setup:
                    raise MissingRequiredFieldError("machine", f"setup_times[{i}]")

                if "specification" not in setup:
                    raise MissingRequiredFieldError("specification", f"setup_times[{i}]")

                # Validate the specification format
                self._validate_setup_time_specification(setup["specification"], i)

    def _validate_setup_time_specification(self, specification: str, index: int) -> None:
        """
        Validates a setup time specification string.

        Args:
            specification (str): The setup time specification.
            index (int): The index of the setup time in the setup_times list.

        Raises:
            InstanceSchemaError: For schema-related errors.
        """
        # Split the specification into lines and remove leading/trailing whitespace
        lines = [line.strip() for line in specification.strip().split("\n")]

        # Skip empty lines
        lines = [line for line in lines if line]

        if not lines:
            raise InstanceSchemaError(
                f"Empty setup time specification for setup_times[{index}]",
                f"setup_times[{index}].specification",
            )

        # First line should be the tool header
        header = lines[0].split("|")
        if len(header) < 2:
            raise InstanceSchemaError(
                f"Invalid tool header format for setup_times[{index}] - must contain at least two tools separated by '|'",
                f"setup_times[{index}].specification",
            )

        num_tools = len(header)

        # Check each setup time line
        for i, line in enumerate(lines[1:], 1):
            parts = line.split("|")
            if len(parts) != 2:
                raise InstanceSchemaError(
                    f"Invalid setup time line format at line {i+1}: '{line}'",
                    f"setup_times[{index}].specification",
                )

            tool = parts[0]
            if tool not in header:
                raise InstanceSchemaError(
                    f"Unknown tool '{tool}' at line {i+1}", f"setup_times[{index}].specification"
                )

            times = parts[1].split()
            if len(times) != num_tools:
                raise InstanceSchemaError(
                    f"Setup time line {i+1} has {len(times)} times, but there are {num_tools} destination tools",
                    f"setup_times[{index}].specification",
                )

            # Check that times are integers
            for time in times:
                try:
                    int(time)
                except ValueError:
                    raise InstanceSchemaError(
                        f"Setup time '{time}' at line {i+1} is not a valid integer",
                        f"setup_times[{index}].specification",
                    )

    def _validate_outages(self, outages: list) -> None:
        """
        Validates the outages configuration.

        Args:
            outages (list): The outages configuration.

        Raises:
            InstanceSchemaError: For schema-related errors.
        """
        if not isinstance(outages, list):
            raise InstanceSchemaError("Outages must be a list", "outages")

        for i, outage in enumerate(outages):
            if not isinstance(outage, dict):
                raise InstanceSchemaError(f"Outage entry {i+1} must be a dictionary", "outages")

            # Required fields
            if "component" not in outage:
                raise MissingRequiredFieldError("component", f"outages[{i}]")

            if "type" not in outage:
                raise MissingRequiredFieldError("type", f"outages[{i}]")

            if "duration" not in outage:
                raise MissingRequiredFieldError("duration", f"outages[{i}]")

            if "frequency" not in outage:
                raise MissingRequiredFieldError("frequency", f"outages[{i}]")

            # Validate outage type
            valid_types = {"maintenance", "repair", "breakdown", "fail", "recharge", "recharging"}
            if outage["type"] not in valid_types:
                raise InvalidFieldValueError(
                    f"outages[{i}].type", outage["type"], f"One of: {', '.join(valid_types)}"
                )

            # Validate duration and frequency are either integers or dicts with stochastic parameters
            self._validate_time_specification(outage["duration"], f"outages[{i}].duration")
            self._validate_time_specification(outage["frequency"], f"outages[{i}].frequency")

    def _validate_time_specification(self, time_spec: Any, field_path: str) -> None:
        """
        Validates a time specification, which can be an integer or a dict with stochastic parameters.

        Args:
            time_spec (Any): The time specification.
            field_path (str): The path to the field being validated.

        Raises:
            InvalidFieldValueError: If the time specification is invalid.
        """
        if isinstance(time_spec, int):
            # Simple integer time is always valid
            return

        if isinstance(time_spec, dict):
            # Check for distribution type
            if "type" in time_spec:
                valid_types = {"poisson", "gamma", "uni", "uniform", "normal", "gaussian"}
                if time_spec["type"] not in valid_types:
                    raise InvalidFieldValueError(
                        f"{field_path}.type", time_spec["type"], f"One of: {', '.join(valid_types)}"
                    )

                # Check required parameters for each distribution type
                dist_type = time_spec["type"]
                if dist_type == "poisson":
                    pass
                elif dist_type == "gamma":
                    if "scale" not in time_spec:
                        raise MissingRequiredFieldError("scale", f"{field_path}")
                elif dist_type in ["uniform", "uni"]:
                    if "offset" not in time_spec:
                        raise MissingRequiredFieldError("offset", f"{field_path}")
                elif dist_type in ["gaussian", "normal"]:
                    if "std" not in time_spec:
                        raise MissingRequiredFieldError("std", f"{field_path}")
            else:
                # Simple time behavior dict must have a base value
                if "base" not in time_spec:
                    raise MissingRequiredFieldError("base", f"{field_path}")
        else:
            raise InvalidFieldValueError(
                field_path, str(time_spec), "Integer or dictionary with stochastic parameters"
            )

    def _validate_init_state(self, init_state: dict) -> None:
        """
        Validates the initial state configuration if present.

        Args:
            init_state (dict): The initial state configuration.

        Raises:
            InstanceSchemaError: For schema-related errors.
        """
        # This is a simplified validation, as init_state is optional and complex
        if not isinstance(init_state, dict):
            raise InstanceSchemaError("Init state must be a dictionary", "init_state")

        # Validate transport section if present
        if "transport" in init_state:
            if not isinstance(init_state["transport"], list):
                raise InstanceSchemaError(
                    "Transport section must be a list", "init_state.transport"
                )

            for i, transport in enumerate(init_state["transport"]):
                if not isinstance(transport, dict):
                    raise InstanceSchemaError(
                        f"Transport entry {i+1} must be a dictionary", "init_state.transport"
                    )

                # Each transport must have a location
                if "location" not in transport:
                    raise MissingRequiredFieldError("location", f"init_state.transport[{i}]")

    def __repr__(self) -> str:
        """
        Returns a string representation of the validator.

        Returns:
            str: The string representation.
        """
        return "SimpleDSLValidator()"
