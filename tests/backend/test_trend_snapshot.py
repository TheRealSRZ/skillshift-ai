"""Read-only snapshot verification (Member 2), with synthetic test inputs."""

from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.store import load_json
from backend.trend_snapshot import SnapshotValidationError, validate_snapshot
from backend.routes import analysis, trends


client = TestClient(app)
PAYLOAD = {
    "profile": {"education": "Synthetic IT student", "skills": ["skill_python", "skill_sql"], "interests": []},
    "scenario": "moderate",
}


def catalogs():
    return load_json("skills.json"), load_json("sources.json")


def synthetic_snapshot():
    return deepcopy(load_json("trends.json"))


def validated(snapshot):
    return validate_snapshot(snapshot, *catalogs())


def test_current_snapshot_keeps_frontend_contract_and_provenance():
    snapshot = validated(synthetic_snapshot())
    assert snapshot["snapshot_id"] == "synthetic_snapshot_oct2026"
    assert snapshot["evidence_status"] == "synthetic_demo"
    assert snapshot["source_ids"] == ["src_demo"]
    assert snapshot["source_details"][0]["id"] == "src_demo"
    assert snapshot["observed_date"] == "2026-10-01"
    assert snapshot["retrieved_date"] == "2026-10-19"
    assert snapshot["multipliers"]["skill_cloud"] == 1.05
    assert "not" in snapshot["multiplier_note"].lower()


def test_current_api_trends_and_analysis_read_same_metadata():
    trend_response = client.get("/api/trends")
    match_response = client.post("/api/analyze", json=PAYLOAD)
    assert trend_response.status_code == match_response.status_code == 200
    t, m = trend_response.json(), match_response.json()
    assert t["snapshot_id"] == m["trend_snapshot_id"]
    assert t["evidence_status"] == m["evidence_status"] == "synthetic_demo"
    assert t["source_ids"] == m["source_ids"] == ["src_demo"]
    assert t["observed_date"] == m["observed_date"]
    assert m["scenario_version"] == "scenario_assumptions_v1"
    assert m["scenario_multipliers"] == {}
    assert m["matches"][0]["readiness_score"] == 54.2

@pytest.mark.parametrize("field, invalid", [
    ("snapshot_id", ""),
    ("region", None),
    ("observed_date", "2026-13-01"),
    ("retrieved_date", "yesterday"),
    ("source_ids", []),
    ("source_ids", ["src_demo", "src_demo"]),
    ("source_ids", ["src_not_real"]),
    ("multipliers", {"skill_nonexistent": 1.2}),
    ("multipliers", {"skill_python": 0}),
    ("multipliers", {"skill_python": -0.2}),
    ("multipliers", {"skill_python": float("nan")}),
    ("multipliers", {"skill_python": True}),
    ("multipliers", {"skill_python": "1.1"}),
])
def test_reject_bad_snapshots(field, invalid):
    snapshot = synthetic_snapshot()
    snapshot[field] = invalid
    with pytest.raises(SnapshotValidationError):
        validated(snapshot)


def test_retrieved_date_cannot_precede_observed_date():
    snapshot = synthetic_snapshot()
    snapshot["retrieved_date"] = "2026-09-01"
    with pytest.raises(SnapshotValidationError, match="retrieved_date"):
        validated(snapshot)


def test_unknown_real_source_cannot_be_used_to_launder_synthetic_multipliers():
    snapshot = synthetic_snapshot()
    snapshot["source_ids"] = ["src_dosm_jmi_q2_2026"]
    with pytest.raises(SnapshotValidationError, match="Synthetic snapshots"):
        validated(snapshot)


def test_snapshot_update_changes_scores_but_keeps_synthetic_label(monkeypatch):
    """Simulates Member 4 handoff without writing into their data files."""
    baseline = client.post("/api/analyze", json=PAYLOAD).json()
    revised = synthetic_snapshot()
    revised["snapshot_id"] = "synthetic_phase3_test_revision"
    revised["multipliers"]["skill_power_bi"] = 1.50  # illustrative only
    original_loader = analysis.load_json

    def fake_loader(name):
        if name == "trends.json":
            return revised
        return original_loader(name)

    monkeypatch.setattr(analysis, "load_json", fake_loader)
    response = client.post("/api/analyze", json=PAYLOAD)
    assert response.status_code == 200
    result = response.json()
    assert result["trend_snapshot_id"] == "synthetic_phase3_test_revision"
    assert result["data_label"] == baseline["data_label"]
    assert result["evidence_status"] == "synthetic_demo"
    score_before = next(x["readiness_score"] for x in baseline["matches"] if x["role_id"] == "role_data_analyst")
    score_after = next(x["readiness_score"] for x in result["matches"] if x["role_id"] == "role_data_analyst")
    assert score_before == 54.2
    assert score_after == 48.0  # Python+SQL 6, total 3+3+4.5+2=12.5


def test_both_scenarios_share_snapshot_and_assumptions_are_explicit():
    response = client.post("/api/scenarios", json=PAYLOAD)
    assert response.status_code == 200
    out = response.json()
    assert out["moderate"]["trend_snapshot_id"] == out["rapid"]["trend_snapshot_id"]
    assert out["moderate"]["scenario_version"] == out["rapid"]["scenario_version"]
    assert out["moderate"]["scenario_multipliers"] == {}
    assert out["rapid"]["scenario_multipliers"]["skill_cloud"] == 1.2
    assert "Illustrative" in out["rapid"]["scenario_description"]


def test_bad_active_snapshot_does_not_return_fake_200(monkeypatch):
    original_analysis = analysis.load_json
    original_trends = trends.load_json
    bad = synthetic_snapshot()
    bad["multipliers"] = {"skill_python": -99}
    monkeypatch.setattr(analysis, "load_json", lambda name: bad if name == "trends.json" else original_analysis(name))
    monkeypatch.setattr(trends, "load_json", lambda name: bad if name == "trends.json" else original_trends(name))
    assert client.post("/api/analyze", json=PAYLOAD).status_code == 503
    assert client.post("/api/scenarios", json=PAYLOAD).status_code == 503
    assert client.get("/api/trends").status_code == 503


def test_snapshot_validation_does_not_mutate_shared_data():
    original = synthetic_snapshot()
    snapshot = validated(original)
    snapshot["multipliers"]["skill_cloud"] = 22
    # Its source_details are added to a new dict; this boundary doesn't alter catalog data.
    assert "source_details" not in original
    assert original["multipliers"]["skill_cloud"] == 1.05
