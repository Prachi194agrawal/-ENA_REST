"""
Thread-safe TTL response cache backed by cachetools.

Usage
-----
    cache = ResponseCache(maxsize=512, ttl=300)
    cache.set("key", {"data": 1})
    value = cache.get("key")   # returns None on miss
"""

import threading
from typing import Any

from cachetools import TTLCache


class ResponseCache:
    """LRU + TTL in-memory cache for ENA HTTP responses.

    Parameters
    ----------
    maxsize:
        Maximum number of entries to keep.
    ttl:
        Time-to-live in seconds for each entry (default 5 minutes).
    """

    def __init__(self, maxsize: int = 512, ttl: float = 300.0) -> None:
        self._cache: TTLCache[str, Any] = TTLCache(maxsize=maxsize, ttl=ttl)
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: str) -> Any | None:
        """Return cached value or *None* on miss / expiry."""
        with self._lock:
            return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        """Store *value* under *key*."""
        with self._lock:
            self._cache[key] = value

    def invalidate(self, key: str) -> None:
        """Remove a single entry if it exists."""
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        """Evict all entries."""
        with self._lock:
            self._cache.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._cache)

    def __contains__(self, key: str) -> bool:
        with self._lock:
            return key in self._cache
