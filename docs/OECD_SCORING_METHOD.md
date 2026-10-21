# SkillShift AI — OECD AI Exposure Evidence Methodology

## Purpose
Provide a transparent, independently generated occupation-level AI capability exposure indicator for six SkillShift curated careers. This is **not** a job replacement forecast, a Malaysian labor-market statistic, or a measure of an individual user's employability.

## Source and reuse
OECD (2026), *The OECD AI Exposure Measure: Mapping the OECD AI Capability Indicators to Occupations*, OECD Artificial Intelligence Papers No. 59. DOI: https://doi.org/10.1787/f3da0f0a-en . The uploaded workbook identifies a CC BY 4.0 licence: retain appropriate attribution when reusing the data. Workbook sheets: `README`, `Data`, `Scenario`, `Codebook`.

## Inputs and output
- `data/external/oecd/OECD AI Capability Gap Index_public data.xlsx`: unmodified source workbook.
- `data/onet_career_mapping.json`: project-reviewed representative MASCO-to-O*NET mappings; not an official occupational crosswalk.
- `data_pipeline/build_oecd_ai_exposure.py`: reproducible standard-library processor.
- `data/processed/oecd_ai_exposure_evidence.json`: backend-readable output.

Run from the repository root: `python data_pipeline/build_oecd_ai_exposure.py`.

## Measure and interpretation
Workbook `Data` column `AI Capability Gap Index (Reversed, norm.)` is a normalized **0–1** reversed capability gap. The workbook's `Codebook` states the calculation as `1 - (AI Capability Gap Index Total / 23)`. Higher reversed index = comparatively greater overlap between currently measured AI capabilities and occupational requirements. This is **not** a percentage of work automatable, a probability of unemployment, a predicted percentage of jobs lost, or a validated Malaysia-specific score. The source uses US O*NET occupations.

When displaying the indicator, show the original index, e.g. `0.854 / 1.000` or `85.4 / 100 (index points)` with the explicit label `AI capability exposure index — not job replacement %`. Multiplication by 100 for display does not change the meaning. Do **not** infer categories (`low`, `medium`, `high`) or career rankings as official OECD classifications; any such cutoffs require their own separately documented methodology.

## OECD research scenario
Workbook `Scenario` changes *six cognitive AI capability domains* by +1 level: Language, Social Interaction, Problem Solving, Creativity, Metacognition, and Knowledge/Learning/Memory. This is a hypothetical **research sensitivity scenario**; it does not specify when such capabilities will materialize. It is NOT SkillShift's `moderate` vs `fast` disruption scenario. Keep it labelled distinctly and never present the difference as a forecast over time.

## Joining policy
Use only exact O*NET-SOC code matches from `data/onet_career_mapping.json`. A matched US occupational code remains a representative proxy for the Malaysian MASCO group, *not* official equivalence. In the supplied workbook, exact code matches exist for: `13-2011.00`, `13-1161.00`, `17-2071.00`, `29-1141.00`. They do not exist for `15-1252.00` and `15-2051.00`; leave both baseline and scenario indexes `null`, retain `missing_exact_onet_code`, and do not infer zero exposure.

## Backend integration contract
- Read `careers[]`, joined by `career_id` (e.g. `role_accountant_auditor`).
- Display `baseline_ai_exposure_index_0_to_1` with source attribution and `oecd_record_status`.
- `oecd_plus_one_cognitive_scenario_index_0_to_1` is optional; label it explicitly as *OECD +1 cognitive capability research scenario*.
- If baseline is `null`, display `Not available from this OECD source` instead of `0`.
- Do not overwrite `careers.json`, `trends.json`, SkillShift's 1–4 skill importance weights, matching scores, or SkillShift moderate/fast scenario assumptions from these fields without an approved, documented integration design.
- Record the fact that the processor was run separately from the original publication date; regenerating the JSON does not mean OECD released new observations.

## Verification
1. Run the processor from the project root.
2. Confirm six entries, four exact code matches, and two explicit nulls.
3. Check source licence/attribution and review the representative occupation-mapping limitations.
4. Run `python data_pipeline/validate_careers.py` and `python -m pytest -q` to confirm no regression.

## Final adoption decision for the hackathon (21 October 2026)
The documented default is **read-only evidence integration**. Preserve all existing SkillShift career weights, recommendation ranking formulas, `trends.json` multipliers and moderate/fast scenarios. Show OECD baseline as a separate descriptive **index out of 1.000**, preserve `null`, and label the +1 cognitive scenario as hypothetical. No unvalidated risk thresholds are adopted. A future scored-model integration requires explicit team approval and regression tests.

## Machine-readable contract
The actual JSON has a top-level `careers` array, not `career_exposure`. Join `careers[].career_id` with `careers.json[].id`. Display `baseline_ai_exposure_index_0_to_1` only when `oecd_record_status == "matched_exact_onet_code"`. A missing value is `null`, not zero. Read `source_publication_year`, `doi`, `publisher`, `geography` from the root, and `occupation_mapping_note` for the US-to-Malaysia proxy limitation. See `MEMBER2_EVIDENCE_INTEGRATION.md` for a full integration specification.

## Coverage and current values (verified against the uploaded workbook's processed output)

| Career ID | O*NET occupation | Baseline normalized index | Status |
| --- | --- | ---: | --- |
| `role_software_developer` | 15-1252.00 | `null` | missing exact O*NET code |
| `role_data_professional` | 15-2051.00 | `null` | missing exact O*NET code |
| `role_accountant_auditor` | 13-2011.00 | 0.854066 | matched |
| `role_marketing_professional` | 13-1161.00 | 0.856771 | matched |
| `role_electrical_engineer` | 17-2071.00 | 0.843004 | matched |
| `role_nursing_professional` | 29-1141.00 | 0.663774 | matched |

The values are neither percentages of tasks replaced nor job-loss predictions. Cross-occupation comparison is research context, not validated Malaysian career advice.
