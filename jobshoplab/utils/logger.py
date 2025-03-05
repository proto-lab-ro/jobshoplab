import logging
import sys


def get_logger(
    name: str,
    loglevel: int | str | str,
    handler: logging.Handler = logging.StreamHandler(sys.stdout),
) -> logging.Logger:
    """
    get a logger object with the given name and log level.
    matches various log levels and converts them to the corresponding logging level.

    Args:
        name (str): The name of the logger.
        loglevel (int|str): The log level.
    Returns:
        logging.Logger: The logger object.
    Raises:
        ValueError: If the loglevel is invalid.
    """
    logger = logging.getLogger(name)
    # Ensure the logger doesn't propagate messages to the root logger
    logger.propagate = False

    # Create a formatter and set it for the handler
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(handler)

    # Set the log level for this logger
    match loglevel:
        case "DEBUG":
            logger.setLevel(logging.DEBUG)
        case "INFO":
            logger.setLevel(logging.INFO)
        case "WARNING":
            logger.setLevel(logging.WARNING)
        case "ERROR":
            logger.setLevel(logging.ERROR)
        case "CRITICAL":
            logger.setLevel(logging.CRITICAL)
        case "debug":
            logger.setLevel(logging.DEBUG)
        case "info":
            logger.setLevel(logging.INFO)
        case "warning":
            logger.setLevel(logging.WARNING)
        case "error":
            logger.setLevel(logging.ERROR)
        case "critical":
            logger.setLevel(logging.CRITICAL)
        case 0:
            logger.setLevel(logging.DEBUG)
        case 1:
            logger.setLevel(logging.INFO)
        case 2:
            logger.setLevel(logging.WARNING)
        case 3:
            logger.setLevel(logging.ERROR)
        case 4:
            logger.setLevel(logging.CRITICAL)
        case _:
            raise ValueError(f"Invalid loglevel: {loglevel}")
    return logger
