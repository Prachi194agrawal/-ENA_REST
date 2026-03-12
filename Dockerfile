# ────────────────────────────────────────────────────────────────
# ENA MCP Server – multi-stage Docker build
# ────────────────────────────────────────────────────────────────

# ── Stage 1: build wheel ─────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build tooling
RUN pip install --no-cache-dir hatchling

# Copy project metadata first (layer-cache friendly)
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/

# Build the distribution wheel
RUN pip wheel --no-deps --wheel-dir /wheels .

# ── Stage 2: minimal runtime image ──────────────────────────────
FROM python:3.12-slim AS runtime

# Non-root user for security
RUN addgroup --system ena && adduser --system --ingroup ena ena

WORKDIR /app

# Install the wheel and its runtime dependencies
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels

# Run as non-root
USER ena

# Stdio transport – no port needed
ENTRYPOINT ["ena-mcp"]
