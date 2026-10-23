"""Attack-style regression tests for the API trust boundary (no live network)."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.ai_quota import ai_job_slot
from fastapi import HTTPException

client = TestClient(app)
VALID = {'profile': {'education': 'Test user', 'skills': ['skill_sql'], 'interests': []}, 'scenario': 'moderate'}


def test_security_headers_and_no_cors_wildcard():
    response = client.get('/api/catalog')
    assert response.status_code == 200
    assert response.headers['x-content-type-options'] == 'nosniff'
    assert response.headers['x-frame-options'] == 'DENY'
    assert response.headers['cache-control'] == 'no-store'
    assert "object-src 'none'" in response.headers['content-security-policy']
    assert "frame-ancestors 'none'" in response.headers['content-security-policy']
    assert 'access-control-allow-origin' not in response.headers


def test_body_rejection_from_content_length(monkeypatch):
    monkeypatch.setenv('API_MAX_BODY_BYTES', '1024')
    response = client.post('/api/analyze', json={'profile': {'education': 'z'*2500, 'skills': []}})
    assert response.status_code == 413
    assert response.headers['x-content-type-options'] == 'nosniff'


def test_body_limit_without_content_length(monkeypatch):
    monkeypatch.setenv('API_MAX_BODY_BYTES', '1024')
    def big_stream():
        yield b'{"profile":{"education":"'
        yield b'x' * 1100
        yield b'"}}'
    response = client.post('/api/analyze', content=big_stream(), headers={'Content-Type': 'application/json'})
    assert response.status_code == 413


def test_wrong_content_type_fails_without_parsing():
    response = client.post('/api/analyze', content='profile=abc', headers={'Content-Type': 'application/x-www-form-urlencoded'})
    assert response.status_code == 415


def test_small_valid_json_and_unicode_work():
    assert client.post('/api/analyze', json=VALID).status_code == 200
    unicode_profile = {**VALID, 'profile': {**VALID['profile'], 'education': 'Pelajar universiti'}}
    assert client.post('/api/analyze', json=unicode_profile).status_code == 200


def test_ip_rate_limit_blocks_bursts_but_health_remains_available(monkeypatch):
    monkeypatch.setenv('API_RATE_PER_MINUTE', '2')
    assert client.get('/api/catalog').status_code == 200
    assert client.post('/api/analyze', json=VALID).status_code == 200
    blocked = client.post('/api/scenarios', json=VALID)
    assert blocked.status_code == 429
    assert int(blocked.headers['retry-after']) > 0
    assert client.get('/api/health').status_code == 200
    # A real ASGI client address is used rather than a forgeable forwarded header.
    assert client.get('/api/catalog', headers={'X-Forwarded-For': '8.8.8.8'}).status_code == 429


def test_rate_database_failure_fails_closed(monkeypatch, tmp_path):
    parent_as_file = tmp_path / 'not-a-directory'
    parent_as_file.write_text('x')
    monkeypatch.setenv('API_RATE_DB_PATH', str(parent_as_file / 'hits.sqlite3'))
    response = client.post('/api/analyze', json=VALID)
    assert response.status_code == 503
    assert 'traceback' not in response.text.lower()


def test_invalid_rate_limit_settings_fail_closed(monkeypatch):
    monkeypatch.setenv('API_RATE_PER_MINUTE', '-1')
    assert client.post('/api/analyze', json=VALID).status_code == 503


def test_request_models_reject_unbounded_strings_and_extras():
    too_long = {**VALID, 'profile': {**VALID['profile'], 'skills': ['A'*10000]}}
    assert client.post('/api/analyze', json=too_long).status_code == 422
    unknown_field = {**VALID, 'surprise_admin': True}
    assert client.post('/api/analyze', json=unknown_field).status_code == 422
    long_interest = {**VALID, 'profile': {**VALID['profile'], 'interests': ['X' * 10000]}}
    assert client.post('/api/analyze', json=long_interest).status_code == 422


def test_bad_runpod_endpoint_or_job_id_never_used_in_urls(monkeypatch):
    from ai.runpod_client import ask_ai
    import ai.runpod_client as runpod
    monkeypatch.setenv('RUNPOD_API_KEY', 'fake-test-key')
    monkeypatch.setenv('RUNPOD_ENDPOINT_ID', '../malicious')
    monkeypatch.setattr(runpod.requests, 'post', lambda *a, **kw: pytest.fail('must not send'))
    with pytest.raises(ValueError, match='endpoint ID'):
        ask_ai('safe test')

    monkeypatch.setenv('RUNPOD_ENDPOINT_ID', 'legitimate-endpoint')
    class BadJob:
        def raise_for_status(self): pass
        def json(self): return {'id': '../../unexpected-path'}
    monkeypatch.setattr(runpod.requests, 'post', lambda *a, **kw: BadJob())
    monkeypatch.setattr(runpod.requests, 'get', lambda *a, **kw: pytest.fail('must not poll unsafe job ID'))
    with pytest.raises(RuntimeError, match='invalid job ID'):
        ask_ai('safe test')


def test_poll_timeout_cannot_outlive_gpu_concurrency_slot(monkeypatch):
    monkeypatch.setenv('AI_QUOTA_DB_PATH', str(Path(os.getenv('API_RATE_DB_PATH')).with_name('ai_slot.sqlite3')))
    monkeypatch.setenv('AI_SLOT_TTL_SECONDS', '300')
    monkeypatch.setenv('RUNPOD_POLL_TIMEOUT', '600')
    with pytest.raises(HTTPException) as err:
        with ai_job_slot('test-uuid'):
            pass
    assert err.value.status_code == 503


def test_production_fails_closed_without_host_allowlist(monkeypatch):
    env = dict(os.environ, APP_ENV='production', AI_ENABLED='false')
    env.pop('ALLOWED_HOSTS', None)
    result = subprocess.run([sys.executable, '-c', 'import backend.main'],
                            cwd=Path(__file__).resolve().parents[2], env=env,
                            capture_output=True, text=True, timeout=10)
    assert result.returncode != 0
    assert 'ALLOWED_HOSTS' in result.stderr


def test_production_does_not_open_api_docs(monkeypatch):
    env = dict(os.environ, APP_ENV='production', ALLOWED_HOSTS='example.com', AI_ENABLED='false')
    result = subprocess.run([sys.executable, '-c', 'from backend.main import app; print(app.openapi_url)'],
                            cwd=Path(__file__).resolve().parents[2], env=env,
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == 'None'


def test_deleting_account_anonymizes_quota_identifier(monkeypatch, tmp_path):
    from backend.ai_quota import ai_job_slot, anonymize_deleted_user
    import sqlite3
    user_id = '33333333-3333-4333-8333-333333333333'
    db = tmp_path / 'ai_quota.sqlite3'
    monkeypatch.setenv('AI_QUOTA_DB_PATH', str(db))
    monkeypatch.setenv('AI_COOLDOWN_SECONDS', '0')
    with ai_job_slot(user_id):
        pass
    anonymize_deleted_user(user_id)
    with sqlite3.connect(db) as connection:
        rows = connection.execute('SELECT user_id FROM ai_attempts').fetchall()
        assert len(rows) == 1
        assert rows[0][0].startswith('deleted:')
        assert user_id not in rows[0][0]


def test_production_paid_ai_requires_explicit_quota_location():
    env = dict(os.environ, APP_ENV='production', ALLOWED_HOSTS='example.com', AI_ENABLED='true')
    env.pop('AI_QUOTA_DB_PATH', None)
    result = subprocess.run([sys.executable, '-c', 'import backend.main'],
                            cwd=Path(__file__).resolve().parents[2], env=env,
                            capture_output=True, text=True, timeout=10)
    assert result.returncode != 0
    assert 'AI_QUOTA_DB_PATH' in result.stderr
