"""Member 2 release checks: what-if is deterministic, bounded and read-only.

The SQL migration is validated structurally here; only a live Supabase/Postgres
instance can verify trigger/RLS behavior, so it must be tested on deployment.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)
BASE = {'education': 'Student', 'skills': ['skill_python', 'skill_sql'], 'interests': ['data']}
ROLE = 'role_data_analyst'


def _body(**kwargs):
    return {'profile': BASE, 'target_role': ROLE, 'add_skills': ['skill_power_bi'], 'scenario': 'moderate', **kwargs}


def test_whatif_recomputes_using_real_matching_weights():
    original = client.post('/api/analyze', json={'profile': BASE, 'scenario': 'moderate'}).json()
    initial = next(r for r in original['matches'] if r['role_id'] == ROLE)
    preview = client.post('/api/what-if', json=_body())
    assert preview.status_code == 200, preview.text
    result = preview.json()
    updated_profile = {**BASE, 'skills': BASE['skills'] + ['skill_power_bi']}
    updated = client.post('/api/analyze', json={'profile': updated_profile, 'scenario': 'moderate'}).json()
    expected = next(r for r in updated['matches'] if r['role_id'] == ROLE)
    assert result['original_readiness'] == initial['readiness_score']
    assert result['hypothetical_readiness'] == expected['readiness_score']
    assert result['delta_points'] == round(expected['readiness_score'] - initial['readiness_score'], 1)
    assert result['trend_snapshot_id'] == original['trend_snapshot_id']
    assert 'not verified' in result['note'].lower()
    assert 'skill_power_bi' not in result['remaining_missing_skills']
    assert 'skill_power_bi' not in BASE['skills']  # no mutation


def test_whatif_works_for_rapid_scenario_and_guest():
    response = client.post('/api/what-if', json=_body(scenario='rapid'))
    assert response.status_code == 200, response.text
    assert response.json()['scenario'] == 'rapid'
    assert 'x-request-id' in response.headers
    assert len(response.headers['x-request-id']) == 32
    # No authentication, no RunPod, no profile persistence required.
    assert client.post('/api/roadmap', json={
        'target_role': ROLE, 'missing_skills': ['skill_power_bi'], 'scenario': 'moderate'
    }).status_code == 200


def test_whatif_rejects_unknown_role_skill_and_already_held_skills():
    assert client.post('/api/what-if', json=_body(target_role='role_missing')).status_code == 422
    assert client.post('/api/what-if', json=_body(add_skills=['skill_not_in_catalog'])).status_code == 422
    assert client.post('/api/what-if', json=_body(add_skills=['skill_python'])).status_code == 422
    assert client.post('/api/what-if', json=_body(add_skills=['skill_networking'])).status_code == 422
    assert client.post('/api/what-if', json=_body(add_skills=[])).status_code == 422
    assert client.post('/api/what-if', json=_body(add_skills=['skill_power_bi'] * 2)).status_code == 422


def test_whatif_is_bounded_and_rejects_unexpected_fields():
    too_many = ['skill_power_bi'] * 11
    assert client.post('/api/what-if', json=_body(add_skills=too_many)).status_code == 422
    assert client.post('/api/what-if', json=_body(injected_admin=True)).status_code == 422
    assert client.post('/api/what-if', json=_body(target_role='../role_data_analyst')).status_code == 422
    assert client.post('/api/what-if', json=_body(add_skills=['skill_sql\x00'])).status_code == 422
    assert client.post('/api/what-if', json=_body(profile={**BASE, 'education': 'A\x00B'})).status_code == 422
    assert client.post('/api/what-if', json=_body(profile={**BASE, 'education': 'Pelajar universiti 🎓'})).status_code == 200
    assert client.post('/api/what-if', json=_body(profile={**BASE, 'education': 'Code <script>example</script>'})).status_code == 200


def test_whatif_rate_limited_like_other_api_routes(monkeypatch, tmp_path):
    monkeypatch.setenv('API_RATE_DB_PATH', str(tmp_path / 'api_rate.sqlite3'))
    monkeypatch.setenv('API_RATE_PER_MINUTE', '1')
    assert client.post('/api/what-if', json=_body()).status_code == 200
    second = client.post('/api/what-if', json=_body())
    assert second.status_code == 429
    assert int(second.headers['retry-after']) > 0


def test_request_ids_are_server_generated_not_client_echoed():
    first = client.get('/api/catalog', headers={'X-Request-ID': 'fake-user-controlled'})
    second = client.get('/api/catalog')
    assert first.status_code == second.status_code == 200
    assert first.headers['x-request-id'] != 'fake-user-controlled'
    assert first.headers['x-request-id'] != second.headers['x-request-id']


def test_invalid_app_env_fails_closed():
    root = Path(__file__).resolve().parents[2]
    env = {**os.environ, 'APP_ENV': 'prod'}
    proc = subprocess.run([sys.executable, '-c', 'import backend.main'], cwd=root,
                          env=env, capture_output=True, text=True, timeout=15)
    assert proc.returncode != 0
    assert 'APP_ENV must be' in proc.stderr


def test_invalid_production_hostname_fails_closed():
    root = Path(__file__).resolve().parents[2]
    for bad in ('*.replit.app', 'http://example.com', 'example.com:443', '*'):
        env = {**os.environ, 'APP_ENV': 'production', 'ALLOWED_HOSTS': bad, 'AI_ENABLED': 'false'}
        proc = subprocess.run([sys.executable, '-c', 'import backend.main'], cwd=root,
                              env=env, capture_output=True, text=True, timeout=15)
        assert proc.returncode != 0
        assert 'ALLOWED_HOSTS' in proc.stderr


def test_migration_has_private_definer_and_bounded_storage():
    migration = (Path(__file__).resolve().parents[2] / 'supabase/migrations/20261023_skillshift_storage_limits.sql').read_text()
    assert migration.count('SECURITY DEFINER SET search_path =') == 2
    assert 'pg_advisory_xact_lock' in migration
    assert 'BEFORE INSERT' in migration
    assert 'octet_length(result::text)' in migration
    assert 'octet_length(roadmap::text)' in migration
    assert 'FROM public.saved_analyses' in migration
    assert 'FROM public.saved_roadmaps' in migration


def test_whatif_combined_missing_skills_reach_complete_readiness():
    result = client.post('/api/what-if', json=_body(add_skills=['skill_power_bi', 'skill_data_viz']))
    assert result.status_code == 200
    assert result.json()['hypothetical_readiness'] == 100.0
    assert result.json()['remaining_missing_skills'] == []


def test_whatif_source_catalog_failure_does_not_leak_exception(monkeypatch):
    import backend.routes.what_if as what_if_route
    loader = what_if_route.load_json
    def corrupt_catalog(name):
        if name == 'careers.json':
            return [{'id': ROLE, 'title': 'Broken catalog'}]
        return loader(name)
    monkeypatch.setattr(what_if_route, 'load_json', corrupt_catalog)
    response = client.post('/api/what-if', json=_body())
    assert response.status_code == 503
    assert 'traceback' not in response.text.lower()


def test_uncoverable_course_gaps_cannot_consume_ai_quota(monkeypatch):
    from backend.routes import roadmap as route
    monkeypatch.setenv('AI_ENABLED', 'true')
    monkeypatch.setattr(route, 'verify_supabase_user',
                        lambda _token: (_ for _ in ()).throw(AssertionError('No GPU budget required')))
    request = {
        'target_role': 'role_security_analyst',
        'missing_skills': ['skill_networking'],
        'scenario': 'moderate',
    }
    plain = client.post('/api/roadmap', json=request)
    assert plain.status_code == 200
    assert not plain.json()['steps']
    personalized = client.post('/api/roadmap/personalize', json=request,
                               headers={'Authorization': 'Bearer nonempty-test-token'})
    assert personalized.status_code == 422
    assert 'No approved courses' in personalized.json()['detail']
