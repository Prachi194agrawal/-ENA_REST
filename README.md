# ENA MCP Server

> **Expose a Subset of ENA REST Services as MCP** — GSoC 2026 project for EMBL-EBI

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/protocol-MCP-green.svg)](https://modelcontextprotocol.io/)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

The **ENA MCP Server** wraps the [European Nucleotide Archive (ENA)](https://www.ebi.ac.uk/ena/) REST APIs behind the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/), enabling AI agents and LLM-based tools to query authoritative genomic metadata in a safe, structured, and reproducible way.

---

## ✨ Features

| Feature | Description |
|---|---|
| **10 MCP tools** | Study, sample, run, experiment, sequence, taxonomy, and search |
| **Caching** | TTL + LRU cache — reduces redundant ENA calls |
| **Rate limiting** | Token-bucket limiter — polite ENA citizen |
| **Auto-retry** | Exponential back-off for transient errors |
| **Pydantic schemas** | Strong input validation and explicit output contracts |
| **Composable queries** | Combine tax_id, platform, and free-text filters in one call |
| **Prompts** | Built-in LLM guide for ENA query syntax |

---

## 🗂 Project Structure

```
ena-mcp-server/
├── src/ena_mcp/
│   ├── server.py           # MCP server entrypoint
│   ├── client/
│   │   └── ena_client.py   # Async HTTP client (cache + rate-limit + retry)
│   ├── schemas/            # Pydantic models for all ENA result types
│   ├── tools/              # One module per ENA domain
│   └── utils/
│       ├── cache.py        # TTL + LRU response cache
│       └── rate_limiter.py # Token-bucket rate limiter
├── tests/                  # pytest test suite
├── docs/                   # Architecture, tool specs, examples
├── Dockerfile
├── .env.example
└── pyproject.toml
```

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repo
git clone https://github.com/enasequence/ena-mcp-server
cd ena-mcp-server

# Create a virtual environment
python -m venv .venv && source .venv/bin/activate

# Install (editable mode for development)
pip install -e ".[dev]"
```

### Run the server

```bash
# stdio transport (used by MCP hosts)
ena-mcp

# With custom settings
ENA_RATE_LIMIT=3 ENA_CACHE_TTL=600 LOG_LEVEL=DEBUG ena-mcp
```

### Configure Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ena": {
      "command": "ena-mcp",
      "env": {
        "ENA_RATE_LIMIT": "5",
        "ENA_CACHE_TTL": "300"
      }
    }
  }
}
```

### Configure VS Code / GitHub Copilot

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "ena-mcp": {
      "type": "stdio",
      "command": "ena-mcp"
    }
  }
}
```

---

## 🔧 Available MCP Tools

### Study Tools
| Tool | Description |
|---|---|
| `get_study` | Fetch metadata for a study/project (PRJEB…, ERP…, SRP…) |
| `list_study_runs` | List sequencing runs for a study (paginated) |
| `list_study_samples` | List samples for a study (paginated) |

### Sample Tools
| Tool | Description |
|---|---|
| `get_sample` | Fetch metadata for a sample (ERS…, SAMEA…) |
| `search_samples` | Search samples by organism, country, environment |

### Run Tools
| Tool | Description |
|---|---|
| `get_run` | Fetch metadata for a sequencing run (ERR…, SRR…) |
| `get_run_files` | Get FTP download URLs and MD5s for FASTQ/SRA files |

### Experiment Tools
| Tool | Description |
|---|---|
| `get_experiment` | Fetch metadata for an experiment (ERX…, SRX…) |

### Search Tools
| Tool | Description |
|---|---|
| `search_ena` | Free-text / structured search across any ENA result type |
| `search_by_taxon` | Search by NCBI taxonomy ID (with optional subtree) |
| `list_result_types` | Discover all available ENA result types |

### Sequence / Browser Tools
| Tool | Description |
|---|---|
| `get_sequence` | Fetch FASTA nucleotide sequence for an accession |
| `get_record_xml` | Fetch full XML record for any accession |
| `get_taxonomy_info` | Fetch taxonomy info by NCBI tax ID |

---

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=src --cov-report=term-missing

# Run only unit tests (no integration)
pytest tests/test_cache.py tests/test_rate_limiter.py
```

---

## ⚙️ Configuration

All settings can be overridden via environment variables or a `.env` file:

| Variable | Default | Description |
|---|---|---|
| `ENA_PORTAL_BASE` | `https://www.ebi.ac.uk/ena/portal/api` | ENA Portal API base URL |
| `ENA_BROWSER_BASE` | `https://www.ebi.ac.uk/ena/browser/api` | ENA Browser API base URL |
| `ENA_TIMEOUT` | `30` | HTTP request timeout (seconds) |
| `ENA_MAX_RETRIES` | `3` | Max retry attempts for transient errors |
| `ENA_RATE_LIMIT` | `5` | Requests per second (token-bucket rate) |
| `ENA_CACHE_TTL` | `300` | Cache TTL in seconds |
| `ENA_CACHE_SIZE` | `512` | Max cached responses |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## 🐳 Docker

```bash
# Build
docker build -t ena-mcp-server .

# Run (stdio mode — pipe to your MCP host)
docker run --rm -i ena-mcp-server
```

---

## 📚 Documentation

- [Architecture & Design](docs/architecture.md)
- [MCP Tool Specifications](docs/tools.md)
- [AI Agent Workflow Examples](docs/examples.md)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Make changes and add tests
4. Run `ruff check src tests` and `mypy src`
5. Submit a pull request

---

## 📄 License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

---

## 🔗 Links

- [ENA REST API Documentation](https://www.ebi.ac.uk/ena/portal/api/doc)
- [MCP Specification](https://modelcontextprotocol.io/specification/)
- [GSoC 2026 EMBL-EBI Projects](https://www.ebi.ac.uk/about/events/gsoc)
