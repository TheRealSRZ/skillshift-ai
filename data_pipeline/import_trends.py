"""Import DOSM JMI major-occupation observations into a dated, auditable snapshot.

Run from the repository root:
    python data_pipeline/import_trends.py
    python data_pipeline/import_trends.py --input data/jmi_major_occupation_2025_2026.csv --output data/processed/dosm_major_group_signals.json

IMPORTANT: these are broad major-occupation online job-offering counts, NOT
occupation-specific employment growth, skill demand, or AI exposure.
This script deliberately does not modify data/trends.json or fabricate skill multipliers.
"""

import argparse
import csv
import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

PERIOD_RE = re.compile(r"^(\d{4})-Q([1-4])$")
REQUIRED_FIELDS = {
    "period", "occupation_group", "job_offerings", "geography",
    "metric", "source_title", "source_url",
}
METRIC = "online_job_offerings_major_group"


def quarter_number(value):
    match = PERIOD_RE.fullmatch(value)
    if not match:
        raise ValueError(f"Invalid quarter: {value!r}; expected YYYY-Q1 through YYYY-Q4")
    return int(match.group(1)) * 4 + int(match.group(2)) - 1


def load_records(path):
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not REQUIRED_FIELDS.issubset(reader.fieldnames):
            raise ValueError(f"CSV must contain columns: {', '.join(sorted(REQUIRED_FIELDS))}")
        records = []
        seen = set()
        for line_number, raw in enumerate(reader, start=2):
            if None in raw:
                raise ValueError(f"Line {line_number}: extra CSV columns")
            r = {k: (raw.get(k) or "").strip() for k in REQUIRED_FIELDS}
            if not all(r.values()):
                raise ValueError(f"Line {line_number}: required field is empty")
            quarter_number(r["period"])
            if r["geography"] != "Malaysia" or r["metric"] != METRIC:
                raise ValueError(f"Line {line_number}: unexpected geography or metric")
            if not r["source_url"].startswith("https://"):
                raise ValueError(f"Line {line_number}: source must have an HTTPS URL")
            if not re.fullmatch(r"\d+", r["job_offerings"]):
                raise ValueError(f"Line {line_number}: job_offerings must be a nonnegative integer")
            value = int(r["job_offerings"])
            key = (r["period"], r["occupation_group"])
            if key in seen:
                raise ValueError(f"Line {line_number}: duplicate quarter/occupation group {key}")
            seen.add(key)
            r["job_offerings"] = value
            records.append(r)
    if not records:
        raise ValueError("Input CSV is empty")
    return records


def build_snapshot(records, source_file):
    by_group = defaultdict(dict)
    provenance = {(r["source_title"], r["source_url"]) for r in records}
    if len(provenance) != 1:
        raise ValueError("Mixed source titles/URLs: split data sources into separate snapshots")
    source_title, source_url = next(iter(provenance))
    periods = sorted({r["period"] for r in records}, key=quarter_number)
    if len(periods) < 2:
        raise ValueError("At least two quarters are required for a comparison")
    previous_period, latest_period = periods[-2:]
    if quarter_number(latest_period) - quarter_number(previous_period) != 1:
        raise ValueError("Latest two quarters are not consecutive: cannot label as quarter-on-quarter")
    for r in records:
        by_group[r["occupation_group"]][r["period"]] = r["job_offerings"]

    comparisons = []
    missing_groups = []
    for group in sorted(by_group):
        observations = by_group[group]
        if previous_period not in observations or latest_period not in observations:
            missing_groups.append(group)
            continue
        old, new = observations[previous_period], observations[latest_period]
        difference = new - old
        comparisons.append({
            "occupation_group": group,
            "previous_period": previous_period,
            "previous_job_offerings": old,
            "latest_period": latest_period,
            "latest_job_offerings": new,
            "absolute_change": difference,
            "percent_change": round(100 * difference / old, 2) if old else None,
            "direction": "increase" if difference > 0 else "decrease" if difference < 0 else "unchanged",
            "evidence_level": "major_occupation_group",
        })
    if not comparisons:
        raise ValueError("No occupation groups have observations in both latest quarters")
    return {
        "snapshot_id": f"dosm_jmi_major_group_{latest_period.lower().replace('-', '_')}",
        "status": "observed_major_group_qoq_comparison",
        "geography": "Malaysia",
        "metric": METRIC,
        "source_id": "src_dosm_jmi_q2_2026" if "q22026" in source_url.lower() else None,
        "source_title": source_title,
        "source_url": source_url,
        "input_file": str(source_file).replace("\\", "/"),
        "periods_available": periods,
        "previous_period": previous_period,
        "latest_period": latest_period,
        "generated_date": date.today().isoformat(),
        "method": "Quarter-on-quarter change = (latest - previous) / previous * 100. Null when previous count is zero; rounded to 2 decimals.",
        "career_specific": False,
        "skill_specific": False,
        "ai_exposure_measure": False,
        "can_directly_adjust_career_scores": False,
        "limitations": [
            "Online job offerings are not unique vacancies, employment totals, or verified skill demand.",
            "Major occupation groups are broader than MASCO four-digit career groups.",
            "Quarterly movement is not a forecast, AI impact, or evidence of an individual career's growth.",
            "A backend must not apply these group-level percentages as career- or skill-specific score multipliers.",
        ],
        "missing_latest_quarter_groups": missing_groups,
        "group_comparisons": comparisons,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/jmi_major_occupation_2025_2026.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/dosm_major_group_signals.json"))
    args = parser.parse_args()
    if not args.input.is_file():
        parser.error(f"Input file not found: {args.input}")
    if args.input.resolve() == args.output.resolve():
        parser.error("Output must not overwrite input")
    try:
        result = build_snapshot(load_records(args.input), args.input)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Created {args.output} ({len(result['group_comparisons'])} major-group comparisons)")
    print(f"Compared {result['previous_period']} with {result['latest_period']}")
    print("Note: descriptive major-group observations only; no career/skill multipliers generated.")


if __name__ == "__main__":
    main()
