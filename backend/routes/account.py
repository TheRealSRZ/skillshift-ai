"""Authenticated account deletion. Never exposed to unverified client-supplied user IDs."""
import os
from uuid import UUID
from urllib.parse import urlsplit

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, Header, HTTPException

load_dotenv()

router = APIRouter(prefix='/api/account', tags=['Account'])

def _settings():
    url = os.getenv('SUPABASE_URL', '').strip().rstrip('/')
    publishable = os.getenv('SUPABASE_PUBLISHABLE_KEY', '').strip()
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '').strip()
    # Supabase hosted project URLs must be HTTPS; no untrusted request supplied URLs.
    parsed = urlsplit(url)
    if (parsed.scheme != 'https' or not parsed.hostname or
            not parsed.hostname.endswith('.supabase.co') or
            parsed.username or parsed.password or parsed.port or
            not publishable or not service_key):
        raise HTTPException(503, detail='Account deletion is not configured')
    return url, publishable, service_key

@router.delete('/me')
def delete_current_account(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(401, detail='Authentication required')
    access_token = authorization[7:].strip()
    if not access_token or len(access_token) > 8192:
        raise HTTPException(401, detail='Invalid session')
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
            except (ValueError, TypeError, KeyError):
                raise HTTPException(502, detail='Identity provider returned invalid data')
            removed = client.delete(f'{url}/auth/v1/admin/users/{user_id}', headers={
                'apikey': service_key,
                'Authorization': f'Bearer {service_key}',
            })
            if removed.status_code not in (200, 204):
                raise HTTPException(502, detail='Account deletion could not be completed')
    except httpx.RequestError:
        raise HTTPException(503, detail='Identity service temporarily unavailable')
    return {'deleted': True}
