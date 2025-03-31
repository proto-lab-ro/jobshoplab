# Import Exception from the built-in module
from builtins import Exception

from jobshoplab.utils import get_logger


class JobShopException(Exception):
    def __init__(self, message):
        self.message = message
        self.logger = get_logger(__name__, loglevel="error")
        self.logger.error(self.message)

    def __str__(self):
        return self.message


class StopIteration(JobShopException):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class FileNotFound(JobShopException):
    def __init__(self, file):
        self.message = f"File not found: {file}"
        super().__init__(self.message)


class NoJsspSpecified(JobShopException):
    def __init__(self):
        self.message = f"No JSSP Instance specified"
        super().__init__(self.message)


class ValueNotSet(JobShopException):
    def __init__(self, key, value):
        self.message = f"Value {key} not set: {value}"
        super().__init__(self.message)


class InvalidValue(JobShopException):
    def __init__(self, key, value, message=""):
        self.message = f"Invalid value {key}: {value} {message}"
        super().__init__(self.message)


class InvalidKey(JobShopException):
    def __init__(self, key):
        self.message = f"Invalid key: {key}"
        super().__init__(self.message)


class InvalidType(JobShopException):
    def __init__(self, key, value, expected_type):
        self.message = f"Invalid type {key}: {value}, expected {expected_type}"
        super().__init__(self.message)


class NotImplementedError(JobShopException):
    def __init__(self):
        self.message = f"Sorry not done yet"
        super().__init__(self.message)


class InvalidObservationSpace(JobShopException):
    def __init__(self, message):
        self.message = f"Invalid observation space: {message}"
        super().__init__(self.message)


class InvalidActionSpace(JobShopException):
    def __init__(self, message):
        self.message = f"Invalid action space: {message}"
        super().__init__(self.message)


class UnsuccessfulStateMachineResult(JobShopException):
    def __init__(self):
        self.message = f"The state machine did not return a successful result. Can not continue."
        super().__init__(self.message)


class ActionOutOfActionSpace(JobShopException):
    def __init__(self, action, action_space):
        self.message = f"Action {action} is out of action space {action_space}"
        super().__init__(self.message)


class EnvDone(JobShopException):
    def __init__(self):
        self.message = f"Environment is done. Can not continue."
        super().__init__(self.message)


class DslSyntaxError(JobShopException):
    def __init__(self, message, line):
        self.message = f"DSL Syntax Error: {message} at line {line}"
        super().__init__(self.message)


class MissingSpecificationError(JobShopException):
    def __init__(self, specification_name):
        self.message = f"Missing required specification: {specification_name}"
        super().__init__(self.message)


class InvalidTimeSpecification(JobShopException):
    def __init__(self, message):
        self.message = f"Invalid time specification: {message}"
        super().__init__(self.message)


class UnknownLocationNameError(JobShopException):
    def __init__(self, name):
        self.message = f"Unknown location name: {name}"
        super().__init__(self.message)


class InvalidDurationError(JobShopException):
    def __init__(self, value, expected_type="integer"):
        self.message = f"Duration must be an {expected_type}, got {type(value).__name__}"
        super().__init__(self.message)


class InvalidDistributionError(JobShopException):
    def __init__(self, message):
        self.message = f"Invalid distribution specification: {message}"
        super().__init__(self.message)


class UnknownDistributionTypeError(JobShopException):
    def __init__(self, dist_type):
        self.message = f"Unknown distribution function: {dist_type}"
        super().__init__(self.message)


class InvalidTimeBehaviorError(JobShopException):
    def __init__(self, behavior):
        self.message = f"Unknown time behavior: {behavior}"
        super().__init__(self.message)


class InvalidSetupTimesError(JobShopException):
    def __init__(self, machine_id):
        self.message = f"No setup times found for machine {machine_id}"
        super().__init__(self.message)


class InvalidToolUsageError(JobShopException):
    def __init__(self, job_id):
        self.message = f"No tool usage found for job {job_id}"
        super().__init__(self.message)


class InvalidTransportConfig(JobShopException):
    def __init__(self, message):
        self.message = f"Invalid transport configuration: {message}"
        super().__init__(self.message)


class ComponentAssociationError(JobShopException):
    def __init__(self, component_id, component_type):
        self.message = f"{component_type} with id={component_id} cannot be associated with a machine"
        super().__init__(self.message)


class MissingComponentError(JobShopException):
    def __init__(self, component_id, component_type):
        self.message = f"Missing {component_type} component with id={component_id}"
        super().__init__(self.message)


class InvalidOutageTypeError(JobShopException):
    def __init__(self, outage_type):
        self.message = f"Unknown outage type: {outage_type}"
        super().__init__(self.message)


class BufferFullError(JobShopException):
    def __init__(self, buffer_id):
        self.message = f"Buffer {buffer_id} is full, cannot add more items"
        super().__init__(self.message)


class JobNotInBufferError(JobShopException):
    def __init__(self, job_id, buffer_id):
        self.message = f"Job {job_id} not found in buffer {buffer_id}"
        super().__init__(self.message)


class InvalidDispatchRuleError(JobShopException):
    def __init__(self, mode, allowed_modes):
        self.message = f"Invalid dispatch rule mode: {mode}. Allowed modes: {allowed_modes}"
        super().__init__(self.message)


class OperationMachineMatchError(JobShopException):
    def __init__(self, operation_id, expected_machine, actual_machine):
        self.message = f"Operation {operation_id} is in prebuffer of machine {expected_machine} but is assigned to machine {actual_machine}"
        super().__init__(self.message)
