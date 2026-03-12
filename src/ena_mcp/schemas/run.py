"""
Pydantic schemas for ENA Run records.

ENA result type: ``run``
Accession prefixes: ERR, SRR, DRR
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Run(BaseModel):
    """Metadata for a single ENA sequencing run."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    # Core identifiers
    run_accession: str = Field(..., description="ENA run accession (e.g. ERR123456)")
    experiment_accession: str | None = Field(None, description="Parent experiment accession")
    sample_accession: str | None = Field(None, description="Sample accession")
    study_accession: str | None = Field(None, description="Study accession")

    # Sequencing details
    library_name: str | None = Field(None, description="Library name")
    library_strategy: str | None = Field(None, description="e.g. WGS, AMPLICON, RNA-Seq")
    library_source: str | None = Field(None, description="e.g. GENOMIC, TRANSCRIPTOMIC")
    library_selection: str | None = Field(None, description="e.g. RANDOM, PCR")
    library_layout: str | None = Field(None, description="PAIRED or SINGLE")
    instrument_platform: str | None = Field(None, description="e.g. ILLUMINA, OXFORD_NANOPORE")
    instrument_model: str | None = Field(None, description="Instrument model name")
    nominal_length: int | None = Field(None, description="Nominal insert size for paired libraries")

    # Read statistics
    read_count: int | None = Field(None, description="Total reads in this run")
    base_count: int | None = Field(None, description="Total bases in this run")

    # File metadata
    fastq_ftp: str | None = Field(None, description="Semicolon-separated FTP FASTQ file URLs")
    fastq_md5: str | None = Field(None, description="Semicolon-separated MD5 checksums")
    submitted_ftp: str | None = Field(None, description="FTP URLs of submitted files")
    sra_ftp: str | None = Field(None, description="FTP SRA file URLs")

    # Organism
    tax_id: str | None = Field(None, description="NCBI taxonomy ID")
    scientific_name: str | None = Field(None, description="Organism scientific name")

    # Dates
    first_public: str | None = Field(None, description="ISO-8601 date first made public")
    last_updated: str | None = Field(None, description="ISO-8601 date of last update")


class RunSearchParams(BaseModel):
    """Input parameters for run-related MCP tools."""

    accession: str = Field(..., description="ENA run accession, e.g. ERR123456.")
    fields: list[str] | None = Field(None, description="Optional specific fields to return.")
