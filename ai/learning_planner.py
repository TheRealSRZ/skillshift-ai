
"""Member 3: safe learning roadmap with RunPod fallback."""

def generate_roadmap(
    target_role: str,
    missing_skills: list[str],
    scenario: str,
    verified_courses: list[dict],
    *,
    use_ai=False
):
    # Try RunPod only when AI is requested.
    if use_ai:
        try:
            from ai.runpod_client import ask_ai

            prompt = (
                f"Target career: {target_role}\n"
                f"Missing skills: {missing_skills}\n"
                f"Scenario: {scenario}\n"
                "Suggest a learning roadmap using verified courses only."
            )

            ai_response = ask_ai(prompt)

            # Do not trust AI-generated recommendations yet.
            # Structured validation will be implemented later.
            if not ai_response:
                raise ValueError("Empty AI response")

            raise ValueError("AI response validation not implemented yet")

        except Exception:
            # If RunPod fails, use the safe fallback below.
            pass

    missing = set(missing_skills)
    covered = set()
    steps = []

    for course in verified_courses:
        if not course.get("verified") or not course.get("url"):
            continue

        matched = missing.intersection(
            course.get("skill_ids", [])
        ) - covered

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
            )
        })

    return {
        "target_role": target_role,
        "scenario": scenario,
        "generation_mode": "deterministic_fallback",
        "steps": steps,
        "uncovered_skills": sorted(missing - covered),
        "note": (
            "Starter dataset has no verified courses. "
            "Member 4 must validate real resources."
            if not steps and missing
            else "Times are course estimates, not guarantees."
        )
    }
