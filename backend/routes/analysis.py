"""Profile analysis and consistent scenario comparison endpoints."""

from fastapi import APIRouter, HTTPException

from backend.matching import match_roles
from backend.schemas import AnalyzeRequest
from backend.store import load_json
from backend.trend_snapshot import load_validated_snapshot, SnapshotValidationError

router = APIRouter(prefix="/api")


def _load_analysis_data(body: AnalyzeRequest):
    try:
        skill_catalog = load_json("skills.json")
        careers = load_json("careers.json")
        trend = load_validated_snapshot(load_json, skills=skill_catalog)
        supported = {item["id"] for item in skill_catalog}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Career data is temporarily unavailable.",
        ) from exc

    unknown = set(body.profile.skills) - supported
    if unknown:
        raise HTTPException(
            status_code=422,
            detail={"unknown_skill_ids": sorted(unknown)},
        )
    return careers, trend


def _safe_match(body: AnalyzeRequest, careers: list[dict], trend: dict, scenario: str):
    try:
        return match_roles(body.profile.skills, careers, trend, scenario)
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Career matching is temporarily unavailable due to invalid source data.",
        ) from exc


@router.post("/analyze")
def analyze(body: AnalyzeRequest):
    careers, trend = _load_analysis_data(body)
    return _safe_match(body, careers, trend, body.scenario)


@router.post("/scenarios")
def scenarios(body: AnalyzeRequest):
    careers, trend = _load_analysis_data(body)  # Same snapshot for both scenarios.
    return {
        "moderate": _safe_match(body, careers, trend, "moderate"),
        "rapid": _safe_match(body, careers, trend, "rapid"),
    }
