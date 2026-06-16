"""Report history and generation models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ReportRecord(BaseModel):
    id: str | None = None
    agent: str
    title: str | None = None
    content: dict[str, Any] = Field(default_factory=dict)
    model: str | None = None
    provider: str | None = None
    created_at: str | None = None


class ReportHistoryResponse(BaseModel):
    reports: list[ReportRecord] = Field(default_factory=list)
    persisted: bool = False
    request_id: str | None = None


class ReportGenerateRequest(BaseModel):
    agent: str = Field(min_length=1)
    title: str | None = None
    content: dict[str, Any] = Field(default_factory=dict)


class ReportGenerateResponse(BaseModel):
    report: ReportRecord
    persisted: bool = False
    request_id: str | None = None
