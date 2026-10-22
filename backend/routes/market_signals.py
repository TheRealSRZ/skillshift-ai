"""Read-only, evidence-only DOSM market signals endpoint.

Member 4 handoff; adding this file does not activate the route until Member 2
registers its router in backend/main.py.
"""

from fastapi import APIRouter, HTTPException
from backend.store import load_json

router = APIRouter(prefix="/api")

EXPECTED_CAREERS = {
    "role_software_developer",
    "role_accountant_auditor",
    "role_marketing_professional",
    "role_data_professional",
    "role_electrical_engineer",
    "role_nursing_professional",
}


def validate_market_signals(payload):
    """Validate the expected six-career coverage schema; never infer missing figures."""
    if not isinstance(payload, dict):
        raise ValueError("Market signals must be a JSON object")
    if (payload.get("career_specific") is not True
            or payload.get("skill_specific") is not False
            or payload.get("ai_impact_measure") is not False):
        raise ValueError("This must remain career-level DOSM evidence, not a skill or AI impact signal")
    if payload.get("geography") != "Malaysia":
        raise ValueError("Expected Malaysia market observations")
    periods = payload.get("periods")
    if not isinstance(periods, list) or len(periods) != 2 or not all(isinstance(p, str) and p for p in periods):
        raise ValueError("Exactly two labelled comparison periods are required")
    if payload.get("can_directly_adjust_career_scores") is not False:
        raise ValueError("Market evidence must not directly adjust career scores")
    signals = payload.get("career_signals")
    if not isinstance(signals, list) or len(signals) != len(EXPECTED_CAREERS):
        raise ValueError("Exactly six career signals are required")
    seen = set()
    observed = missing = 0
    for entry in signals:
        if not isinstance(entry, dict):
            raise ValueError("Invalid career signal")
        cid = entry.get("career_id")
        if cid not in EXPECTED_CAREERS or cid in seen:
            raise ValueError("Unknown or repeated career ID")
        seen.add(cid)
        if (entry.get("previous_period") != periods[0]
                or entry.get("latest_period") != periods[1]
                or entry.get("geography") != "Malaysia"
                or entry.get("metric") != "online_job_offerings_occupation"):
            raise ValueError("Inconsistent observation scope or reporting period")
        if entry.get("can_directly_adjust_career_scores") is not False:
            raise ValueError("Individual market signals must not adjust scores")
        if entry.get("ai_impact_measure") is not False:
            raise ValueError("Market observations must not be labelled AI impact")
        status = entry.get("data_status")
        if status == "insufficient_data":
            for key in ("previous_job_offerings", "latest_job_offerings", "absolute_change", "percent_change", "direction"):
                if entry.get(key) is not None:
                    raise ValueError("Missing-data entries must use null for observed values")
            if entry.get("source_ids") != [] or entry.get("source_urls") != []:
                raise ValueError("Unavailable observations must not present evidence links")
            missing += 1
        elif status == "observed_comparison_available":
            old, new = entry.get("previous_job_offerings"), entry.get("latest_job_offerings")
            if type(old) is not int or type(new) is not int or old <= 0 or new < 0:
                raise ValueError("Observed counts must be valid integers")
            delta = new - old
            if entry.get("absolute_change") != delta or entry.get("percent_change") != round(100 * delta / old, 2):
                raise ValueError("Observed changes do not match counts")
            if entry.get("direction") != ("increase" if delta > 0 else "decrease" if delta < 0 else "unchanged"):
                raise ValueError("Incorrect trend direction")
            if (type(entry.get("percent_change")) not in (int, float)
                    or type(entry.get("absolute_change")) is not int):
                raise ValueError("Observed differences must be numeric, not booleans")
            if not isinstance(entry.get("source_urls"), list) or not entry["source_urls"]:
                raise ValueError("Observed entries require source links")
            if not all(isinstance(url, str) and url.startswith("https://") for url in entry["source_urls"]):
                raise ValueError("All evidence source links must use HTTPS")
            if (not isinstance(entry.get("source_ids"), list) or not entry["source_ids"]
                    or not all(isinstance(sid, str) and sid for sid in entry["source_ids"])):
                raise ValueError("Observed evidence must have source IDs")
            observed += 1
        else:
            raise ValueError("Unsupported data status")
    if payload.get("observed_count") != observed or payload.get("insufficient_data_count") != missing:
        raise ValueError("Summary counts do not match entries")
    return payload


@router.get("/market-signals")
def market_signals():
    try:
        return validate_market_signals(load_json("processed/market_signals_six_careers.json"))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Market evidence is temporarily unavailable due to missing or invalid source data.",
        ) from exc
