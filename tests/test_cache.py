"""
Unit tests for the ResponseCache utility.
"""

from __future__ import annotations

import time

from ena_mcp.utils.cache import ResponseCache


class TestResponseCache:
    def test_set_and_get(self) -> None:
        cache = ResponseCache(maxsize=10, ttl=60)
        cache.set("key1", {"data": 42})
        assert cache.get("key1") == {"data": 42}

    def test_get_missing_returns_none(self) -> None:
        cache = ResponseCache(maxsize=10, ttl=60)
        assert cache.get("nonexistent") is None

    def test_ttl_expiry(self) -> None:
        cache = ResponseCache(maxsize=10, ttl=0.1)  # 100ms TTL
        cache.set("key", "value")
        assert cache.get("key") == "value"
        time.sleep(0.2)
        assert cache.get("key") is None

    def test_invalidate(self) -> None:
        cache = ResponseCache(maxsize=10, ttl=60)
        cache.set("k", 1)
        cache.invalidate("k")
        assert cache.get("k") is None

    def test_invalidate_nonexistent_is_safe(self) -> None:
        cache = ResponseCache(maxsize=10, ttl=60)
        cache.invalidate("does_not_exist")  # should not raise

    def test_clear(self) -> None:
        cache = ResponseCache(maxsize=10, ttl=60)
        for i in range(5):
            cache.set(str(i), i)
        assert len(cache) == 5
        cache.clear()
        assert len(cache) == 0

    def test_contains(self) -> None:
        cache = ResponseCache(maxsize=10, ttl=60)
        cache.set("x", 99)
        assert "x" in cache
        assert "y" not in cache

    def test_maxsize_eviction(self) -> None:
        cache = ResponseCache(maxsize=3, ttl=60)
        for i in range(5):
            cache.set(str(i), i)
        # LRU eviction means we have at most 3 entries
        assert len(cache) <= 3

    def test_overwrite(self) -> None:
        cache = ResponseCache(maxsize=10, ttl=60)
        cache.set("k", "old")
        cache.set("k", "new")
        assert cache.get("k") == "new"
