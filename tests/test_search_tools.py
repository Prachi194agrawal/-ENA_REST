"""
Tests for search tool module.
"""

from __future__ import annotations

import json

import pytest
from mcp.server import Server
from mcp.types import CallToolRequest, CallToolRequestParams, ListToolsRequest

from ena_mcp.tools.search import register_search_tools


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
class TestSearchTools:
    async def test_search_ena_by_query(self, mock_client) -> None:
        server = Server("test")
        register_search_tools(server, mock_client)

        results = await _call_tool(
            server,
            "search_ena",
            {
                "result": "study",
                "query": 'scientific_name="Homo sapiens"',
                "limit": 5,
            },
        )
        data = json.loads(results[0].text)
        assert data["result_type"] == "study"
        assert "records" in data

    async def test_search_ena_with_tax_id_filter(self, mock_client) -> None:
        server = Server("test")
        register_search_tools(server, mock_client)

        results = await _call_tool(
            server,
            "search_ena",
            {
                "result": "sample",
                "tax_id": 9606,
                "limit": 10,
            },
        )
        data = json.loads(results[0].text)
        # The query should include tax_id=9606
        assert "9606" in (data.get("query") or "")

    async def test_search_ena_with_platform_filter(self, mock_client) -> None:
        server = Server("test")
        register_search_tools(server, mock_client)

        results = await _call_tool(
            server,
            "search_ena",
            {
                "result": "run",
                "instrument_platform": "ILLUMINA",
            },
        )
        data = json.loads(results[0].text)
        assert "ILLUMINA" in (data.get("query") or "")

    async def test_search_by_taxon_exact(self, mock_client) -> None:
        server = Server("test")
        register_search_tools(server, mock_client)

        results = await _call_tool(
            server,
            "search_by_taxon",
            {
                "tax_id": 9606,
                "result": "study",
                "include_subordinate_taxa": False,
            },
        )
        data = json.loads(results[0].text)
        assert data["tax_id"] == 9606
        call_args = mock_client.portal_search.call_args
        assert "tax_id=9606" in call_args.kwargs.get("query", "")

    async def test_search_by_taxon_subtree(self, mock_client) -> None:
        server = Server("test")
        register_search_tools(server, mock_client)

        await _call_tool(
            server,
            "search_by_taxon",
            {
                "tax_id": 9605,
                "result": "sample",
                "include_subordinate_taxa": True,
            },
        )
        call_args = mock_client.portal_search.call_args
        assert "tax_tree=9605" in call_args.kwargs.get("query", "")

    async def test_list_result_types(self, mock_client) -> None:
        server = Server("test")
        register_search_tools(server, mock_client)

        results = await _call_tool(server, "list_result_types", {})
        data = json.loads(results[0].text)
        assert "result_types" in data
        assert data["count"] >= 0

    async def test_list_tools_includes_all_search_tools(self, mock_client) -> None:
        server = Server("test")
        register_search_tools(server, mock_client)

        tools = await _list_tools(server)
        names = {t.name for t in tools}
        assert {"search_ena", "search_by_taxon", "list_result_types"} <= names
