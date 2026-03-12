"""
Pydantic schemas for free-text / advanced ENA search.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, field_validator

# Valid ENA Portal result types
RESULT_TYPES = Literal[
    "study",
    "sample",
    "run",
    "experiment",
    "analysis",
    "sequence",
    "assembly",
    "wgs_set",
    "coding",
    "noncoding",
    "tsa_set",
    "taxon",
    "read_experiment",
    "read_run",
    "read_study",
    "read_sample",
    "analysis_study",
    "analysis_experiment",
    "analysis_sample",
    "analysis_run",
    "clone",
    "clone_placement",
    "project",
]


class SearchParams(BaseModel):
    """Input parameters for the search_ena MCP tool."""

    result: RESULT_TYPES = Field(
        ...,
        description=("ENA result type to search (e.g. 'study', 'sample', 'run', 'sequence')."),
    )
    query: str | None = Field(
        None,
        description=(
            "ENA free-text query string.  Supports EMBL-EBI query syntax, "
            "e.g. 'scientific_name=\"Homo sapiens\"' or "
            "'library_strategy=WGS AND instrument_platform=ILLUMINA'."
        ),
    )
    fields: list[str] | None = Field(
        None,
        description="Specific metadata fields to include in the response.",
    )
    limit: Annotated[int, Field(ge=1, le=1000)] = Field(
        20,
        description="Maximum number of results to return (1–1000).",
    )
    offset: Annotated[int, Field(ge=0)] = Field(
        0,
        description="Pagination offset.",
    )
    tax_id: int | None = Field(
        None,
        description="Filter results by NCBI taxonomy ID.",
    )
    instrument_platform: str | None = Field(
        None,
        description="Filter by sequencing platform, e.g. ILLUMINA, OXFORD_NANOPORE.",
    )

    @field_validator("query", mode="before")
    @classmethod
    def strip_query(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip() or None
        return v


class SearchResponse(BaseModel):
    """Response envelope for search results."""

    result_type: str = Field(..., description="The ENA result type that was queried")
    query: str | None = Field(None, description="The query string used")
    count: int = Field(..., description="Number of records returned in this page")
    offset: int = Field(0, description="Pagination offset used")
    limit: int = Field(20, description="Page size used")
    records: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of matching records (fields vary by result type)",
    )
