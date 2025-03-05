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
