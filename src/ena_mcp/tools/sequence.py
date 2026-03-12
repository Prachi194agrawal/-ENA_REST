"""
MCP tools for ENA sequence / nucleotide record retrieval.

Tools exposed
-------------
get_sequence       – Fetch FASTA sequence for an accession
get_record_xml     – Fetch full XML record for any accession
get_taxonomy_info  – Fetch taxonomy record by NCBI tax ID
"""

from __future__ import annotations

import json
import logging
from typing import Any

from mcp.server import Server
from mcp.types import TextContent, Tool

from ena_mcp.client.ena_client import ENAClient, ENANotFoundError

logger = logging.getLogger(__name__)


def register_sequence_tools(server: Server, client: ENAClient) -> None:
    """Register sequence / browser tools on *server*."""

    @server.list_tools()
    async def _list() -> list[Tool]:
        return [
            Tool(
                name="get_sequence",
                description=(
                    "Retrieve the FASTA nucleotide sequence for an ENA accession.  "
                    "Works for sequence entries (e.g. AY123456), assemblies, and WGS sets."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "accession": {
                            "type": "string",
                            "description": "ENA sequence accession, e.g. AY123456 or LN999999.",
                        },
                    },
                    "required": ["accession"],
                },
            ),
            Tool(
                name="get_record_xml",
                description=(
                    "Fetch the full XML representation of any ENA record.  "
                    "Useful for retrieving complete metadata not available via the Portal API."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "accession": {
                            "type": "string",
                            "description": "Any valid ENA accession.",
                        },
                    },
                    "required": ["accession"],
                },
            ),
            Tool(
                name="get_taxonomy_info",
                description=(
                    "Retrieve ENA taxonomy records for a given NCBI taxonomy ID.  "
                    "Returns scientific name, rank, and lineage."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tax_id": {
                            "type": "integer",
                            "description": "NCBI taxonomy ID (e.g. 9606 for Homo sapiens).",
                        },
                    },
                    "required": ["tax_id"],
                },
            ),
        ]

    @server.call_tool()
    async def _call(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        if name == "get_sequence":
            accession: str = arguments["accession"].strip().upper()
            try:
                fasta = await client.browser_fasta(accession)
                return [TextContent(type="text", text=json.dumps({
                    "accession": accession,
                    "format": "fasta",
                    "sequence": fasta,
                }, indent=2))]
            except ENANotFoundError as exc:
                return [TextContent(type="text", text=json.dumps({
                    "error": "not_found",
                    "message": str(exc),
                    "accession": accession,
                }))]

        if name == "get_record_xml":
            accession = arguments["accession"].strip().upper()
            try:
                xml = await client.browser_xml(accession)
                return [TextContent(type="text", text=json.dumps({
                    "accession": accession,
                    "format": "xml",
                    "record": xml,
                }, indent=2))]
            except ENANotFoundError as exc:
                return [TextContent(type="text", text=json.dumps({
                    "error": "not_found",
                    "message": str(exc),
                    "accession": accession,
                }))]

        if name == "get_taxonomy_info":
            tax_id: int = int(arguments["tax_id"])
            records = await client.get_taxonomy(tax_id)
            if not records:
                return [TextContent(type="text", text=json.dumps({
                    "error": "not_found",
                    "message": f"No taxonomy records found for tax_id={tax_id}",
                    "tax_id": tax_id,
                }))]
            return [TextContent(type="text", text=json.dumps({
                "tax_id": tax_id,
                "count": len(records),
                "records": records,
            }, indent=2))]

        return [TextContent(type="text", text=json.dumps({
            "error": "unknown_tool",
            "message": f"Tool {name!r} is not handled by this module.",
        }))]
