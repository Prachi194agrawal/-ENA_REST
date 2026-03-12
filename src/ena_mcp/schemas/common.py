"""
Shared Pydantic base models used across all ENA schemas.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")

# ---------------------------------------------------------------------------
# Base record
# ---------------------------------------------------------------------------


class ENARecord(BaseModel):
    """Minimal common fields present on every ENA record."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    accession: str = Field(..., description="Primary ENA accession (e.g. PRJEB12345)")
    description: str | None = Field(None, description="Free-text description")


# ---------------------------------------------------------------------------
# Error contract
# ---------------------------------------------------------------------------


class ErrorResponse(BaseModel):
    """Structured error returned by MCP tools on failure."""

    error: str = Field(..., description="Machine-readable error type")
    message: str = Field(..., description="Human-readable explanation")
    accession: str | None = Field(None, description="Accession that caused the error, if any")
    details: dict[str, Any] | None = Field(None, description="Optional extra context")


# ---------------------------------------------------------------------------
# Paginated wrapper
# ---------------------------------------------------------------------------


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response envelope."""

    total: int | None = Field(None, description="Total matching records (may be None if unknown)")
    offset: int = Field(0, description="Requested pagination offset")
    limit: int = Field(20, description="Requested page size")
    results: list[T] = Field(default_factory=list, description="Page of result records")
