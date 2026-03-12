"""
Pydantic schemas for ENA Experiment records.

ENA result type: ``experiment``
Accession prefixes: ERX, SRX, DRX
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Experiment(BaseModel):
    """Metadata for an ENA experiment."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    experiment_accession: str = Field(..., description="ENA experiment accession (e.g. ERX123456)")
    study_accession: str | None = Field(None, description="Parent study accession")
    sample_accession: str | None = Field(None, description="Sample accession")
    experiment_alias: str | None = Field(None, description="Submitter-supplied alias")
    experiment_title: str | None = Field(None, description="Experiment title")
    description: str | None = Field(None, description="Free-text description")

    # Library
    library_name: str | None = Field(None, description="Library name")
    library_strategy: str | None = Field(None, description="e.g. WGS, RNA-Seq")
    library_source: str | None = Field(None, description="e.g. GENOMIC, TRANSCRIPTOMIC")
    library_selection: str | None = Field(None, description="e.g. RANDOM, PCR")
    library_layout: str | None = Field(None, description="PAIRED or SINGLE")

    # Platform
    instrument_platform: str | None = Field(None, description="Sequencing platform")
    instrument_model: str | None = Field(None, description="Instrument model")

    # Organism
    tax_id: str | None = Field(None, description="NCBI taxonomy ID")
    scientific_name: str | None = Field(None, description="Organism scientific name")

    first_public: str | None = Field(None, description="ISO-8601 date first made public")
    last_updated: str | None = Field(None, description="ISO-8601 date of last update")


class ExperimentSearchParams(BaseModel):
    """Input parameters for experiment-related MCP tools."""

    accession: str = Field(..., description="ENA experiment accession, e.g. ERX123456.")
    fields: list[str] | None = Field(None, description="Optional specific fields to return.")
