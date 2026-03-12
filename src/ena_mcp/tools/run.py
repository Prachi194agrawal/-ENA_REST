"""
MCP tools for ENA Run lookup.

Tools exposed
-------------
get_run          – Fetch metadata for a single run by accession
get_run_files    – Return download URLs (FASTQ/SRA) for a run
"""

from __future__ import annotations

import json
import logging
from typing import Any

from mcp.server import Server
from mcp.types import TextContent, Tool

from ena_mcp.client.ena_client import ENAClient, ENANotFoundError

logger = logging.getLogger(__name__)

RUN_DEFAULT_FIELDS = [
    "run_accession",
    "experiment_accession",
    "sample_accession",
    "study_accession",
    "scientific_name",
    "tax_id",
    "library_name",
    "library_strategy",
    "library_source",
    "library_selection",
    "library_layout",
    "instrument_platform",
    "instrument_model",
    "read_count",
    "base_count",
    "fastq_ftp",
    "fastq_md5",
    "first_public",
    "last_updated",
]


def register_run_tools(server: Server, client: ENAClient) -> None:
    """Register all run-related MCP tools on *server*."""

    @server.list_tools()
    async def _list() -> list[Tool]:
        return [
            Tool(
                name="get_run",
                description=(
                    "Retrieve complete metadata for a single ENA sequencing run.  "
                    "Returns library strategy, platform, read counts, and file metadata."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "accession": {
                            "type": "string",
                            "description": "ENA run accession (ERR…, SRR…, or DRR…).",
                            "pattern": "^(ERR|SRR|DRR)[0-9]+$",
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
                name="get_run_files",
                description=(
                    "Return the FTP download URLs and MD5 checksums for FASTQ / SRA files "
                    "associated with an ENA run.  Useful for programmatic data access."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "accession": {
                            "type": "string",
                            "description": "ENA run accession (ERR…, SRR…, or DRR…).",
                            "pattern": "^(ERR|SRR|DRR)[0-9]+$",
                        },
                    },
                    "required": ["accession"],
                },
            ),
        ]

    @server.call_tool()
    async def _call(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        accession: str = arguments["accession"].strip().upper()

        if name == "get_run":
            fields: list[str] | None = arguments.get("fields")
            try:
                records = await client.portal_search(
                    result="read_run",
                    accession=accession,
                    fields=fields or RUN_DEFAULT_FIELDS,
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

        if name == "get_run_files":
            try:
                urls = await client.browser_fastq_urls(accession)
                # Also fetch md5 via portal
                records = await client.portal_search(
                    result="read_run",
                    accession=accession,
                    fields=["run_accession", "fastq_ftp", "fastq_md5", "submitted_ftp", "sra_ftp"],
                    limit=1,
                )
                md5s = records[0].get("fastq_md5", "") if records else ""
                return [TextContent(type="text", text=json.dumps({
                    "accession": accession,
                    "download_urls": urls,
                    "md5_checksums": md5s.split(";") if md5s else [],
                }, indent=2))]
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
