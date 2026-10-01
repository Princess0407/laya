# Copyright 2026 Aayush Chawla
# SPDX-License-Identifier: Apache-2.0

"""Engine API authentication dependency and rotation endpoint."""

from __future__ import annotations

import hmac

import structlog
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from laya.security.keychain import (
    ensure_engine_token,
    get_engine_token,
    rotate_engine_token,
)

log = structlog.get_logger()

router = APIRouter()

# Interim exemption: n8n workflows post to /events without auth until a dedicated
# n8n ingest token is implemented by the maintainer (see PR notes / architecture cut).
INTERIM_N8N_EXEMPT_ROUTES: set[tuple[str, str]] = {
    ("POST", "/events"),
}


async def require_engine_auth(request: Request) -> str:
    """Validate the engine API bearer token on incoming REST requests.

    Exemptions:
    - Named interim routes (e.g. POST /events from n8n)
    - GET /health is exempted at the router inclusion level in main.py.
    """
    path = request.url.path.rstrip("/")
    if (request.method, path) in INTERIM_N8N_EXEMPT_ROUTES:
        return ""

    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )

    presented = auth_header[7:].strip()
    expected = get_engine_token()

    if not expected or not hmac.compare_digest(presented, expected):
        log.warning("engine_auth_failed", path=path, method=request.method)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return presented


class RotateTokenResponse(BaseModel):
    token: str


@router.post("/auth/rotate", response_model=RotateTokenResponse)
async def rotate_token() -> RotateTokenResponse:
    """Rotate the engine API token in OS keychain and drop in-process cache.

    Requires valid engine auth (inherited from router include).
    The old token fails immediately for subsequent requests.
    """
    new_token = rotate_engine_token()
    return RotateTokenResponse(token=new_token)
