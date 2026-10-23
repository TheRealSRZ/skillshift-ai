"""What-if readiness simulator: deterministic, catalog-grounded, no paid AI.

User profile is never persisted or mutated. The result models a hypothetical
skill acquisition, not future employment likelihood or verified skill mastery.
"""
from fastapi import APIRouter, HTTPException

from backend.matching import match_roles
from backend.schemas import WhatIfRequest
from backend.store import load_json
from backend.trend_snapshot import load_validated_snapshot

router = APIRouter(prefix="/api")


@router.post("/what-if")
def simulate_skills(body: WhatIfRequest):
    try:
        skills = load_json("skills.json")
        careers = load_json("careers.json")
        trend = load_validated_snapshot(load_json, skills=skills)
        supported = {skill["id"] for skill in skills}
        roles = {role["id"]: role for role in careers}
        if len(supported) != len(skills) or len(roles) != len(careers):
            raise ValueError("Duplicate catalog IDs")
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise HTTPException(status_code=503, detail="Career data is temporarily unavailable.") from exc

    if body.target_role not in roles:
        raise HTTPException(status_code=422, detail={"unknown_role_id": body.target_role})
    unknown = sorted((set(body.profile.skills) | set(body.add_skills)) - supported)
    if unknown:
        raise HTTPException(status_code=422, detail={"unknown_skill_ids": unknown})
    try:
        required = set(roles[body.target_role]["required_skills"])
    except (TypeError, KeyError) as exc:
        raise HTTPException(status_code=503, detail="Career data is temporarily unavailable.") from exc
    invalid = sorted(set(body.add_skills) - required)
    if invalid:
        raise HTTPException(status_code=422, detail={"skills_not_required_for_role": invalid})
    already_held = sorted(set(body.add_skills) & set(body.profile.skills))
    if already_held:
        raise HTTPException(status_code=422, detail={"skills_already_held": already_held})

    try:
        base = match_roles(body.profile.skills, careers, trend, body.scenario)
        simulated = match_roles(
            list(set(body.profile.skills) | set(body.add_skills)), careers, trend, body.scenario,
        )
        original = next(match for match in base["matches"] if match["role_id"] == body.target_role)
        hypothetical = next(match for match in simulated["matches"] if match["role_id"] == body.target_role)
    except (ValueError, KeyError, TypeError, StopIteration) as exc:
        raise HTTPException(status_code=503, detail="Career matching is temporarily unavailable.") from exc

    return {
        "target_role": body.target_role,
        "scenario": body.scenario,
        "trend_snapshot_id": base["trend_snapshot_id"],
        "original_readiness": original["readiness_score"],
        "hypothetical_readiness": hypothetical["readiness_score"],
        "delta_points": round(hypothetical["readiness_score"] - original["readiness_score"], 1),
        "added_skill_ids": body.add_skills,
        "remaining_missing_skills": hypothetical["missing_skills"],
        "note": "Hypothetical weighted skill overlap only. Assumes selected skills are acquired; not verified mastery or hiring probability.",
    }
