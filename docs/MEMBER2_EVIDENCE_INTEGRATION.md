# SkillShift AI — Member 2: Evidence Integration Contract

**Status:** Handoff specification only. Do not change the existing matching, scenario or trend logic until the team approves its calculation policy. Based on the processed evidence files reviewed 21 October 2026. See `docs/OECD_SCORING_METHOD.md` and `docs/ONET_SCORING_METHOD.md`.

## 1. Data file roles (no merging required)

| Path relative to repository root | Lookup | Purpose | May change recommendation numbers now? |
| --- | --- | --- | --- |
| `data/careers.json` | `career.id`, `required_skills[skill_id]` | Current approved matching inputs; 1–4 team weights | **Yes: existing source of truth** |
| `data/processed/onet_combined_skill_evidence.json` | `career_skill_evidence[]`: `career_id` + `skill_id` | Direct US O*NET skill ratings, proposed project weight, linked US tasks, and supporting explanations | **No**; read-only evidence |
| `data/processed/oecd_ai_exposure_evidence.json` | `careers[]`: `career_id` | OECD baseline exposure and +1 cognitive research scenario | **No**; display separately |
| `data/processed/dosm_major_group_signals.json` | Inspect the group's identifiers in its actual JSON before joining | Dated Malaysian *major-group* labour-market context, not career-specific AI exposure | **No**; context only |
| `data/trends.json` | Existing backend's skill multiplier keys | Existing team-level scenario/trend assumptions | Existing behavior only; **do not relabel as OECD/DOSM-derived** |

All JSON paths must be resolved relative to the project root, not the caller's current working directory. IDs beginning `role_` match `careers.json`. Do not map by display title.

## 2. OECD JSON contract — exact field names

Top-level: `dataset`, `publisher`, `source_publication_year`, `doi`, `generated_date`, `geography`, `index_scale`, `baseline_sheet`, `scenario_sheet`, `careers`.

For each item in `careers[]`:

- `career_id`: e.g. `role_accountant_auditor`; join to `data/careers.json` `id`.
- `masco_code`, `onet_code`, `occupation_mapping_status`, `occupation_mapping_note`: display/methodology context; **not** an officially verified MASCO-to-O*NET crosswalk.
- `oecd_record_status`: `matched_exact_onet_code` or `missing_exact_onet_code`.
- `oecd_occupation_title`: nullable US reference occupation title.
- `baseline_ai_exposure_index_0_to_1`: nullable float in [0,1], e.g. `0.854066`.
- `oecd_plus_one_cognitive_scenario_index_0_to_1`: nullable float in [0,1]. Hypothetical OECD *research* scenario, not SkillShift moderate/fast future scenario.
- `interpretation`: text warning; keep equivalent caveat in UI.

**Missing data:** If `oecd_record_status != 'matched_exact_onet_code'` or the baseline is `null`, show **“OECD indicator unavailable for this occupation mapping.”** Do not convert `null` to `0`, infer a low exposure, or borrow the nearest occupation value. Currently four of six exact matches; software (`15-1252.00`) and data (`15-2051.00`) are unmatched in the supplied workbook. Revisit only after a documented, justified crosswalk/source update.

**Sample safe rendering:**

- `AI capability exposure index (OECD, 2026): 0.854 / 1.000`
- `Source: OECD AI Exposure Measure; representative US occupation: Accountants and Auditors; not a Malaysia-specific AI job-loss forecast.`
- `OECD +1 cognitive capability scenario: [display separately if enabled]; hypothetical research sensitivity test, no prediction date.`

Avoid: `85.4% of accountants' jobs will be replaced`, `85% automation risk`, and arbitrary *low / medium / high* classification without approved benchmark calibration. `0.854 × 100 = 85.4 index points/100` is allowed **only** when prominently marked as an **index**, not percent of jobs.

## 3. O*NET combined JSON contract — exact field names

Top-level: `dataset_id`, `generated_at_utc`, `input_datasets`, `source_geography`, `scoring_policy`, `coverage`, `warnings`, `career_skill_evidence`.

Index `career_skill_evidence[]` by `(career_id, skill_id)`.

- `current_team_weight_1_to_4`: existing team weight.
- `recommended_backend_weight_1_to_4`: **same existing team weight** pending team approval.
- `proposed_direct_rating_weight_1_to_4`: nullable proposal; **never auto-overwrite** `careers.json`.
- `evidence_category`: currently `direct_rating_only`, `task_support`, `task_support_partial`, `team_estimate_only`.
- `direct_skill_evidence`: original importance, element ID/name, rating date, conversion, source caveat.
- `task_evidence`: status, task count and dated task descriptions/ratings. **Task importance is not a skill-importance value.**
- `explanation`: user-facing explanation starter; rephrase carefully with provenance.

Coverage in reviewed output: 36 career-skill pairs, 5 direct ratings, 24 task-linked pairs, 7 team-estimate-only pairs. All curated-career weights remain unchanged. Task-to-skill links are team-reviewed interpretations, not official crosswalks; arrange teammate review before claiming independent verification.

## 4. Safe implementation order

1. **Read-only integration:** Load two evidence datasets once (or cached), validate their shapes and ranges, join by stable IDs, and expose *optional* evidence alongside existing analysis results. For missing evidence return `null`, not a fake 0. Keep existing response schema backward compatible.
2. **UI explanation:** Show current skill weight from `careers.json`; display O*NET evidence and OECD index in separate panels, each with publication/source information and caveats. Missing results must not crash analyses.
3. **No behavior drift:** Keep existing ranking formulas, `backend/trend_snapshot.py` multipliers, `data/trends.json`, and `backend/scenarios.py` unchanged initially. Do not present research scenarios as forecasts or source-backed adjustment factors.
4. **Tests:** Ensure all existing backend tests pass; add tests for all six IDs, 4 matched/2 unmatched OECD, null-handling, exact join, preserved ranking results, malformed index rejection, and response-schema compatibility.
5. **Only if team approves score adoption:** Write an explicit, versioned weight-change proposal comparing each old weight, proposed weight, source, affected career and expected ranking changes; review, then change `careers.json` or introduce an explicit gated override—not both. Re-run snapshot tests and record decision in docs. OECD indices must not become raw rank multipliers without a separately validated and approved model.

## 5. Minimal acceptance checks

- [ ] All six curated `career_id`s join to `careers.json`; synthetic demo careers are handled as `evidence_unavailable`.
- [ ] All 36 O*NET career–skill combinations join; no duplicate key accepted.
- [ ] OECD four exact matches render index values; two missing records render unavailable.
- [ ] AI exposure is **never** labelled job-loss probability; task IM is **never** labelled a direct skill IM.
- [ ] Scenario labels distinguish OECD +1 cognitive sensitivity vs SkillShift moderate/fast assumptions.
- [ ] Existing matching/rankings do not change, and regression tests pass.
- [ ] Display cites: OECD (2026), DOI `10.1787/f3da0f0a-en`; O*NET records' original rating dates vary by occupation.

## 6. Dataset update vs live updates

The OECD processor reads a **local workbook**, and the O*NET scripts read **local extracts**. Neither is a live API or automatically refreshing feed. The generated date is the date the pipeline ran, not the OECD/O*NET measurement date. Updating the workbook requires checking source changes, rerunning the relevant scripts, and retesting. These evidence sources do **not** themselves meet a requirement for an automatically refreshed, recommendation-changing live trend feed.

## 7. Source and attribution

OECD (2026), *The OECD AI Exposure Measure: Mapping the OECD AI Capability Indicators to Occupations*, OECD Artificial Intelligence Papers, No. 59. https://doi.org/10.1787/f3da0f0a-en. The provided workbook's README marks the dataset **CC BY 4.0**; retain attribution, source identification and a link to licence https://creativecommons.org/licenses/by/4.0/. The OECD index is an AI-capability gap indicator of US-referenced occupations, not a statement about Malaysian employment outcomes.


## 8. Simple handoff summary for Member 2 (start here)

**What is happening?** Member 4 has prepared evidence from O*NET, OECD and DOSM. **You have to let the backend retrieve and display the right evidence for each career, while keeping the current matching system working.** Think of this as adding explanations to existing career recommendations—not replacing the scoring engine.

| File to read | In simple terms | What to fetch / match | What the user should see | What NOT to do |
| --- | --- | --- | --- | --- |
| `data/careers.json` | Our main career and skill data | Find the career by `id`; get `required_skills` | Existing career recommendation and skill weights (1–4) | Don't change the weights without team approval |
| `data/processed/onet_combined_skill_evidence.json` | **Why a skill matters** | Match `career_skill_evidence[]` using **both** `career_id` and `skill_id` | Supporting O*NET skill rating **or** related occupation tasks, plus evidence date | Don't treat task ratings as official skill scores; don't automatically apply proposed weights |
| `data/processed/oecd_ai_exposure_evidence.json` | **How an occupation overlaps with measured AI capabilities** | Match `careers[]` using `career_id`; read `baseline_ai_exposure_index_0_to_1` | OECD exposure **index** (e.g. `0.854 / 1.000`) or “Unavailable” | Don't call it an AI replacement percentage; `null` is not `0` |
| `data/processed/dosm_major_group_signals.json` | **What broad Malaysian job-group data shows** | Read the occupational **major-group** record and its dated comparison; check whether a reliable group match is available | Broad labour-market context, with quarter and source | Don't claim it describes a specific career or skill trend; don't use it to alter ranking automatically |
| `data/trends.json` | Current **team-defined** trend assumptions | Keep the existing backend loading logic | Current trend/scenario behavior, clearly described as assumptions | Don't describe its multipliers as measured OECD or DOSM data |

### Recommended order (simple)

1. **Keep existing recommendations working:** Continue using `careers.json` and the current matching calculations.
2. **Add an optional evidence lookup:** When a career is recommended, use its exact `career_id` to look up OECD data. For each listed skill, use `(career_id, skill_id)` to look up O*NET evidence.
3. **Display the evidence separately:** Show O*NET skill/task explanations and the OECD exposure index with original source dates. Show DOSM information only as **major-group context** where the grouping is justified.
4. **Handle missing values safely:** Two of six careers currently have no exact OECD match; display **“Unavailable”**. Synthetic demo careers may also have no research evidence. Do not crash or substitute made-up values.
5. **Test before merging:** All six curated careers load; all 36 O*NET entries are reachable; 4 OECD values and 2 unavailable statuses display correctly; **existing career rankings remain identical**; backend tests pass.

**Example:** If the recommended career is `role_data_professional` and a skill is `skill_data_cleaning`, keep the weight from `careers.json`; fetch the related O*NET task explanation from the combined file. The OECD indicator for this career is currently **unavailable** in the supplied workbook, so show that clearly rather than assigning a risk score.

**Bottom line for Member 2:** **`careers.json` decides current scores; O*NET explains skills; OECD describes AI-capability exposure; DOSM provides dated broad Malaysian market context.** These files can be loaded separately—there is **no need to merge all the JSON files or rewrite the scoring logic** for the first integration.

## 9. Important unfinished work — live/updatable trend integration (Member 2 + Member 4)

**Please do not mark the trend requirement complete yet.** Member 4 has prepared a dated DOSM source and an importer, but the current backend still uses **team-defined skill multipliers** in `data/trends.json`. The real DOSM observations do not yet drive career recommendations. We must finish this together and demonstrate a change when genuinely updated source data is supplied.

| Component | Current state | Who / what happens next |
| --- | --- | --- |
| `data/jmi_major_occupation_2025_2026.csv` | Historical DOSM quarterly data, currently through 2026-Q2 | **Member 4:** maintain accurate dated source data; add newly released quarterly records when available |
| `data_pipeline/import_trends.py` | Processes quarterly observations into comparative major-group signals; can select a new latest quarter if that quarter is added to its input | **Member 4:** rerun importer after source update; validate period and source provenance |
| `data/processed/dosm_major_group_signals.json` | Real, dated major-occupational-group comparison (e.g. Professionals group); **not career-level skill-demand or AI exposure** | **Member 2:** optionally display as an evidence panel, with actual period and limitation |
| `data/trends.json` and `backend/trend_snapshot.py` | Existing skill multipliers are team-defined assumptions; the backend consumes these | **Member 2:** preserve existing behavior until a reviewed, valid trend-to-skill/career mapping is approved |
| Actual dated market trend changes recommendation | **Not yet implemented / validated** | **Team:** choose a defensible career- or skill-relevant updatable market source, document the conversion/mapping and capped effect, implement behind tests, and compare recommendation results before/after a real source update |
| Automatic source retrieval | **Not yet implemented** | **Team:** if required for the demo, implement a documented update/refresh mechanism; adding a row manually and rerunning a script is an updateable local pipeline, **not automatic fetching** |

### Simple division of responsibilities

1. **Member 4 (data):** Provide dated, accurately sourced observations; document whether a figure is at *major-group*, *career* or *skill* level; ensure importer handles a newly published period; propose only defensible joins and formulas.
2. **Member 2 (backend):** After team approval, read a validated updatable trend snapshot and use it in the recommendation/scoring path **only if** that data genuinely supports the affected career/skill. Keep current behavior as fallback until testing passes.
3. **Together:** Verify an actual source update changes the recorded trend, and visibly changes at least one appropriate recommendation or its ordering/priority for a justified reason. Log the source, observation date, update time, calculation and before/after result. Do **not** use synthetic quarter data as proof of a real updated labour-market trend.

**Current limitation:** DOSM's broad *Professionals* category cannot justify a direct Python-demand multiplier, or a trend specific to Nursing, Software Development or any other particular career. A read-only DOSM evidence endpoint is useful, but **does not itself satisfy the dynamic recommendation requirement**. If we cannot find a reliable direct signal within the hackathon timeline, label the demonstration calculation as **assumption-based**, and do not present it as observed market demand.

**Quick reminder:** `careers.json` = current career scores; **O*NET** = skill/task evidence; **OECD** = AI capability exposure; **DOSM** = dated broad market context; `trends.json` = **existing synthetic/assumption-based trend multipliers**. The unfinished bridge is **real updatable trend evidence → valid career/skill adjustment → tested recommendation change**.

## 10. Final notes for Member 2 (quick reference)

**Optional cleanup — three demo careers:** `data/careers.json` still contains `role_data_analyst`, `role_security_analyst`, and `role_cloud_engineer` marked `synthetic_demo`. **If your backend no longer uses these demo careers, you may remove them** after checking related references (such as demo profiles, tests, UI and API routes) and rerunning validation/tests. If anything still depends on them, keep them until those references are updated. The new O*NET/OECD evidence is for the **six curated careers**, not these three demo entries.

**Final quick reference:** Use the **dataset table in Section 8** to see *which JSON file to fetch and why*, then follow **Section 8's five-step integration flow**: keep existing recommendations → look up O*NET/OECD evidence by IDs → display dated explanations → handle missing values → test. **Section 9** explains the unfinished real-trend-to-recommendation work; this still needs team collaboration.
