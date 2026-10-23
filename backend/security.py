"""HTTP boundary controls for SkillShift's public FastAPI endpoints.

No client-supplied X-Forwarded-For value is trusted: the ASGI server / trusted
reverse proxy must populate scope['client'] correctly. SQLite counters work for
one instance with a persistent shared disk, not for autoscaling deployments.
"""
from __future__ import annotations

from contextlib import closing
import hashlib
import logging
import os
from pathlib import Path
import sqlite3
import time
from uuid import uuid4
from typing import Callable

from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)
MAX_DEFAULT_BODY_BYTES = 32 * 1024
RATE_LIMITED_PATHS = frozenset({
    '/api/analyze', '/api/scenarios', '/api/roadmap',
    '/api/roadmap/personalize', '/api/what-if',
})
JSON_POST_PATHS = RATE_LIMITED_PATHS


def _bounded_int(name: str, fallback: int, minimum: int, maximum: int) -> int:
    try:
        result = int(os.getenv(name, str(fallback)))
    except ValueError as exc:
        raise RuntimeError(f'Invalid security setting {name}') from exc
    if not minimum <= result <= maximum:
        raise RuntimeError(f'Invalid security setting {name}')
    return result


def _rate_db_path() -> Path:
    path = os.getenv('API_RATE_DB_PATH')
    return Path(path).expanduser() if path else Path(__file__).resolve().parents[1] / 'instance' / 'api_rate.sqlite3'


def _rate_admit(client_ip: str) -> tuple[bool, int]:
    """Atomic 60-second rolling-window guard. DB failure is fail-closed."""
    limit = _bounded_int('API_RATE_PER_MINUTE', 120, 1, 10000)
    now = time.time()
    hashed_ip = hashlib.sha256(client_ip.encode('utf-8')).hexdigest()
    path = _rate_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(str(path), timeout=3.0, isolation_level=None)) as conn:
        conn.execute('PRAGMA busy_timeout=3000')
        conn.execute('''CREATE TABLE IF NOT EXISTS api_rate_hits (
            id INTEGER PRIMARY KEY, ip_hash TEXT NOT NULL, started_at REAL NOT NULL
        )''')
        conn.execute('''CREATE INDEX IF NOT EXISTS idx_api_rate_hits_ip_time
            ON api_rate_hits(ip_hash, started_at)''')
        conn.execute('BEGIN IMMEDIATE')
        try:
            # Retention is short; rate-limit tables must not become permanent IP logs.
            conn.execute('DELETE FROM api_rate_hits WHERE started_at < ?', (now - 120,))
            count, oldest = conn.execute('''SELECT COUNT(*), MIN(started_at) FROM api_rate_hits
                WHERE ip_hash=? AND started_at >= ?''', (hashed_ip, now - 60)).fetchone()
            if count >= limit:
                conn.execute('COMMIT')
                return False, max(1, int(61 - (now - oldest)))
            conn.execute('INSERT INTO api_rate_hits (ip_hash, started_at) VALUES (?, ?)', (hashed_ip, now))
            conn.execute('COMMIT')
            return True, 0
        except BaseException:
            if conn.in_transaction:
                conn.execute('ROLLBACK')
            raise


class ApiSecurityMiddleware:
    """Bound API body size, reject unexpected content types, and emit safe headers.

    The small JSON requests are buffered before passing to FastAPI, so an
    untrusted stream without Content-Length cannot bypass the byte limit.
    """

    def __init__(self, app: Callable):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return
        path = scope.get('path', '')
        method = scope.get('method', 'GET').upper()
        raw_headers = scope.get('headers', [])
        headers = {key.lower(): value for key, value in raw_headers}
        is_api = path.startswith('/api/')
        request_id = uuid4().hex if is_api else None
        started = time.monotonic()

        async def secure_send(message):
            if message['type'] == 'http.response.start':
                # Record only server-generated IDs, bounded static route categories,
                # status and duration. Never log tokens, request bodies or query params.
                status = int(message['status'])
                if is_api and status >= 400:
                    category = path if path in RATE_LIMITED_PATHS else 'other_api'
                    logger.info('api_response request_id=%s route=%s status=%d elapsed_ms=%d',
                                request_id, category, status, round((time.monotonic()-started)*1000))
                present = {key.lower() for key, _ in message.get('headers', [])}
                security_headers = {
                    b'x-content-type-options': b'nosniff',
                    b'x-frame-options': b'DENY',
                    b'referrer-policy': b'strict-origin-when-cross-origin',
                    b'permissions-policy': b'camera=(), microphone=(), geolocation=()',
                    b'content-security-policy': (
                        b"default-src 'self'; base-uri 'self'; object-src 'none'; "
                        b"frame-ancestors 'none'; form-action 'self'; "
                        b"script-src 'self'; style-src 'self' 'unsafe-inline'; "
                        b"img-src 'self' data: https:; font-src 'self' data: https:; "
                        b"connect-src 'self' https://*.supabase.co wss://*.supabase.co"
                    ),
                }
                if is_api:
                    security_headers[b'cache-control'] = b'no-store'
                    security_headers[b'x-request-id'] = request_id.encode('ascii')
                if os.getenv('SECURITY_HSTS_ENABLED', 'false').lower() == 'true':
                    # Enable only when the *whole public site* uses HTTPS.
                    security_headers[b'strict-transport-security'] = b'max-age=31536000'
                for key, value in security_headers.items():
                    if key not in present:
                        message.setdefault('headers', []).append((key, value))
            await send(message)

        async def reject(code: int, message: str, extra_headers: dict[str, str] | None = None):
            response = JSONResponse({'detail': message}, status_code=code, headers=extra_headers)
            await response(scope, receive, secure_send)

        if is_api and path != '/api/health':
            try:
                client_ip = str((scope.get('client') or ('unknown',))[0])
                allowed, retry_after = await run_in_threadpool(_rate_admit, client_ip)
            except (sqlite3.Error, OSError, RuntimeError) as exc:
                logger.error('Public API rate controls unavailable (%s)', type(exc).__name__)
                await reject(503, 'Request protection is temporarily unavailable.')
                return
            if not allowed:
                await reject(429, 'Too many requests. Please try again shortly.', {'Retry-After': str(retry_after)})
                return

        if method in {'POST', 'PUT', 'PATCH', 'DELETE'} and is_api:
            try:
                limit = _bounded_int('API_MAX_BODY_BYTES', MAX_DEFAULT_BODY_BYTES, 1024, 1024 * 1024)
            except RuntimeError:
                await reject(503, 'Request protection is temporarily unavailable.')
                return
            size = headers.get(b'content-length')
            if size is not None:
                try:
                    declared = int(size)
                    if declared < 0:
                        raise ValueError()
                except ValueError:
                    await reject(400, 'Invalid Content-Length.')
                    return
                if declared > limit:
                    await reject(413, 'Request body is too large.')
                    return
            if method == 'POST' and path in JSON_POST_PATHS:
                content_type = headers.get(b'content-type', b'').decode('latin-1').split(';', 1)[0].strip().lower()
                if content_type != 'application/json':
                    await reject(415, 'JSON request body required.')
                    return

            chunks = []
            total = 0
            while True:
                message = await receive()
                if message['type'] == 'http.disconnect':
                    return
                if message['type'] != 'http.request':
                    continue
                chunk = message.get('body', b'')
                total += len(chunk)
                if total > limit:
                    await reject(413, 'Request body is too large.')
                    return
                chunks.append(chunk)
                if not message.get('more_body', False):
                    break
            body = b''.join(chunks)
            delivered = False

            async def bounded_receive():
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {'type': 'http.request', 'body': body, 'more_body': False}
                return await receive()

            await self.app(scope, bounded_receive, secure_send)
            return

        await self.app(scope, receive, secure_send)
