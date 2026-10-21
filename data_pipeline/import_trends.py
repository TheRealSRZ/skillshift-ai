"""Build dated DOSM JMI major-occupation trend evidence from a validated CSV.

From repository root:
    python data_pipeline/import_trends.py
    python data_pipeline/import_trends.py --input data/jmi_major_occupation_2025_2026.csv --output data/processed/dosm_major_group_signals.json

Descriptive observations only: not career-specific, skill-specific, or AI forecasts.
"""

import argparse
import csv
import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

PERIOD_RE = re.compile(r"^(\d{4})-Q([1-4])$")
REQUIRED_FIELDS = {"period", "occupation_group", "job_offerings", "geography", "metric", "source_title", "source_url"}
METRIC = "online_job_offerings_major_group"
# The change in published counts near this boundary warrants a comparability review.
# This flag DOES NOT assert that DOSM changed its method.
REVIEW_BOUNDARY = ("2025-Q2", "2025-Q3")


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
        records, seen = [], set()
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
            key = (r["period"], r["occupation_group"])
            if key in seen:
                raise ValueError(f"Line {line_number}: duplicate quarter/occupation group {key}")
            seen.add(key)
            r["job_offerings"] = int(r["job_offerings"])
            records.append(r)
    if not records:
        raise ValueError("Input CSV is empty")
    return records


def build_snapshot(records, source_file):
    provenance = {(r["source_title"], r["source_url"]) for r in records}
    if len(provenance) != 1:
        raise ValueError("Mixed source titles/URLs: split data sources into separate snapshots")
    source_title, source_url = next(iter(provenance))
    periods = sorted({r["period"] for r in records}, key=quarter_number)
    if len(periods) < 2:
        raise ValueError("At least two quarters required")
    previous_period, latest_period = periods[-2:]
    if quarter_number(latest_period) - quarter_number(previous_period) != 1:
        raise ValueError("Latest two quarters are not consecutive")

    by_group = defaultdict(dict)
    totals = defaultdict(int)
    for r in records:
        by_group[r["occupation_group"]][r["period"]] = r["job_offerings"]
        totals[r["period"]] += r["job_offerings"]
    if totals[previous_period] <= 0 or totals[latest_period] <= 0:
        raise ValueError("Market totals must be positive")

    comparisons, missing_groups = [], []
    for group in sorted(by_group):
        values = by_group[group]
        if previous_period not in values or latest_period not in values:
            missing_groups.append(group)
            continue
        old, new = values[previous_period], values[latest_period]
        old_share = old / totals[previous_period]
        new_share = new / totals[latest_period]
        delta = new - old
        comparisons.append({
            "occupation_group": group,
            "previous_period": previous_period,
            "previous_job_offerings": old,
            "latest_period": latest_period,
            "latest_job_offerings": new,
            "absolute_change": delta,
            "percent_change": round(100 * delta / old, 2) if old else None,
            "direction": "increase" if delta > 0 else "decrease" if delta < 0 else "unchanged",
            "evidence_level": "major_occupation_group",
            "previous_market_share_pct": round(100 * old_share, 4),
            "latest_market_share_pct": round(100 * new_share, 4),
            "market_share_change_pp": round(100 * (new_share - old_share), 4),
            "relative_market_share_change_pct": round(100 * (new_share / old_share - 1), 2) if old_share else None,
        })
    if not comparisons:
        raise ValueError("No groups available in both latest quarters")
    crosses_review_boundary = (previous_period, latest_period) == REVIEW_BOUNDARY
    # Historical warning appears even though the latest comparison is Q1->Q2 2026.
    historical_warnings = []
    if all(p in periods for p in REVIEW_BOUNDARY):
        early, late = REVIEW_BOUNDARY
        change_pct = round((totals[late] / totals[early] - 1) * 100, 2) if totals[early] else None
        historical_warnings.append({
            "between": [early, late],
            "flag": "large_historical_jump_review_comparability",
            "total_change_pct": change_pct,
            "methodology_break_confirmed": False,
            "note": "Unusually large published-volume movement; reason not established. Do not infer an official series break or AI impact.",
        })
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
        "method": "Quarter-on-quarter count change = (new-old)/old*100. Market share = group offerings / sum of reported groups that period. Percentage-point change = latest share - previous share. Relative share change = (latest share/previous share - 1)*100. Null where denominator is zero.",
        "career_specific": False,
        "skill_specific": False,
        "ai_exposure_measure": False,
        "can_directly_adjust_career_scores": False,
        "previous_reported_group_total": totals[previous_period],
        "latest_reported_group_total": totals[latest_period],
        "historical_reported_group_totals": [{"period": p, "sum_of_reported_groups": totals[p]} for p in periods],
        "market_share_denominator": "sum_of_available_reported_occupation_groups_per_period",
        "latest_comparison_crosses_2025_q3_review_boundary": crosses_review_boundary,
        "historical_comparability_warnings": historical_warnings,
        "limitations": [
            "Online job offerings are not unique vacancies, employment totals, or verified skill demand.",
            "Group-share denominators sum reported occupation rows; missing groups or revisions can distort comparisons with published grand totals.",
            "2025-Q2 to Q3 had a large published volume jump; cause of any discontinuity is unverified.",
            "Major occupation groups are broader than MASCO four-digit career groups.",
            "Quarterly movement is not a forecast, AI impact, or evidence of an individual career's growth.",
            "Do not directly convert these major-group signals into specific career or skill score multipliers.",
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
    print(f"Historical warnings: {len(result['historical_comparability_warnings'])}")
    print("Descriptive group-level evidence only; no AI or career skill multipliers generated.")


if __name__ == "__main__":
    main()
