# Copyright 2026 Aayush Chawla
# SPDX-License-Identifier: Apache-2.0

"""Engine API authentication dependency."""

from __future__ import annotations

import hmac

import structlog
from fastapi import HTTPException, Request, status

from laya.security.keychain import get_engine_token

log = structlog.get_logger()

# Interim exemption: the bundled n8n workflows call these endpoints without a
# credential. They stay open until n8n gets its own engine credential
# (engine/docs/n8n-engine-auth.md). Keep this list to exactly what the
# workflows call; everything else on the same routers requires the app token.
INTERIM_N8N_EXEMPT_ROUTES: set[tuple[str, str]] = {
    ("POST", "/events"),
    ("GET", "/repos"),
    ("POST", "/ingestion-errors"),
}

# n8n reads single metadata keys (GET /metadata/{key}). Listing and writing
# metadata are not exempt: a metadata write can repoint a workflow's config
# (e.g. the Bitbucket Server URL its credential is sent to).
_N8N_METADATA_PREFIX = "/metadata/"

# Vendor OAuth redirects arrive from the user's browser with no bearer header.
VENDOR_OAUTH_EXEMPT_ROUTES: set[tuple[str, str]] = {
    ("GET", "/egress/connections/oauth/callback"),
}


def is_auth_exempt(method: str, path: str) -> bool:
    """Return True if the route is exempted from engine bearer authentication."""
    if (method, path) in INTERIM_N8N_EXEMPT_ROUTES or (method, path) in VENDOR_OAUTH_EXEMPT_ROUTES:
        return True
    return method == "GET" and path.startswith(_N8N_METADATA_PREFIX)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def require_engine_auth(request: Request) -> str:
    """Validate the engine API bearer token on incoming REST requests.

    Exemptions:
    - The n8n routes and the vendor OAuth callback (see `is_auth_exempt`).
    - GET /health is exempted at the router inclusion level in main.py.
    """
    path = request.url.path.rstrip("/")
    if is_auth_exempt(request.method, path):
        return ""

    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise _unauthorized()

    presented = auth_header[7:].strip()
    expected = get_engine_token()

    # Compare as bytes: hmac.compare_digest raises TypeError on non-ASCII str,
    # and header values are latin-1 decoded, so a bearer containing bytes
    # >= 0x80 would surface as a 500 instead of a 401.
    if not expected or not hmac.compare_digest(
        presented.encode("utf-8"), expected.encode("utf-8")
    ):
        log.warning("engine_auth_failed", path=path, method=request.method)
        raise _unauthorized()

    return presented
