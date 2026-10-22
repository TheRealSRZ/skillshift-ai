"""Public, catalog-grounded learning roadmap endpoint (Member 2)."""

import logging
import time

from fastapi import APIRouter, Header, HTTPException
from backend.ai_access import verify_supabase_user
from backend.ai_quota import ai_job_slot

from backend.roadmap_adapter import RoadmapDataError, ai_roadmap_enabled, generate_safe_roadmap
from backend.schemas import RoadmapRequest
from backend.store import load_json

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)


def _roadmap(body: RoadmapRequest, *, personalize: bool, authorization: str | None = None):
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

    if personalize and not ai_roadmap_enabled():
        raise HTTPException(
            status_code=503,
            detail="AI personalization is currently disabled. Your approved roadmap remains available.",
        )
    if personalize and not body.missing_skills:
        raise HTTPException(status_code=422, detail="No skill gaps to personalize")

    def build(*, attempt_ai: bool):
        return generate_safe_roadmap(
            body.target_role, body.missing_skills, body.scenario,
            resources, skill_ids, attempt_ai=attempt_ai,
        )

    try:
        if personalize:
            # Verify session with Supabase (not untrusted JWT claims), then
            # reserve a server-side GPU budget slot before calling RunPod.
            user_id = verify_supabase_user(authorization)
            with ai_job_slot(user_id) as job_id:
                started = time.monotonic()
                try:
                    result = build(attempt_ai=True)
                finally:
                    # Safe observability: opaque request ID, duration and no
                    # request body, bearer token, prompts, raw outputs or secrets.
                    logger.info("AI request %s finished in %.2fs", job_id, time.monotonic() - started)
        else:
            result = build(attempt_ai=False)

        # Never return the fallback from the optional route as an AI result.
        # The frontend keeps its existing approved plan on any AI failure.
        if personalize and result["generation_mode"] != "runpod_validated":
            raise HTTPException(
                status_code=503,
                detail="AI personalization was unavailable. Your approved roadmap has not changed.",
            )
        return result
    except (RoadmapDataError, ValueError, TypeError, KeyError) as exc:
        raise HTTPException(status_code=503, detail="Verified learning roadmap temporarily unavailable.") from exc


@router.post("/roadmap")
def roadmap(body: RoadmapRequest):
    """Stage 1: immediate approved-course roadmap, never invokes RunPod."""
    return _roadmap(body, personalize=False)


@router.post("/roadmap/personalize")
def personalize_roadmap(body: RoadmapRequest, authorization: str | None = Header(default=None)):
    """Stage 2: opt-in RunPod selection, still behind Member 2's catalog checks."""
    return _roadmap(body, personalize=True, authorization=authorization)
