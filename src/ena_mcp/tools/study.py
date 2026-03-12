"""
MCP tools for ENA Study / Project lookup.

Tools exposed
-------------
get_study          – Fetch metadata for a single study by accession
list_study_runs    – List all runs belonging to a study
list_study_samples – List all samples belonging to a study
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.server import Server
from mcp.types import TextContent, Tool

from ena_mcp.client.ena_client import ENAClient, ENANotFoundError
from ena_mcp.schemas.study import StudySearchParams

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default fields returned when the caller does not specify
# ---------------------------------------------------------------------------

STUDY_DEFAULT_FIELDS = [
    "study_accession",
    "secondary_study_accession",
    "bioproject_accession",
    "study_title",
    "study_type",
    "description",
    "center_name",
    "tax_id",
    "scientific_name",
    "first_public",
    "last_updated",
    "experiment_count",
    "run_count",
    "sample_count",
]

STUDY_RUN_FIELDS = [
    "run_accession",
    "experiment_accession",
    "instrument_platform",
    "instrument_model",
    "library_strategy",
    "library_layout",
    "read_count",
    "base_count",
    "first_public",
]

STUDY_SAMPLE_FIELDS = [
    "sample_accession",
    "secondary_sample_accession",
    "scientific_name",
    "tax_id",
    "sample_title",
    "collection_date",
    "country",
    "first_public",
]


# ---------------------------------------------------------------------------
# Tool logic helpers
# ---------------------------------------------------------------------------

async def _get_study(client: ENAClient, accession: str, fields: list[str] | None) -> dict[str, Any]:
    """Fetch a single study record and return a normalised dict."""
    records = await client.portal_search(
        result="study",
        accession=accession.strip().upper(),
        fields=fields or STUDY_DEFAULT_FIELDS,
        limit=1,
    )
    if not records:
        raise ENANotFoundError(accession)
    return records[0]


async def _list_study_runs(
    client: ENAClient,
    study_accession: str,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    return await client.portal_search(
        result="read_run",
        query=f"study_accession={study_accession.strip().upper()}",
        fields=STUDY_RUN_FIELDS,
        limit=limit,
        offset=offset,
    )


async def _list_study_samples(
    client: ENAClient,
    study_accession: str,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    return await client.portal_search(
        result="sample",
        query=f"study_accession={study_accession.strip().upper()}",
        fields=STUDY_SAMPLE_FIELDS,
        limit=limit,
        offset=offset,
    )


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------

def register_study_tools(server: Server, client: ENAClient) -> None:  # noqa: C901
    """Register all study-related MCP tools on *server*."""

    @server.list_tools()
    async def _list() -> list[Tool]:
        return [
            Tool(
                name="get_study",
                description=(
                    "Fetch comprehensive metadata for a single ENA study / project "
                    "using its accession number.  "
                    "Returns title, organism, run/sample counts, dates, and more."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "accession": {
                            "type": "string",
                            "description": (
                                "ENA study accession, e.g. PRJEB12345, ERP001234, or SRP012345."
                            ),
                            "pattern": "^(PRJ|ERP|SRP|DRP)[A-Z0-9]+$",
                        },
                        "fields": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of specific fields to return.",
                        },
                    },
                    "required": ["accession"],
                },
            ),
            Tool(
                name="list_study_runs",
                description=(
                    "List sequencing runs associated with an ENA study. "
                    "Supports pagination via limit and offset."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "study_accession": {
                            "type": "string",
                            "description": "ENA study accession (PRJEB…, ERP…, SRP…).",
                        },
                        "limit": {
                            "type": "integer",
                            "default": 20,
                            "minimum": 1,
                            "maximum": 1000,
                            "description": "Page size.",
                        },
                        "offset": {
                            "type": "integer",
                            "default": 0,
                            "minimum": 0,
                            "description": "Pagination offset.",
                        },
                    },
                    "required": ["study_accession"],
                },
            ),
            Tool(
                name="list_study_samples",
                description=(
                    "List samples linked to an ENA study.  "
                    "Returns sample accessions, organism info, collection context, and dates."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "study_accession": {
                            "type": "string",
                            "description": "ENA study accession.",
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
                    "required": ["study_accession"],
                },
            ),
        ]

    @server.call_tool()
    async def _call(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        import json

        if name == "get_study":
            params = StudySearchParams(**arguments)
            try:
                record = await _get_study(client, params.accession, params.fields)
                return [TextContent(type="text", text=json.dumps(record, indent=2))]
            except ENANotFoundError as exc:
                return [TextContent(type="text", text=json.dumps({
                    "error": "not_found",
                    "message": str(exc),
                    "accession": params.accession,
                }))]

        if name == "list_study_runs":
            acc = arguments["study_accession"]
            limit = int(arguments.get("limit", 20))
            offset = int(arguments.get("offset", 0))
            try:
                runs = await _list_study_runs(client, acc, limit, offset)
                return [TextContent(type="text", text=json.dumps({
                    "study_accession": acc,
                    "count": len(runs),
                    "offset": offset,
                    "limit": limit,
                    "runs": runs,
                }, indent=2))]
            except ENANotFoundError as exc:
                return [TextContent(type="text", text=json.dumps({
                    "error": "not_found", "message": str(exc),
                }))]

        if name == "list_study_samples":
            acc = arguments["study_accession"]
            limit = int(arguments.get("limit", 20))
            offset = int(arguments.get("offset", 0))
            try:
                samples = await _list_study_samples(client, acc, limit, offset)
                return [TextContent(type="text", text=json.dumps({
                    "study_accession": acc,
                    "count": len(samples),
                    "offset": offset,
                    "limit": limit,
                    "samples": samples,
                }, indent=2))]
            except ENANotFoundError as exc:
                return [TextContent(type="text", text=json.dumps({
                    "error": "not_found", "message": str(exc),
                }))]

        return [TextContent(type="text", text=json.dumps({
            "error": "unknown_tool",
            "message": f"Tool {name!r} is not handled by this module.",
        }))]
