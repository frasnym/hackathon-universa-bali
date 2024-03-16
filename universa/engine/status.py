from enum import Enum
from typing import Any, Callable, Tuple

from ..utils.logs import get_logger


class Status(Enum):
    """
    Base class for all statuses - enables easy conversion between different status objects.
    """

    @classmethod
    def from_status(cls, status: "Status"):
        """
        Exchange from given status to this class status.
        """
        try:
            return cls(status.value)
        except ValueError as e:
            raise ValueError(
                f"Status not found: {status}. Check your conversion from {status.__class__} to {cls.__class__}."
            )

    def __bool__(self):
        return bool(self.value)


class MachineStatus(Status):
    """
    StateMachine context status.
    """

    CONTEXT_0: int = 0
    CONTEXT_1: int = 1
    CONTEXT_2: int = 2
    CONTEXT_3: int = 3
    STOP: int = 4

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.name}"

    def __str__(self):
        if self == MachineStatus.CONTEXT_0:
            return "Either we are starting the graph or we solved it - this is a ROOT state."
        elif self == MachineStatus.CONTEXT_1:
            return "We still have some nodes to solve - this is a ROOT state."
        elif self == MachineStatus.CONTEXT_2:
            return "Either solve children nodes or backtrack if they are solved - this is a INTERMEDIATE state."
        elif self == MachineStatus.CONTEXT_3:
            return "Either solve or go back to parent - this is a LEAF state."


class OperationStatus(Status):
    """
    Operation status describes how the operation ended.
    """

    SUCCESS: int = 1
    FAILURE: int = 0

    @classmethod
    def status(cls, func: Callable) -> Callable:
        """
        Decorator to add status to the operation.
        """
        status_logger = get_logger(__name__)

        def wrapper(*args, **kwargs) -> Tuple[Any, int]:
            try:
                result = func(*args, **kwargs)
                return result, cls.SUCCESS, None
            except Exception as e:
                status_logger.error(f"Operation {func.__name__} failed with error: {e}")
                raise e

        return wrapper
