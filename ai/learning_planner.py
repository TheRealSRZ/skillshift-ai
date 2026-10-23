
"""Member 3: verified learning roadmap with RunPod fallback."""

import json
import logging
import re

logger = logging.getLogger(__name__)

from ai.runpod_client import ask_ai


def generate_roadmap(
    target_role: str,
    missing_skills: list[str],
    scenario: str,
    verified_courses: list[dict],
    *,
    use_ai=False,
):
    missing = set(missing_skills)

    # Never let the AI invent courses or URLs.
    eligible = [
        course
        for course in verified_courses
        if course.get("verified")
        and course.get("url")
        and course.get("id")
        and missing.intersection(course.get("skill_ids", []))
    ]

    selected_courses = []
    generation_mode = "deterministic_fallback"

    if use_ai and eligible:
        try:
            prompt = (
                "You are SkillShift AI, a learning roadmap assistant.\n"
                "Select courses ONLY from the supplied list.\n"
                "Return ONLY a valid JSON array of course IDs.\n"
                "Do not invent course IDs, URLs, or statistics.\n\n"
                f"Target career: {target_role}\n"
                f"Missing skill IDs: {sorted(missing)}\n"
                f"Scenario: {scenario}\n"
                "Available verified courses:\n"
                + json.dumps(
                    [
                        {
                            "id": c["id"],
                            "title": c["title"],
                            "skill_ids": c.get("skill_ids", []),
                        }
                        for c in eligible
                    ]
                )
            )

            raw = ask_ai(prompt)
            if not isinstance(raw, str) or len(raw) > 16000:
                raise ValueError('AI output exceeds safe limits')

            # Accept a JSON array even when Qwen wraps it in explanations.
            match = re.search(r'\[\s*"[^"]+"(?:\s*,\s*"[^"]+")*\s*\]', raw)

            if not match:
                raise ValueError("AI did not return a valid course ID array")

            selected_ids = json.loads(match.group(0))

            if not isinstance(selected_ids, list):
                raise ValueError("AI must return a JSON array")

            eligible_by_id = {c["id"]: c for c in eligible}

            if (
                not selected_ids
                or not all(
                    isinstance(cid, str) and cid in eligible_by_id
                    for cid in selected_ids
                )
                or len(selected_ids) != len(set(selected_ids))
            ):
                raise ValueError("Invalid AI course selection")

            
            selected_courses = [
                eligible_by_id[cid] for cid in selected_ids
            ]

            # Calculate the skills covered by all eligible courses.
            baseline_coverage = set()
            for course in eligible:
                baseline_coverage.update(
                    missing.intersection(course.get("skill_ids", []))
                )

            # Calculate the skills covered by AI-selected courses.
            ai_coverage = set()
            for course in selected_courses:
                ai_coverage.update(
                    missing.intersection(course.get("skill_ids", []))
                )

            # Reject AI selections that miss coverable skills.
            if not baseline_coverage.issubset(ai_coverage):
                raise ValueError("AI selection has incomplete skill coverage")

            generation_mode = "runpod_ai"


        except Exception as e:
            # Diagnostic categories come only from our own validation messages;
            # never log raw provider output, course prompt, token, or API key.
            known_failures = {
                "AI did not return a valid course ID array": "missing_course_id_array",
                "AI must return a JSON array": "invalid_array_type",
                "Invalid AI course selection": "invalid_or_duplicate_course_ids",
                "AI selection has incomplete skill coverage": "incomplete_skill_coverage",
                "AI output exceeds safe limits": "oversized_ai_output",
            }
            category = known_failures.get(str(e), 'external_error_or_malformed_output') if isinstance(e, ValueError) else 'provider_or_transport_error'
            logger.warning("AI roadmap fallback: %s (%s)", type(e).__name__, category)
            selected_courses = []
            generation_mode = "deterministic_fallback"

    # Safe fallback if AI is unavailable or returns invalid data.
    if generation_mode == "deterministic_fallback":
        selected_courses = eligible

    covered = set()
    steps = []

    for course in selected_courses:
        matched = (
            missing.intersection(course.get("skill_ids", []))
            - covered
        )

        if not matched:
            continue

        covered.update(matched)

        steps.append({
            "step": len(steps) + 1,
            "course_id": course["id"],
            "title": course["title"],
            "url": course["url"],
            "estimated_hours": course.get("estimated_hours"),
            "reason": (
                "Covers missing skills: "
                + ", ".join(sorted(matched))
            ),
        })

    return {
        "target_role": target_role,
        "scenario": scenario,
        "generation_mode": generation_mode,
        "steps": steps,
        "uncovered_skills": sorted(missing - covered),
        "note": (
            "No verified courses cover the remaining skills."
            if missing - covered
            else "Times are course estimates, not guarantees."
        ),
    }
