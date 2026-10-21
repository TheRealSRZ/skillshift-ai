"""Build traceable OECD AI-exposure evidence for SkillShift AI.

Usage: python data_pipeline/build_oecd_ai_exposure.py
Dependencies: Python standard library only.
Does NOT modify careers.json, trends.json, or backend weights.
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "data/external/oecd/OECD AI Capability Gap Index_public data.xlsx"
MAPPING = ROOT / "data/onet_career_mapping.json"
OUT = ROOT / "data/processed/oecd_ai_exposure_evidence.json"
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
      "p": "http://schemas.openxmlformats.org/package/2006/relationships"}


def read_sheet(z: ZipFile, name: str, shared: list[str]) -> list[list[object]]:
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    relationships = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    paths = {rel.get("Id"): rel.get("Target") for rel in relationships}
    sheet_entry = next((s for s in wb.findall("s:sheets/s:sheet", NS) if s.get("name") == name), None)
    if sheet_entry is None:
        raise ValueError(f"Missing workbook sheet: {name}")
    rid = sheet_entry.get("{" + NS["r"] + "}id")
    target = paths[rid].lstrip("/")
    path = target if target.startswith("xl/") else "xl/" + target
    root = ET.fromstring(z.read(path))
    rows: list[list[object]] = []
    for r in root.findall("s:sheetData/s:row", NS):
        result: list[object] = []
        for c in r.findall("s:c", NS):
            ref = c.get("r", "A1")
            letters = re.match(r"[A-Z]+", ref).group()
            index = 0
            for letter in letters:
                index = index * 26 + ord(letter) - ord("A") + 1
            index -= 1
            while len(result) <= index:
                result.append(None)
            v = c.find("s:v", NS)
            inline = c.find("s:is/s:t", NS)
            if inline is not None:
                value: object = inline.text or ""
            elif v is None or v.text is None:
                value = None
            elif c.get("t") == "s":
                value = shared[int(v.text)]
            elif c.get("t") in {"str", "e"}:
                value = v.text
            else:
                value = float(v.text)
            result[index] = value
        rows.append(result)
    return rows


def read_oecd(path: Path) -> dict[str, dict[str, tuple[str, float]]]:
    with ZipFile(path) as z:
        strings: list[str] = []
        if "xl/sharedStrings.xml" in z.namelist():
            shared_root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in shared_root.findall("s:si", NS):
                strings.append("".join(t.text or "" for t in si.findall(".//s:t", NS)))
        data: dict[str, dict[str, tuple[str, float]]] = {}
        for sheet in ("Data", "Scenario"):
            rows = read_sheet(z, sheet, strings)
            if len(rows) < 5 or str(rows[2][0]) != "OCC_Code":
                raise ValueError(f"Unexpected OECD {sheet} sheet header")
            found: dict[str, tuple[str, float]] = {}
            for row in rows[4:]:
                if len(row) <= 2 or not isinstance(row[0], str) or not isinstance(row[2], (int, float)):
                    continue
                code, title, score = row[0], str(row[1]), float(row[2])
                if not (0 <= score <= 1):
                    raise ValueError(f"Exposure outside 0-1 in {sheet}: {code}")
                if code in found:
                    raise ValueError(f"Duplicate OECD occupation in {sheet}: {code}")
                found[code] = (title, score)
            data[sheet] = found
        return data


def build() -> dict:
    if not WORKBOOK.is_file():
        raise FileNotFoundError(f"OECD workbook not found: {WORKBOOK}")
    mappings = json.loads(MAPPING.read_text(encoding="utf-8"))
    if not isinstance(mappings, list):
        raise ValueError("Expected mapping JSON to be a list")
    oecd = read_oecd(WORKBOOK)
    results: list[dict] = []
    for m in mappings:
        code = m.get("onet_code")
        if not code or m.get("mapping_status") != "verified":
            continue
        baseline, scenario = oecd["Data"].get(code), oecd["Scenario"].get(code)
        entry = {
            "career_id": "role_" + str(m["career_id"]).removeprefix("role_"),
            "masco_code": m.get("masco_code"),
            "onet_code": code,
            "occupation_mapping_status": m.get("mapping_status"),
            "occupation_mapping_note": m.get("mapping_note", ""),
            "oecd_record_status": "matched_exact_onet_code" if baseline and scenario else "missing_exact_onet_code",
            "oecd_occupation_title": baseline[0] if baseline else None,
            "baseline_ai_exposure_index_0_to_1": round(baseline[1], 6) if baseline else None,
            "oecd_plus_one_cognitive_scenario_index_0_to_1": round(scenario[1], 6) if scenario else None,
            "interpretation": "Higher index indicates higher measured AI capability overlap; NOT predicted replacement probability.",
        }
        if baseline and scenario and baseline[0] != scenario[0]:
            raise ValueError(f"Occupation title mismatch across OECD sheets: {code}")
        results.append(entry)
    output = {
        "dataset": "OECD AI Capability Gap Index",
        "publisher": "OECD",
        "source_publication_year": 2026,
        "doi": "10.1787/f3da0f0a-en",
        "input_file": "data/external/oecd/OECD AI Capability Gap Index_public data.xlsx",
        "mapping_file": "data/onet_career_mapping.json",
        "generated_date": date.today().isoformat(),
        "geography": "O*NET-SOC occupations (US classification), not Malaysian labour-market observations",
        "baseline_sheet": "Data",
        "scenario_sheet": "Scenario (+1 cognitive capability; OECD-defined, NOT SkillShift moderate/fast scenario)",
        "index_scale": "0-1 (higher indicates greater AI exposure)",
        "not_job_loss_probability": True,
        "can_directly_replace_malaysian_occupation_ratings": False,
        "can_directly_adjust_matching_scores": False,
        "mapping_policy": "Use exact O*NET code only; unmatched occupations remain null, never substitute loosely similar titles.",
        "careers": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    matched = sum(x["oecd_record_status"] == "matched_exact_onet_code" for x in results)
    print(f"PASS: OECD baseline and research scenario processed for {matched}/{len(results)} careers -> {OUT}")
    for x in results:
        print(f"  {x['career_id']}: {x['oecd_record_status']}; baseline={x['baseline_ai_exposure_index_0_to_1']}")
    print("NOTE: AI exposure is not job-replacement probability or a validated Malaysian career prediction.")
    return output


if __name__ == "__main__":
    build()
