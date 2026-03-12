"""
Tests for run tool module.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest
from mcp.server import Server
from mcp.types import CallToolRequest, CallToolRequestParams, ListToolsRequest

from ena_mcp.tools.run import register_run_tools


async def _call_tool(server: Server, name: str, arguments: dict) -> list:
    handler = server.request_handlers[CallToolRequest]
    req = CallToolRequest(params=CallToolRequestParams(name=name, arguments=arguments))
    result = await handler(req)
    return result.root.content


async def _list_tools(server: Server) -> list:
    handler = server.request_handlers[ListToolsRequest]
    result = await handler(ListToolsRequest())
    return result.root.tools


@pytest.mark.asyncio
class TestRunTools:
    async def test_get_run_success(self, mock_client) -> None:
        server = Server("test")
        register_run_tools(server, mock_client)

        results = await _call_tool(server, "get_run", {"accession": "ERR123456"})
        data = json.loads(results[0].text)
        assert data["run_accession"] == "ERR123456"
        assert data["library_strategy"] == "WGS"

    async def test_get_run_not_found(self, mock_client) -> None:
        mock_client.portal_search = AsyncMock(return_value=[])
        server = Server("test")
        register_run_tools(server, mock_client)

        # Valid accession format but not in mock → empty results → not_found
        results = await _call_tool(server, "get_run", {"accession": "ERR999999"})
        data = json.loads(results[0].text)
        assert data["error"] == "not_found"

    async def test_get_run_files(self, mock_client) -> None:
        server = Server("test")
        register_run_tools(server, mock_client)

        results = await _call_tool(server, "get_run_files", {"accession": "ERR123456"})
        data = json.loads(results[0].text)
        assert data["accession"] == "ERR123456"
        assert len(data["download_urls"]) >= 1
        assert all(url.startswith("ftp://") for url in data["download_urls"])

    async def test_list_tools_registered(self, mock_client) -> None:
        server = Server("test")
        register_run_tools(server, mock_client)

        tools = await _list_tools(server)
        names = {t.name for t in tools}
        assert {"get_run", "get_run_files"} <= names
