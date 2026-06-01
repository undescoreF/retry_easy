import asyncio
import inspect
import time

import pytest

from retry_easy import retry

# =============================================================================
# PARAMETER VALIDATION
# =============================================================================


def test_validation_invalid_attempts():
    with pytest.raises(ValueError, match="attempts must be >= 1"):
        retry(attempts=0)


def test_validation_invalid_delay():
    with pytest.raises(ValueError, match="delay must be >= 0"):
        retry(delay=-0.1)


def test_validation_invalid_backoff():
    with pytest.raises(ValueError, match="backoff must be >= 0"):
        retry(backoff=-1.0)


def test_validation_invalid_jitter():
    with pytest.raises(ValueError, match="jitter must be >= 0"):
        retry(jitter=-0.5)


def test_validation_exceptions_not_tuple():
    with pytest.raises(TypeError, match="must be a tuple"):
        retry(exceptions=[ValueError])


def test_validation_exceptions_empty():
    with pytest.raises(ValueError, match="must not be empty"):
        retry(exceptions=())


def test_validation_exceptions_invalid_class():
    with pytest.raises(TypeError, match="must contain only Exception subclasses"):
        retry(exceptions=(ValueError, "not_an_exception"))


# =============================================================================
# SYNCHRONOUS FUNCTIONALITY
# =============================================================================


def test_sync_immediate_success():
    @retry(attempts=3, delay=0)
    def func():
        return "ok"

    assert func() == "ok"


def test_sync_retry_then_success():
    calls = 0

    @retry(attempts=3, delay=0)
    def func():
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ValueError("transient error")
        return "success"

    assert func() == "success"
    assert calls == 3


def test_sync_retry_exhausted():
    @retry(attempts=2, delay=0)
    def func():
        raise ValueError("persistent error")

    with pytest.raises(ValueError, match="persistent error"):
        func()


def test_sync_exception_filter():
    calls = 0

    @retry(attempts=3, delay=0, exceptions=(ValueError,))
    def func():
        nonlocal calls
        calls += 1
        raise TypeError("should bubble immediately")

    with pytest.raises(TypeError):
        func()
    assert calls == 1


def test_sync_preserves_metadata():
    def my_func():
        pass

    decorated = retry(attempts=1)(my_func)
    assert decorated.__name__ == "my_func"
    assert decorated.__doc__ == "Original docstring."


# =============================================================================
# SYNCHRONOUS TIMING & BACKOFF
# =============================================================================


def test_sync_backoff_timing():
    calls = 0

    @retry(attempts=3, delay=0.1, backoff=2.0)
    def func():
        nonlocal calls
        calls += 1
        raise ValueError("fail")

    start = time.monotonic()
    with pytest.raises(ValueError):
        func()
    elapsed = time.monotonic() - start

    assert elapsed == pytest.approx(0.3, abs=0.05)


# =============================================================================
# SYNCHRONOUS JITTER
# =============================================================================


def test_sync_jitter_bounds():
    calls = 0

    @retry(attempts=3, delay=0.1, jitter=0.1)
    def func():
        nonlocal calls
        calls += 1
        raise ValueError("fail")

    start = time.monotonic()
    with pytest.raises(ValueError):
        func()
    elapsed = time.monotonic() - start

    assert 0.15 <= elapsed <= 0.45


# =============================================================================
# ASYNCHRONOUS FUNCTIONALITY
# =============================================================================


@pytest.mark.asyncio
async def test_async_immediate_success():
    @retry(attempts=3, delay=0)
    async def func():
        return "ok"

    assert await func() == "ok"


@pytest.mark.asyncio
async def test_async_retry_then_success():
    calls = 0

    @retry(attempts=3, delay=0)
    async def func():
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ValueError("transient error")
        return "success"

    assert await func() == "success"
    assert calls == 3


@pytest.mark.asyncio
async def test_async_retry_exhausted():
    @retry(attempts=2, delay=0)
    async def func():
        raise ValueError("persistent error")

    with pytest.raises(ValueError, match="persistent error"):
        await func()


@pytest.mark.asyncio
async def test_async_backoff_timing():
    calls = 0

    @retry(attempts=3, delay=0.1, backoff=2.0)
    async def func():
        nonlocal calls
        calls += 1
        raise ValueError("fail")

    start = time.monotonic()
    with pytest.raises(ValueError):
        await func()
    elapsed = time.monotonic() - start

    assert elapsed == pytest.approx(0.3, abs=0.05)


# =============================================================================
# ASYNCHRONOUS CANCELLATION
# =============================================================================


@pytest.mark.asyncio
async def test_async_cancelled_error_not_retried():
    """CancelledError must propagate immediately without triggering retries."""
    calls = 0

    @retry(attempts=5, delay=2.0)
    async def func():
        nonlocal calls
        calls += 1
        await asyncio.sleep(10)

    task = asyncio.create_task(func())
    await asyncio.sleep(0.05)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

    assert calls == 1


# =============================================================================
# EDGE CASES & TYPE PRESERVATION
# =============================================================================


def test_single_attempt_no_sleep():
    """If attempts=1, no sleep should be called."""
    calls = 0

    @retry(attempts=1, delay=10.0)
    def func():
        nonlocal calls
        calls += 1
        raise ValueError("fail")

    start = time.monotonic()
    with pytest.raises(ValueError):
        func()
    elapsed = time.monotonic() - start

    assert calls == 1
    assert elapsed < 0.05


def test_backoff_zero():
    """backoff=0.0 should zero out the delay after the first sleep."""
    calls = 0

    @retry(attempts=3, delay=0.1, backoff=0.0)
    def func():
        nonlocal calls
        calls += 1
        raise ValueError("fail")

    start = time.monotonic()
    with pytest.raises(ValueError):
        func()
    elapsed = time.monotonic() - start

    assert elapsed == pytest.approx(0.1, abs=0.05)


def test_sync_remains_sync():
    @retry()
    def func():
        return 42

    assert not inspect.iscoroutinefunction(func)


def test_async_remains_async():
    @retry()
    async def func():
        return 42

    assert inspect.iscoroutinefunction(func)
