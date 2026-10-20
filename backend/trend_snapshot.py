"""Validate a dated skills trend snapshot before it influences career scoring.

Member 4 owns the data and import process. This module is a read-only boundary.
The numbers in a snapshot are not automatically verified labour-market statistics.
"""

from copy import deepcopy
from datetime import date
from math import isfinite
from typing import Callable
import re


class SnapshotValidationError(ValueError):
    """Active snapshot or its reference catalogs are invalid."""


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SnapshotValidationError(f"{field} must be a non-empty string")
    return value


def _date(value: object, field: str) -> date:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise SnapshotValidationError(f"{field} must use YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise SnapshotValidationError(f"{field} is not a valid calendar date") from exc


def validate_snapshot(snapshot: object, skills: object, sources: object) -> dict:
    """Return an enriched copy that preserves existing frontend fields.

    Only a properly named, dated, source-linked snapshot can become active.
    The source registry resolves citations but does NOT certify multipliers.
    """
    if not isinstance(snapshot, dict):
        raise SnapshotValidationError("Trend snapshot must be an object")
    if not isinstance(skills, list) or not skills:
        raise SnapshotValidationError("Skills catalog must be a nonempty list")
    if not isinstance(sources, list) or not sources:
        raise SnapshotValidationError("Sources catalog must be a nonempty list")

    known_skills = set()
    for skill in skills:
        if not isinstance(skill, dict):
            raise SnapshotValidationError("Invalid skills catalog record")
        sid = _required_text(skill.get("id"), "Skill ID")
        if sid in known_skills:
            raise SnapshotValidationError(f"Duplicate skill ID: {sid}")
        known_skills.add(sid)

    known_sources = {}
    for source in sources:
        if not isinstance(source, dict):
            raise SnapshotValidationError("Invalid source catalog record")
        source_id = _required_text(source.get("id"), "Source ID")
        _required_text(source.get("title"), f"Source title for {source_id}")
        if source_id in known_sources:
            raise SnapshotValidationError(f"Duplicate source ID: {source_id}")
        known_sources[source_id] = source

    for name in ("snapshot_id", "label", "region"):
        _required_text(snapshot.get(name), name)

    observed = _date(snapshot.get("observed_date"), "observed_date")
    retrieved = _date(snapshot.get("retrieved_date"), "retrieved_date")
    if retrieved < observed:
        raise SnapshotValidationError("retrieved_date cannot precede observed_date")

    raw_ids = snapshot.get("source_ids")
    if not isinstance(raw_ids, list) or not raw_ids:
        raise SnapshotValidationError("source_ids must be a nonempty list")
    if any(not isinstance(s, str) or not s.strip() for s in raw_ids):
        raise SnapshotValidationError("source_ids must contain nonempty strings")
    if len(raw_ids) != len(set(raw_ids)):
        raise SnapshotValidationError("source_ids contains duplicate IDs")
    unknown_sources = sorted(set(raw_ids) - known_sources.keys())
    if unknown_sources:
        raise SnapshotValidationError(f"Unknown source IDs: {unknown_sources}")

    multipliers = snapshot.get("multipliers")
    if not isinstance(multipliers, dict):
        raise SnapshotValidationError("multipliers must be a skill-ID-to-number object")
    unknown_skills = sorted(set(multipliers) - known_skills)
    if unknown_skills:
        raise SnapshotValidationError(f"Unknown multiplier skill IDs: {unknown_skills}")
    for sid, value in multipliers.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise SnapshotValidationError(f"Multiplier for {sid} must be numeric")
        if not isfinite(value) or value <= 0:
            raise SnapshotValidationError(f"Multiplier for {sid} must be finite and positive")

    status = snapshot.get("evidence_status")
    if status is not None:
        _required_text(status, "evidence_status")
    else:
        status = "synthetic_demo" if snapshot["region"] == "synthetic_demo" else "unverified"

    if snapshot["region"] == "synthetic_demo" and status != "synthetic_demo":
        raise SnapshotValidationError("Synthetic snapshots must use synthetic_demo status")
    if status == "synthetic_demo" and any(
        known_sources[sid].get("usable_as_real_evidence") is True for sid in raw_ids
    ):
        raise SnapshotValidationError("Synthetic snapshots cannot cite real evidence as support for demo multipliers")

    enriched = deepcopy(snapshot)
    enriched["evidence_status"] = status
    enriched["source_details"] = [
        {
            "id": known_sources[sid]["id"],
            "title": known_sources[sid]["title"],
            "url": known_sources[sid].get("url"),
            "published_date": known_sources[sid].get("published_date"),
            "retrieved_date": known_sources[sid].get("retrieved_date"),
            "geography": known_sources[sid].get("geography"),
            "source_type": known_sources[sid].get("source_type"),
        }
        for sid in raw_ids
    ]
    enriched["multiplier_note"] = (
        "Skill multipliers are supplied by the data pipeline. "
        "Source citations alone do not validate a multiplier or prove skill demand is rising."
    )
    return enriched


def load_validated_snapshot(load_file: Callable[[str], object], skills: object | None = None) -> dict:
    """Read one active snapshot and verify references against the existing catalogs."""
    if skills is None:
        skills = load_file("skills.json")
    sources = load_file("sources.json")
    snapshot = load_file("trends.json")
    return validate_snapshot(snapshot, skills, sources)
