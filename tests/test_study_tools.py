"""
Integration-style tests for ENA study tools.

Uses a mock ENAClient so no real HTTP calls are made.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest
from mcp.server import Server
from mcp.types import CallToolRequest, CallToolRequestParams, ListToolsRequest

from ena_mcp.tools.study import register_study_tools


async def _call_tool(server: Server, name: str, arguments: dict) -> list:
    """Helper: invoke a registered call_tool handler via the MCP request type."""
    handler = server.request_handlers[CallToolRequest]
    req = CallToolRequest(params=CallToolRequestParams(name=name, arguments=arguments))
    result = await handler(req)
    return result.root.content


async def _list_tools(server: Server) -> list:
    handler = server.request_handlers[ListToolsRequest]
    result = await handler(ListToolsRequest())
    return result.root.tools


@pytest.mark.asyncio
class TestStudyTools:
    async def test_get_study_success(self, mock_client) -> None:
        server = Server("test")
        register_study_tools(server, mock_client)

        results = await _call_tool(server, "get_study", {"accession": "PRJEB12345"})
        assert results
        data = json.loads(results[0].text)
        assert data["study_accession"] == "PRJEB12345"
        assert data["study_title"] == "Whole-genome sequencing of Homo sapiens"

    async def test_get_study_not_found(self, mock_client) -> None:
        mock_client.portal_search = AsyncMock(return_value=[])
        server = Server("test")
        register_study_tools(server, mock_client)

        results = await _call_tool(server, "get_study", {"accession": "PRJEBNOTREAL"})
        data = json.loads(results[0].text)
        assert data["error"] == "not_found"

    async def test_list_study_runs(self, mock_client) -> None:
        server = Server("test")
        register_study_tools(server, mock_client)

        results = await _call_tool(
            server, "list_study_runs",
            {"study_accession": "PRJEB12345", "limit": 5},
        )
        data = json.loads(results[0].text)
        assert "runs" in data
        assert data["study_accession"] == "PRJEB12345"
        assert data["limit"] == 5

    async def test_list_study_samples(self, mock_client) -> None:
        server = Server("test")
        register_study_tools(server, mock_client)

        results = await _call_tool(
            server, "list_study_samples",
            {"study_accession": "PRJEB12345"},
        )
        data = json.loads(results[0].text)
        assert "samples" in data

    async def test_list_tools_registered(self, mock_client) -> None:
        server = Server("test")
        register_study_tools(server, mock_client)

        tools = await _list_tools(server)
        names = [t.name for t in tools]
        assert "get_study" in names
        assert "list_study_runs" in names
        assert "list_study_samples" in names
