"""Supabase identity verification for optional GPU-consuming operations.

Only the Supabase Auth server is trusted for user identity. No browser-provided
user ID, guest persona, or unverified JWT claim is accepted.
"""
from __future__ import annotations

import os
from urllib.parse import urlsplit
from uuid import UUID

import httpx
from fastapi import HTTPException


def parse_bearer_token(authorization: str | None) -> str:
    """Accept one well-formed bearer token; never trust client-supplied IDs."""
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Sign in to use this feature.')
    token = authorization[7:]
    if not token or token != token.strip() or len(token) > 8192 or any(ch.isspace() for ch in token):
        raise HTTPException(status_code=401, detail='Invalid authentication token.')
    return token


def supabase_public_settings() -> tuple[str, str]:
    """Trust only a configured HTTPS Supabase-hosted origin, never request input."""
    base = os.getenv('SUPABASE_URL', '').strip().rstrip('/')
    publishable_key = os.getenv('SUPABASE_PUBLISHABLE_KEY', '').strip()
    parts = urlsplit(base)
    if (parts.scheme != 'https' or not parts.hostname or
            not parts.hostname.endswith('.supabase.co') or
            parts.username or parts.password or parts.port or parts.path or
            parts.query or parts.fragment or not publishable_key):
        raise HTTPException(status_code=503, detail='Account verification is not configured.')
    return base, publishable_key


def verify_supabase_user(authorization: str | None) -> str:
    token = parse_bearer_token(authorization)
    base, publishable_key = supabase_public_settings()
    try:
        with httpx.Client(timeout=8.0, follow_redirects=False) as client:
            response = client.get(
                f'{base}/auth/v1/user',
                headers={'apikey': publishable_key, 'Authorization': f'Bearer {token}'},
            )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail='Account verification is temporarily unavailable.') from exc
    if response.status_code in (401, 403):
        raise HTTPException(status_code=401, detail='Sign in again to personalize your roadmap.')
    if response.status_code != 200:
        raise HTTPException(status_code=503, detail='Account verification is temporarily unavailable.')
    try:
        return str(UUID(response.json()['id']))
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        raise HTTPException(status_code=503, detail='Account verification returned invalid data.') from exc
