# GSoC 2026 Proposal
## Expose a Subset of ENA REST Services as MCP
**Organisation:** EMBL-EBI  
**Mentor:** Senthilnathan Vijayaraja  
**Applicant:** Prachi Agrawal  
**Project Length:** Medium – 175 hours  
**Difficulty:** Medium  
**Repository:** https://github.com/Prachi194agrawal/-ENA_REST

---

## 1. About Me

I am a Python developer with strong experience in REST API design, async programming, and software architecture. I am deeply interested in the intersection of bioinformatics and AI tooling — specifically in making rich scientific databases like ENA accessible to modern LLM-based agents in a principled, reproducible way.

I have been contributing to open-source projects and am comfortable with the full software development lifecycle: design, implementation, testing, documentation, CI/CD, and containerisation.

**Skills:**
- Python 3.11+ — async/await, type hints, Pydantic v2, pytest
- REST APIs, HTTP, JSON schema design
- Model Context Protocol (MCP) — server, tool, and prompt authoring
- Docker, GitHub Actions CI/CD
- Software architecture: modular design, separation of concerns
- API performance: caching, rate limiting, retry strategies

---

## 2. Project Synopsis

The European Nucleotide Archive (ENA) provides one of the world's most comprehensive stores of publicly available nucleotide sequences and associated metadata. However, its REST APIs are not natively accessible to modern AI agents that rely on the **Model Context Protocol (MCP)** — a standard that defines explicit tool schemas, inputs, and outputs so LLMs can call external services reliably without hallucinating.

This project bridges that gap: it implements a **production-ready MCP server** that wraps a carefully selected subset of ENA REST endpoints, making ENA data queryable by any MCP-compatible AI agent (Claude Desktop, VS Code Copilot, LangChain, custom agents) in a safe, structured, and traceable way.

---

## 3. What I Have Already Built (Pre-GSoC Work)

To demonstrate genuine commitment and capability, I have already implemented a working prototype covering the core scope of this project. All code is public at the repository above.

### 3.1 Architecture

The server follows a clean 4-layer architecture:

```
MCP Host (Claude / Copilot / LangChain)
          │  JSON-RPC over stdin/stdout (MCP)
          ▼
    ena-mcp-server
    ├── server.py          ← MCP entrypoint, tool registration
    ├── tools/             ← One module per ENA domain
    ├── schemas/           ← Pydantic v2 models (validation + contracts)
    ├── client/            ← Async HTTP client
    └── utils/             ← Cache + rate limiter
          │  HTTPS
          ▼
    ENA REST APIs (Portal API + Browser API)
```

### 3.2 MCP Tools Implemented (14 tools across 6 domains)

| Domain | Tools | ENA API Used |
|---|---|---|
| **Study** | `get_study`, `list_study_runs`, `list_study_samples` | Portal API |
| **Sample** | `get_sample`, `search_samples` | Portal API |
| **Run** | `get_run`, `get_run_files` | Portal API |
| **Experiment** | `get_experiment` | Portal API |
| **Search** | `search_ena`, `search_by_taxon`, `list_result_types` | Portal API |
| **Sequence** | `get_sequence`, `get_record_xml`, `get_taxonomy_info` | Browser API |

Every tool has:
- A fully-specified JSON Schema `inputSchema` with type, description, regex patterns, and required fields
- Structured JSON output with consistent field names
- Structured error responses (`not_found`, `rate_limited`, `server_error`) rather than raw exceptions

### 3.3 Reliability Layer (ENAClient)

The HTTP client (`src/ena_mcp/client/ena_client.py`) implements three composable reliability layers:

| Layer | Mechanism | Default |
|---|---|---|
| Rate limiting | Async token-bucket (`RateLimiter`) | 5 req/s, burst 10 |
| Response caching | TTL + LRU (`ResponseCache` via `cachetools`) | 300 s TTL, 512 entries |
| Retry / resilience | `tenacity` exponential back-off | 3 attempts, 1–10 s wait |

Both ENA API families are supported:
- **Portal API** (`/ena/portal/api/search`) — structured JSON search with field selection
- **Browser API** (`/ena/browser/api`) — raw FASTA, XML, and file metadata

### 3.4 Schema Validation (Pydantic v2)

Six Pydantic model files (`schemas/`) cover every ENA result type exposed:
`Study`, `Sample`, `Run`, `Experiment`, `Search`, `Common`.

Models serve dual roles: input validation before any HTTP call, and output normalisation to produce consistent field names/types regardless of which ENA backend returned the data.

### 3.5 Testing

```
tests/
├── conftest.py          # Shared fixtures (STUDY, SAMPLE, RUN, EXPERIMENT, TAXONOMY data)
├── test_cache.py        # 66 lines — TTL/LRU cache unit tests
├── test_client.py       # 122 lines — ENAClient integration & error path tests
├── test_rate_limiter.py # 60 lines — token-bucket rate limiter tests
├── test_run_tools.py    # 67 lines — MCP run tool call/list tests
├── test_search_tools.py # 111 lines — search_ena, search_by_taxon, list_result_types
└── test_study_tools.py  # 86 lines — get_study, list_study_runs, list_study_samples
```
**Total: 648 lines of tests** using `pytest-asyncio` and `pytest-httpx` for HTTP mocking.

### 3.6 Documentation

| Document | Contents |
|---|---|
| `docs/architecture.md` | Component diagram, layer table, design decisions, security notes, extension guide |
| `docs/tools.md` | Full input/output/error contracts for all 14 tools |
| `docs/examples.md` | 5 end-to-end AI agent workflows (study exploration, WGS discovery, taxonomy-based discovery, sample verification, metagenomics) |
| `README.md` | Quick-start, configuration reference, Docker usage |
| `demo.py` | Live demo script hitting real ENA — pretty-prints results with `rich` |

### 3.7 CI/CD & Containerisation

- **GitHub Actions** (`.github/workflows/ci.yml`): 3 jobs on every push/PR to `main`
  - `lint` — `ruff check`, `ruff format --check`, `mypy src` on Python 3.11
  - `test` — `pytest` + `coverage` XML artifact, matrix across Python 3.11 and 3.12
  - `docker` — builds the production Docker image
- **Multi-stage Dockerfile**: builder stage produces a wheel; runtime stage is minimal `python:3.12-slim` running as a non-root user

---

## 4. What I Will Do During GSoC (Remaining Work)

The pre-GSoC prototype covers the core infrastructure. The GSoC period will be used to harden, extend, and polish the project to a truly production-ready state. The planned work is divided into four phases across 175 hours.

---

### Phase 1 — Expand Tool Coverage & Assembly Support (Weeks 1–3, ~40 hrs)

**Goal:** Cover all major ENA result types, including assembly and WGS sets.

#### 4.1 Assembly & WGS Tools (new `tools/assembly.py`)

| Tool | Description |
|---|---|
| `get_assembly` | Fetch metadata for a genome assembly (GCA/GCF accession) |
| `list_assembly_sequences` | List contig/chromosome sequences in an assembly |
| `search_assemblies` | Search assemblies by organism, assembly level, release date |

#### 4.2 Enhanced Run Tools

- `compare_runs` — Compare two or more runs side-by-side (platform, read depth, library strategy)
- `get_run_quality_metrics` — Surface quality fields (e.g. `quality_score`, `gc_percent`) where available

#### 4.3 Submission Metadata Tools

- `get_submission` — Fetch submission-level metadata for ERA accessions
- `list_submission_files` — List files associated with a submission

**Deliverables:** ≥3 new tools, full Pydantic schemas, tests, docs updated.

---

### Phase 2 — Composed Multi-Step Queries & Normalisation (Weeks 4–6, ~40 hrs)

**Goal:** Enable agents to answer complex, multi-entity questions in a single tool call.

#### 4.4 Composite Query Tool

```python
Tool: compose_ena_query
Description: Execute a chain of ENA queries and merge results into one response.
Input:
  steps: list of {tool, arguments} objects
  merge_on: shared field to join results on (e.g. "study_accession")
Output: merged, deduplicated JSON array
```

This allows an LLM to express "give me studies AND their samples AND runs in one call" without needing to chain three separate tool calls.

#### 4.5 Cross-Result Normalisation

Currently each domain has its own field names. Phase 2 will introduce:
- A **canonical accession resolver**: given any accession format (PRJ/ERP/SRP, ERR/SRR, ERS/SRS), resolve to all equivalent identifiers
- A **field mapping layer** that unifies common fields (`organism`, `tax_id`, `platform`, `date`) across result types so LLM context is consistent

#### 4.6 Async Parallel Queries

Modify `ENAClient` to support concurrent Portal API requests using `asyncio.gather`, with shared rate-limiter token accounting. This can give 3–5× throughput for composite queries.

**Deliverables:** `compose_ena_query` tool, normalisation layer, parallel client, tests.

---

### Phase 3 — Production Hardening (Weeks 7–9, ~40 hrs)

**Goal:** Make the server robust enough for long-running agent sessions.

#### 4.7 Persistent Disk Cache (optional)

Add an optional `diskcache`-backed persistent cache layer so responses survive server restarts. Controlled via `ENA_CACHE_BACKEND=disk` env var, with `ENA_CACHE_DIR` path.

#### 4.8 Metrics & Health Endpoint

- Expose a `get_server_stats` MCP tool: cache hit rate, total requests, rate-limit wait time, uptime
- Add structured logging (JSON log mode via `LOG_FORMAT=json`) for production observability

#### 4.9 Input Validation Hardening

- Extend Pydantic validators to catch semantically invalid inputs (e.g. future dates, negative read counts)
- Add a `validate_accession` tool that returns the accession type and canonical form without hitting ENA

#### 4.10 Error Recovery & Graceful Degradation

- On `ENARateLimitError`: return a structured response with `retry_after` hint instead of propagating failure
- On `ENAServerError`: return cached stale data (if available) with a `stale: true` flag

**Deliverables:** persistent cache, `get_server_stats`, `validate_accession`, improved error handling.

---

### Phase 4 — Integration, Documentation & Demo (Weeks 10–12, ~55 hrs)

**Goal:** End-to-end agent integration, final documentation, and a live demo.

#### 4.11 Claude Desktop / VS Code Copilot Integration Demo

Produce a screencast and written walkthrough showing a real LLM agent:
1. Discovering ENA studies for a given organism using `search_by_taxon`
2. Drilling into a study with `get_study`, `list_study_runs`, `list_study_samples`
3. Downloading FASTQ file URLs with `get_run_files`
4. Fetching a FASTA sequence with `get_sequence`

#### 4.12 LangChain / Agents SDK Integration Example

Add an `examples/` directory with a runnable Python script demonstrating ENA MCP used from a LangChain agent, showing how the tool schemas are auto-discovered.

#### 4.13 Complete API Reference (Sphinx / MkDocs)

- Auto-generate API reference from docstrings
- Host on GitHub Pages via a `docs` GitHub Actions job
- Include a "Getting Started" tutorial for bioinformaticians unfamiliar with MCP

#### 4.14 Performance Benchmarks

- Benchmark cache hit rate improvement across 100 repeated queries
- Benchmark rate-limiter overhead vs. raw `httpx`
- Include results in `docs/performance.md`

#### 4.15 Test Coverage Target: ≥90%

Reach ≥90% line coverage across `src/`, including edge cases: invalid accessions, rate-limit errors, 5xx retries, cache TTL expiry.

**Deliverables:** integration demo, LangChain example, Sphinx docs, benchmarks, full coverage.

---

## 5. Timeline

| Week | Dates | Milestone |
|---|---|---|
| Community Bonding | May | Sync with mentor, agree on API priority list, set up dev environment |
| **Week 1–2** | June 1–14 | Assembly tools (`get_assembly`, `list_assembly_sequences`, `search_assemblies`), schemas, tests |
| **Week 3** | June 15–21 | Enhanced run tools (`compare_runs`, `get_run_quality_metrics`), submission tools |
| **Week 4–5** | June 22 – July 5 | `compose_ena_query`, canonical accession resolver, field normalisation layer |
| **Week 6** | July 6–12 | Async parallel queries in `ENAClient`, rate-limiter token accounting |
| **Midterm Eval** | July 14 | Phase 1 & 2 complete; 7 new tools, composite query, normalisation |
| **Week 7–8** | July 15–28 | Persistent disk cache, `get_server_stats`, `validate_accession` |
| **Week 9** | July 29 – Aug 4 | Error recovery (stale cache, retry_after), JSON logging mode |
| **Week 10** | Aug 5–11 | Claude Desktop / Copilot integration demo + screencast |
| **Week 11** | Aug 12–18 | LangChain example, Sphinx docs, GitHub Pages deployment |
| **Week 12** | Aug 19–25 | Performance benchmarks, test coverage push to ≥90%, final polish |
| **Final Eval** | Aug 25 | All deliverables submitted, PR merged |

---

## 6. Deliverables Summary

### Already Delivered (Pre-GSoC)
- [x] 14 MCP tools across 6 domains (study, sample, run, experiment, search, sequence)
- [x] Async HTTP client with rate limiting, TTL+LRU caching, and retry
- [x] Pydantic v2 schemas for all result types
- [x] 648-line pytest test suite
- [x] Architecture, tool spec, and agent workflow documentation
- [x] Multi-stage Dockerfile with non-root user
- [x] GitHub Actions CI: ruff + mypy + pytest (3.11, 3.12) + Docker build

### To Be Delivered During GSoC
- [ ] ≥7 new tools (assembly, enhanced run, submission, compose, validate)
- [ ] Canonical accession resolver and cross-result field normalisation
- [ ] Async parallel query support
- [ ] Optional persistent disk cache
- [ ] `get_server_stats` observability tool
- [ ] Error recovery with stale cache and `retry_after`
- [ ] Claude Desktop + VS Code Copilot integration demo
- [ ] LangChain agent example
- [ ] Sphinx/MkDocs API reference hosted on GitHub Pages
- [ ] Performance benchmarks
- [ ] ≥90% test coverage

---

## 7. Why This Project Matters

ENA holds over 7 petabases of publicly available nucleotide sequence data and is the primary archive for sequencing data from major consortia (1000 Genomes, COVID-19, MetaSUB). Today, a researcher or AI agent that wants to ask "Find me all Illumina WGS runs for *Homo sapiens* deposited after 2022 with >30× coverage" must:

1. Read the ENA Portal API documentation
2. Construct the correct query syntax manually
3. Parse heterogeneous JSON responses
4. Handle pagination, rate limits, and retries themselves

With this MCP server, an AI agent can do all of that in a single, validated, cacheable tool call — and compose multiple such queries into a coherent multi-step workflow. This is the foundation for the next generation of AI-assisted bioinformatics.

---

## 8. References

- ENA Portal API: https://www.ebi.ac.uk/ena/portal/api/doc
- ENA Browser API: https://www.ebi.ac.uk/ena/browser/api
- Model Context Protocol specification: https://modelcontextprotocol.io/specification/
- Project repository: https://github.com/Prachi194agrawal/-ENA_REST
