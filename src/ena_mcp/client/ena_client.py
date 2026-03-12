"""
Async HTTP client for the ENA Portal and Browser REST APIs.

Features
--------
* Automatic retry with exponential back-off (tenacity)
* Token-bucket rate limiting (polite ENA citizen)
* TTL response cache (reduces redundant network calls)
* Structured error handling with descriptive exceptions

ENA base URLs
-------------
Portal API  – https://www.ebi.ac.uk/ena/portal/api
Browser API – https://www.ebi.ac.uk/ena/browser/api
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Any

import httpx
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ena_mcp.utils.cache import ResponseCache
from ena_mcp.utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants / defaults (overridable via environment variables)
# ---------------------------------------------------------------------------

PORTAL_BASE = os.getenv("ENA_PORTAL_BASE", "https://www.ebi.ac.uk/ena/portal/api")
BROWSER_BASE = os.getenv("ENA_BROWSER_BASE", "https://www.ebi.ac.uk/ena/browser/api")
DEFAULT_TIMEOUT = float(os.getenv("ENA_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("ENA_MAX_RETRIES", "3"))
RATE_LIMIT = float(os.getenv("ENA_RATE_LIMIT", "5"))   # req/s
CACHE_TTL = float(os.getenv("ENA_CACHE_TTL", "300"))    # seconds
CACHE_SIZE = int(os.getenv("ENA_CACHE_SIZE", "512"))


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class ENAClientError(Exception):
    """Base class for all ENA client errors."""


class ENANotFoundError(ENAClientError):
    """Raised when ENA returns HTTP 404."""

    def __init__(self, accession: str) -> None:
        super().__init__(f"ENA record not found: {accession!r}")
        self.accession = accession


class ENARateLimitError(ENAClientError):
    """Raised when ENA returns HTTP 429."""

    def __init__(self) -> None:
        super().__init__("ENA rate limit exceeded – retry after a moment")


class ENAServerError(ENAClientError):
    """Raised for 5xx responses from ENA."""

    def __init__(self, status_code: int, body: str) -> None:
        super().__init__(f"ENA server error {status_code}: {body[:200]}")
        self.status_code = status_code


# ---------------------------------------------------------------------------
# Retry predicate helpers
# ---------------------------------------------------------------------------

def _is_retryable(exc: BaseException) -> bool:
    """Only retry on transient network / server errors."""
    return isinstance(exc, (httpx.TransportError, ENAServerError))


# ---------------------------------------------------------------------------
# Main client
# ---------------------------------------------------------------------------

class ENAClient:
    """Async HTTP client for ENA REST services.

    Parameters
    ----------
    cache_ttl:
        Cache entry TTL in seconds.
    cache_size:
        Maximum number of cached responses.
    rate_limit:
        Maximum requests per second.
    timeout:
        HTTP request timeout in seconds.
    """

    def __init__(
        self,
        *,
        cache_ttl: float = CACHE_TTL,
        cache_size: int = CACHE_SIZE,
        rate_limit: float = RATE_LIMIT,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._cache = ResponseCache(maxsize=cache_size, ttl=cache_ttl)
        self._limiter = RateLimiter(rate=rate_limit, burst=max(rate_limit * 2, 10))
        self._http = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "Accept": "*/*",
                "User-Agent": "ena-mcp-server/0.1.0 (GSoC 2026)",
            },
            follow_redirects=True,
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self._http.aclose()

    async def __aenter__(self) -> "ENAClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    # ------------------------------------------------------------------
    # Low-level fetch helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _cache_key(url: str, params: dict[str, Any]) -> str:
        serialised = json.dumps({"url": url, "params": params}, sort_keys=True)
        return hashlib.sha256(serialised.encode()).hexdigest()

    async def _get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        *,
        use_cache: bool = True,
    ) -> Any:
        """Core GET with rate limiting, caching, and retry logic."""
        params = params or {}
        cache_key = self._cache_key(url, params)

        if use_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                logger.debug("Cache hit: %s", cache_key[:12])
                return cached

        result = await self._fetch_with_retry(url, params)

        if use_cache:
            self._cache.set(cache_key, result)

        return result

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, ENAServerError)),
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _fetch_with_retry(self, url: str, params: dict[str, Any]) -> Any:
        """Single HTTP GET attempt; wrapped by tenacity for retries."""
        async with self._limiter:
            logger.debug("GET %s params=%s", url, params)
            response = await self._http.get(url, params=params)

        return self._handle_response(response)

    @staticmethod
    def _handle_response(response: httpx.Response) -> Any:
        """Raise structured errors or parse and return JSON / text."""
        if response.status_code == 404:
            # Try to extract accession from URL path
            path_parts = response.url.path.rstrip("/").split("/")
            accession = path_parts[-1] if path_parts else "unknown"
            raise ENANotFoundError(accession)

        if response.status_code == 429:
            raise ENARateLimitError()

        if response.status_code >= 500:
            raise ENAServerError(response.status_code, response.text)

        response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if "json" in content_type:
            return response.json()
        return response.text

    # ------------------------------------------------------------------
    # Portal API – structured JSON queries
    # ------------------------------------------------------------------

    async def portal_search(
        self,
        result: str,
        *,
        query: str | None = None,
        accession: str | None = None,
        fields: list[str] | None = None,
        limit: int = 20,
        offset: int = 0,
        format: str = "json",
    ) -> list[dict[str, Any]]:
        """Query the ENA Portal search API.

        Parameters
        ----------
        result:
            Result type: ``study``, ``sample``, ``run``, ``experiment``,
            ``analysis``, ``sequence``, ``assembly``, ``taxon``.
        query:
            Free-text or structured EMBL-EBI query string.
        accession:
            ENA accession (e.g. ``PRJEB12345``, ``ERS123456``).
        fields:
            List of fields to return.  Defaults to a sensible preset.
        limit:
            Maximum records to return (1–1000).
        offset:
            Pagination offset.
        format:
            Response format.  Only ``"json"`` is supported here.
        """
        params: dict[str, Any] = {
            "result": result,
            "limit": min(max(limit, 1), 1000),
            "offset": max(offset, 0),
            "format": format,
        }
        if query:
            params["query"] = query
        if accession:
            params["accession"] = accession
        if fields:
            params["fields"] = ",".join(fields)

        url = f"{PORTAL_BASE}/search"
        data = await self._get(url, params)

        # Portal returns a list of dicts
        if isinstance(data, list):
            return data
        # Some edge cases return a single dict or empty string
        if isinstance(data, dict):
            return [data]
        return []

    async def get_fields(self, result: str) -> list[dict[str, Any]]:
        """Return available fields for a given result type."""
        url = f"{PORTAL_BASE}/returnFields"
        data = await self._get(url, {"result": result})
        return data if isinstance(data, list) else []

    async def get_results(self) -> list[dict[str, Any]]:
        """Return all available ENA result types."""
        url = f"{PORTAL_BASE}/results"
        data = await self._get(url, {"dataPortalType": "sequence", "format": "json"})
        return data if isinstance(data, list) else []

    # ------------------------------------------------------------------
    # Browser API – raw record formats
    # ------------------------------------------------------------------

    async def browser_xml(self, accession: str) -> str:
        """Fetch an accession's full XML record from the ENA Browser."""
        url = f"{BROWSER_BASE}/xml/{accession}"
        data = await self._get(url, {})
        return str(data)

    async def browser_fasta(self, accession: str) -> str:
        """Fetch FASTA sequence(s) for a given accession."""
        url = f"{BROWSER_BASE}/fasta/{accession}"
        data = await self._get(url, {})
        return str(data)

    async def browser_fastq_urls(self, accession: str) -> list[str]:
        """Return FTP FASTQ download URLs for a run accession."""
        records = await self.portal_search(
            "read_run",
            accession=accession,
            fields=["fastq_ftp", "submitted_ftp", "sra_ftp"],
            limit=1,
        )
        if not records:
            raise ENANotFoundError(accession)
        rec = records[0]
        urls: list[str] = []
        for field in ("fastq_ftp", "submitted_ftp", "sra_ftp"):
            raw = rec.get(field, "")
            if raw:
                urls.extend(f"ftp://{u}" for u in raw.split(";") if u)
        return urls

    # ------------------------------------------------------------------
    # Taxonomy helpers
    # ------------------------------------------------------------------

    async def get_taxonomy(self, tax_id: str | int) -> list[dict[str, Any]]:
        """Search ENA records by NCBI taxonomy ID."""
        return await self.portal_search(
            "taxon",
            query=f"tax_id={tax_id}",
            fields=["tax_id", "scientific_name", "lineage", "rank"],
        )
