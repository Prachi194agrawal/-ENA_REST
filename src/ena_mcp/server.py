"""
ENA MCP Server – main entrypoint.

This module wires together the MCP server, the ENA HTTP client, and all
tool modules.  It uses the stdio transport so any MCP-compatible host
(Claude Desktop, VS Code Copilot, LangChain, etc.) can spawn it as a
subprocess and communicate over stdin / stdout.

Usage
-----
    # Direct
    python -m ena_mcp.server

    # Via installed script
    ena-mcp

    # With custom settings (see .env.example)
    ENA_RATE_LIMIT=3 ENA_CACHE_TTL=600 ena-mcp
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

# Load .env before anything else so env-vars are available at import time
load_dotenv()

import mcp.server.stdio as mcp_stdio
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from ena_mcp import __version__
from ena_mcp.client.ena_client import ENAClient
from ena_mcp.tools import (
    register_experiment_tools,
    register_run_tools,
    register_sample_tools,
    register_search_tools,
    register_sequence_tools,
    register_study_tools,
)

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Server factory
# ---------------------------------------------------------------------------

def create_server() -> tuple[Server, ENAClient]:
    """Instantiate the MCP server and ENA client; register all tools."""
    server = Server("ena-mcp-server")
    client = ENAClient()

    # Each register_* function attaches its own list_tools / call_tool hooks.
    # The MCP SDK merges all registered handlers internally.
    register_study_tools(server, client)
    register_sample_tools(server, client)
    register_run_tools(server, client)
    register_experiment_tools(server, client)
    register_search_tools(server, client)
    register_sequence_tools(server, client)

    # ------------------------------------------------------------------
    # Server-level prompts (optional hints for LLMs)
    # ------------------------------------------------------------------
    @server.list_prompts()
    async def _list_prompts():  # type: ignore[no-untyped-def]
        from mcp.types import Prompt, PromptArgument

        return [
            Prompt(
                name="ena_query_guide",
                description=(
                    "Guide for composing effective ENA queries.  "
                    "Explains accession formats, available result types, "
                    "and example query strings."
                ),
                arguments=[
                    PromptArgument(
                        name="topic",
                        description="Topic to focus on (accessions | query_syntax | result_types)",
                        required=False,
                    ),
                ],
            ),
        ]

    @server.get_prompt()
    async def _get_prompt(name: str, arguments: dict | None):  # type: ignore[no-untyped-def]
        from mcp.types import GetPromptResult, PromptMessage, TextContent

        if name == "ena_query_guide":
            topic = (arguments or {}).get("topic", "all")
            text = _build_query_guide(topic)
            return GetPromptResult(
                description="ENA query guide",
                messages=[PromptMessage(role="user", content=TextContent(type="text", text=text))],
            )
        raise ValueError(f"Unknown prompt: {name!r}")

    return server, client


def _build_query_guide(topic: str) -> str:  # noqa: PLR0912
    sections: list[str] = []

    if topic in ("accessions", "all"):
        sections.append("""## ENA Accession Formats

| Prefix        | Type            | Example        |
|---------------|-----------------|----------------|
| PRJ, ERP, SRP | Study/Project   | PRJEB12345     |
| ERS, SRS, DRS | Sample          | ERS123456      |
| ERX, SRX, DRX | Experiment      | ERX123456      |
| ERR, SRR, DRR | Run             | ERR123456      |
| ERP, SRP      | Submission      | ERA123456      |
| SAMEA, SAME   | BioSample       | SAMEA12345     |
""")

    if topic in ("query_syntax", "all"):
        sections.append("""## ENA Query Syntax Examples

    scientific_name="Homo sapiens"
    tax_id=9606
    tax_tree=9606                              # includes child taxa
    library_strategy=WGS
    instrument_platform=ILLUMINA
    country="United Kingdom"
    collection_date>=2020-01-01
    scientific_name="Homo sapiens" AND library_strategy=WGS
    (instrument_platform=ILLUMINA OR instrument_platform=OXFORD_NANOPORE) AND read_count>1000000
""")

    if topic in ("result_types", "all"):
        sections.append("""## Common ENA Result Types

    study       – Research projects / BioProjects
    sample      – Biological samples / BioSamples
    experiment  – Library preparation + sequencing platform
    run         – Individual sequencing runs (FASTQ files)
    sequence    – Nucleotide sequence entries
    assembly    – Genome assemblies
    analysis    – Computed analyses (SNP calls, etc.)
    taxon       – Taxonomy records
""")

    return "\n".join(sections) if sections else "No guide available for this topic."


# ---------------------------------------------------------------------------
# Async main
# ---------------------------------------------------------------------------

async def async_main() -> None:
    server, client = create_server()

    logger.info("Starting ENA MCP Server v%s", __version__)

    init_options = InitializationOptions(
        server_name="ena-mcp-server",
        server_version=__version__,
        capabilities=server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={},
        ),
    )

    try:
        async with mcp_stdio.stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, init_options)
    finally:
        await client.aclose()
        logger.info("ENA MCP Server shut down.")


def main() -> None:
    """Synchronous entry point (used by `ena-mcp` script)."""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        logger.info("Interrupted.")


if __name__ == "__main__":
    main()
