"""
MCP tools for free-text and advanced ENA search.

Tools exposed
-------------
search_ena         – Generic search across any ENA result type
search_by_taxon    – Convenience wrapper that filters by taxonomy ID
list_result_types  – Return all available ENA result types
"""

from __future__ import annotations

import json
import logging
from typing import Any

from mcp.server import Server
from mcp.types import TextContent, Tool

from ena_mcp.client.ena_client import ENAClient
from ena_mcp.schemas.search import SearchParams

logger = logging.getLogger(__name__)


def register_search_tools(server: Server, client: ENAClient) -> None:
    """Register all search-related MCP tools on *server*."""

    @server.list_tools()
    async def _list() -> list[Tool]:
        return [
            Tool(
                name="search_ena",
                description=(
                    "Perform a flexible search across any ENA data type using the "
                    "ENA Portal query syntax.  Supports free text, structured filters, "
                    "and pagination.  "
                    "Example query: 'scientific_name=\"Homo sapiens\" AND library_strategy=WGS'."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "result": {
                            "type": "string",
                            "description": (
                                "ENA result type to search.  Common values: "
                                "study, sample, run, experiment, sequence, assembly."
                            ),
                        },
                        "query": {
                            "type": "string",
                            "description": "ENA Portal query string.",
                        },
                        "fields": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Fields to include in each result record.",
                        },
                        "limit": {
                            "type": "integer",
                            "default": 20,
                            "minimum": 1,
                            "maximum": 1000,
                        },
                        "offset": {
                            "type": "integer",
                            "default": 0,
                            "minimum": 0,
                        },
                        "tax_id": {
                            "type": "integer",
                            "description": "Filter by NCBI taxonomy ID.",
                        },
                        "instrument_platform": {
                            "type": "string",
                            "description": (
                                "Filter by sequencing platform, "
                                "e.g. ILLUMINA, OXFORD_NANOPORE, PACBIO_SMRT."
                            ),
                        },
                    },
                    "required": ["result"],
                },
            ),
            Tool(
                name="search_by_taxon",
                description=(
                    "Search ENA records for a specific organism identified by its "
                    "NCBI taxonomy ID.  Returns studies, samples, runs, or experiments "
                    "depending on the result type specified."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tax_id": {
                            "type": "integer",
                            "description": "NCBI taxonomy ID (e.g. 9606 for Homo sapiens).",
                        },
                        "result": {
                            "type": "string",
                            "default": "study",
                            "description": "ENA result type (study, sample, run, experiment).",
                        },
                        "include_subordinate_taxa": {
                            "type": "boolean",
                            "default": True,
                            "description": "Include child taxa in the search.",
                        },
                        "limit": {
                            "type": "integer",
                            "default": 20,
                            "minimum": 1,
                            "maximum": 1000,
                        },
                        "offset": {
                            "type": "integer",
                            "default": 0,
                            "minimum": 0,
                        },
                    },
                    "required": ["tax_id"],
                },
            ),
            Tool(
                name="list_result_types",
                description=(
                    "Return all ENA data portal result types with their descriptions.  "
                    "Use this to discover which result types can be searched with search_ena."
                ),
                inputSchema={"type": "object", "properties": {}},
            ),
        ]

    @server.call_tool()
    async def _call(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        if name == "search_ena":
            params = SearchParams(**arguments)

            # Build compound query
            query_parts: list[str] = []
            if params.query:
                query_parts.append(params.query)
            if params.tax_id:
                query_parts.append(f"tax_id={params.tax_id}")
            if params.instrument_platform:
                query_parts.append(f"instrument_platform={params.instrument_platform}")
            compound_query = " AND ".join(query_parts) if query_parts else None

            records = await client.portal_search(
                result=params.result,
                query=compound_query,
                fields=params.fields,
                limit=params.limit,
                offset=params.offset,
            )
            return [TextContent(type="text", text=json.dumps({
                "result_type": params.result,
                "query": compound_query,
                "count": len(records),
                "offset": params.offset,
                "limit": params.limit,
                "records": records,
            }, indent=2))]

        if name == "search_by_taxon":
            tax_id: int = arguments["tax_id"]
            result: str = arguments.get("result", "study")
            include_sub: bool = arguments.get("include_subordinate_taxa", True)
            limit: int = int(arguments.get("limit", 20))
            offset: int = int(arguments.get("offset", 0))

            # tax_tree includes child taxa; tax_id is exact
            query_field = "tax_tree" if include_sub else "tax_id"
            query = f"{query_field}={tax_id}"

            records = await client.portal_search(
                result=result,
                query=query,
                limit=limit,
                offset=offset,
            )
            return [TextContent(type="text", text=json.dumps({
                "tax_id": tax_id,
                "result_type": result,
                "include_subordinate_taxa": include_sub,
                "count": len(records),
                "offset": offset,
                "limit": limit,
                "records": records,
            }, indent=2))]

        if name == "list_result_types":
            result_types = await client.get_results()
            return [TextContent(type="text", text=json.dumps({
                "count": len(result_types),
                "result_types": result_types,
            }, indent=2))]

        return [TextContent(type="text", text=json.dumps({
            "error": "unknown_tool",
            "message": f"Tool {name!r} is not handled by this module.",
        }))]
