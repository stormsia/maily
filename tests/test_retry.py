from __future__ import annotations

import asyncio
import random

import pytest

from mailtmapi.exceptions import (
    MailAPIError,
    MailAuthError,
    MailNotFoundError,
    MailRateLimitError,
)
from mailtmapi.utils.retry import async_retry


@pytest.fixture
def sleep_spy(monkeypatch):
    """Capture asyncio.sleep delays instead of actually sleeping."""
    delays: list[float] = []

    async def fake_sleep(delay: float) -> None:
        delays.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    return delays


async def test_returns_value_without_retry(sleep_spy):
    calls = 0

    @async_retry()
    async def ok():
        nonlocal calls
        calls += 1
        return "done"

    assert await ok() == "done"
    assert calls == 1
    assert sleep_spy == []


async def test_retries_then_succeeds(sleep_spy):
    calls = 0

    @async_retry(jitter=False)
    async def flaky():
        nonlocal calls
        calls += 1
        if calls < 3:
            raise MailAPIError("boom")
        return calls

    assert await flaky() == 3
    assert sleep_spy == [0.5, 1.0]


async def test_exhausts_attempts_and_raises_last_error(sleep_spy):
    calls = 0

    @async_retry(max_attempts=3, jitter=False)
    async def always_fail():
        nonlocal calls
        calls += 1
        raise MailAPIError(f"fail-{calls}")

    with pytest.raises(MailAPIError, match="fail-3"):
        await always_fail()
    assert calls == 3
    assert len(sleep_spy) == 2


@pytest.mark.parametrize("exc", [MailAuthError("nope"), MailNotFoundError("gone")])
async def test_non_retryable_errors_raise_immediately(sleep_spy, exc):
    calls = 0

    @async_retry(max_attempts=5)
    async def fail():
        nonlocal calls
        calls += 1
        raise exc

    with pytest.raises(type(exc)):
        await fail()
    assert calls == 1
    assert sleep_spy == []


async def test_rate_limit_retry_after_is_honored_and_capped(sleep_spy):
    calls = 0

    @async_retry(max_attempts=3, max_delay=10.0, jitter=False)
    async def limited():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise MailRateLimitError("slow down", retry_after=120.0)
        raise MailRateLimitError("again", retry_after=2.0)

    with pytest.raises(MailRateLimitError):
        await limited()
    assert sleep_spy == [10.0, 2.0]


async def test_backoff_caps_at_max_delay(sleep_spy):
    @async_retry(max_attempts=5, base_delay=1.0, max_delay=3.0, jitter=False)
    async def fail():
        raise MailAPIError("x")

    with pytest.raises(MailAPIError):
        await fail()
    assert sleep_spy == [1.0, 2.0, 3.0, 3.0]


@pytest.mark.parametrize(("rand", "expected"), [(0.0, 0.5), (1.0, 1.0)])
async def test_jitter_bounds(sleep_spy, monkeypatch, rand, expected):
    monkeypatch.setattr(random, "random", lambda: rand)

    @async_retry(max_attempts=2, base_delay=1.0, jitter=True)
    async def fail():
        raise MailAPIError("x")

    with pytest.raises(MailAPIError):
        await fail()
    assert sleep_spy == [expected]


async def test_custom_exception_tuple_is_retried(sleep_spy):
    class CustomError(Exception):
        pass

    calls = 0

    @async_retry(max_attempts=2, jitter=False, exceptions=(CustomError,))
    async def flaky():
        nonlocal calls
        calls += 1
        raise CustomError("nope")

    with pytest.raises(CustomError):
        await flaky()
    assert calls == 2


async def test_unrelated_exception_propagates(sleep_spy):
    @async_retry()
    async def boom():
        raise ValueError("not a mail error")

    with pytest.raises(ValueError, match="not a mail error"):
        await boom()
    assert sleep_spy == []


async def test_preserves_function_metadata():
    @async_retry()
    async def documented():
        """docstring"""

    assert documented.__name__ == "documented"
    assert documented.__doc__ == "docstring"


def test_max_attempts_below_one_raises_value_error():
    with pytest.raises(ValueError, match="max_attempts"):
        async_retry(max_attempts=0)
