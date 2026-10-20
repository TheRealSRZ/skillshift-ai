"""Read-only endpoint for the same validated snapshot used in matching."""
from fastapi import APIRouter, HTTPException
from backend.store import load_json
from backend.trend_snapshot import load_validated_snapshot

router = APIRouter(prefix="/api")


@router.get("/trends")
def trends():
    try:
        return load_validated_snapshot(load_json)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Trend evidence is temporarily unavailable due to invalid source data.",
        ) from exc
