"""Phase 4: public roadmap trust-boundary and RunPod fallback tests (no network)."""

from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.store import load_json
from backend.roadmap_adapter import RoadmapDataError, generate_safe_roadmap, verified_course_index
from backend.routes import roadmap as roadmap_route
import backend.roadmap_adapter as adapter

client = TestClient(app)
REQUEST = {
    "target_role": "role_data_analyst",
    "missing_skills": ["skill_power_bi", "skill_data_viz"],
    "scenario": "moderate",
}


def test_existing_frontend_response_shape_and_verified_course_details(monkeypatch):
    monkeypatch.delenv("AI_ENABLED", raising=False)
    r = client.post("/api/roadmap", json=REQUEST)
    assert r.status_code == 200
    data = r.json()
    assert set(data) == {"target_role", "scenario", "generation_mode", "steps", "uncovered_skills", "note"}
    assert data["generation_mode"] == "deterministic_fallback"
    assert data["uncovered_skills"] == []
    assert [x["course_id"] for x in data["steps"]] == ["course_powerbi", "course_data_viz"]
    assert data["steps"][0]["url"] == "https://learn.microsoft.com/en-us/training/paths/prepare-visualize-data-power-bi/"
    assert data["steps"][0]["estimated_hours"] == 8.2
    assert [x["step"] for x in data["steps"]] == [1, 2]


def test_flag_off_never_calls_hosted_model(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "false")
    real = adapter.generate_roadmap

    def planner(*args, use_ai=False):
        if use_ai:
            pytest.fail("RunPod must not be called when AI_ENABLED is false")
        return real(*args, use_ai=False)

    monkeypatch.setattr(adapter, "generate_roadmap", planner)
    assert client.post("/api/roadmap", json=REQUEST).status_code == 200


def test_member3_runpod_exception_returns_fallback(monkeypatch):
    # Mock the network call, even if a developer has real RunPod credentials.
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setattr("ai.learning_planner.ask_ai", lambda _: (_ for _ in ()).throw(RuntimeError("offline")))
    r = client.post("/api/roadmap", json=REQUEST)
    assert r.status_code == 200
    result = r.json()
    assert result["generation_mode"] == "deterministic_fallback"
    assert "AI personalization unavailable" in result["note"]
    assert len(result["steps"]) == 2


def test_valid_runpod_selection_is_rehydrated_from_catalog(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "true")
    real = adapter.generate_roadmap

    def planner(*args, use_ai=False):
        if not use_ai:
            return real(*args, use_ai=False)
        return {
            "target_role": "role_data_analyst", "scenario": "moderate",
            "generation_mode": "runpod_ai",
            "steps": [
                {"course_id": "course_data_viz", "reason": "Build clear visual reports after core analytics.",
                 "title": "FORGED TITLE", "url": "https://evil.example/", "estimated_hours": 99999},
                {"course_id": "course_powerbi", "reason": "Develop Power BI fundamentals for the role."},
            ],
            "uncovered_skills": ["pretend_missing"],
            "note": "Made-up model note",
        }

    monkeypatch.setattr(adapter, "generate_roadmap", planner)
    result = client.post("/api/roadmap", json=REQUEST).json()
    assert result["generation_mode"] == "runpod_validated"
    assert [c["course_id"] for c in result["steps"]] == ["course_data_viz", "course_powerbi"]
    assert result["steps"][0]["title"] == "Design effective reports in Power BI"
    assert result["steps"][0]["estimated_hours"] == 5.12
    assert "evil.example" not in str(result)
    assert "Made-up model note" not in str(result)
    assert result["uncovered_skills"] == []


@pytest.mark.parametrize("bad_steps", [
    [{"course_id": "fake_course", "reason": "Learn this next."}],
    [{"course_id": "course_powerbi", "reason": "Learn this next."},
     {"course_id": "course_powerbi", "reason": "Repeat this course."}],
    [{"course_id": "course_powerbi", "reason": "x"}],
    [{"course_id": "course_powerbi", "reason": "Learn Power BI."}],  # Drops known data-viz coverage
    [{"course_id": "course_cloud", "reason": "Course for unrelated skill."}],
    "broken type",
])
def test_invalid_or_incomplete_model_output_falls_back(monkeypatch, bad_steps):
    monkeypatch.setenv("AI_ENABLED", "true")
    real = adapter.generate_roadmap

    def planner(*args, use_ai=False):
        if not use_ai:
            return real(*args, use_ai=False)
        return {"steps": bad_steps, "generation_mode": "runpod_ai"}

    monkeypatch.setattr(adapter, "generate_roadmap", planner)
    r = client.post("/api/roadmap", json=REQUEST)
    assert r.status_code == 200
    data = r.json()
    assert data["generation_mode"] == "deterministic_fallback"
    assert data["uncovered_skills"] == []


def test_ai_exception_falls_back_without_leaking_error(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "true")
    real = adapter.generate_roadmap

    def planner(*args, use_ai=False):
        if use_ai:
            raise RuntimeError("secret=RUNPOD_PRIVATE_SECRET")
        return real(*args, use_ai=False)

    monkeypatch.setattr(adapter, "generate_roadmap", planner)
    text = client.post("/api/roadmap", json=REQUEST).text
    assert "RUNPOD_PRIVATE_SECRET" not in text
    assert "deterministic_fallback" in text


def test_unknown_role_is_rejected_422():
    r = client.post("/api/roadmap", json={**REQUEST, "target_role": "role_fake"})
    assert r.status_code == 422
    assert r.json()["detail"]["unknown_role_id"] == "role_fake"


def test_skill_not_required_for_role_is_rejected_422():
    r = client.post("/api/roadmap", json={**REQUEST, "missing_skills": ["skill_cloud"]})
    assert r.status_code == 422
    assert r.json()["detail"]["skills_not_required_for_role"] == ["skill_cloud"]


def test_duplicate_missing_skills_do_not_duplicate_course_selection(monkeypatch):
    monkeypatch.delenv("AI_ENABLED", raising=False)
    r = client.post("/api/roadmap", json={**REQUEST, "missing_skills": ["skill_power_bi"] * 3})
    assert r.status_code == 200
    assert len(r.json()["steps"]) == 1
    assert r.json()["uncovered_skills"] == []


def test_skills_with_no_course_remain_uncovered(monkeypatch):
    monkeypatch.delenv("AI_ENABLED", raising=False)
    r = client.post("/api/roadmap", json={"target_role": "role_security_analyst", "missing_skills": ["skill_security"], "scenario": "rapid"})
    assert r.status_code == 200
    assert r.json()["steps"] == []
    assert r.json()["uncovered_skills"] == ["skill_security"]


def test_broken_approved_course_url_returns_503(monkeypatch):
    resources = deepcopy(load_json("learning_resources.json"))
    resources[0]["url"] = "javascript:alert(1)"
    original = roadmap_route.load_json
    monkeypatch.setattr(roadmap_route, "load_json", lambda name: resources if name == "learning_resources.json" else original(name))
    r = client.post("/api/roadmap", json=REQUEST)
    assert r.status_code == 503
    assert "javascript" not in r.text


def test_duplicate_course_ids_and_unknown_skill_are_blocked():
    known = {x["id"] for x in load_json("skills.json")}
    resources = deepcopy(load_json("learning_resources.json"))
    resources.append(deepcopy(resources[0]))
    with pytest.raises(RoadmapDataError, match="duplicate"):
        verified_course_index(resources, known)
    resources = deepcopy(load_json("learning_resources.json"))
    resources[0]["skill_ids"] = ["skill_gibberish"]
    with pytest.raises(RoadmapDataError, match="unknown skill"):
        verified_course_index(resources, known)


def test_over_limit_missing_skills_returns_422():
    r = client.post("/api/roadmap", json={**REQUEST, "missing_skills": ["skill_power_bi"] * 31})
    assert r.status_code == 422


def test_catalog_missing_gives_generic_503(monkeypatch):
    original = roadmap_route.load_json

    def fail_one(name):
        if name == "learning_resources.json":
            raise FileNotFoundError("private directory path")
        return original(name)

    monkeypatch.setattr(roadmap_route, "load_json", fail_one)
    r = client.post("/api/roadmap", json=REQUEST)
    assert r.status_code == 503
    assert "private directory" not in r.text


def test_verified_course_index_rejects_nonfinite_hours():
    known = {x["id"] for x in load_json("skills.json")}
    resources = deepcopy(load_json("learning_resources.json"))
    resources[0]["estimated_hours"] = float("inf")
    with pytest.raises(RoadmapDataError, match="estimated_hours"):
        verified_course_index(resources, known)


def test_real_member3_planner_mocked_runpod_course_order(monkeypatch):
    """End-to-end: real Member 3 parsing + our boundary, no RunPod charges."""
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setattr(
        "ai.learning_planner.ask_ai",
        lambda _: '["course_data_viz", "course_powerbi"]',
    )
    result = client.post("/api/roadmap", json=REQUEST)
    assert result.status_code == 200
    data = result.json()
    assert data["generation_mode"] == "runpod_validated"
    assert [s["course_id"] for s in data["steps"]] == ["course_data_viz", "course_powerbi"]
    assert data["uncovered_skills"] == []


def test_real_member3_planner_mocked_runpod_hallucination_is_fallback(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setattr("ai.learning_planner.ask_ai", lambda _: '["invented_course"]')
    data = client.post("/api/roadmap", json=REQUEST).json()
    assert data["generation_mode"] == "deterministic_fallback"
    assert [s["course_id"] for s in data["steps"]] == ["course_powerbi", "course_data_viz"]


def test_real_member3_planner_dropped_coverage_is_fallback(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setattr("ai.learning_planner.ask_ai", lambda _: '["course_powerbi"]')
    data = client.post("/api/roadmap", json=REQUEST).json()
    assert data["generation_mode"] == "deterministic_fallback"
    assert data["uncovered_skills"] == []


def test_member3_internal_fallback_is_not_mislabelled_as_ai(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "true")
    real = adapter.generate_roadmap
    def planner(*args, use_ai=False):
        # Member 3 can catch RunPod exceptions itself, returning the fallback.
        return real(*args, use_ai=False)
    monkeypatch.setattr(adapter, "generate_roadmap", planner)
    data = client.post("/api/roadmap", json=REQUEST).json()
    assert data["generation_mode"] == "deterministic_fallback"
    assert "AI personalization unavailable" in data["note"]


def test_member3_direct_runpod_client_parses_serverless_response(monkeypatch):
    from ai.runpod_client import ask_ai
    import ai.runpod_client as runpod_client

    monkeypatch.setenv("RUNPOD_API_KEY", "test-private-not-live")
    monkeypatch.setenv("RUNPOD_ENDPOINT_ID", "example-id")
    requests_made = []
    class Response:
        def __init__(self, data): self.data = data
        def raise_for_status(self): pass
        def json(self): return self.data
    def fake_post(url, **kwargs):
        requests_made.append(url)
        return Response({"id": "job-001"})
    def fake_get(url, **kwargs):
        requests_made.append(url)
        return Response({"status": "COMPLETED", "output": [{"choices": [{"text": '["course_powerbi"]'}]}]})
    monkeypatch.setattr(runpod_client.requests, "post", fake_post)
    monkeypatch.setattr(runpod_client.requests, "get", fake_get)
    assert ask_ai("test prompt") == '["course_powerbi"]'
    assert requests_made[0].endswith("/run")
    assert requests_made[1].endswith("/status/job-001")


def test_member3_runpod_client_rejects_placeholder_worker_output(monkeypatch):
    from ai.runpod_client import ask_ai
    import ai.runpod_client as runpod_client
    monkeypatch.setenv("RUNPOD_API_KEY", "test-private-not-live")
    monkeypatch.setenv("RUNPOD_ENDPOINT_ID", "example-id")
    class Response:
        def __init__(self, data): self.data = data
        def raise_for_status(self): pass
        def json(self): return self.data
    monkeypatch.setattr(runpod_client.requests, "post", lambda *a, **k: Response({"id": "job-001"}))
    monkeypatch.setattr(runpod_client.requests, "get", lambda *a, **k: Response({"status": "COMPLETED", "output": {"output": "Echo: test"}}))
    with pytest.raises((TypeError, AttributeError, KeyError, RuntimeError)):
        ask_ai("test prompt")
