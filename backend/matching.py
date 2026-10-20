"""Deterministic, explainable career-readiness scoring."""

from math import isfinite

from backend.scenarios import SCENARIO_DISCLAIMER, SCENARIO_MULTIPLIERS, scenario_metadata


def positive_weight(value: object, name: str) -> float:
    """Reject invalid source weights before they affect career scores."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    weight = float(value)
    if not isfinite(weight) or weight <= 0:
        raise ValueError(f"{name} must be finite and greater than zero")
    return weight


def match_roles(skills: list[str], careers: list[dict], trend: dict, scenario: str) -> dict:
    if scenario not in SCENARIO_MULTIPLIERS:
        raise ValueError(f"Unsupported scenario: {scenario}")
    if not isinstance(careers, list) or not careers:
        raise ValueError("Career catalog must contain at least one role")
    if not isinstance(trend, dict):
        raise ValueError("Trend snapshot must be an object")

    raw_trend_weights = trend.get("multipliers", {})
    if not isinstance(raw_trend_weights, dict):
        raise ValueError("Trend multipliers must be an object")

    trend_weights = {
        sid: positive_weight(value, f"Trend multiplier for {sid}")
        for sid, value in raw_trend_weights.items()
    }
    scenario_weights = {
        sid: positive_weight(value, f"Scenario multiplier for {sid}")
        for sid, value in SCENARIO_MULTIPLIERS[scenario].items()
    }
    user_skills = set(skills)  # Duplicate/order-independent
    results = []
    seen_role_ids = set()

    for role in careers:
        if not isinstance(role, dict):
            raise ValueError("Each career must be an object")
        role_id = role.get("id")
        if not isinstance(role_id, str) or not role_id.strip():
            raise ValueError("Each career must have a non-empty id")
        if role_id in seen_role_ids:
            raise ValueError(f"Duplicate career id: {role_id}")
        seen_role_ids.add(role_id)
        title = role.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ValueError(f"Career {role_id} has no valid title")
        required = role.get("required_skills")
        if not isinstance(required, dict) or not required:
            raise ValueError(f"Career {role_id} has no required skills")

        numerator = 0.0
        denominator = 0.0
        breakdown = []
        for sid, raw_base_weight in required.items():
            if not isinstance(sid, str) or not sid.strip():
                raise ValueError(f"Career {role_id} has an invalid skill id")
            base_weight = positive_weight(raw_base_weight, f"Base weight for {role_id}/{sid}")
            effective = base_weight * trend_weights.get(sid, 1.0) * scenario_weights.get(sid, 1.0)
            if not isfinite(effective) or effective <= 0:
                raise ValueError(f"Invalid effective weight for {role_id}/{sid}")
            denominator += effective
            matched = sid in user_skills
            if matched:
                numerator += effective
            breakdown.append({
                "skill_id": sid,
                "matched": matched,
                "effective_weight": round(effective, 3),
            })

        if not isfinite(denominator) or denominator <= 0:
            raise ValueError(f"Invalid total weight for career {role_id}")
        score = max(0.0, min(100.0, round(100.0 * (numerator / denominator), 1)))
        results.append({
            "role_id": role_id,
            "title": title,
            "readiness_score": score,
            "matched_skills": [s["skill_id"] for s in breakdown if s["matched"]],
            "missing_skills": [s["skill_id"] for s in breakdown if not s["matched"]],
            "breakdown": breakdown,
            "sdgs": role.get("sdgs", []),
        })

    results.sort(key=lambda item: (-item["readiness_score"], item["role_id"]))
    return {
        "scenario": scenario,
        "trend_snapshot_id": trend.get("snapshot_id"),
        "data_label": trend.get("label"),
        "scenario_disclaimer": SCENARIO_DISCLAIMER,
        **scenario_metadata(scenario),
        "evidence_status": trend.get("evidence_status", "unverified"),
        "observed_date": trend.get("observed_date"),
        "retrieved_date": trend.get("retrieved_date"),
        "region": trend.get("region"),
        "source_ids": trend.get("source_ids", []),
        "matches": results,
    }
