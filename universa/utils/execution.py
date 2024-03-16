import functools
from typing import Any, Callable

from .logs import general_logger


def retry(num_retries: int = 2):
    """
    Simple retrying decorator. Will raise error only if all attempts failed.

    Args:
        * `num_retries` (`int`): Number of retries.

    Returns:
        * `Any`: Any return value of the decorated function.

    Raises:
        * `Exception`: Any exception raised by the decorated function.
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            _exc = None
            for i in range(1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    _exc = e
                    general_logger.warning(
                        f"Error in {func.__name__} at {i+1} attempt: {e}"
                    )
                    pass
            if isinstance(_exc, Exception):
                raise _exc
            else:
                raise Exception(f"Function {func.__name__} failed {num_retries} times")

        return wrapper

    return decorator
