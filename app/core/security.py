"""Authentication: Supabase JWT validation with a dev bypass.

Verification order in ``supabase`` mode:
1. Asymmetric JWKS (ES256/RS256) using the project's published signing keys.
2. Legacy HS256 shared secret (``SUPABASE_JWT_SECRET``).

In ``dev`` mode a fixed mock user is returned so the API can be exercised locally without a
real Supabase session.
"""

from __future__ import annotations

import time
from typing import Any

import httpx
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import JWTError

from app.core.config import get_settings
from app.core.errors import AuthError
from app.core.logging import get_logger
from app.models.common import AuthUser
from app.services import supabase_service

logger = get_logger("app.security")

_bearer = HTTPBearer(auto_error=False)

DEV_USER = AuthUser(
    user_id="00000000-0000-0000-0000-000000000000",
    email="dev@pilotmycareer.local",
    role="authenticated",
    plan="pro_monthly",
    plan_key="shield_pro",
    unlimited=True,
)

_JWKS_CACHE: dict[str, Any] = {"keys": None, "fetched_at": 0.0}
_JWKS_TTL_SECONDS = 600


def _jwks_url() -> str:
    base = get_settings().supabase_url.rstrip("/")
    return f"{base}/auth/v1/.well-known/jwks.json"


def _get_jwks(force: bool = False) -> dict[str, Any] | None:
    now = time.time()
    if (
        not force
        and _JWKS_CACHE["keys"] is not None
        and now - _JWKS_CACHE["fetched_at"] < _JWKS_TTL_SECONDS
    ):
        return _JWKS_CACHE["keys"]
    if not get_settings().supabase_url:
        return None
    try:
        resp = httpx.get(_jwks_url(), timeout=5.0)
        resp.raise_for_status()
        keys = resp.json()
        if keys.get("keys"):
            _JWKS_CACHE["keys"] = keys
            _JWKS_CACHE["fetched_at"] = now
            return keys
    except Exception:  # pragma: no cover - network/JWKS unavailability is non-fatal
        logger.warning("JWKS fetch failed; will try HS256 fallback")
    return None


def _verify_jwks(token: str) -> dict[str, Any] | None:
    jwks = _get_jwks()
    if not jwks:
        return None
    try:
        header = jwt.get_unverified_header(token)
    except JWTError:
        return None
    kid = header.get("kid")
    key = next((k for k in jwks["keys"] if k.get("kid") == kid), None)
    if key is None:
        # Key may have rotated; refresh once.
        jwks = _get_jwks(force=True)
        if not jwks:
            return None
        key = next((k for k in jwks["keys"] if k.get("kid") == kid), None)
        if key is None:
            return None
    try:
        return jwt.decode(
            token,
            key,
            algorithms=[key.get("alg", "ES256")],
            audience="authenticated",
            options={"verify_aud": True},
        )
    except JWTError:
        return None


def _verify_hs256(token: str) -> dict[str, Any] | None:
    secret = get_settings().supabase_jwt_secret
    if not secret:
        return None
    try:
        return jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience="authenticated",
            options={"verify_aud": True},
        )
    except JWTError:
        return None


def _claims_to_user(claims: dict[str, Any]) -> AuthUser:
    user = AuthUser(
        user_id=str(claims.get("sub")),
        email=claims.get("email"),
        role=claims.get("role", "authenticated"),
    )
    if get_settings().supabase_configured:
        enrichment = supabase_service.fetch_user_profile(user.user_id)
        if enrichment:
            user.plan = enrichment.get("plan")
            user.plan_key = enrichment.get("plan_key")
            user.unlimited = enrichment.get("unlimited")
    return user


def verify_supabase_token(token: str) -> AuthUser:
    """Validate a Supabase access token, raising AuthError on failure."""
    claims = _verify_jwks(token) or _verify_hs256(token)
    if not claims or not claims.get("sub"):
        raise AuthError("Invalid or expired token")
    return _claims_to_user(claims)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthUser:
    """FastAPI dependency that resolves the authenticated user."""
    if get_settings().auth_mode == "dev":
        request.state.user_id = DEV_USER.user_id
        return DEV_USER

    if credentials is None or not credentials.credentials:
        raise AuthError("Missing Authorization bearer token")

    user = verify_supabase_token(credentials.credentials)
    request.state.user_id = user.user_id
    request.state.access_token = credentials.credentials
    return user
