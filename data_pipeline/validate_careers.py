"""Cross-file validator for SkillShift AI career datasets.

Place in data_pipeline/validate_careers.py and run:
    python data_pipeline/validate_careers.py

Uses Python standard library only. Read-only: does not change the dataset.
"""

import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ERRORS: list[str] = []
WARNINGS: list[str] = []
CHECKS = 0


def check(ok: bool, description: str) -> None:
    global CHECKS
    CHECKS += 1
    if not ok:
        ERRORS.append(description)


def load_unique_json(filename: str):
    path = DATA / filename
    if not path.is_file():
        raise ValueError(f"Missing file: data/{filename}")

    def reject_duplicate_keys(items):
        values = {}
        for key, value in items:
            if key in values:
                raise ValueError(f"Duplicate JSON key '{key}' in data/{filename}")
            values[key] = value
        return values

    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle, object_pairs_hook=reject_duplicate_keys)


def index_records(records, filename: str, key: str = "id"):
    check(isinstance(records, list), f"{filename} must contain a JSON array")
    if not isinstance(records, list):
        return {}
    check(all(isinstance(row, dict) and isinstance(row.get(key), str) and row[key] for row in records),
          f"{filename} has a missing or invalid '{key}'")
    identifiers = [row.get(key) for row in records if isinstance(row, dict)]
    check(len(identifiers) == len(set(identifiers)), f"{filename} contains duplicate '{key}'")
    return {row[key]: row for row in records if isinstance(row, dict) and isinstance(row.get(key), str)}


def proper_url(value):
    return isinstance(value, str) and urlsplit(value).scheme == "https" and bool(urlsplit(value).netloc)


def run():
    try:
        careers_data = load_unique_json("careers.json")
        skills_data = load_unique_json("skills.json")
        sources_data = load_unique_json("sources.json")
        courses_data = load_unique_json("learning_resources.json")
        trends_data = load_unique_json("trends.json")
        occupation_data = load_unique_json("occupation_trends.json")
        sdg_mapping_data = load_unique_json("sdg_mapping.json")
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print("FAIL: Could not read all six JSON files:", exc)
        return 1

    careers = index_records(careers_data, "careers.json")
    skills = index_records(skills_data, "skills.json")
    sources = index_records(sources_data, "sources.json")

    # SDG reference file must cover every SDG used by career and skill records.
    check(isinstance(sdg_mapping_data, list), "sdg_mapping.json must contain a JSON array")
    sdg_reference: dict[int, dict] = {}
    if isinstance(sdg_mapping_data, list):
        for row in sdg_mapping_data:
            if not isinstance(row, dict):
                check(False, "sdg_mapping.json contains a non-object entry")
                continue
            number = row.get("sdg")
            check(type(number) is int and 1 <= number <= 17,
                  f"sdg_mapping.json: invalid SDG number {number!r}")
            if type(number) is not int or not 1 <= number <= 17:
                continue
            check(number not in sdg_reference,
                  f"sdg_mapping.json: duplicate SDG {number}")
            check(isinstance(row.get("title"), str) and bool(row["title"].strip()),
                  f"sdg_mapping.json: SDG {number} missing title")
            check(isinstance(row.get("rationale"), str) and bool(row["rationale"].strip()),
                  f"sdg_mapping.json: SDG {number} missing rationale")
            sdg_reference[number] = row

    courses = index_records(courses_data, "learning_resources.json")
    check(isinstance(occupation_data, list), "occupation_trends.json must be an array")
    if not isinstance(occupation_data, list):
        occupation_data = []
    check(isinstance(trends_data, dict), "trends.json must be an object")
    if not isinstance(trends_data, dict):
        trends_data = {}

    # Confirm the consistent standardized source schema, source metadata, and claims.
    if isinstance(sources_data, list) and sources_data:
        reference_keys = list(sources_data[0])
        for record in sources_data:
            check(list(record) == reference_keys,
                  f"Source {record.get('id')} has a different field set or order")
    claim_owners = {}
    for src_id, src in sources.items():
        real = bool(src.get("usable_as_real_evidence"))
        if real:
            check(proper_url(src.get("url")), f"{src_id}: missing/invalid HTTPS source URL")
            check(bool(src.get("retrieved_date")), f"{src_id}: retrieval date missing")
            check(bool(src.get("license_status")), f"{src_id}: licence status missing")
            check(bool(src.get("evidence_location")), f"{src_id}: evidence location missing")
        source_claims = src.get("supported_claims", [])
        check(isinstance(source_claims, list), f"{src_id}: supported_claims must be a list")
        for claim in source_claims if isinstance(source_claims, list) else []:
            cid = claim.get("claim_id") if isinstance(claim, dict) else None
            check(bool(cid) and bool(claim.get("claim")) and bool(claim.get("evidence_location")),
                  f"{src_id}: incomplete evidence claim")
            check(cid not in claim_owners, f"Duplicate claim ID: {cid}")
            if cid:
                claim_owners[cid] = src_id

    check(len(skills) >= 19, f"Expected at least 19 skills; found {len(skills)}")
    for sid, skill in skills.items():
        sdgs = skill.get("sdgs")
        check(isinstance(sdgs, list) and bool(sdgs) and all(type(x) is int and 1 <= x <= 17 for x in sdgs),
              f"{sid}: invalid or missing SDG mapping")
        if isinstance(sdgs, list):
            for number in sdgs:
                if type(number) is int and 1 <= number <= 17:
                    check(number in sdg_reference,
                          f"{sid}: SDG {number} missing from sdg_mapping.json")
        check(bool(skill.get("sdg_rationale")), f"{sid}: missing SDG explanation")
        check(skill.get("sdg_mapping_method") == "team_defined_interpretation",
              f"{sid}: SDG mapping must be explicitly team-defined")

    required_careers = ["role_software_developer", "role_accountant_auditor","role_data_professional","role_marketing_professional","role_electrical_engineer","role_nursing_professional"]
    for rid in required_careers:
        check(rid in careers, f"Missing career: {rid}")
    for career_id, career in careers.items():
        req = career.get("required_skills", {})
        check(isinstance(req, dict) and bool(req), f"{career_id}: required_skills must be a nonempty object")
        if isinstance(req, dict):
            for sid, weight in req.items():
                check(sid in skills, f"{career_id}: unknown skill {sid}")
                check(type(weight) is int and 1 <= weight <= 4,
                      f"{career_id}: {sid} has invalid team-defined weight {weight!r}")
        if career_id in required_careers:
            check(career.get("market") == "Malaysia", f"{career_id}: market should be Malaysia")
            check(bool(career.get("masco_code")), f"{career_id}: MASCO code missing")
            sdgs = career.get("sdgs", [])
            check(isinstance(sdgs, list) and bool(sdgs) and all(type(x) is int and 1 <= x <= 17 for x in sdgs),
                  f"{career_id}: role SDGs missing or invalid")
            check(career.get("evidence_status") == "curated_with_assumptions",
                  f"{career_id}: should distinguish verified evidence from assumed weights")
            check(isinstance(req, dict) and len(req) == 6, f"{career_id}: expected six selected skills")
        else:
            check(career.get("evidence_status") == "synthetic_demo",
                  f"{career_id}: demo career must be clearly labelled synthetic")
        # Include demo career SDG references if present, without changing their labels.
        career_sdgs = career.get("sdgs", [])
        if isinstance(career_sdgs, list):
            for number in career_sdgs:
                if type(number) is int and 1 <= number <= 17:
                    check(number in sdg_reference,
                          f"{career_id}: SDG {number} missing from sdg_mapping.json")
        source_ids = career.get("source_ids", [])
        for source_id in source_ids:
            check(source_id in sources, f"{career_id}: unknown source {source_id}")
        for cid in career.get("evidence_claim_ids", []):
            check(cid in claim_owners, f"{career_id}: claim not found: {cid}")
            check(claim_owners.get(cid) in source_ids,
                  f"{career_id}: claim {cid} belongs to a source missing from source_ids")

    check(len(courses) >= 19, f"Expected at least 19 courses; found {len(courses)}")
    allowed_categories = {"foundational", "ai_adaptation"}
    for cid, course in courses.items():
        skill_ids = course.get("skill_ids", [])
        check(isinstance(skill_ids, list) and bool(skill_ids), f"{cid}: skill_ids missing")
        for sid in skill_ids if isinstance(skill_ids, list) else []:
            check(sid in skills, f"{cid}: unknown skill ID {sid}")
        check(course.get("learning_category") in allowed_categories, f"{cid}: invalid learning_category")
        check(proper_url(course.get("url")), f"{cid}: URL missing or not HTTPS")
        check(course.get("cost") == "free_learning", f"{cid}: cost unexpectedly differs from free_learning")
        duration = course.get("estimated_hours")
        check(duration is None or (type(duration) in (float, int) and duration > 0),
              f"{cid}: estimated_hours must be positive or null")
        if duration is None:
            WARNINGS.append(f"{cid}: duration is unknown; display 'Duration varies', not 0 h")
        check(bool(course.get("verified_date")), f"{cid}: missing verified_date")

    for career_id in required_careers:
        career = careers.get(career_id, {})
        needed_skills = set(career.get("required_skills", {}))
        covered = {sid for course in courses.values() for sid in course.get("skill_ids", [])}
        uncovered = sorted(needed_skills - covered)
        check(not uncovered, f"{career_id}: missing learning resources for {uncovered}")
        if career_id == "role_accountant_auditor":
            ai_courses = [c for c in courses.values() if c.get("learning_category") == "ai_adaptation"
                          and needed_skills.intersection(c.get("skill_ids", []))]
            check(len(ai_courses) >= 2, "Accountants and Auditors: expected two AI-adaptation resources")

    seen_trend_keys = set()
    seen_observations = {}
    for obs in occupation_data:
        if not isinstance(obs, dict):
            check(False, "occupation_trends.json contains a non-object record")
            continue
        cid, period, metric = obs.get("occupation_id"), obs.get("period"), obs.get("metric")
        unique_key = (cid, period, metric)
        check(unique_key not in seen_trend_keys, f"Duplicate occupation trend observation: {unique_key}")
        seen_trend_keys.add(unique_key)
        check(cid in careers, f"Unknown occupation in occupation_trends.json: {cid}")
        check(obs.get("source_id") in sources, f"{cid}: unknown observation source")
        check(obs.get("market") == "Malaysia", f"{cid}: market should be Malaysia")
        check(metric == "online_job_postings", f"{cid}: unexpected metric {metric}")
        check(period == "2026-Q2", f"{cid}: unexpected period {period}; Q2-only plan")
        check(type(obs.get("value")) is int and obs["value"] >= 0, f"{cid}: value must be a nonnegative integer")
        check(obs.get("evidence_status") == "official_reported", f"{cid}: evidence_status should be official_reported")
        seen_observations[cid] = obs

    expected_offerings = {"role_software_developer": 19899, "role_accountant_auditor": 22067}
    for cid, expected in expected_offerings.items():
        obs = seen_observations.get(cid, {})
        check(obs.get("value") == expected, f"{cid}: expected {expected:,} Q2 2026 job offerings")
        check(obs.get("source_id") == "src_dosm_jmi_q2_2026", f"{cid}: should use Q2 2026 DOSM source")
    check(len(occupation_data) == 2, "Q2-only plan should have exactly two career observations")

    check(trends_data.get("region") == "synthetic_demo", "trends.json must be clearly labelled synthetic")
    check("src_demo" in trends_data.get("source_ids", []), "Synthetic trend fixture should reference src_demo")
    check(all(sid in skills for sid in trends_data.get("multipliers", {})),
          "Synthetic trend fixture references a skill not in skills.json")
    check(all(isinstance(v, (int, float)) and v > 0 for v in trends_data.get("multipliers", {}).values()),
          "Synthetic trend multipliers must be positive numbers")

    # Domain 1 may still need a periodic refresh pipeline and scenario functionality.
    print(f"Checked {len(careers)} careers, {len(skills)} skills, {len(sources)} sources, "
          f"{len(courses)} courses, {len(occupation_data)} occupation observations.")
    print(f"RESULT: {CHECKS - len(ERRORS)} / {CHECKS} checks passed; {len(ERRORS)} error(s)")
    for issue in ERRORS:
        print("  ERROR:", issue)
    for note in WARNINGS:
        print("  NOTE:", note)
    if ERRORS:
        print("FAIL: Correct the dataset errors before committing.")
        return 1
    print("PASS: All required career datasets are cross-file consistent.")
    print("NOTE: This does not test live URLs, verify all source claims, or test the teammates' backend.")
    print("NOTE: Updatable trends and scenario generation remain team-level Domain 1 work.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
