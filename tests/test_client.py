"""
Unit tests for the ENAClient HTTP layer.

All network I/O is replaced by pytest-httpx mocks so these tests
run fully offline.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
from pytest_httpx import HTTPXMock

from ena_mcp.client.ena_client import (
    ENAClient,
    ENANotFoundError,
    ENARateLimitError,
    ENAServerError,
)

def _json_response(data: Any, status: int = 200) -> httpx.Response:
    return httpx.Response(
        status_code=status,
        headers={"content-type": "application/json"},
        content=json.dumps(data).encode(),
    )


def _text_response(text: str, status: int = 200) -> httpx.Response:
    return httpx.Response(
        status_code=status,
        headers={"content-type": "text/plain; charset=utf-8"},
        content=text.encode(),
    )


@pytest.mark.asyncio
class TestENAClientPortal:
    async def test_portal_search_returns_list(self, httpx_mock: HTTPXMock) -> None:
        payload = [{"study_accession": "PRJEB12345", "study_title": "Test Study"}]
        # No URL filter – matches any request (query params vary per call)
        httpx_mock.add_response(json=payload)

        async with ENAClient(cache_ttl=0) as client:
            results = await client.portal_search("study", accession="PRJEB12345")

        assert results == payload

    async def test_portal_search_404_raises_not_found(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(status_code=404)

        async with ENAClient(cache_ttl=0) as client:
            with pytest.raises(ENANotFoundError):
                await client.portal_search("study", accession="PRJXXINVALID")

    async def test_portal_search_429_raises_rate_limit(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(status_code=429)

        async with ENAClient(cache_ttl=0) as client:
            with pytest.raises(ENARateLimitError):
                await client.portal_search("study")

    async def test_portal_search_500_raises_server_error(self, httpx_mock: HTTPXMock) -> None:
        # Reusable so tenacity retries can all be matched
        httpx_mock.add_response(status_code=503, text="Service Unavailable", is_reusable=True)

        async with ENAClient(cache_ttl=0) as client:
            with pytest.raises(ENAServerError) as exc_info:
                await client.portal_search("study")
        assert exc_info.value.status_code == 503

    async def test_response_is_cached(self, httpx_mock: HTTPXMock) -> None:
        payload = [{"study_accession": "PRJEB99999"}]
        # Only one response registered – second call must hit cache
        httpx_mock.add_response(json=payload)

        async with ENAClient(cache_ttl=60) as client:
            r1 = await client.portal_search("study", accession="PRJEB99999")
            r2 = await client.portal_search("study", accession="PRJEB99999")

        assert r1 == r2 == payload
        # Only one actual HTTP call should have been made
        assert len(httpx_mock.get_requests()) == 1

    async def test_empty_list_response(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(json=[])

        async with ENAClient(cache_ttl=0) as client:
            results = await client.portal_search("run", query="nothing_matches")

        assert results == []


@pytest.mark.asyncio
class TestENAClientBrowser:
    async def test_browser_fasta(self, httpx_mock: HTTPXMock) -> None:
        fasta = ">AY123456\nATCGATCG\n"
        httpx_mock.add_response(text=fasta)

        async with ENAClient(cache_ttl=0) as client:
            result = await client.browser_fasta("AY123456")

        assert ">AY123456" in result

    async def test_browser_xml(self, httpx_mock: HTTPXMock) -> None:
        xml = "<ROOT><ACCESSION>ERS123456</ACCESSION></ROOT>"
        httpx_mock.add_response(text=xml)

        async with ENAClient(cache_ttl=0) as client:
            result = await client.browser_xml("ERS123456")

        assert "ERS123456" in result

    async def test_browser_fasta_404(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(status_code=404)

        async with ENAClient(cache_ttl=0) as client:
            with pytest.raises(ENANotFoundError):
                await client.browser_fasta("INVALID")
