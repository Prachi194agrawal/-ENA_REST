# MCP Tool Specifications

Complete reference for all tools exposed by the ENA MCP Server.

---

## Study Tools

### `get_study`

Fetch comprehensive metadata for a single ENA study / project.

**Input**

| Field | Type | Required | Description |
|---|---|---|---|
| `accession` | string | ✅ | Study accession matching `^(PRJ\|ERP\|SRP\|DRP)[A-Z0-9]+$` |
| `fields` | string[] | ❌ | Specific fields to return |

**Output** — JSON object with fields:

`study_accession`, `secondary_study_accession`, `bioproject_accession`,
`study_title`, `study_type`, `description`, `center_name`, `tax_id`,
`scientific_name`, `first_public`, `last_updated`, `experiment_count`,
`run_count`, `sample_count`

**Error** — `{"error": "not_found", "message": "...", "accession": "..."}`

---

### `list_study_runs`

List sequencing runs for a study (paginated).

**Input**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `study_accession` | string | ✅ | — | ENA study accession |
| `limit` | integer | ❌ | 20 | Page size (1–1000) |
| `offset` | integer | ❌ | 0 | Pagination offset |

**Output**

```json
{
  "study_accession": "PRJEB12345",
  "count": 20,
  "offset": 0,
  "limit": 20,
  "runs": [ { "run_accession": "ERR123456", ... } ]
}
```

---

### `list_study_samples`

List samples linked to a study (paginated).

**Input** — same shape as `list_study_runs`.

**Output**

```json
{
  "study_accession": "PRJEB12345",
  "count": 10,
  "samples": [ { "sample_accession": "ERS123456", ... } ]
}
```

---

## Sample Tools

### `get_sample`

Retrieve full metadata for a single ENA sample.

**Input**

| Field | Type | Required | Description |
|---|---|---|---|
| `accession` | string | ✅ | ERS…, SAMEA…, or SAME… |
| `fields` | string[] | ❌ | Specific fields |

**Output** — JSON object with fields including organism, collection metadata, and geographic coordinates.

---

### `search_samples`

Search ENA samples with composite filters.

**Input**

| Field | Type | Required | Description |
|---|---|---|---|
| `query` | string | ❌ | ENA query string |
| `tax_id` | integer | ❌ | NCBI taxonomy ID |
| `country` | string | ❌ | Country of collection |
| `environmental` | boolean | ❌ | Env/metagenome samples only |
| `fields` | string[] | ❌ | Fields to return |
| `limit` | integer | ❌ | Page size |
| `offset` | integer | ❌ | Pagination offset |

---

## Run Tools

### `get_run`

Retrieve complete metadata for a sequencing run.

**Input**

| Field | Type | Required | Description |
|---|---|---|---|
| `accession` | string | ✅ | ERR…, SRR…, or DRR… |
| `fields` | string[] | ❌ | Specific fields |

---

### `get_run_files`

Return download URLs and MD5 checksums for FASTQ/SRA files.

**Input** — `accession` (ERR…, SRR…, DRR…)

**Output**

```json
{
  "accession": "ERR123456",
  "download_urls": ["ftp://ftp.sra.ebi.ac.uk/..."],
  "md5_checksums": ["abc123..."]
}
```

---

## Experiment Tools

### `get_experiment`

Retrieve metadata for a single ENA experiment.

**Input** — `accession` (ERX…, SRX…, DRX…), optional `fields`.

---

## Search Tools

### `search_ena`

Perform a flexible search across any ENA result type.

**Input**

| Field | Type | Required | Description |
|---|---|---|---|
| `result` | string | ✅ | ENA result type (study, sample, run, etc.) |
| `query` | string | ❌ | ENA Portal query string |
| `fields` | string[] | ❌ | Fields to return |
| `limit` | integer | ❌ | Page size (1–1000) |
| `offset` | integer | ❌ | Pagination offset |
| `tax_id` | integer | ❌ | Filter by taxonomy ID |
| `instrument_platform` | string | ❌ | Filter by platform |

Compound filters are joined with `AND` automatically.

---

### `search_by_taxon`

Search ENA records for a specific organism by NCBI taxonomy ID.

**Input**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `tax_id` | integer | ✅ | — | NCBI taxonomy ID |
| `result` | string | ❌ | `study` | Result type |
| `include_subordinate_taxa` | boolean | ❌ | `true` | Include child taxa |
| `limit` | integer | ❌ | 20 | Page size |
| `offset` | integer | ❌ | 0 | Offset |

---

### `list_result_types`

Return all available ENA Portal result types.

**Input** — none

**Output**

```json
{
  "count": 25,
  "result_types": [
    { "result": "study", "description": "..." },
    ...
  ]
}
```

---

## Sequence / Browser Tools

### `get_sequence`

Fetch the FASTA nucleotide sequence for an ENA accession.

**Input** — `accession` (e.g. `AY123456`)

**Output**

```json
{
  "accession": "AY123456",
  "format": "fasta",
  "sequence": ">AY123456\nATCGATCG...\n"
}
```

---

### `get_record_xml`

Fetch the full XML record for any ENA accession via the Browser API.

**Input** — `accession`

**Output** — `{"accession": "...", "format": "xml", "record": "<?xml ..."}`

---

### `get_taxonomy_info`

Retrieve taxonomy records by NCBI tax ID.

**Input** — `tax_id` (integer)

**Output**

```json
{
  "tax_id": 9606,
  "count": 1,
  "records": [
    {
      "tax_id": "9606",
      "scientific_name": "Homo sapiens",
      "lineage": "...",
      "rank": "species"
    }
  ]
}
```

---

## Error Semantics

All tools return structured errors rather than raising exceptions to the MCP host.

| `error` value | HTTP status | Meaning |
|---|---|---|
| `not_found` | 404 | Accession does not exist in ENA |
| `rate_limited` | 429 | ENA rate limit hit (retry later) |
| `server_error` | 5xx | ENA server-side error |
| `unknown_tool` | — | Internal routing error |

Example error response:

```json
{
  "error": "not_found",
  "message": "ENA record not found: 'PRJEBINVALID'",
  "accession": "PRJEBINVALID"
}
```
