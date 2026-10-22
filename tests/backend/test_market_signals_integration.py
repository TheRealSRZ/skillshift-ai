"""Phase 6C: read-only six-career DOSM contract and refresh integration tests."""

import copy
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.routes import market_signals as module
from backend.store import load_json

client = TestClient(app)
DATA = Path(__file__).resolve().parents[2] / 'data'


def test_market_signals_endpoint_matches_validated_source():
    response = client.get('/api/market-signals')
    assert response.status_code == 200
    assert response.json() == module.validate_market_signals(
        load_json('processed/market_signals_six_careers.json')
    )
    assert response.headers['content-type'].startswith('application/json')


def test_exact_six_careers_and_explicit_unavailable_data():
    data = client.get('/api/market-signals').json()
    signals = data['career_signals']
    assert {s['career_id'] for s in signals} == module.EXPECTED_CAREERS
    assert (data['observed_count'], data['insufficient_data_count']) == (3, 3)
    assert data['can_directly_adjust_career_scores'] is False
    assert all(s['can_directly_adjust_career_scores'] is False for s in signals)
    assert all(s['ai_impact_measure'] is False for s in signals)
    for signal in signals:
        if signal['data_status'] == 'observed_comparison_available':
            assert signal['previous_period'] == '2026-Q1'
            assert signal['latest_period'] == '2026-Q2'
            assert signal['source_urls']
        else:
            for key in ('previous_job_offerings', 'latest_job_offerings', 'absolute_change', 'percent_change', 'direction'):
                assert signal[key] is None


@pytest.mark.parametrize('tamper', [
    lambda p: p['career_signals'].append(copy.deepcopy(p['career_signals'][0])),
    lambda p: p['career_signals'][0].update(career_id='role_unlisted'),
    lambda p: p['career_signals'][0].update(percent_change=99.9),
    lambda p: p['career_signals'][0].update(previous_job_offerings=True),
    lambda p: p['career_signals'][0].update(direction='increase'),
    lambda p: p['career_signals'][3].update(latest_job_offerings=0),
    lambda p: p.update(can_directly_adjust_career_scores=True),
    lambda p: p['career_signals'][0].update(ai_impact_measure=True),
    lambda p: p.update(observed_count=6),
    lambda p: p.update(ai_impact_measure=True),
    lambda p: p.update(skill_specific=True),
    lambda p: p['career_signals'][0].update(source_urls=['javascript:alert(1)']),
    lambda p: p['career_signals'][3].update(source_urls=['https://example.invalid']),
    lambda p: p['career_signals'][0].update(latest_period='2099-Q4'),
])
def test_rejects_bad_evidence_without_inventing_fallback(tamper):
    data = load_json('processed/market_signals_six_careers.json')
    tamper(data)
    with pytest.raises(ValueError):
        module.validate_market_signals(data)


def test_endpoint_returns_503_for_invalid_or_missing_snapshot(monkeypatch):
    monkeypatch.setattr(module, 'load_json', lambda filename: {'bad': 'source'})
    response = client.get('/api/market-signals')
    assert response.status_code == 503
    assert 'temporarily unavailable' in response.json()['detail']
    monkeypatch.setattr(module, 'load_json', lambda filename: (_ for _ in ()).throw(FileNotFoundError(filename)))
    assert client.get('/api/market-signals').status_code == 503


def test_endpoint_refresh_reads_updated_snapshot_without_restarting_server(monkeypatch, tmp_path):
    """Simulates published snapshot replacement, and verifies API fetch reads it afresh."""
    source = load_json('processed/market_signals_six_careers.json')
    target = tmp_path / 'signals.json'
    target.write_text(json.dumps(source), encoding='utf-8')

    def read_temp(filename):
        assert filename == 'processed/market_signals_six_careers.json'
        return json.loads(target.read_text(encoding='utf-8'))

    monkeypatch.setattr(module, 'load_json', read_temp)
    assert client.get('/api/market-signals').json()['career_signals'][0]['latest_job_offerings'] == 19899

    # TEST FIXTURE ONLY: this is NOT an updated DOSM observation.
    updated = copy.deepcopy(source)
    example = updated['career_signals'][0]
    example['latest_job_offerings'] = 19999
    delta = 19999 - example['previous_job_offerings']
    example['absolute_change'] = delta
    example['percent_change'] = round(100 * delta / example['previous_job_offerings'], 2)
    example['direction'] = 'decrease' if delta < 0 else 'increase' if delta > 0 else 'unchanged'
    target.write_text(json.dumps(updated), encoding='utf-8')

    fresh = client.get('/api/market-signals')
    assert fresh.status_code == 200
    assert fresh.json()['career_signals'][0]['latest_job_offerings'] == 19999
    assert fresh.json()['career_signals'][0]['percent_change'] == -0.45
    assert load_json('processed/market_signals_six_careers.json')['career_signals'][0]['latest_job_offerings'] == 19899


def test_market_router_does_not_change_matching_or_synthetic_scenarios():
    profile = {'profile': {'education': 'Diploma', 'skills': ['skill_python', 'skill_sql'], 'interests': []}, 'scenario': 'moderate'}
    before = client.post('/api/analyze', json=profile)
    assert before.status_code == 200
    # Read-only fetch must not touch the matching inputs or scenario multipliers.
    assert client.get('/api/market-signals').status_code == 200
    after = client.post('/api/analyze', json=profile)
    assert after.status_code == 200
    assert before.json() == after.json()
    assert client.get('/api/trends').status_code == 200


def test_source_csv_rebuild_propagates_to_endpoint_without_touching_matching(monkeypatch, tmp_path):
    """Full source CSV -> existing Member 4 builder -> JSON -> endpoint test.

    Uses an isolated CSV copy with fabricated test input. Does not update project DOSM data.
    """
    import csv
    import subprocess
    import sys

    original_source = DATA / 'dosm_career_offerings_2026_q1_q2.csv'
    source_rows = list(csv.DictReader(original_source.open(encoding='utf-8-sig', newline='')))
    for row in source_rows:
        if row['career_id'] == 'role_software_developer' and row['period'] == '2026-Q2':
            row['job_offerings'] = '19999'  # TEST ONLY, not an actual DOSM figure.
    input_csv = tmp_path / 'test_offerings.csv'
    with input_csv.open('w', encoding='utf-8', newline='') as out:
        writer = csv.DictWriter(out, fieldnames=source_rows[0].keys())
        writer.writeheader()
        writer.writerows(source_rows)

    generated = tmp_path / 'regenerated_market_signals.json'
    cmd = [
        sys.executable, str(DATA.parent / 'data_pipeline' / 'build_six_career_signals.py'),
        '--careers', str(DATA / 'careers.json'),
        '--input', str(input_csv), '--output', str(generated),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=str(DATA.parent))
    payload = json.loads(generated.read_text(encoding='utf-8'))
    module.validate_market_signals(payload)
    before = client.post('/api/analyze', json={
        'profile': {'education': 'Diploma', 'skills': ['skill_python'], 'interests': []},
        'scenario': 'moderate'
    }).json()
    monkeypatch.setattr(module, 'load_json', lambda _: json.loads(generated.read_text(encoding='utf-8')))
    response = client.get('/api/market-signals')
    assert response.status_code == 200
    software = next(s for s in response.json()['career_signals'] if s['career_id'] == 'role_software_developer')
    assert software['latest_job_offerings'] == 19999
    assert software['percent_change'] == -0.45
    after = client.post('/api/analyze', json={
        'profile': {'education': 'Diploma', 'skills': ['skill_python'], 'interests': []},
        'scenario': 'moderate'
    }).json()
    assert before == after
    assert load_json('processed/market_signals_six_careers.json')['career_signals'][0]['latest_job_offerings'] == 19899
