# AI Agent Workflow Examples

This document shows how an AI agent (or a developer testing the server manually)
can compose ENA MCP tools to answer real bioinformatics questions.

---

## Example 1 — Exploring a Known Study

**Question:** *"What sequencing data is available for project PRJEB12345?"*

**Agent workflow:**

```
1. get_study(accession="PRJEB12345")
   → Returns title, organism, run_count, sample_count, dates

2. list_study_samples(study_accession="PRJEB12345", limit=5)
   → Returns 5 samples with organism, country, collection_date

3. list_study_runs(study_accession="PRJEB12345", limit=5)
   → Returns 5 runs with instrument_platform, library_strategy, read_count

4. get_run_files(accession="ERR123456")     # pick the first run
   → Returns FTP download URLs and MD5 checksums
```

---

## Example 2 — Finding Human WGS Data

**Question:** *"Find me recent Illumina whole-genome sequencing runs for Homo sapiens."*

```
1. search_ena(
       result="run",
       query='scientific_name="Homo sapiens"',
       instrument_platform="ILLUMINA",
       limit=10
   )
   → Returns 10 matching runs with accessions and metadata

2. get_run(accession="ERR4567890")     # inspect a specific run
   → Full run metadata
```

---

## Example 3 — Taxonomy-Based Discovery

**Question:** *"What ENA studies cover the Hominidae family (tax ID 9604)?"*

```
1. get_taxonomy_info(tax_id=9604)
   → Confirms scientific_name="Hominidae", rank="family"

2. search_by_taxon(
       tax_id=9604,
       result="study",
       include_subordinate_taxa=True,
       limit=20
   )
   → Returns studies covering Homo sapiens, Pan troglodytes, etc.
```

---

## Example 4 — Verifying a Sample and Its Sequence

**Question:** *"What is sample ERS123456 and what sequence data does it have?"*

```
1. get_sample(accession="ERS123456")
   → Returns organism, country, collection_date, study_accession

2. search_ena(
       result="run",
       query="sample_accession=ERS123456"
   )
   → Finds all runs derived from this sample

3. get_sequence(accession="LN999999")     # if a sequence accession is known
   → Returns FASTA sequence
```

---

## Example 5 — Metagenomics Discovery

**Question:** *"Find environmental soil samples from the UK."*

```
search_samples(
    country="United Kingdom",
    environmental=True,
    query='tissue_type="soil"',
    limit=25
)
→ Returns samples with geographic_location_latitude/longitude
```

---

## Example 6 — Composing Multiple Filters

**Question:** *"Give me Oxford Nanopore RNA-seq runs from mouse (tax ID 10090)."*

```
search_ena(
    result="run",
    tax_id=10090,
    instrument_platform="OXFORD_NANOPORE",
    query="library_strategy=RNA-Seq",
    limit=20
)
```

The server merges the `tax_id` and `instrument_platform` filters with the
free-text `query` using `AND`, producing:

```
tax_id=10090 AND instrument_platform=OXFORD_NANOPORE AND library_strategy=RNA-Seq
```

---

## Example 7 — Discovering Available Fields

**Question:** *"What result types can I search in ENA?"*

```
list_result_types()
→ Returns all supported ENA data portal result types with descriptions
```

---

## ENA Query Syntax Reference

The built-in `ena_query_guide` prompt provides a compact reference:

```
# Ask the MCP host to retrieve the prompt:
get_prompt("ena_query_guide", topic="query_syntax")
```

### Useful query patterns

```
# Exact taxonomy
tax_id=9606

# Taxonomy with all subtaxa
tax_tree=9606

# Date ranges
collection_date>=2020-01-01

# Multiple conditions
scientific_name="Homo sapiens" AND library_strategy=WGS AND read_count>10000000

# OR conditions
(instrument_platform=ILLUMINA OR instrument_platform=OXFORD_NANOPORE)

# Full-text
study_title="metagenome"
```
