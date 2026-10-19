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
        "ai.runpod_client.ask_ai",
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

