"""Data-access helpers.

Persistence is centralized in ``app.services.supabase_service`` and ``report_service``. This
module exists as the place to add direct-SQL repositories (via ``app.db.database``) if/when a
use case needs them. Kept intentionally thin for now.
"""

from __future__ import annotations

from app.services import report_service, supabase_service

__all__ = ["report_service", "supabase_service"]
