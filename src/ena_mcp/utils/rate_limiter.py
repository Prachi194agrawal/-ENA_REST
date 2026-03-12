"""
Token-bucket rate limiter for ENA HTTP requests.

ENA asks clients to be polite – this limiter ensures we never exceed
a configurable request-per-second threshold.

Usage
-----
    limiter = RateLimiter(rate=5.0, burst=10)
    async with limiter:        # waits if necessary
        response = await client.get(...)
"""

import asyncio
import time


class RateLimiter:
    """Async token-bucket rate limiter.

    Parameters
    ----------
    rate:
        Sustained requests per second (tokens refilled per second).
    burst:
        Maximum burst size (bucket capacity).
    """

    def __init__(self, rate: float = 5.0, burst: float = 10.0) -> None:
        if rate <= 0:
            raise ValueError("rate must be positive")
        if burst <= 0:
            raise ValueError("burst must be positive")
        self._rate = rate
        self._burst = burst
        self._tokens: float = burst
        self._last_refill: float = time.monotonic()
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _refill(self) -> None:
        """Refill tokens proportional to elapsed time (called under lock)."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._burst, self._tokens + elapsed * self._rate)
        self._last_refill = now

    # ------------------------------------------------------------------
    # Async context-manager API
    # ------------------------------------------------------------------

    async def acquire(self) -> None:
        """Block asynchronously until a token is available."""
        async with self._lock:
            self._refill()
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return
            # Calculate precise sleep time
            deficit = 1.0 - self._tokens
            sleep_time = deficit / self._rate
            await asyncio.sleep(sleep_time)
            self._refill()
            self._tokens -= 1.0

    async def __aenter__(self) -> "RateLimiter":
        await self.acquire()
        return self

    async def __aexit__(self, *_: object) -> None:
        pass
