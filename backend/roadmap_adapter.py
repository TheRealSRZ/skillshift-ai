"""Member 2: trust boundary between Member 3's learning planner and the public API.

The hosted model may choose/order approved course IDs and explain why. The server
reconstructs every course title, URL and study duration from Member 4's catalog.
No RunPod secret, prompt, arbitrary URL or invented course is passed to the UI.
"""

from __future__ import annotations

import logging
import math
import os
from urllib.parse import urlsplit

from ai.learning_planner import generate_roadmap

logger = logging.getLogger(__name__)
MAX_STEPS = 15


class RoadmapDataError(ValueError):
    """A trusted input catalog or deterministic result violates the contract."""


def ai_roadmap_enabled() -> bool:
    """Off by default; switch on only after Member 3's adapter passes review."""
    return os.getenv("AI_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}


def verified_course_index(resources: object, known_skill_ids: set[str]) -> dict[str, dict]:
    """Return server-approved courses, rejecting broken records claiming verification.

    `verified=True` is a claim approved by Member 4, not independently proven here.
    HTTPS syntax checking does not establish that a linked course really exists.
    """
    if not isinstance(resources, list):
        raise RoadmapDataError("Learning-resource catalog is not a list")

    index: dict[str, dict] = {}
    seen_ids: set[str] = set()
    for course in resources:
        if not isinstance(course, dict):
            raise RoadmapDataError("Invalid course record")
        cid = course.get("id")
        if not isinstance(cid, str) or not cid.strip() or cid in seen_ids:
            raise RoadmapDataError("Missing or duplicate course ID")
        seen_ids.add(cid)
        if course.get("verified") is not True:
            continue

        title = course.get("title")
        url = course.get("url")
        skills = course.get("skill_ids")
        hours = course.get("estimated_hours")
        if not isinstance(title, str) or not title.strip():
            raise RoadmapDataError("Verified course needs a title")
        if not isinstance(url, str):
            raise RoadmapDataError("Verified course needs an HTTPS URL")
        parts = urlsplit(url)
        if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
            raise RoadmapDataError("Verified course needs an HTTPS URL without credentials")
        if (not isinstance(skills, list) or not skills
                or any(not isinstance(s, str) or s not in known_skill_ids for s in skills)):
            raise RoadmapDataError("Verified course has unknown skill IDs")
        if hours is not None and (isinstance(hours, bool) or not isinstance(hours, (int, float))
                                  or not math.isfinite(hours) or hours <= 0):
            raise RoadmapDataError("Verified course has invalid estimated_hours")
        index[cid] = course
    return index


def _validated_steps(raw: object, *, target_role: str, scenario: str,
                     missing_skills: list[str], courses: dict[str, dict],
                     generation_mode: str) -> dict:
    """Normalize planner output; never trust model-provided URL/title/hours/coverage."""
    if not isinstance(raw, dict):
        raise ValueError("Planner response must be a JSON object")
    if raw.get("target_role") not in (None, target_role):
        raise ValueError("Planner changed target role")
    if raw.get("scenario") not in (None, scenario):
        raise ValueError("Planner changed scenario")
    proposed = raw.get("steps")
    if not isinstance(proposed, list) or len(proposed) > MAX_STEPS:
        raise ValueError("Invalid planner steps")

    desired = set(missing_skills)
    covered: set[str] = set()
    used: set[str] = set()
    steps: list[dict] = []
    for selection in proposed:
        if not isinstance(selection, dict):
            raise ValueError("Malformed course selection")
        cid = selection.get("course_id")
        reason = selection.get("reason")
        if not isinstance(cid, str) or cid not in courses or cid in used:
            raise ValueError("Planner selected an unverified or duplicate course ID")
        if not isinstance(reason, str) or not 3 <= len(reason.strip()) <= 350:
            raise ValueError("Course explanation is missing or out of bounds")
        if any(ord(ch) < 32 and ch not in "\n\t" for ch in reason):
            raise ValueError("Course explanation contains control characters")
        source = courses[cid]
        matches = desired.intersection(source["skill_ids"])
        if not matches:
            raise ValueError("Course does not cover any requested missing skill")
        used.add(cid)
        covered.update(matches)
        steps.append({
            "step": len(steps) + 1,
            "course_id": cid,
            "title": source["title"],
            "url": source["url"],
            "estimated_hours": source.get("estimated_hours"),
            "reason": reason.strip(),
        })

    note = ("AI-assisted ordering using only the approved course catalog; "
            "hours are provider estimates, not guarantees; AI explanations are not independently verified."
            if generation_mode == "runpod_validated" else
            "Only Member 4-approved courses are shown. Study times are estimates.")
    if desired - covered:
        note += " Some skills have no approved course coverage."
    return {
        "target_role": target_role,
        "scenario": scenario,
        "generation_mode": generation_mode,
        "steps": steps,
        "uncovered_skills": sorted(desired - covered),
        "note": note,
    }


def generate_safe_roadmap(target_role: str, missing_skills: list[str], scenario: str,
                          resources: object, known_skill_ids: set[str]) -> dict:
    """Use deterministic path first, optional RunPod second, with safe fallback.

    Member 3's generate_roadmap must maintain the current (target_role,
    missing_skills, scenario, verified_courses, *, use_ai=False) signature. When
    use_ai=True, its steps must contain course_id and a short reason.
    """
    courses = verified_course_index(resources, known_skill_ids)
    unique_missing = list(dict.fromkeys(missing_skills))
    verified = list(courses.values())
    try:
        baseline = generate_roadmap(target_role, unique_missing, scenario, verified, use_ai=False)
        safe_fallback = _validated_steps(
            baseline, target_role=target_role, scenario=scenario,
            missing_skills=unique_missing, courses=courses,
            generation_mode="deterministic_fallback",
        )
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        raise RoadmapDataError("Deterministic planner contract is invalid") from exc

    # No reason to consume AI/GPU time if nothing can be taught from the catalog.
    if not ai_roadmap_enabled() or not safe_fallback["steps"]:
        return safe_fallback

    try:
        proposed = generate_roadmap(target_role, unique_missing, scenario, verified, use_ai=True)
        # Member 3 internally falls back on request/parse errors. Never report
        # that as successful RunPod inference merely because use_ai=True.
        if not isinstance(proposed, dict) or proposed.get("generation_mode") != "runpod_ai":
            raise ValueError("Member 3 planner reported no successful AI selection")
        ai_result = _validated_steps(
            proposed, target_role=target_role, scenario=scenario,
            missing_skills=unique_missing, courses=courses,
            generation_mode="runpod_validated",
        )
        # The LLM may reorder or replace verified courses, not reduce proven coverage.
        if set(ai_result["uncovered_skills"]) != set(safe_fallback["uncovered_skills"]):
            raise ValueError("AI output reduced approved course coverage")
        return ai_result
    except Exception as exc:  # Boundary: third-party calls can fail in many ways.
        logger.warning("AI roadmap unavailable (%s); using verified fallback", type(exc).__name__)
        safe_fallback["note"] = ("AI personalization unavailable; showing approved fallback. "
                                 + safe_fallback["note"])
        return safe_fallback
