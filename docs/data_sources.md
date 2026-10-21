# Malaysian evidence â€” Member 4

Suggested starting points:
- TalentCorp Malaysia Critical Occupations List (MyCOL): https://www.talentcorp.com.my/
- Department of Statistics Malaysia: https://open.dosm.gov.my/
- OpenDOSM catalogue: https://open.dosm.gov.my/data-catalogue
- MASCO occupational classification: official Malaysian government references

Record source title, URL, report period, access/retrieval date, specific page/table, geography, license and exact skill or trend claim. A periodic report can be imported, but it is **not** a live feed. A single listing snapshot is not evidence of an increasing trend.

`data/*.json` CURRENTLY CONTAINS SYNTHETIC DEMO CONTENT â€” NOT MALAYSIAN LABOR STATISTICS. Replace with verified data before final submission. The live data pipeline must produce real, dated update signals.

---------------------------------------------------------------------------------------
# Malaysian Evidence and Data Sources — Member 4

**Project:** SkillShift AI  
**Review date:** 21 October 2026  
**Status:** Six Malaysian career profiles and supporting O*NET/OECD evidence pipelines prepared. Career matching still uses the existing team-assigned weights; evidence integrations and a recommendation-changing real trend signal need backend/team work.

## 1. Dataset overview

SkillShift AI combines Malaysian occupational references, international occupational evidence, dated Malaysian job-market observations, selected learning resources, and team-defined career matching weights. **A source-supported skill does not mean its 1–4 importance weight was measured by the source.**

| Career ID | Malaysian occupation | MASCO | Evidence status |
|---|---|---|---|
| `role_software_developer` | Software Developer | 2512 | Curated with assumptions |
| `role_accountant_auditor` | Accountants and Auditors | 2411 | Curated with assumptions |
| `role_data_professional` | Data Professionals | 2524 | Curated with assumptions |
| `role_marketing_professional` | Advertising and Marketing Professionals | 2431 | Curated with assumptions |
| `role_electrical_engineer` | Electrical Engineers | 2151 | Curated with assumptions |
| `role_nursing_professional` | Nursing Professionals | 2221 | Curated with assumptions |

`data/careers.json` also contains three **synthetic demo careers**: `role_data_analyst`, `role_security_analyst`, `role_cloud_engineer`. These are not verified Malaysian occupational evidence. Member 2/team leader may remove them **only after checking frontend, backend and test dependencies**.

The current source registry, `data/sources.json`, contains **21 source entries**, including newly added O*NET and OECD entries. `data/learning_resources.json` contains **39 skill-linked learning resource records** in the last reviewed file. These counts are from the supplied project files, not proof that every external URL is currently reachable.

## 2. Source register and scope

| Source ID / publisher | Relevant use | Important limitation |
|---|---|---|
| `src_mycol_2024` — TalentCorp MyCOL 2024/2025 | Critical-occupation evidence for specific Malaysian job titles | Critical-occupation status is not an AI risk score or job-growth forecast |
| `src_masco_2020`, `src_masco_accountants_2020`, `src_masco_data_2020` | Official MASCO classifications | No numeric skill importance or AI exposure |
| `src_emasco_data_2524`, `src_emasco_data_analyst_skills_2524` | Data occupation duties and Data Analyst-specific skills | Data Analyst specialization does not represent every Data Professional |
| `src_emasco_marketing_2431`, `src_emasco_marketing_exec_2431_02` | Marketing occupation and specialization duties/skills | Marketing Executive is a representative specialization |
| `src_emasco_electrical_2151` | Electrical engineering duties | No quantitative weights; specializations vary |
| `src_emasco_nursing_2221`, `src_emasco_professional_nurse_2221_01` | Nursing duties and professional nurse skills | Scope of practice, training and registration requirements apply |
| `src_ict_2024`, `src_gbs_2024`, `src_ee_2024` — TalentCorp | Selected role skills and sector AI context | Cannot generalize selected role classifications to an entire MASCO group |
| `src_dosm_jmi_q2_2026` — DOSM | Q2 2026 Malaysian job offering observations and major-group data | Job offerings are not skill-level demand or a job-loss forecast |
| `src_esco_121` — European Commission | International occupation/skill taxonomy | Not Malaysian employer demand |
| `src_onet_31_0` — USDOL/ETA O*NET | US occupational skills importance and task evidence | Representative US occupations, not an official MASCO crosswalk |
| `src_oecd_ai_exposure_2026` — OECD | Occupational AI capability exposure and a research sensitivity scenario | Not job-replacement probability or Malaysian adoption |
| `src_ilo_genai_exposure_2025` — ILO | Supporting methodology on task-level GenAI exposure | Not SkillShift's numerical career score |
| `src_retail_2024` — TalentCorp | Optional background sector research | No current direct supported claim in the registry |
| `src_demo` | Synthetic test data provenance | Must never be presented as real occupational evidence |

The **complete source-specific URLs, evidence locations, claim IDs, retrieval dates, licensing status and reuse conditions** live in `data/sources.json`. Avoid maintaining a second competing claim registry in this Markdown file.

### Direct primary references

- **O*NET 31.0:** https://www.onetcenter.org/database.html ; database licence: https://www.onetcenter.org/license_db.html . O*NET database information attributed to USDOL/ETA, under CC BY 4.0; our MASCO crosswalk and weight conversions are adaptations, not endorsed by USDOL/ETA.
- **OECD AI exposure research:** https://doi.org/10.1787/f3da0f0a-en . The supplied workbook's README describes CC BY 4.0; cite OECD (2026) and identify extraction/display adaptations.
- **DOSM Q2 2026:** https://www.dosm.gov.my/portal-main/release-content/big-data-analytics-job-market-insights-q22026 .
- **MASCO/eMASCO:** https://emasco.mohr.gov.my/ .
- **MyCOL and workforce studies:** refer to the exact TalentCorp PDFs in `data/sources.json`; reuse rights for several original reports remain **not verified**.
- **ESCO:** https://esco.ec.europa.eu/en/use-esco/download ; acknowledge the European Commission and indicate adaptations.

## 3. Six curated careers: skills and claims

All skills below are represented by stable `skill_id` keys and 1–4 team-selected weights in `data/careers.json`. Supporting occupation evidence does **not** establish those exact numbers.

| Career | Selected skills, with current team weights | Primary justification and caveat |
|---|---|---|
| Software Developer | Software Configuration **3**; Design **4**; Testing **3**; AI Fluency **2**; Critical Thinking **2**; Innovative Thinking **2** | TalentCorp ICT Software Engineer profile and MASCO 2512. TalentCorp's low AI-impact classification applies to its named Software Engineer role, not a universal guarantee for all developers. |
| Accountants and Auditors | Financial Analysis & Reporting **4**; Accounting Principles **4**; Attention to Detail **3**; Ethical Judgement **3**; Cost-Benefit Analysis **2**; Innovative Thinking **2** | TalentCorp GBS finance/accounting cluster and MASCO 2411. Named medium-impact subroles cannot establish a grade for the full occupation; `ai_impact` remains `null`. |
| Data Professionals | Data Analysis **4**; Data Cleaning **4**; Python **3**; SQL **3**; Data Visualization **3**; Critical Thinking **2** | MASCO 2524 group duties plus specific eMASCO Data Analyst (2524-02) skills. The broader group includes other specialties. |
| Advertising and Marketing Professionals | Marketing Strategy **4**; Digital Marketing **4**; Market Research **3**; Campaign Performance **3**; Marketing Communication **3**; Critical Thinking **2** | eMASCO 2431 and Marketing Executive (2431-02), a narrower representative role. |
| Electrical Engineers | Electrical System Design **4**; Electrical Circuits **4**; Electrical Safety **3**; Fault Diagnosis **3**; Electrical Simulation **2**; Critical Thinking **2** | eMASCO 2151 duties. Simulation is a team-selected learning extension, not an explicitly mandatory group-level skill. |
| Nursing Professionals | Patient Care & Monitoring **4**; Nursing Assessment & Care Planning **4**; Medication Safety **3**; Infection Prevention **3**; Patient Communication **3**; Critical Thinking **2** | eMASCO 2221 and Professional Nurse (2221-01). Learning resources do not authorize clinical practice or replace professional registration. |

All career SDG tags are project interpretations rather than verified impacts. No occupation-wide AI job-replacement percentage is claimed.

## 4. O*NET occupational mapping and skill evidence

`data/onet_career_mapping.json` records these **reviewed representative** MASCO-to-O*NET mappings; `mapping_status: verified` in the processing file indicates the project's internal mapping review and is **not an official occupational crosswalk**.

| Malaysian career | O*NET-SOC | Representative US occupation | Fit |
|---|---|---|---|
| Software Developer | `15-1252.00` | Software Developers | Representative |
| Accountants and Auditors | `13-2011.00` | Accountants and Auditors | Representative |
| Data Professionals | `15-2051.00` | Data Scientists | **Partial**: broader Malaysian data grouping |
| Advertising and Marketing Professionals | `13-1161.00` | Market Research Analysts and Marketing Specialists | Good, but narrower than all advertising work |
| Electrical Engineers | `17-2071.00` | Electrical Engineers | Strong, local regulations may differ |
| Nursing Professionals | `29-1141.00` | Registered Nurses | Strong, legal practice scopes may differ |

**Reproducible processing:**

1. `data_pipeline/clean_onet.py` reads the locally held O*NET workbooks and generates `data/processed/onet_occupation_skills.csv` and `onet_occupation_tasks.csv`.
2. `data_pipeline/build_onet_skill_importance.py` produces `onet_skill_importance_evidence.json` from **unsuppressed, directly matched Skills IM** ratings only. O*NET LV is a different scale.
3. `data_pipeline/build_onet_task_evidence.py` produces `onet_task_skill_evidence.json` with manually selected relevant O*NET task IDs and ratings. **Task importance is not a numerical skill-importance score.**
4. `data_pipeline/build_onet_combined_evidence.py` combines both into `data/processed/onet_combined_skill_evidence.json`, the main **read-only explanation dataset** for Member 2.

Latest combined evidence: **36 curated career–skill pairs**, **5 direct general-skill ratings**, **24 task-linked pairs** (17 stronger task supports; 7 partial), and **7 team-estimate-only pairs**. The direct O*NET proposal uses a *project-defined* conversion `min(4, floor(IM))` on eligible importance ratings (1–5); this is **not O*NET's own 1–4 scale**. `careers.json` weights have **not** been changed. Different O*NET occupations have different original measurement dates; retain per-record dates. Task-to-skill interpretations still require teammate review.

**Method document:** `docs/ONET_SCORING_METHOD.md`.

## 5. OECD AI capability exposure

**Input:** `data/external/oecd/OECD AI Capability Gap Index_public data.xlsx` (workbook location expected by the processor). `data_pipeline/build_oecd_ai_exposure.py` writes `data/processed/oecd_ai_exposure_evidence.json`.

The workbook contains the reversed normalized **AI Capability Gap Index**. Higher values indicate **greater measured overlap between occupational requirements and AI capabilities** under the OECD research method. These are **indices, not percentages of job loss, predicted unemployment, or Malaysia-specific adoption rates**.

| Career | OECD baseline index (0–1) | Match status |
|---|---:|---|
| Accountants and Auditors | 0.854066 | Exact mapped O*NET code |
| Advertising and Marketing Professionals | 0.856771 | Exact mapped O*NET code |
| Electrical Engineers | 0.8430 (rounded) | Exact mapped O*NET code |
| Nursing Professionals | 0.6638 (rounded) | Exact mapped O*NET code |
| Software Developer | `null` | Exact code missing from supplied workbook |
| Data Professionals | `null` | Exact code missing from supplied workbook |

**Display:** “OECD AI capability exposure index: 0.854 / 1.000”, with source and caveat. A missing value displays as **unavailable**, never zero or low exposure. Do not invent thresholds labelled *high replacement risk*. The workbook's **+1 cognitive capability** case is a hypothetical OECD research scenario, **not** the application's moderate/fast AI adoption prediction. Do not substitute another occupation to fill the missing codes without a documented, justified crosswalk.

**Method document:** `docs/OECD_SCORING_METHOD.md`.

## 6. DOSM job-market evidence and unfinished trend integration

| Evidence | Observed scope | Permitted claim |
|---|---|---|
| Q2 2026 occupation snapshot | Software Developers: **19,899** online job offerings; Accountants and Auditors: **22,067** | DOSM-reported quarterly observations only |
| `data/jmi_major_occupation_2025_2026.csv` | Malaysian **major occupational groups**, multiple quarters | Comparisons for broad groups, not individual careers or skills |
| `data/processed/dosm_major_group_signals.json` | Latest/previous quarters, generated by `data_pipeline/import_trends.py` | Updatable **when the underlying CSV is updated and importer reruns**; no automatic download |
| `data/trends.json` | Existing **team-defined synthetic skill multipliers** | App integration assumptions, not measured DOSM trends |

The importer processes the latest available valid periods and has a refresh test (`data_pipeline/test_import_trends_refresh.py`). **It does not autonomously fetch new quarterly releases.** Broad Professionals-group changes must not be described as Software Developer- or Data Professional-specific trends, and cannot directly support a particular skill's multiplier.

**Domain 1 remaining gap:** Evidence display alone is not a genuinely updated signal **changing recommendations**. The team still needs an approved, defensible link between an updatable dated market/AI signal and the relevant career/skill recommendation, plus a test showing that changing valid source observations changes the recommendation. Coordinate this with Member 2; do not relabel existing synthetic multipliers as real DOSM-derived calculations.

## 7. Learning resources and SDGs

- `data/learning_resources.json` contains **39 resources** in the reviewed dataset, linked to stable skill IDs. Foundational and AI-adaptation offerings are distinct; many cover only part of a skill.
- Use verified provider/course pages, account for country-specific learning applicability and possible paid certificates, and represent unknown course lengths with `estimated_hours: null`, **not zero hours**.
- Personalized pathways and estimated hours still depend on backend sequencing, skill-gap selection and appropriate frontend rendering.
- Career/skill SDG mappings are in `data/careers.json` and `data/skills.json`; titles and general explanations live in `data/sdg_mapping.json`. SDGs are **team-defined relevance claims**, not measured impact.
- **Pending check:** Nursing references **SDG 3**; verify `data/sdg_mapping.json` defines SDG 3 before shipping. Also review other career and skill SDG references, duplicated entries and unused scripts after the handoff.

## 8. Files, ownership, reproducibility and tests

| File(s) | Purpose | Owner / next action |
|---|---|---|
| `data/sources.json` | Canonical source registry and claim metadata (**21 records**) | Member 4 maintains; avoid duplicate source IDs |
| `data/careers.json`, `data/skills.json`, `data/learning_resources.json` | Existing career profiles, IDs, estimated weights and learning references | Member 4 data QA; matching changes require team approval |
| `data/processed/onet_combined_skill_evidence.json` | Read-only O*NET skill and task explanations | Member 2 joins by `career_id` + `skill_id` |
| `data/processed/oecd_ai_exposure_evidence.json` | OECD baseline and hypothetical research scenario | Member 2 joins `careers[].career_id`; handle `null` |
| `data/processed/dosm_major_group_signals.json` | Broad DOSM dated observations | Member 2 displays as context; trend-to-matching work remains open |
| `data/trends.json` | Existing team-assumption multipliers | Keep labelled synthetic until a separately validated model replaces them |
| `docs/ONET_SCORING_METHOD.md`, `docs/OECD_SCORING_METHOD.md` | Evidence calculation and caveat documents | Cite in implementation/demo |
| `docs/MEMBER2_EVIDENCE_INTEGRATION.md` | **Exact JSON fields and handoff instructions** | Member 2's main integration guide |

Run from the repository root after placing the updated source registry and documentation:

```powershell
python data_pipeline/validate_sources.py
python data_pipeline/validate_careers.py
python -m pytest -q
```

For complete reproduction of the three evidence outputs (with required input files installed locally):

```powershell
python data_pipeline/build_onet_skill_importance.py
python data_pipeline/build_onet_task_evidence.py
python data_pipeline/build_onet_combined_evidence.py
python data_pipeline/build_oecd_ai_exposure.py
```

**Validation scope:** Passing tests checks the rules they implement; it does not prove every external course URL, task crosswalk, licence, future trend signal or user interface is correct. Preserve evidence dates and licensing. Do not commit unreviewed third-party `data/external/` workbooks by using `git add .`.

## 9. Handoff and pending tasks

**Ready for Member 2:** six curated Malaysian career records; O*NET skill/task explanations; OECD occupational exposure for four exact matches with two `null`; dated DOSM broad-group evidence; source citations and scoring cautions. **Do not silently replace current 1–4 career weights or moderate/fast scenario values.**

**Pending after sharing the branch:** real updatable trend → recommendation effect; frontend/backend joining and testing; missing SDG 3; script overlap/unused-code review; confirming demo-career dependencies and optional removal; source permissions/URL checks; full demo validation.

**Quick Member 2 reference:** `docs/MEMBER2_EVIDENCE_INTEGRATION.md` — use its dataset lookup table, simple integration flow and unfinished DOSM trend section. When the team agrees on a revised scoring formula, update the source-of-truth inputs and run tests before deploying.

**Attribution:** This project uses information from the O*NET database by USDOL/ETA, and the ESCO classification of the European Commission. OECD research is cited in `src_oecd_ai_exposure_2026`; project-specific mappings and derived displays are adaptations. Consult each source's full attribution and licence terms in `data/sources.json`.
