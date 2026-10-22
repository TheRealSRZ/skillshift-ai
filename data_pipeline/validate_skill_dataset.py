"""SkillShift AI: post-commit-safe skill/weight integrity checks.

Run from repo root: python data_pipeline/validate_skill_dataset.py
Read-only; checks current data contracts, not differences against Git HEAD.
For a historical change review, inspect the actual Git diff separately.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
EXPECTED_CHANGES = {
    ("role_electrical_engineer", "skill_electrical_safety"): (3, 4),
    ("role_nursing_professional", "skill_medication_safety"): (3, 4),
    ("role_nursing_professional", "skill_critical_thinking"): (2, 3),
}
REQUIRED_SKILL_FIELDS = {"id", "name", "sdgs", "sdg_rationale", "sdg_mapping_method",
                         "description", "practical_example", "description_provenance"}


def load(filename):
    return json.loads((DATA / filename).read_text(encoding="utf-8"))


def main():
    skills = load("skills.json")
    careers = load("careers.json")
    evidence = load("skill_weight_evidence.json")
    errors = []

    def require(condition, message):
        if not condition:
            errors.append(message)

    require(isinstance(skills, list) and len(skills) == 36, "Expected 36 skills")
    skill_ids = set()
    for skill in skills:
        sid = skill.get("id")
        require(isinstance(sid, str) and bool(sid.strip()), f"Invalid skill ID: {sid!r}")
        require(sid not in skill_ids, f"Duplicate skill ID: {sid}")
        skill_ids.add(sid)
        require(REQUIRED_SKILL_FIELDS.issubset(skill), f"{sid}: missing required skill fields")
        for field in ("name", "sdg_rationale", "sdg_mapping_method", "description", "practical_example"):
            require(isinstance(skill.get(field), str) and bool(skill[field].strip()), f"{sid}: invalid {field}")
        require(isinstance(skill.get("sdgs"), list) and bool(skill["sdgs"]), f"{sid}: invalid SDGs")
        require(skill.get("description_provenance") == "team_authored_general_skill_explanation",
                f"{sid}: incorrect description provenance")

    require(isinstance(careers, list) and len(careers) == 9, "Expected 9 careers")
    by_career = {}
    for career in careers:
        cid = career.get("id")
        require(cid not in by_career, f"Duplicate career ID: {cid}")
        by_career[cid] = career
        required = career.get("required_skills")
        require(isinstance(required, dict) and bool(required), f"{cid}: empty/invalid required_skills")
        if isinstance(required, dict):
            for sid, weight in required.items():
                require(sid in skill_ids, f"{cid}: unknown skill {sid}")
                require(type(weight) is int and 1 <= weight <= 4, f"{cid}/{sid}: invalid importance weight {weight}")

    reviewed = evidence.get("scope", {}).get("careers_reviewed", [])
    require(len(reviewed) == 6 and len(set(reviewed)) == 6, "Expected six unique reviewed careers")
    expected_pairs = {(cid, sid) for cid in reviewed if cid in by_career
                      for sid in by_career[cid].get("required_skills", {})}
    entries = evidence.get("assignments", [])
    require(isinstance(entries, list), "Evidence assignments must be a list")
    seen = set()
    for entry in entries:
        key = (entry.get("career_id"), entry.get("skill_id"))
        require(key not in seen, f"Duplicate evidence pair: {key}")
        seen.add(key)
        role = by_career.get(key[0], {})
        weight = role.get("required_skills", {}).get(key[1])
        require(weight == entry.get("weight"), f"{key}: current weight mismatch")
        require(isinstance(entry.get("justification"), str) and bool(entry["justification"].strip()),
                f"{key}: missing justification")
        require(bool(entry.get("evidence")), f"{key}: no evidence")
        require(entry.get("weight_provenance") == "team_defined_judgement_not_official_source_score",
                f"{key}: incorrect weight provenance")
        expected_prior = EXPECTED_CHANGES[key][0] if key in EXPECTED_CHANGES else weight
        require(entry.get("previous_weight") == expected_prior,
                f"{key}: wrong historical previous_weight")
        if key in EXPECTED_CHANGES:
            require(weight == EXPECTED_CHANGES[key][1], f"{key}: expected revised weight not applied")
    require(seen == expected_pairs and len(seen) == 36, "Evidence must cover exactly 36 career-skill pairs")

    if errors:
        print(f"FAIL: {len(errors)} skill dataset issue(s)")
        for error in errors[:50]:
            print(" -", error)
        raise SystemExit(1)
    print("PASS: 36 skills have required fields, descriptions, examples and provenance")
    print("PASS: 9 careers have valid skill IDs and importance weights")
    print("PASS: all 36 evidence entries match current career weights")
    print("PASS: the three approved changes and recorded previous values match")
    print("NOTE: Post-commit-safe; does not claim unchanged fields compared with historical Git state.")
    print("NOTE: Use Git diff/history for historical preservation and separate source validation for citations.")


if __name__ == "__main__":
    main()
