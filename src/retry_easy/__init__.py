"""
retry_easy
----------

A lightweight, zero-dependency retry decorator for synchronous and
asynchronous Python functions.
"""

from __future__ import annotations

import asyncio
import functools
import inspect
import random
import sys
import time
from typing import Callable

if sys.version_info >= (3, 10):
    from typing import ParamSpec, TypeVar
else:
    from typing_extensions import ParamSpec, TypeVar

__version__ = "0.1.0"
__all__ = ["retry"]

P = ParamSpec("P")
R = TypeVar("R")


def retry(
    attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    jitter: float = 0.0,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Retry decorator for synchronous and asynchronous functions.

    Parameters
    ----------
    attempts : int, default=3
        Maximum number of attempts. Must be >= 1.

    delay : float, default=1.0
        Initial delay between attempts in seconds. Must be >= 0.

    backoff : float, default=1.0
        Delay multiplier applied after each failed attempt.
        - 1.0 = fixed delay
        - 2.0 = exponential backoff

    exceptions : tuple[type[Exception], ...]
        Exceptions that should trigger a retry. Must not be empty.
        Any other exception (including KeyboardInterrupt, SystemExit)
        is raised immediately.

    jitter : float, default=0.0
        Maximum random delay (in seconds) added to prevent thundering herd.
        - 0.0 = no jitter (deterministic)
        - > 0.0 = random uniform delay between 0 and jitter added to each wait

    Raises
    ------
    ValueError
        If any parameter is invalid.

    TypeError
        If `exceptions` is not a tuple of Exception subclasses.

    Examples
    --------
    >>> @retry(attempts=3, delay=1)
    ... def fetch():
    ...     pass

    >>> @retry(
    ...     attempts=5,
    ...     exceptions=(ConnectionError, TimeoutError),
    ...     jitter=0.5,
    ... )
    ... async def api_call():
    ...     pass
    """

    # --- Validation ---
    if attempts < 1:
        raise ValueError("attempts must be >= 1")
    if delay < 0:
        raise ValueError("delay must be >= 0")
    if backoff < 0:
        raise ValueError("backoff must be >= 0")
    if jitter < 0:
        raise ValueError("jitter must be >= 0")

    if not isinstance(exceptions, tuple):
        raise TypeError("exceptions must be a tuple of exception classes")
    if not exceptions:
        raise ValueError("exceptions must not be empty")
    if not all(
        inspect.isclass(exc) and issubclass(exc, Exception) for exc in exceptions
    ):
        raise TypeError("exceptions must contain only Exception subclasses")

    # --- Decorator ---
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        is_async = inspect.iscoroutinefunction(func)

        def _compute_wait(delay: float) -> float:
            return delay + random.uniform(0, jitter)

        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            current_delay = delay
            last_exc: Exception | None = None

            for attempt in range(attempts):
                try:
                    return await func(*args, **kwargs)
                except asyncio.CancelledError:
                    raise  # Never retry cancellation
                except exceptions as exc:
                    last_exc = exc
                    if attempt < attempts - 1:
                        await asyncio.sleep(_compute_wait(current_delay))
                        current_delay *= backoff

            if last_exc is not None:
                raise last_exc
            raise RuntimeError("Retry loop finished without an exception")

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            current_delay = delay
            last_exc: Exception | None = None

            for attempt in range(attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt < attempts - 1:
                        time.sleep(_compute_wait(current_delay))
                        current_delay *= backoff

            if last_exc is not None:
                raise last_exc
            raise RuntimeError("Retry loop finished without an exception")

        return async_wrapper if is_async else sync_wrapper

    return decorator
