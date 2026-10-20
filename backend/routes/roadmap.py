"""Public, catalog-grounded learning roadmap endpoint (Member 2)."""

from fastapi import APIRouter, HTTPException

from backend.roadmap_adapter import RoadmapDataError, generate_safe_roadmap
from backend.schemas import RoadmapRequest
from backend.store import load_json

router = APIRouter(prefix="/api")


@router.post("/roadmap")
def roadmap(body: RoadmapRequest):
    try:
        skills = load_json("skills.json")
        careers = load_json("careers.json")
        resources = load_json("learning_resources.json")
        if not isinstance(skills, list) or not isinstance(careers, list):
            raise RoadmapDataError("Malformed catalogs")
        skill_ids = {item["id"] for item in skills}
        roles = {item["id"]: item for item in careers}
        if len(skill_ids) != len(skills) or len(roles) != len(careers):
            raise RoadmapDataError("Duplicate IDs in catalogs")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=503, detail="Learning catalogs temporarily unavailable.") from exc

    if body.target_role not in roles:
        raise HTTPException(status_code=422, detail={"unknown_role_id": body.target_role})
    if len(body.missing_skills) > 30:
        raise HTTPException(status_code=422, detail="Too many missing skills")
    if any(not isinstance(skill, str) or len(skill) > 100 for skill in body.missing_skills):
        raise HTTPException(status_code=422, detail="Invalid missing skill IDs")
    try:
        required = set(roles[body.target_role]["required_skills"])
    except (TypeError, KeyError) as exc:
        raise HTTPException(status_code=503, detail="Career catalog temporarily unavailable.") from exc
    unsupported = sorted(set(body.missing_skills) - required)
    if unsupported:
        raise HTTPException(status_code=422, detail={"skills_not_required_for_role": unsupported})

    try:
        return generate_safe_roadmap(
            body.target_role, body.missing_skills, body.scenario,
            resources, skill_ids,
        )
    except (RoadmapDataError, ValueError, TypeError, KeyError) as exc:
        raise HTTPException(status_code=503, detail="Verified learning roadmap temporarily unavailable.") from exc
