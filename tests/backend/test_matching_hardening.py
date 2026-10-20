import copy

import pytest

from backend.matching import match_roles
from backend.store import load_json


def _fixture():
    return [
        {
            "id": "role_test",
            "title": "Test Analyst",
            "required_skills": {
                "skill_python": 3,
                "skill_sql": 3,
                "skill_data_viz": 4,
            },
            "sdgs": [4],
        }
    ], {"snapshot_id": "test_snapshot", "label": "TEST DATA", "multipliers": {}}


def test_hand_calculated_score_and_breakdown():
    careers, trend = _fixture()
    output = match_roles(["skill_python", "skill_sql"], careers, trend, "moderate")
    result = output["matches"][0]
    assert result["readiness_score"] == 60.0
    assert result["missing_skills"] == ["skill_data_viz"]
    assert sum(s["effective_weight"] for s in result["breakdown"]) == 10
    assert output["trend_snapshot_id"] == "test_snapshot"


def test_rapid_scenario_is_hypothetical_but_recalculates():
    careers, trend = _fixture()
    skills = ["skill_python", "skill_sql"]
    assert match_roles(skills, careers, trend, "moderate")["matches"][0]["readiness_score"] == 60
    assert match_roles(skills, careers, trend, "rapid")["matches"][0]["readiness_score"] == 57.7


def test_skill_duplicates_do_not_change_score():
    careers, trend = _fixture()
    once = match_roles(["skill_sql", "skill_python"], careers, trend, "moderate")
    twice = match_roles(["skill_python", "skill_sql", "skill_sql"], careers, trend, "moderate")
    assert once == twice


@pytest.mark.parametrize("weight", [0, -2, float("nan"), float("inf"), True, "3"])
def test_bad_base_weights_are_rejected(weight):
    careers, trend = _fixture()
    careers[0]["required_skills"]["skill_python"] = weight
    with pytest.raises(ValueError, match="Base weight"):
        match_roles(["skill_python"], careers, trend, "moderate")


def test_bad_trend_weight_is_rejected():
    careers, trend = _fixture()
    trend["multipliers"] = {"skill_python": float("nan")}
    with pytest.raises(ValueError, match="Trend multiplier"):
        match_roles(["skill_python"], careers, trend, "moderate")


def test_missing_requirements_are_rejected():
    careers, trend = _fixture()
    careers[0]["required_skills"] = {}
    with pytest.raises(ValueError, match="required skills"):
        match_roles([], careers, trend, "moderate")


def test_stable_sorted_results_on_current_catalog():
    careers = load_json("careers.json")
    trend = load_json("trends.json")
    original = match_roles(["skill_python", "skill_sql"], careers, trend, "moderate")
    reversed_careers = match_roles(["skill_sql", "skill_python"], list(reversed(careers)), trend, "moderate")
    assert original == reversed_careers
    scores = [role["readiness_score"] for role in original["matches"]]
    assert scores == sorted(scores, reverse=True)


def test_invalid_scenario_is_rejected_directly():
    careers, trend = _fixture()
    with pytest.raises(ValueError, match="Unsupported scenario"):
        match_roles([], careers, trend, "fictional")
