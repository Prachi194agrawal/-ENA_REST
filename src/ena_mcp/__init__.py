"""
ena_mcp — MCP server that exposes ENA REST services to AI agents.

Package layout
--------------
ena_mcp/
├── server.py          Main MCP server & entrypoint
├── client/
│   ├── __init__.py
│   └── ena_client.py  Async HTTP client (caching + rate-limiting)
├── schemas/
│   ├── __init__.py
│   ├── common.py      Shared Pydantic base models
│   ├── study.py
│   ├── sample.py
│   ├── run.py
│   ├── experiment.py
│   └── search.py
├── tools/
│   ├── __init__.py
│   ├── study.py
│   ├── sample.py
│   ├── run.py
│   ├── experiment.py
│   ├── search.py
│   └── sequence.py
└── utils/
    ├── __init__.py
    ├── cache.py
    └── rate_limiter.py
"""

__version__ = "0.1.0"
__all__ = ["__version__"]
