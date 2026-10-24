"""Phase 6E: AI spend protection, identity verification, and deployment checks.

All network/provider calls are mocked; these tests never spend RunPod credits.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import tomllib

import httpx
from fastapi import HTTPException
from fastapi.testclient import TestClient
import pytest

from backend.ai_access import verify_supabase_user
from backend.ai_quota import ai_job_slot
from backend.main import app
from backend.routes import roadmap as route
import backend.roadmap_adapter as adapter

REQUEST = {
    'target_role': 'role_data_professional',
    'missing_skills': ['skill_data_viz', 'skill_sql'],
    'scenario': 'moderate',
}
USER1 = '11111111-1111-4111-8111-111111111111'
USER2 = '22222222-2222-4222-8222-222222222222'


@pytest.fixture(autouse=True)
def private_ai_quota(monkeypatch, tmp_path):
    monkeypatch.setenv('AI_QUOTA_DB_PATH', str(tmp_path / 'ai_test.sqlite3'))
    monkeypatch.setenv('AI_DAILY_LIMIT', '3')
    monkeypatch.setenv('AI_GLOBAL_DAILY_LIMIT', '5')
    monkeypatch.setenv('AI_MAX_CONCURRENT', '1')
    monkeypatch.setenv('AI_COOLDOWN_SECONDS', '0')
    monkeypatch.setenv('AI_SLOT_TTL_SECONDS', '300')
    monkeypatch.setenv('AI_ENABLED', 'true')


def _send(token='valid-test-session'):
    headers = {'Authorization': f'Bearer {token}'} if token else {}
    return TestClient(app).post('/api/roadmap/personalize', json=REQUEST, headers=headers)


def test_guest_cannot_consume_gpu(monkeypatch):
    monkeypatch.setattr(adapter, 'generate_roadmap', lambda *args, **kw: pytest.fail('No inference allowed for guests') if kw.get('use_ai') else _baseline(*args))
    result = _send(None)
    assert result.status_code == 401
    assert 'sign in' in result.json()['detail'].lower()


def _baseline(*args):
    from ai.learning_planner import generate_roadmap
    return generate_roadmap(*args, use_ai=False)


def test_authenticated_ai_validation_and_atomic_budget(monkeypatch):
    monkeypatch.setattr(route, 'verify_supabase_user', lambda token: USER1)
    from ai.learning_planner import generate_roadmap

    def planner(*args, use_ai=False):
        if not use_ai:
            return generate_roadmap(*args, use_ai=False)
        courses = args[3]
        selected = [c for c in courses if set(c['skill_ids']).intersection(REQUEST['missing_skills'])]
        return {
            'target_role': REQUEST['target_role'], 'scenario': REQUEST['scenario'],
            'generation_mode': 'runpod_ai',
            'steps': [{'course_id': c['id'], 'reason': 'Review this approved course for your skill.'} for c in selected],
        }
    monkeypatch.setattr(adapter, 'generate_roadmap', planner)
    for _ in range(3):
        response = _send()
        assert response.status_code == 200, response.text
        assert response.json()['generation_mode'] == 'runpod_validated'
    assert _send().status_code == 429
    # A different user is not prevented by this user's allowance.
    monkeypatch.setattr(route, 'verify_supabase_user', lambda token: USER2)
    assert _send().status_code == 200


def test_gpu_slots_are_atomic_and_released_on_failure():
    with ai_job_slot(USER1):
        with pytest.raises(HTTPException) as blocked:
            with ai_job_slot(USER2):
                pytest.fail('Concurrent GPU job must be denied')
        assert blocked.value.status_code == 429
    # Slot is reusable after a completed or failed call.
    with pytest.raises(ValueError):
        with ai_job_slot(USER2):
            raise ValueError('simulated worker exception')
    with ai_job_slot(USER2):
        pass


def test_global_budget_across_accounts(monkeypatch):
    monkeypatch.setenv('AI_DAILY_LIMIT', '5')
    for i in range(5):
        with ai_job_slot(f'user-{i}'):
            pass
    with pytest.raises(HTTPException) as cap:
        with ai_job_slot('user-new'):
            pass
    assert cap.value.status_code == 429
    assert 'Retry-After' in cap.value.headers


def test_quota_is_persistent_across_new_connections(monkeypatch):
    monkeypatch.setenv('AI_DAILY_LIMIT', '1')
    with ai_job_slot(USER1):
        pass
    with pytest.raises(HTTPException) as cap:
        with ai_job_slot(USER1):
            pass
    assert cap.value.status_code == 429


def test_invalid_quota_settings_fail_closed(monkeypatch):
    monkeypatch.setenv('AI_GLOBAL_DAILY_LIMIT', 'no-limit')
    with pytest.raises(HTTPException) as cap:
        with ai_job_slot(USER1):
            pytest.fail('Misconfigured quotas must not grant a slot')
    assert cap.value.status_code == 503


def test_auth_verifier_calls_supabase_not_client_claims(monkeypatch):
    monkeypatch.setenv('SUPABASE_URL', 'https://myproject.supabase.co')
    monkeypatch.setenv('SUPABASE_PUBLISHABLE_KEY', 'public-test-key')
    calls = []

    class MockHTTP:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def get(self, url, headers):
            calls.append((url, headers))
            return httpx.Response(200, json={'id': USER1, 'email': 'test@example.com'})
    monkeypatch.setattr('backend.ai_access.httpx.Client', lambda **kw: MockHTTP())
    assert verify_supabase_user('Bearer access-token-for-test') == USER1
    assert calls[0][0] == 'https://myproject.supabase.co/auth/v1/user'
    assert calls[0][1]['Authorization'] == 'Bearer access-token-for-test'


def test_auth_invalid_token_is_rejected(monkeypatch):
    monkeypatch.setenv('SUPABASE_URL', 'https://myproject.supabase.co')
    monkeypatch.setenv('SUPABASE_PUBLISHABLE_KEY', 'public-test-key')

    class MockHTTP:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def get(self, url, headers): return httpx.Response(401)
    monkeypatch.setattr('backend.ai_access.httpx.Client', lambda **kw: MockHTTP())
    with pytest.raises(HTTPException) as failure:
        verify_supabase_user('Bearer expired-test-token')
    assert failure.value.status_code == 401


def test_auth_rejects_malicious_url(monkeypatch):
    monkeypatch.setenv('SUPABASE_URL', 'https://myproject.supabase.co.evil.example')
    monkeypatch.setenv('SUPABASE_PUBLISHABLE_KEY', 'public-test-key')
    with pytest.raises(HTTPException) as failure:
        verify_supabase_user('Bearer token')
    assert failure.value.status_code == 503


def test_failed_ai_attempt_charges_quota_and_preserves_public_roadmap(monkeypatch):
    monkeypatch.setenv('AI_DAILY_LIMIT', '1')
    monkeypatch.setattr(route, 'verify_supabase_user', lambda token: USER1)
    monkeypatch.setattr('ai.learning_planner.ask_ai', lambda _: (_ for _ in ()).throw(TimeoutError('private-runpod-job')))
    approved = TestClient(app).post('/api/roadmap', json=REQUEST)
    assert approved.status_code == 200
    assert approved.json()['generation_mode'] == 'deterministic_fallback'
    response = _send()
    assert response.status_code == 503
    assert 'private-runpod-job' not in response.text
    assert _send().status_code == 429
    assert TestClient(app).post('/api/roadmap', json=REQUEST).json() == approved.json()


def test_replit_build_run_commands_and_frontend_guard(tmp_path):
    """Verify the published venv startup and fail-closed frontend guard.

    Exercise the shell guard only on POSIX: Windows Bash may invoke WSL.
    """
    import os
    import shutil

    root = Path(__file__).resolve().parents[2]
    config = tomllib.loads((root / '.replit').read_text(encoding='utf-8'))
    build = config['deployment']['build']
    run = config['deployment']['run']
    assert build[:2] == ['bash', '-c']
    assert run[:2] == ['bash', '-c']
    build_command, run_command = build[2], run[2]

    # Replit's system Python is externally managed. Build in an isolated venv.
    assert 'python -m venv .venv' in build_command
    assert 'PIP_CONFIG_FILE=/dev/null' in build_command
    assert '.venv/bin/python -m pip install --no-user -r requirements.txt' in build_command
    assert 'bash scripts/build_frontend.sh' in build_command
    frontend_build = (root / 'scripts/build_frontend.sh').read_text(encoding='utf-8')
    assert 'npm ci' in frontend_build
    assert 'npm run build' in frontend_build
    assert 'dist/index.html' in frontend_build

    # The deployed service must use the same venv and reject a missing React build.
    assert 'frontend/dist/index.html' in run_command
    assert 'frontend/dist is missing' in run_command
    assert 'exit 1' in run_command
    assert '.venv/bin/python -m uvicorn backend.main:app' in run_command
    assert '--host 0.0.0.0' in run_command
    assert '--port ${PORT:-8000}' in run_command
    assert '--workers 1' in run_command

    # The local start script has its own guard, independent from the published run.
    script = (root / 'scripts/start.sh').read_text(encoding='utf-8')
    assert 'REQUIRE_FRONTEND_BUILD' in script
    assert 'frontend/dist/index.html' in script
    assert 'frontend/dist is missing' in script
    assert 'exit 1' in script

    # Do not start Uvicorn. With no dist/ folder, the deployment shell must fail
    # BEFORE any Python interpreter or network listener can be reached.
    if os.name != 'nt' and shutil.which('bash'):
        result = subprocess.run(
            ['bash', '-c', run_command],
            cwd=tmp_path,
            env={**os.environ, 'PORT': '1234'},
            text=True, capture_output=True, timeout=10,
        )
        assert result.returncode != 0
        assert 'frontend/dist is missing' in result.stderr

        (tmp_path / 'scripts').mkdir()
        (tmp_path / 'scripts' / 'start.sh').write_text(script, encoding='utf-8')
        result = subprocess.run(
            ['bash', 'scripts/start.sh'],
            cwd=tmp_path,
            env={**os.environ, 'REQUIRE_FRONTEND_BUILD': 'true', 'PORT': '1234'},
            text=True, capture_output=True, timeout=10,
        )
        assert result.returncode != 0
        assert 'frontend/dist is missing' in result.stderr


def test_ai_valueerror_reports_safe_diagnostic_category(monkeypatch, caplog):
    """The user's logged ValueError should be diagnosable without raw model text."""
    from ai.learning_planner import generate_roadmap
    monkeypatch.setattr('ai.learning_planner.ask_ai', lambda _: 'Not a valid list secret=do-not-log')
    approved = [{
        'id': 'course_test', 'title': 'Test Course', 'url': 'https://example.com',
        'skill_ids': ['skill_sql'], 'verified': True, 'estimated_hours': 1,
    }]
    with caplog.at_level('WARNING'):
        result = generate_roadmap('role_data_professional', ['skill_sql'], 'moderate', approved, use_ai=True)
    assert result['generation_mode'] == 'deterministic_fallback'
    assert 'missing_course_id_array' in caplog.text
    assert 'do-not-log' not in caplog.text
