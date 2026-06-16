"""Shared route helpers: timing, request id, and usage finalization."""

from __future__ import annotations

import time
from dataclasses import dataclass

from fastapi import Request

from app.models.common import ResponseMeta
from app.services import report_service


@dataclass
class RequestTimer:
    request_id: str | None
    _start: float

    def elapsed_ms(self) -> int:
        return int((time.perf_counter() - self._start) * 1000)


def start_timer(request: Request) -> RequestTimer:
    return RequestTimer(
        request_id=getattr(request.state, "request_id", None),
        _start=time.perf_counter(),
    )


def finalize(meta: ResponseMeta, timer: RequestTimer, user_id: str) -> ResponseMeta:
    """Stamp request id + latency onto a response and emit a usage log."""
    meta.request_id = timer.request_id
    meta.latency_ms = timer.elapsed_ms()
    report_service.log_usage(user_id, meta.agent or "unknown", meta)
    return meta
