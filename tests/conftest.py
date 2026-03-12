"""
Shared pytest fixtures and helpers.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from ena_mcp.client.ena_client import ENAClient


# ---------------------------------------------------------------------------
# Sample fixture data
# ---------------------------------------------------------------------------

STUDY_FIXTURE: dict[str, Any] = {
    "study_accession": "PRJEB12345",
    "secondary_study_accession": "ERP013888",
    "study_title": "Whole-genome sequencing of Homo sapiens",
    "study_type": "Whole Genome Sequencing",
    "center_name": "EBI",
    "scientific_name": "Homo sapiens",
    "tax_id": "9606",
    "first_public": "2020-01-01",
    "last_updated": "2023-06-01",
    "experiment_count": 10,
    "run_count": 20,
    "sample_count": 10,
}

SAMPLE_FIXTURE: dict[str, Any] = {
    "sample_accession": "ERS123456",
    "secondary_sample_accession": "SRS111111",
    "sample_title": "Blood sample – HG001",
    "scientific_name": "Homo sapiens",
    "tax_id": "9606",
    "country": "United Kingdom",
    "collection_date": "2019-07-15",
    "first_public": "2020-01-01",
    "study_accession": "PRJEB12345",
}

RUN_FIXTURE: dict[str, Any] = {
    "run_accession": "ERR123456",
    "experiment_accession": "ERX111111",
    "sample_accession": "ERS123456",
    "study_accession": "PRJEB12345",
    "library_strategy": "WGS",
    "library_layout": "PAIRED",
    "instrument_platform": "ILLUMINA",
    "instrument_model": "Illumina NovaSeq 6000",
    "read_count": 50000000,
    "base_count": 15000000000,
    "fastq_ftp": "ftp.sra.ebi.ac.uk/vol1/fastq/ERR123/ERR123456_1.fastq.gz;"
                 "ftp.sra.ebi.ac.uk/vol1/fastq/ERR123/ERR123456_2.fastq.gz",
    "fastq_md5": "abc123;def456",
    "first_public": "2020-02-01",
}

EXPERIMENT_FIXTURE: dict[str, Any] = {
    "experiment_accession": "ERX111111",
    "study_accession": "PRJEB12345",
    "sample_accession": "ERS123456",
    "experiment_title": "WGS of HG001",
    "library_strategy": "WGS",
    "library_source": "GENOMIC",
    "library_selection": "RANDOM",
    "library_layout": "PAIRED",
    "instrument_platform": "ILLUMINA",
    "instrument_model": "Illumina NovaSeq 6000",
    "first_public": "2020-01-15",
}

TAXONOMY_FIXTURE: list[dict[str, Any]] = [
    {
        "tax_id": "9606",
        "scientific_name": "Homo sapiens",
        "lineage": "cellular organisms; Eukaryota; Opisthokonta; Metazoa; ...",
        "rank": "species",
    }
]


# ---------------------------------------------------------------------------
# Mock client fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_client() -> MagicMock:
    """Return a MagicMock ENAClient with all async methods pre-configured."""
    client = MagicMock(spec=ENAClient)

    # portal_search returns different fixtures based on 'result' kwarg
    async def portal_search(result: str, **kwargs: Any) -> list[dict[str, Any]]:
        accession: str = kwargs.get("accession", "")
        if result == "study":
            if accession and accession not in ("PRJEB12345", "ERP013888"):
                return []
            return [STUDY_FIXTURE]
        if result == "sample":
            if accession and accession not in ("ERS123456",):
                return []
            return [SAMPLE_FIXTURE]
        if result in ("run", "read_run"):
            if accession and accession not in ("ERR123456",):
                return []
            return [RUN_FIXTURE]
        if result in ("experiment", "read_experiment"):
            if accession and accession not in ("ERX111111",):
                return []
            return [EXPERIMENT_FIXTURE]
        return []

    client.portal_search = AsyncMock(side_effect=portal_search)
    client.browser_fasta = AsyncMock(return_value=">AY123456\nATCGATCGATCG\n")
    client.browser_xml = AsyncMock(return_value="<ROOT><ACCESSION>AY123456</ACCESSION></ROOT>")
    client.browser_fastq_urls = AsyncMock(
        return_value=[
            "ftp://ftp.sra.ebi.ac.uk/vol1/fastq/ERR123/ERR123456_1.fastq.gz",
            "ftp://ftp.sra.ebi.ac.uk/vol1/fastq/ERR123/ERR123456_2.fastq.gz",
        ]
    )
    client.get_taxonomy = AsyncMock(return_value=TAXONOMY_FIXTURE)
    client.get_results = AsyncMock(return_value=[
        {"result": "study", "description": "Research studies"},
        {"result": "sample", "description": "Biological samples"},
    ])
    client.aclose = AsyncMock()
    return client
