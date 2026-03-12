"""
Pydantic schemas for ENA Study / Project records.

ENA result type: ``study``
Accession prefixes: PRJ (BioProject), ERP, SRP, DRP
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Study(BaseModel):
    """Metadata for an ENA study (project)."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    # Core identifiers
    study_accession: str = Field(..., description="ENA study accession (e.g. PRJEB12345)")
    secondary_study_accession: str | None = Field(None, description="ERP/SRP secondary accession")
    bioproject_accession: str | None = Field(None, description="NCBI BioProject accession")

    # Descriptive fields
    study_title: str | None = Field(None, description="Full study title")
    study_alias: str | None = Field(None, description="Submitter-supplied alias")
    description: str | None = Field(None, description="Free-text study description")
    study_type: str | None = Field(None, description="Study type (e.g. Whole Genome Sequencing)")

    # Scientific scope
    center_name: str | None = Field(None, description="Submitting centre name")
    submission_accession: str | None = Field(None, description="Related ENA submission accession")
    tax_id: str | None = Field(None, description="Primary NCBI taxonomy ID")
    scientific_name: str | None = Field(None, description="Primary organism scientific name")

    # Dates
    first_public: str | None = Field(None, description="ISO-8601 date first made public")
    last_updated: str | None = Field(None, description="ISO-8601 date of last update")

    # Stats
    experiment_count: int | None = Field(None, description="Number of linked experiments")
    run_count: int | None = Field(None, description="Number of linked runs")
    sample_count: int | None = Field(None, description="Number of linked samples")

    # Data links
    ftp_link: str | None = Field(None, description="FTP download link for study data")


class StudySearchParams(BaseModel):
    """Input parameters for the get_study MCP tool."""

    accession: str = Field(
        ...,
        description=("ENA study accession, e.g. PRJEB12345, ERP001234, or SRP012345."),
        pattern=r"^(PRJ|ERP|SRP|DRP)[A-Z0-9]+$",
    )
    fields: list[str] | None = Field(
        None,
        description="Optional list of specific metadata fields to return.",
    )
