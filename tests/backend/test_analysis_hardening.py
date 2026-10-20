from collections import Counter

from fastapi.testclient import TestClient

from backend.main import app
from backend.routes import analysis

client = TestClient(app)
PAYLOAD = {"profile": {"skills": ["skill_python", "skill_sql"]}, "scenario": "moderate"}


def test_scenarios_share_one_trend_snapshot(monkeypatch):
    original = analysis.load_json
    calls = Counter()

    def tracked_load_json(filename):
        calls[filename] += 1
        return original(filename)

    monkeypatch.setattr(analysis, "load_json", tracked_load_json)
    response = client.post("/api/scenarios", json=PAYLOAD)
    assert response.status_code == 200
    result = response.json()
    assert result["moderate"]["trend_snapshot_id"] == result["rapid"]["trend_snapshot_id"]
    assert calls["trends.json"] == 1


def test_corrupt_source_returns_503_not_500(monkeypatch):
    original = analysis.load_json

    def bad_career_data(filename):
        if filename == "careers.json":
            return [{"id": "invalid_role", "title": "Invalid Role", "required_skills": {"skill_python": 0}}]
        return original(filename)

    monkeypatch.setattr(analysis, "load_json", bad_career_data)
    response = client.post("/api/analyze", json=PAYLOAD)
    assert response.status_code == 503
    assert "source data" in response.json()["detail"]


def test_unknown_skills_still_return_422():
    response = client.post("/api/analyze", json={"profile": {"skills": ["skill_does_not_exist"]}})
    assert response.status_code == 422
    assert response.json()["detail"]["unknown_skill_ids"] == ["skill_does_not_exist"]
