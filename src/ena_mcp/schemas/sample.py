"""
Pydantic schemas for ENA Sample / BioSample records.

ENA result type: ``sample``
Accession prefixes: ERS, SRS, DRS, SAME (BioSample)
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Sample(BaseModel):
    """Metadata for an ENA sample / BioSample."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    # Core identifiers
    sample_accession: str = Field(..., description="ENA sample accession (e.g. ERS123456)")
    secondary_sample_accession: str | None = Field(None, description="SRS/DRS secondary accession")
    biosample_accession: str | None = Field(None, description="NCBI BioSample accession (SAME…)")

    # Descriptive fields
    sample_alias: str | None = Field(None, description="Submitter-supplied alias")
    sample_title: str | None = Field(None, description="Sample title")
    sample_description: str | None = Field(None, description="Free-text description")
    center_name: str | None = Field(None, description="Submitting centre name")

    # Organism
    tax_id: str | None = Field(None, description="NCBI taxonomy ID")
    scientific_name: str | None = Field(None, description="Organism scientific name")
    common_name: str | None = Field(None, description="Organism common name")
    strain: str | None = Field(None, description="Organism strain")

    # Collection context
    collection_date: str | None = Field(None, description="Date sample was collected")
    country: str | None = Field(None, description="Country of collection (ENA ontology)")
    geographic_location_latitude: float | None = Field(None, description="Decimal latitude")
    geographic_location_longitude: float | None = Field(None, description="Decimal longitude")
    environmental_sample: bool | None = Field(None, description="True if environmental/metagenome")
    tissue_type: str | None = Field(None, description="Tissue type")

    # Dates
    first_public: str | None = Field(None, description="ISO-8601 date first made public")
    last_updated: str | None = Field(None, description="ISO-8601 date of last update")

    # Linked study
    study_accession: str | None = Field(None, description="Parent study accession")


class SampleSearchParams(BaseModel):
    """Input parameters for sample-related MCP tools."""

    accession: str = Field(
        ...,
        description="ENA sample accession, e.g. ERS123456 or SAMEA12345.",
    )
    fields: list[str] | None = Field(None, description="Optional specific fields to return.")
