from ai.learning_planner import generate_roadmap
from ai.skill_extractor import extract_skills
from unittest.mock import patch

def test_unverified_courses_never_recommended():
    sample=[{'id':'c1','title':'Unverified','url':'https://example.invalid', 'verified':False,'skill_ids':['skill_sql']}]
    result=generate_roadmap('role_data_analyst',['skill_sql'],'moderate',sample)
    assert not result['steps']
    assert result['uncovered_skills']==['skill_sql']

def test_extractor_only_finds_explicit_matches():
    skills=[{'id':'skill_python','name':'Python'},{'id':'skill_sql','name':'SQL'}]
    result=extract_skills('The advert asks for Python.',skills)
    assert [x['skill_id'] for x in result]==['skill_python']


def test_verified_course_is_recommended():
    courses = [
        {
            "id": "course_python",
            "title": "Python Basics",
            "url": "https://example.com/python",
            "verified": True,
            "skill_ids": ["skill_python"],
            "estimated_hours": 10
        }
    ]

    result = generate_roadmap(
        "Data Analyst",
        ["skill_python"],
        "moderate",
        courses
    )

    assert len(result["steps"]) == 1
    assert result["steps"][0]["course_id"] == "course_python"
    assert result["uncovered_skills"] == []


def test_unrelated_course_is_not_recommended():
    courses = [
        {
            "id": "course_design",
            "title": "Graphic Design",
            "url": "https://example.com/design",
            "verified": True,
            "skill_ids": ["skill_design"],
            "estimated_hours": 5
        }
    ]

    result = generate_roadmap(
        "Data Analyst",
        ["skill_python"],
        "moderate",
        courses
    )

    assert result["steps"] == []
    assert result["uncovered_skills"] == ["skill_python"]


def test_missing_skills_without_courses_are_uncovered():
    result = generate_roadmap(
        "Data Analyst",
        ["skill_python", "skill_sql"],
        "moderate",
        []
    )

    assert result["steps"] == []
    assert set(result["uncovered_skills"]) == {
        "skill_python",
        "skill_sql"
    }


def test_runpod_failure_uses_fallback():
    courses = [
        {
            "id": "course_python",
            "title": "Python Basics",
            "url": "https://example.com/python",
            "verified": True,
            "skill_ids": ["skill_python"],
            "estimated_hours": 10,
        }
    ]

    with patch(
        "ai.learning_planner.ask_ai",
        side_effect=RuntimeError("RunPod unavailable"),
    ):
        result = generate_roadmap(
            target_role="Data Analyst",
            missing_skills=["skill_python"],
            scenario="moderate",
            verified_courses=courses,
            use_ai=True,
        )

    assert result["generation_mode"] == "deterministic_fallback"
    assert result["steps"][0]["course_id"] == "course_python"
    assert result["uncovered_skills"] == []


def test_ai_selects_only_verified_courses():
    courses = [
        {
            "id": "course_python",
            "title": "Python Basics",
            "url": "https://example.com/python",
            "verified": True,
            "skill_ids": ["skill_python"],
            "estimated_hours": 10,
        },
        {
            "id": "course_sql",
            "title": "SQL Basics",
            "url": "https://example.com/sql",
            "verified": True,
            "skill_ids": ["skill_sql"],
            "estimated_hours": 8,
        },
    ]

    with patch(
        "ai.learning_planner.ask_ai",
        return_value='["course_sql", "course_python"]',
    ):
        result = generate_roadmap(
            target_role="Data Analyst",
            missing_skills=["skill_python", "skill_sql"],
            scenario="moderate",
            verified_courses=courses,
            use_ai=True,
        )

    assert result["generation_mode"] == "runpod_ai"
    assert [s["course_id"] for s in result["steps"]] == [
        "course_sql",
        "course_python",
    ]
    assert result["uncovered_skills"] == []


def test_ai_cannot_reduce_skill_coverage():
    """AI must not omit skills covered by verified courses."""

    courses = [
        {
            "id": "course_powerbi",
            "title": "Power BI Basics",
            "url": "https://example.com/powerbi",
            "verified": True,
            "skill_ids": ["skill_power_bi"],
            "estimated_hours": 8,
        },
        {
            "id": "course_data_viz",
            "title": "Data Visualization",
            "url": "https://example.com/dataviz",
            "verified": True,
            "skill_ids": ["skill_data_viz"],
            "estimated_hours": 5,
        },
    ]

    # Simulate RunPod selecting only one course.
    with patch(
        "ai.learning_planner.ask_ai",
        return_value='["course_powerbi"]',
    ):
        result = generate_roadmap(
            target_role="Data Analyst",
            missing_skills=[
                "skill_power_bi",
                "skill_data_viz",
            ],
            scenario="moderate",
            verified_courses=courses,
            use_ai=True,
        )

    selected_ids = {
        step["course_id"]
        for step in result["steps"]
    }

    assert selected_ids == {
        "course_powerbi",
        "course_data_viz",
    }

    assert result["uncovered_skills"] == []

    
def test_runpod_cancels_job_on_timeout(monkeypatch):
    import pytest
    import requests
    import ai.runpod_client as client

    monkeypatch.setenv("RUNPOD_API_KEY", "fake-test-key")
    monkeypatch.setenv("RUNPOD_ENDPOINT_ID", "fake-endpoint")
    monkeypatch.setenv("RUNPOD_POLL_TIMEOUT", "0")

    calls = []

    class FakeResponse:
        def __init__(self, data):
            self.data = data

        def raise_for_status(self):
            pass

        def json(self):
            return self.data

    def fake_post(url, **kwargs):
        calls.append(url)

        if url.endswith("/run"):
            return FakeResponse({"id": "test-job-123"})

        if url.endswith("/cancel/test-job-123"):
            return FakeResponse({"status": "CANCELLED"})

        raise AssertionError(f"Unexpected POST URL: {url}")

    monkeypatch.setattr(requests, "post", fake_post)

    # Replace this with the actual public function name
    # from ai/runpod_client.py if it differs.
    with pytest.raises(TimeoutError):
        client.ask_ai("Test prompt")

    assert any(
        url.endswith("/cancel/test-job-123")
        for url in calls
    )

