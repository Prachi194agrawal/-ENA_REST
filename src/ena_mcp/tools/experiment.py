"""
MCP tools for ENA Experiment lookup.

Tools exposed
-------------
get_experiment – Fetch metadata for a single experiment by accession
"""

from __future__ import annotations

import json
import logging
from typing import Any

from mcp.server import Server
from mcp.types import TextContent, Tool

from ena_mcp.client.ena_client import ENAClient, ENANotFoundError

logger = logging.getLogger(__name__)

EXPERIMENT_DEFAULT_FIELDS = [
    "experiment_accession",
    "study_accession",
    "sample_accession",
    "experiment_title",
    "description",
    "library_name",
    "library_strategy",
    "library_source",
    "library_selection",
    "library_layout",
    "instrument_platform",
    "instrument_model",
    "scientific_name",
    "tax_id",
    "first_public",
    "last_updated",
]


def register_experiment_tools(server: Server, client: ENAClient) -> None:
    """Register all experiment-related MCP tools on *server*."""

    @server.list_tools()
    async def _list() -> list[Tool]:
        return [
            Tool(
                name="get_experiment",
                description=(
                    "Retrieve metadata for a single ENA experiment.  "
                    "Returns library design, sequencing platform, and linked accessions."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "accession": {
                            "type": "string",
                            "description": "ENA experiment accession (ERX…, SRX…, or DRX…).",
                            "pattern": "^(ERX|SRX|DRX)[0-9]+$",
                        },
                        "fields": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional specific fields to return.",
                        },
                    },
                    "required": ["accession"],
                },
            ),
        ]

    @server.call_tool()
    async def _call(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        if name == "get_experiment":
            accession: str = arguments["accession"].strip().upper()
            fields: list[str] | None = arguments.get("fields")
            try:
                records = await client.portal_search(
                    result="read_experiment",
                    accession=accession,
                    fields=fields or EXPERIMENT_DEFAULT_FIELDS,
                    limit=1,
                )
                if not records:
                    raise ENANotFoundError(accession)
                return [TextContent(type="text", text=json.dumps(records[0], indent=2))]
            except ENANotFoundError as exc:
                return [TextContent(type="text", text=json.dumps({
                    "error": "not_found",
                    "message": str(exc),
                    "accession": accession,
                }))]

        return [TextContent(type="text", text=json.dumps({
            "error": "unknown_tool",
            "message": f"Tool {name!r} is not handled by this module.",
        }))]
