# Architecture & Design

## Overview

The ENA MCP Server is a lightweight adapter that bridges the ENA REST APIs with
the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/), allowing
AI agents to query authoritative genomic metadata in a deterministic, structured way.

```
┌─────────────────────────────────────────────────────────────────┐
│                        MCP Host Process                         │
│   (Claude Desktop / VS Code Copilot / LangChain / custom agent) │
└────────────────────────────┬────────────────────────────────────┘
                             │  JSON-RPC over stdin/stdout (MCP)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ena-mcp-server (this project)                 │
│                                                                 │
│  ┌──────────────┐   ┌────────────────────────────────────────┐  │
│  │  MCP Server  │   │              Tool Modules              │  │
│  │  (mcp SDK)   │◄──│  study · sample · run · experiment     │  │
│  │              │   │  search · sequence                     │  │
│  └──────┬───────┘   └────────────────┬───────────────────────┘  │
│         │                           │                           │
│         └──────────────────────────►│                           │
│                                     ▼                           │
│                         ┌───────────────────────┐              │
│                         │      ENAClient         │              │
│                         │  ┌─────────────────┐  │              │
│                         │  │  Rate Limiter   │  │              │
│                         │  │  (token bucket) │  │              │
│                         │  └─────────────────┘  │              │
│                         │  ┌─────────────────┐  │              │
│                         │  │  Response Cache │  │              │
│                         │  │  (TTL + LRU)    │  │              │
│                         │  └─────────────────┘  │              │
│                         │  ┌─────────────────┐  │              │
│                         │  │  Retry (tenacity│  │              │
│                         │  │  exp. back-off) │  │              │
│                         │  └─────────────────┘  │              │
│                         └───────────┬───────────┘              │
└─────────────────────────────────────┼─────────────────────────-┘
                                      │  HTTPS
                                      ▼
                      ┌───────────────────────────────┐
                      │       ENA REST APIs            │
                      │  Portal API  /ena/portal/api   │
                      │  Browser API /ena/browser/api  │
                      └───────────────────────────────┘
```

---

## Component Responsibilities

### `server.py` — MCP Server Entrypoint

- Instantiates the `mcp.Server` and `ENAClient`.
- Calls each `register_*_tools()` function to attach tool handlers.
- Registers a built-in `ena_query_guide` prompt.
- Runs the MCP stdio transport loop.

### `client/ena_client.py` — HTTP Client

The single, shared async HTTP client used by all tools. Three key concerns are
separated into composable layers:

| Layer | Mechanism | Default |
|---|---|---|
| Rate limiting | Token-bucket (`RateLimiter`) | 5 req/s, burst 10 |
| Response caching | TTL + LRU (`ResponseCache`) | 5 min TTL, 512 entries |
| Retry / resilience | `tenacity` exponential back-off | 3 attempts, 1–10s wait |

Two ENA API families are supported:

- **Portal API** (`/ena/portal/api/search`) — structured JSON search with field selection.
- **Browser API** (`/ena/browser/api`) — raw FASTA, XML, and file metadata.

### `tools/` — MCP Tool Modules

Each module exposes a `register_*_tools(server, client)` function that registers
`list_tools` and `call_tool` handlers with the MCP server. This pattern keeps
each domain self-contained and independently testable.

| Module | Tools registered |
|---|---|
| `study.py` | `get_study`, `list_study_runs`, `list_study_samples` |
| `sample.py` | `get_sample`, `search_samples` |
| `run.py` | `get_run`, `get_run_files` |
| `experiment.py` | `get_experiment` |
| `search.py` | `search_ena`, `search_by_taxon`, `list_result_types` |
| `sequence.py` | `get_sequence`, `get_record_xml`, `get_taxonomy_info` |

### `schemas/` — Pydantic Models

Pydantic v2 models serve two roles:
1. **Input validation** — MCP tool input schemas are generated from JSON Schema
   aligned with the Pydantic models.
2. **Output normalisation** — Raw ENA JSON is parsed through typed models to
   produce consistent field names and types.

### `utils/` — Shared Utilities

- `cache.py` — Thread-safe `ResponseCache` backed by `cachetools.TTLCache`.
- `rate_limiter.py` — Async token-bucket `RateLimiter`.

---

## Design Decisions

### Why stdio transport?

Stdio is the MCP standard for subprocess servers. It requires zero network
configuration, works behind any firewall, and is supported by every MCP host.

### Why a single shared `ENAClient`?

Creating one client per tool call would waste connections. A single shared
instance lets all tools benefit from the same connection pool, cache, and
rate limiter.

### Why Pydantic for schemas?

MCP tool `inputSchema` fields are plain JSON Schema dicts. Pydantic models
serve as the canonical definition; JSON Schema is derived from them. This gives
us free validation, serialisation, and IDE auto-complete.

### Why not expose all ENA API fields?

Each tool returns a curated default field list. Callers can override this with
`fields=["field1", "field2"]`. This prevents accidentally returning hundreds of
rarely-needed fields in LLM context windows.

### Why separate tool modules instead of one big file?

Separation of concerns: each domain (study, sample, run …) can evolve
independently, be tested in isolation, and be enabled/disabled without affecting
others. It also mirrors the structure of EMBL-EBI's own API categories.

---

## Extending the Server

To add a new ENA result type (e.g. `assembly`):

1. Add a Pydantic schema in `src/ena_mcp/schemas/assembly.py`.
2. Create `src/ena_mcp/tools/assembly.py` with a `register_assembly_tools()` function.
3. Import and call it in `server.py` and `tools/__init__.py`.
4. Add tests in `tests/test_assembly_tools.py`.

---

## Security Considerations

- The server only makes **read-only** requests to ENA (HTTP GET).
- No ENA credentials are required or stored.
- All inputs are validated by Pydantic before reaching the HTTP layer.
- Accession pattern validation (`pattern` field in JSON Schema) prevents
  obviously invalid inputs from reaching ENA.
- Rate limiting protects ENA from accidental abuse.
