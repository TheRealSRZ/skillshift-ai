"""Authenticated account deletion. Never exposed to unverified client-supplied user IDs."""
import logging
import os
import sqlite3
from uuid import UUID

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, Header, HTTPException
from backend.ai_access import parse_bearer_token, supabase_public_settings
from backend.ai_quota import anonymize_deleted_user

load_dotenv()

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api/account', tags=['Account'])

def _settings():
    url, publishable = supabase_public_settings()
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '').strip()
    if not service_key:
        raise HTTPException(503, detail='Account deletion is not configured')
    return url, publishable, service_key

@router.delete('/me')
def delete_current_account(authorization: str | None = Header(default=None)):
    access_token = parse_bearer_token(authorization)
    url, publishable, service_key = _settings()
    try:
        with httpx.Client(timeout=12.0, follow_redirects=False) as client:
            # Supabase Auth validates the signature, expiry, and user identity.
            result = client.get(f'{url}/auth/v1/user', headers={
                'apikey': publishable,
                'Authorization': f'Bearer {access_token}',
            })
            if result.status_code != 200:
                raise HTTPException(401, detail='Invalid or expired session')
            try:
                # Crucially, target UUID comes ONLY from the verified Auth server.
                user_id = str(UUID(result.json()['id']))
            except (ValueError, TypeError, KeyError, AttributeError):
                raise HTTPException(502, detail='Identity provider returned invalid data')
            removed = client.delete(f'{url}/auth/v1/admin/users/{user_id}', headers={
                'apikey': service_key,
                'Authorization': f'Bearer {service_key}',
            })
            if removed.status_code not in (200, 204):
                raise HTTPException(502, detail='Account deletion could not be completed')
    except httpx.RequestError:
        raise HTTPException(503, detail='Identity service temporarily unavailable')
    # Supabase's FK ON DELETE CASCADE removes owned profiles and saved results.
    # Remove local AI quota user identifiers without altering anonymous spend.
    try:
        anonymize_deleted_user(user_id)
    except (sqlite3.Error, OSError) as exc:
        # Auth deletion has already succeeded; never incorrectly claim failure.
        logger.error('Post-deletion quota anonymization unavailable (%s)', type(exc).__name__)
    return {'deleted': True}
