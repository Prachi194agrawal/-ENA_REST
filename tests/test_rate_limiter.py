"""
Unit tests for the token-bucket RateLimiter.
"""

from __future__ import annotations

import asyncio
import time

import pytest

from ena_mcp.utils.rate_limiter import RateLimiter


class TestRateLimiter:
    @pytest.mark.asyncio
    async def test_single_acquire_succeeds(self) -> None:
        limiter = RateLimiter(rate=10.0, burst=10.0)
        # Should not block
        start = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - start
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_burst_exhaustion_causes_wait(self) -> None:
        limiter = RateLimiter(rate=100.0, burst=2.0)
        # Drain the burst
        await limiter.acquire()
        await limiter.acquire()
        # Third call must wait
        start = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - start
        # Should have waited at least 1/rate seconds
        assert elapsed >= 0.005  # generous lower bound to avoid flakiness

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        limiter = RateLimiter(rate=10.0, burst=10.0)
        async with limiter:
            pass  # just ensure it doesn't raise

    def test_invalid_rate_raises(self) -> None:
        with pytest.raises(ValueError, match="rate must be positive"):
            RateLimiter(rate=0.0)

    def test_invalid_burst_raises(self) -> None:
        with pytest.raises(ValueError, match="burst must be positive"):
            RateLimiter(rate=5.0, burst=0.0)

    @pytest.mark.asyncio
    async def test_high_rate_allows_many_concurrent(self) -> None:
        """At a very high rate, many acquires complete quickly."""
        limiter = RateLimiter(rate=1000.0, burst=50.0)
        start = time.monotonic()
        for _ in range(10):
            await limiter.acquire()
        elapsed = time.monotonic() - start
        assert elapsed < 0.5
