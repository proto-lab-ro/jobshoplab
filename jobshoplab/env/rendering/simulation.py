from jobshoplab.types import Config, StateMachineResult
from jobshoplab.utils import get_logger


def dummy_sim(
    log_level: int | str, config: Config, state_history: tuple[StateMachineResult, ...]
) -> None:
    logger = get_logger(__name__, loglevel=log_level)
