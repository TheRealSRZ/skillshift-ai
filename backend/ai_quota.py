"""Atomic, persistent AI job admission controls for a SINGLE shared filesystem.

SQLite transactions serialize slots between local worker processes. All attempts,
including failed ones, count against daily budgets. Slots release in finally.
For horizontally-scaled deployments use a shared transactional DB instead.
"""
from __future__ import annotations

from contextlib import contextmanager, closing
from datetime import datetime, timezone
import os
import math
from pathlib import Path
import sqlite3
import time
from uuid import uuid4

from fastapi import HTTPException


class QuotaUnavailable(Exception):
    """AI budget store could not be checked safely."""


def _int_env(name: str, default: int, *, minimum: int, maximum: int) -> int:
    try:
        result = int(os.getenv(name, str(default)))
    except ValueError as exc:
        raise QuotaUnavailable(f'Invalid setting: {name}') from exc
    if result < minimum or result > maximum:
        raise QuotaUnavailable(f'Invalid setting: {name}')
    return result


def _quota_path() -> Path:
    root = Path(__file__).resolve().parents[1]
    value = os.getenv('AI_QUOTA_DB_PATH')
    return Path(value).expanduser() if value else root / 'instance' / 'ai_quotas.sqlite3'


def _open():
    path = _quota_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(path), timeout=5.0, isolation_level=None)
    connection.execute('PRAGMA busy_timeout = 5000')
    connection.execute('''CREATE TABLE IF NOT EXISTS ai_attempts (
        request_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, started_at REAL NOT NULL
    )''')
    connection.execute('''CREATE INDEX IF NOT EXISTS idx_ai_attempts_user_time
        ON ai_attempts(user_id, started_at)''')
    connection.execute('''CREATE TABLE IF NOT EXISTS ai_active (
        request_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, started_at REAL NOT NULL
    )''')
    return connection


def _admit(user_id: str) -> str:
    user_limit = _int_env('AI_DAILY_LIMIT', 3, minimum=1, maximum=50)
    global_limit = _int_env('AI_GLOBAL_DAILY_LIMIT', 30, minimum=1, maximum=1000)
    concurrent = _int_env('AI_MAX_CONCURRENT', 1, minimum=1, maximum=10)
    cooldown = _int_env('AI_COOLDOWN_SECONDS', 45, minimum=0, maximum=3600)
    slot_ttl = _int_env('AI_SLOT_TTL_SECONDS', 300, minimum=60, maximum=3600)
    # The slot must not expire while a cold-start GPU request can still be
    # running, otherwise a second request could evade the concurrency limit.
    try:
        max_poll = float(os.getenv('RUNPOD_POLL_TIMEOUT', '30'))
    except ValueError as exc:
        raise QuotaUnavailable('Invalid RunPod poll timeout') from exc
    if not math.isfinite(max_poll) or not 0 <= max_poll <= 600 or slot_ttl < max_poll + 45:
        raise QuotaUnavailable('AI_SLOT_TTL_SECONDS must exceed RunPod poll timeout by 45 seconds')
    now = time.time()
    day_start = datetime.fromtimestamp(now, tz=timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0).timestamp()
    request_id = str(uuid4())

    with closing(_open()) as conn:
        conn.execute('BEGIN IMMEDIATE')
        try:
            # Recovery if the original process was killed while holding a slot.
            conn.execute('DELETE FROM ai_active WHERE started_at < ?', (now - slot_ttl,))
            global_used = conn.execute('SELECT COUNT(*) FROM ai_attempts WHERE started_at >= ?', (day_start,)).fetchone()[0]
            user_used = conn.execute('SELECT COUNT(*) FROM ai_attempts WHERE user_id = ? AND started_at >= ?', (user_id, day_start)).fetchone()[0]
            active_global = conn.execute('SELECT COUNT(*) FROM ai_active').fetchone()[0]
            active_user = conn.execute('SELECT COUNT(*) FROM ai_active WHERE user_id = ?', (user_id,)).fetchone()[0]
            latest = conn.execute('SELECT MAX(started_at) FROM ai_attempts WHERE user_id = ?', (user_id,)).fetchone()[0]
            reject = None
            retry = 60
            if user_used >= user_limit or global_used >= global_limit:
                reject = 'AI personalization daily allowance reached. Approved courses remain available.'
                retry = max(1, int(day_start + 86400 - now))
            elif active_user:
                reject = 'AI personalization is already running for this account.'
                retry = 30
            elif active_global >= concurrent:
                reject = 'AI is busy. Please try again shortly; your approved roadmap is available.'
                retry = 20
            elif latest is not None and now - latest < cooldown:
                reject = 'Please wait before requesting AI personalization again.'
                retry = max(1, int(cooldown - (now - latest) + 0.999))
            if reject:
                conn.execute('COMMIT')
                raise HTTPException(status_code=429, detail=reject, headers={'Retry-After': str(retry)})
            conn.execute('INSERT INTO ai_attempts VALUES (?, ?, ?)', (request_id, user_id, now))
            conn.execute('INSERT INTO ai_active VALUES (?, ?, ?)', (request_id, user_id, now))
            # Keep the audit compact without dropping today's quotas.
            conn.execute('DELETE FROM ai_attempts WHERE started_at < ?', (day_start - 86400 * 7,))
            conn.execute('COMMIT')
        except Exception:
            if conn.in_transaction:
                conn.execute('ROLLBACK')
            raise
    return request_id


def _release(request_id: str) -> None:
    with closing(_open()) as conn:
        conn.execute('DELETE FROM ai_active WHERE request_id = ?', (request_id,))


@contextmanager
def ai_job_slot(user_id: str):
    try:
        request_id = _admit(user_id)
    except (sqlite3.Error, OSError, QuotaUnavailable) as exc:
        raise HTTPException(status_code=503, detail='AI usage controls are unavailable; approved courses remain available.') from exc
    try:
        yield request_id
    finally:
        try:
            _release(request_id)
        except (sqlite3.Error, OSError):
            # Fail closed on next admission until the stale slot expires.
            pass


def anonymize_deleted_user(user_id: str) -> None:
    """Erase the Supabase user ID from local AI quotas after account deletion.

    Preserve anonymous global spend counters and active slot IDs so deletion
    cannot reset the GPU daily limit or release another running job early.
    """
    if not _quota_path().exists():
        return
    with closing(_open()) as conn:
        conn.execute('BEGIN IMMEDIATE')
        try:
            # SQL table identifiers cannot be parameterized with DB-API `?`.
            # Keep both statements static; only the user ID is supplied as data.
            conn.execute(
                "UPDATE ai_attempts SET user_id = 'deleted:' || request_id WHERE user_id = ?",
                (user_id,),
            )
            conn.execute(
                "UPDATE ai_active SET user_id = 'deleted:' || request_id WHERE user_id = ?",
                (user_id,),
            )
            conn.execute('COMMIT')
        except Exception:
            if conn.in_transaction:
                conn.execute('ROLLBACK')
            raise
