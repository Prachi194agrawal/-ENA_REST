"""
ENA MCP Server – live demo script.

Calls each tool directly (bypassing MCP transport) and pretty-prints
the output so you can see real ENA data in your terminal.

Usage
-----
    python demo.py                    # runs all demos
    python demo.py study              # only study tools
    python demo.py sample run search  # multiple sections
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from ena_mcp.client.ena_client import ENAClient, ENANotFoundError

console = Console()

# ── Real ENA accessions used in the demo ────────────────────────
DEMO_STUDY = "PRJEB1787"          # 1000 Genomes project
DEMO_SAMPLE = "ERS000002"         # 1000 Genomes sample
DEMO_RUN = "ERR000001"            # 1000 Genomes run
DEMO_EXPERIMENT = "ERX000002"     # 1000 Genomes experiment
DEMO_TAX_ID = 9606                # Homo sapiens
DEMO_SEQUENCE = "X60065"          # Human BRCA1 sequence entry


def _section(title: str) -> None:
    console.rule(f"[bold cyan]{title}[/bold cyan]")


def _print_json(label: str, data: Any) -> None:
    text = json.dumps(data, indent=2, default=str)
    console.print(Panel(
        Syntax(text, "json", theme="monokai", word_wrap=True),
        title=f"[bold green]{label}[/bold green]",
        expand=False,
    ))


# ── Individual demo functions ────────────────────────────────────

async def demo_study(client: ENAClient) -> None:
    _section("📚  Study / Project Tools")

    console.print(f"[yellow]▶ get_study({DEMO_STUDY})[/yellow]")
    study = await client.portal_search(
        result="study",
        accession=DEMO_STUDY,
        fields=[
            "study_accession", "secondary_study_accession",
            "study_title", "first_public", "last_updated",
        ],
        limit=1,
    )
    _print_json("Study metadata", study[0] if study else {})

    console.print(f"\n[yellow]▶ list_study_runs({DEMO_STUDY}, limit=3)[/yellow]")
    runs = await client.portal_search(
        result="read_run",
        query=f"study_accession={DEMO_STUDY}",
        fields=["run_accession", "instrument_platform", "library_strategy", "read_count"],
        limit=3,
    )
    _print_json("First 3 runs", runs)

    console.print(f"\n[yellow]▶ list_study_samples({DEMO_STUDY}, limit=3)[/yellow]")
    samples = await client.portal_search(
        result="sample",
        query=f"study_accession={DEMO_STUDY}",
        fields=["sample_accession", "scientific_name", "country", "collection_date"],
        limit=3,
    )
    _print_json("First 3 samples", samples)


async def demo_sample(client: ENAClient) -> None:
    _section("🧬  Sample Tools")

    console.print(f"[yellow]▶ get_sample({DEMO_SAMPLE})[/yellow]")
    records = await client.portal_search(
        result="sample",
        accession=DEMO_SAMPLE,
        fields=[
            "sample_accession", "sample_title", "scientific_name",
            "tax_id", "country", "collection_date",
        ],
        limit=1,
    )
    _print_json("Sample metadata", records[0] if records else {})

    console.print("\n[yellow]▶ search_samples(scientific_name=Homo sapiens, country=UK, limit=3)[/yellow]")
    results = await client.portal_search(
        result="sample",
        query='scientific_name="Homo sapiens" AND country="United Kingdom"',
        fields=["sample_accession", "scientific_name", "country", "collection_date"],
        limit=3,
    )
    _print_json("UK Homo sapiens samples", results)


async def demo_run(client: ENAClient) -> None:
    _section("🔬  Run Tools")

    console.print(f"[yellow]▶ get_run({DEMO_RUN})[/yellow]")
    records = await client.portal_search(
        result="read_run",
        accession=DEMO_RUN,
        fields=[
            "run_accession", "study_accession", "instrument_platform",
            "instrument_model", "library_strategy", "library_layout",
            "read_count", "base_count", "first_public",
        ],
        limit=1,
    )
    _print_json("Run metadata", records[0] if records else {})

    console.print(f"\n[yellow]▶ get_run_files({DEMO_RUN})[/yellow]")
    try:
        urls = await client.browser_fastq_urls(DEMO_RUN)
        _print_json("Download URLs", {"accession": DEMO_RUN, "urls": urls[:4]})
    except ENANotFoundError:
        console.print("[dim]  (no FASTQ files registered for this run)[/dim]")


async def demo_search(client: ENAClient) -> None:
    _section("🔍  Search Tools")

    console.print("[yellow]▶ search_ena(result=study, query='Homo sapiens WGS', limit=5)[/yellow]")
    results = await client.portal_search(
        result="study",
        query='scientific_name="Homo sapiens"',
        fields=["study_accession", "study_title", "first_public"],
        limit=5,
    )
    # Show as a table
    tbl = Table(title="Studies – Homo sapiens", show_lines=True)
    tbl.add_column("Accession", style="cyan")
    tbl.add_column("Title", max_width=65)
    tbl.add_column("Public", style="dim")
    for r in results:
        tbl.add_row(
            r.get("study_accession", ""),
            (r.get("study_title") or "")[:65],
            r.get("first_public", ""),
        )
    console.print(tbl)

    console.print(f"\n[yellow]▶ search_by_taxon(tax_id={DEMO_TAX_ID}, result=study, subtree=True, limit=3)[/yellow]")
    tax_results = await client.portal_search(
        result="study",
        query=f"tax_tree({DEMO_TAX_ID})",
        fields=["study_accession", "study_title", "first_public"],
        limit=3,
    )
    _print_json(f"Studies under tax_tree={DEMO_TAX_ID}", tax_results)

    console.print("\n[yellow]▶ list_result_types()[/yellow]")
    rt = await client.get_results()
    names = [r.get("resultId") or r.get("result", "") for r in rt]
    console.print(f"  → {len(rt)} result types: {', '.join(names)}")


async def demo_sequence(client: ENAClient) -> None:
    _section("🧪  Sequence / Browser Tools")

    console.print(f"[yellow]▶ get_taxonomy_info(tax_id={DEMO_TAX_ID})[/yellow]")
    tax = await client.get_taxonomy(DEMO_TAX_ID)
    _print_json("Taxonomy record", tax[:1])

    console.print(f"\n[yellow]▶ get_record_xml({DEMO_SAMPLE}) (first 500 chars)[/yellow]")
    try:
        xml = await client.browser_xml(DEMO_SAMPLE)
        console.print(Panel(xml[:500] + "…", title="XML record", expand=False))
    except ENANotFoundError:
        console.print("[dim]  (record not available via Browser API)[/dim]")


# ── Main entry point ─────────────────────────────────────────────

SECTIONS: dict[str, Any] = {
    "study":    demo_study,
    "sample":   demo_sample,
    "run":      demo_run,
    "search":   demo_search,
    "sequence": demo_sequence,
}


async def main(sections: list[str]) -> None:
    console.print(Panel(
        "[bold white]ENA MCP Server — Live Demo[/bold white]\n"
        "[dim]Querying real ENA REST APIs …[/dim]",
        style="bold blue",
    ))

    async with ENAClient() as client:
        for name in sections:
            fn = SECTIONS.get(name)
            if fn:
                await fn(client)
                console.print()
            else:
                console.print(f"[red]Unknown section: {name}[/red]")

    console.print("[bold green]✓ Demo complete.[/bold green]")


if __name__ == "__main__":
    chosen = sys.argv[1:] or list(SECTIONS.keys())
    asyncio.run(main(chosen))
