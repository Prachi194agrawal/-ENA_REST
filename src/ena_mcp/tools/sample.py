"""
MCP tools for ENA Sample / BioSample lookup.

Tools exposed
-------------
get_sample      – Fetch metadata for a single sample by accession
search_samples  – Search samples with flexible filters
"""

from __future__ import annotations

import json
import logging
from typing import Any

from mcp.server import Server
from mcp.types import TextContent, Tool

from ena_mcp.client.ena_client import ENAClient, ENANotFoundError

logger = logging.getLogger(__name__)

SAMPLE_DEFAULT_FIELDS = [
    "sample_accession",
    "secondary_sample_accession",
    "biosample_accession",
    "sample_title",
    "sample_description",
    "scientific_name",
    "tax_id",
    "strain",
    "collection_date",
    "country",
    "geographic_location_latitude",
    "geographic_location_longitude",
    "environmental_sample",
    "tissue_type",
    "center_name",
    "first_public",
    "last_updated",
    "study_accession",
]


def register_sample_tools(server: Server, client: ENAClient) -> None:
    """Register all sample-related MCP tools on *server*."""

    @server.list_tools()
    async def _list() -> list[Tool]:
        return [
            Tool(
                name="get_sample",
                description=(
                    "Retrieve full metadata for a single ENA sample using its accession.  "
                    "Returns organism info, collection context, geographic coordinates, and more."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "accession": {
                            "type": "string",
                            "description": "ENA sample accession (ERS…) or BioSample (SAMEA…, SAME…).",
                        },
                        "fields": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional specific metadata fields.",
                        },
                    },
                    "required": ["accession"],
                },
            ),
            Tool(
                name="search_samples",
                description=(
                    "Search ENA samples using free-text or structured queries.  "
                    "Supports filtering by organism, collection date, country, and more."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "ENA query string, e.g. "
                                "'scientific_name=\"Homo sapiens\" AND country=United Kingdom'."
                            ),
                        },
                        "tax_id": {
                            "type": "integer",
                            "description": "Filter by NCBI taxonomy ID.",
                        },
                        "country": {
                            "type": "string",
                            "description": "Filter by country of collection.",
                        },
                        "environmental": {
                            "type": "boolean",
                            "description": "Return only environmental / metagenome samples.",
                        },
                        "fields": {
                            "type": "array",
                            "items": {"type": "string"},
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
                },
            ),
        ]

    @server.call_tool()
    async def _call(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        if name == "get_sample":
            accession: str = arguments["accession"]
            fields: list[str] | None = arguments.get("fields")
            try:
                records = await client.portal_search(
                    result="sample",
                    accession=accession.strip(),
                    fields=fields or SAMPLE_DEFAULT_FIELDS,
                    limit=1,
                )
                if not records:
                    raise ENANotFoundError(accession)
                return [TextContent(type="text", text=json.dumps(records[0], indent=2))]
            except ENANotFoundError as exc:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "error": "not_found",
                                "message": str(exc),
                                "accession": accession,
                            }
                        ),
                    )
                ]

        if name == "search_samples":
            # Build query from composite filters
            query_parts: list[str] = []
            if raw_q := arguments.get("query"):
                query_parts.append(raw_q)
            if tax_id := arguments.get("tax_id"):
                query_parts.append(f"tax_id={tax_id}")
            if country := arguments.get("country"):
                query_parts.append(f'country="{country}"')
            if arguments.get("environmental"):
                query_parts.append("environmental_sample=true")

            query = " AND ".join(query_parts) if query_parts else None
            fields = arguments.get("fields") or SAMPLE_DEFAULT_FIELDS
            limit = int(arguments.get("limit", 20))
            offset = int(arguments.get("offset", 0))

            records = await client.portal_search(
                result="sample",
                query=query,
                fields=fields,
                limit=limit,
                offset=offset,
            )
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "query": query,
                            "count": len(records),
                            "offset": offset,
                            "limit": limit,
                            "samples": records,
                        },
                        indent=2,
                    ),
                )
            ]

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": "unknown_tool",
                        "message": f"Tool {name!r} is not handled by this module.",
                    }
                ),
            )
        ]
