# Malaysian evidence â€” Member 4

Suggested starting points:
- TalentCorp Malaysia Critical Occupations List (MyCOL): https://www.talentcorp.com.my/
- Department of Statistics Malaysia: https://open.dosm.gov.my/
- OpenDOSM catalogue: https://open.dosm.gov.my/data-catalogue
- MASCO occupational classification: official Malaysian government references

Record source title, URL, report period, access/retrieval date, specific page/table, geography, license and exact skill or trend claim. A periodic report can be imported, but it is **not** a live feed. A single listing snapshot is not evidence of an increasing trend.

`data/*.json` CURRENTLY CONTAINS SYNTHETIC DEMO CONTENT â€” NOT MALAYSIAN LABOR STATISTICS. Replace with verified data before final submission. The live data pipeline must produce real, dated update signals.

---------------------------------------------------------------------------------------
# Malaysian Evidence â€” Member 4

**Project:** SkillShift AI
**Dataset review date:** 20 October 2026
**Status:** Software Developer and Accountants and Auditors prepared as evidence-supported integration drafts; application integration and live/updatable trend behaviour remain to be tested.

## 1. Dataset Overview

SkillShift AI aims to help Malaysian users understand changing career requirements, identify skill gaps, and find relevant learning resources for adapting to AI-driven workplace changes.

Two Malaysian occupation profiles have been curated for integration:

| Occupation | MASCO 2020 code | Sector / scope | Evidence status |
|---|---|---|---|
| Software Developer | 2512 | Information and Communications Technology (ICT) | Curated with documented assumptions |
| Accountants and Auditors | 2411 | Accounting and Finance | Curated with documented assumptions |

The repository also retains **three synthetic demo career profiles** (Data Analyst, Cybersecurity Analyst, and Cloud Engineer) for integration testing. Their illustrative skill requirements are **not verified Malaysian career evidence** and should be excluded from real-user recommendations until replaced or explicitly marked as demo data.

The dataset combines Malaysian workforce reports, official occupational classifications, an international classification reference (ESCO), dated DOSM job-market observations, and skill-linked learning resources. Source titles, URLs, evidence locations, reporting periods, retrieval dates, geography, licensing status, and limitations are recorded in `data/sources.json`.

**Data integrity rule:** A periodic report is not a live feed. A single job-market observation does not demonstrate rising or declining demand. Synthetic skill multipliers must not be presented as measured Malaysian labour-market changes.

## 2. Data Sources and Evidence Register

| Source ID / provider | Evidence used | Exact reference or period | Scope / caution |
|---|---|---|---|
| `src_mycol_2024` â€” TalentCorp MyCOL 2024/2025 | Software Developers and Accountants and Auditors critical-occupation profiles | Software Developers: printed pp. 249â€“250; Accountants and Auditors: pp. 223â€“224; list: Table 7, pp. 85â€“87 | Critical-occupation evidence is not an AI-impact score or proof of future growth |
| `src_masco_2020` â€” MASCO 2020 / eMASCO | Official Software Developers occupation code | Unit group 2512 | Classification only; not labour-market demand |
| `src_masco_accountants_2020` â€” MASCO 2020 / eMASCO | Official Accountants and Auditors occupation code | Unit group 2411 | Classification only; not labour-market demand |
| `src_ict_2024` â€” TalentCorp ICT Impact Study | Six Software Engineer skills; low AI-impact classification | Chapter 4, printed pp. 106â€“107 | Software Engineer is mapped approximately to Software Developer |
| `src_gbs_2024` â€” TalentCorp GBS Impact Study | Finance and Accounting Function skills and selected role-level AI impacts | Chapter 4, pp. 38â€“103; finance/accounting roles and skills at printed p. 95 | Job-cluster findings are not necessarily universal for MASCO 2411 |
| `src_dosm_jmi_q2_2026` â€” DOSM Job Market Insights | Official Software Developer and Accountants and Auditors online job offerings | **2026-Q2**, release dated 18 August 2026; media statement / release overview | One quarter, occupation-level observations; not a live feed or skill-demand time series |
| `src_esco_121` â€” European Commission ESCO v1.2.1 | Supporting occupation and skill taxonomy | English CSV downloads, including occupation and occupationâ€“skill relationship files | International classification; not Malaysian observed demand |
| Microsoft Learn, OpenLearn, OpenTuition | Free-to-learn foundational and AI-adaptation materials | Specific links and review dates in `data/learning_resources.json` | Some content is partial, some durations unknown, and optional software can require paid access |

### Official source links

- **TalentCorp MyCOL 2024/2025:** https://www.talentcorp.com.my/images/uploads/publication/204/MyMahir-Malaysia-Critical-Occupations-List-MyCOL20242025-1773385490.pdf
- **TalentCorp ICT Impact Study:** https://www.talentcorp.com.my/images/uploads/publication/199/Impact-Study-of-Artificial-Intelligence-Digital-and-Green-Economy-on-the-Malaysian-Workforce-Volume-2-Sector-Information-and-Communications-Technology-1747879475.pdf
- **TalentCorp GBS Impact Study:** https://www.talentcorp.com.my/images/uploads/publication/198/Impact-Study-of-Artificial-Intelligence-Digital-and-Green-Economy-on-the-Malaysian-Workforce-Volume-2-Sector-Global-Business-Services-1747879429.pdf
- **eMASCO Software Developers (2512):** https://emasco.mohr.gov.my/masco/2512
- **eMASCO Accountants and Auditors (2411):** https://emasco.mohr.gov.my/masco/2411
- **DOSM Job Market Insights Q2 2026:** https://www.dosm.gov.my/portal-main/release-content/big-data-analytics-job-market-insights-q22026
- **ESCO classification downloads:** https://esco.ec.europa.eu/en/use-esco/download
- **OpenDOSM catalogue (additional dataset discovery):** https://open.dosm.gov.my/data-catalogue

Relevant sources were retrieved/reviewed on **20 October 2026** as recorded in `data/sources.json`. The MyCOL **2024/2025** label describes the report edition; do not infer an exact publication date from the edition name alone.

### Source licensing and attribution

The `license_status` in `data/sources.json` differentiates identified terms from permissions that have not been verified:

- **DOSM:** Government Open Data Terms of Use 1.0 is linked in its source record; attribution to the Department of Statistics Malaysia is recorded. Scope of terms for any particular original workbook should be checked before redistribution.
- **ESCO classification:** Reuse conditions and European Commission acknowledgement are recorded; adaptations must be identified. ESCO API software licensing is separate from classification-data reuse.
- **TalentCorp reports and MASCO pages:** Explicit redistribution terms have **not been verified**. `not_verified` describes the project's verification status; it is not an official licence name or a declaration that reuse is forbidden.

Use report citations and limited, accurately attributed facts; do not assume that a publicly accessible PDF may automatically be redistributed in full.

## 3. Career 1 â€” Software Developer (MASCO 2512)

**Country:** Malaysia
**Sector:** ICT
**MyCOL:** Included in MyCOL 2024/2025, detailed profile at printed pp. 249â€“250.

### Skills from the TalentCorp ICT study

| TalentCorp category | Skill | Dataset ID | Team-defined weight |
|---|---|---|---:|
| Specific | Software Configuration | `skill_software_configuration` | 3 |
| Specific | Software Design | `skill_software_design` | 4 |
| Specific | Software Testing | `skill_software_testing` | 3 |
| Basic | Digital and AI Fluency | `skill_ai_fluency` | 2 |
| Basic | Critical Thinking | `skill_critical_thinking` | 2 |
| Basic | Innovative Thinking | `skill_innovative_thinking` | 2 |

The listed skills come from TalentCorp's **Software Engineer** profile, ICT study printed pp. 106â€“107. SkillShift AI maps this profile to **Software Developers (MASCO 2512)**; these two occupation definitions are related but are not treated as identical.

### AI impact

TalentCorp classifies its **Software Engineer** profile among low AI-impacted roles. This assessment is source-specific; it does not establish low demand, future job security, or zero automation exposure for every Software Developer.

### Job-market observation

DOSM Job Market Insights **Q2 2026** reports **19,899 online job offerings for Software Developers**. The record in `data/occupation_trends.json` references `src_dosm_jmi_q2_2026` and is not used as proof of employment growth or a skill-demand forecast.

## 4. Career 2 â€” Accountants and Auditors (MASCO 2411)

**Country:** Malaysia
**Sector:** Accounting and Finance
**MyCOL:** Accountants and Auditors are included for the job titles identified in MyCOL 2024/2025, detailed profile at printed pp. 223â€“224.
**Classification:** eMASCO unit group **2411**.

### Skills from TalentCorp GBS Finance and Accounting Function

| Skill | Dataset ID | Team-defined weight |
|---|---|---:|
| Financial Analysis and Reporting | `skill_financial_analysis_reporting` | 4 |
| Accounting Principles | `skill_accounting_principles` | 4 |
| Attention to Detail | `skill_attention_to_detail` | 3 |
| Ethical Judgement | `skill_ethical_judgement` | 3 |
| Cost-Benefit Analysis | `skill_cost_benefit_analysis` | 2 |
| Innovative Thinking | `skill_innovative_thinking` | 2 |

TalentCorp's **Finance and Accounting Function** skills table (GBS study, printed p. 95) supports the existence of these skills within the broader GBS job cluster. SkillShift AI selected these six for the MASCO 2411 prototype and assigned illustrative matching weights **1â€“4**. **TalentCorp did not publish these weights**, and the job-cluster list should not be presented as a ranking of all Malaysian accountants' skills.

The existing `skill_innovative_thinking` record is reused across both careers rather than duplicated.

### AI impact

The GBS study identifies certain roles, including **Cost Accountant, Internal Auditor and General Ledger Accountant**, among medium AI-impacted roles. Those observations concern the named specialisations and should not be generalized to all **Accountants and Auditors (MASCO 2411)**. The prototype therefore uses `ai_impact: null` for the combined occupation pending more occupation-specific evidence.

### Job-market observation

DOSM Job Market Insights **Q2 2026** reports **22,067 online job offerings for Accountants and Auditors**. The record in `data/occupation_trends.json` references `src_dosm_jmi_q2_2026`.

This is a single quarterly snapshot, not a forecast, a unique-vacancy count, total employment, or evidence that accounting job demand is increasing.

### Evidence tracing

The career's `source_ids` link to MyCOL, MASCO, TalentCorp GBS, and DOSM. Its `evidence_claim_ids` refer to particular claims within `data/sources.json`, allowing members of the team to identify the supporting source and page. Source mappings and all numerical weights remain subject to team review.

## 5. Malaysian Job-Market Data and Trend Signals

| Occupation | Period | DOSM metric represented in the app | Reported value | Source ID |
|---|---|---|---:|---|
| Software Developers (MASCO 2512) | 2026-Q2 | Online job offerings | 19,899 | `src_dosm_jmi_q2_2026` |
| Accountants and Auditors (MASCO 2411) | 2026-Q2 | Online job offerings | 22,067 | `src_dosm_jmi_q2_2026` |

The application's JSON field uses the key `metric: "online_job_postings"`; the original published measure is described as **online job offerings**.

The downloaded **`data/Data JMI Q2 2026.xlsx`** workbook and the cleaned **`data/jmi_major_occupation_2025_2026.csv`** contain broader **major-occupation-group** statistics. The CSV was produced with `data_pipeline/clean_jmi.py`. These files **must not** be treated as accountant-specific or software-developer-specific historical series. A Q1 2026 workbook was considered separately, but the current occupation-level app dataset intentionally retains **Q2 only** until comparable occupation-specific figures have been fully reconciled.

`data/trends.json` contains **synthetic integration-test skill multipliers**. They are not derived from the two real Q2 occupation observations. A working trend refresh/import mechanism, dated updates and proof that changing a valid signal updates recommendations are still required to meet the Domain 1 trend-signal feature.

## 6. Learning Resources and Personalized Pathways

`data/learning_resources.json` contains **19 skill-linked resources** after the Career 2 update:

- **14 foundational resources** and **5 AI-adaptation resources**.
- The original 12 resources cover Software Developer and initial demo skills; **7 additional resources** support accounting and finance.
- Existing Innovative Thinking content is reused across careers.

### Seven new accounting resources

| Course / study material | Provider | Skill ID | Category | Duration |
|---|---|---|---|---|
| Introduction to Bookkeeping and Accounting | OpenLearn | `skill_accounting_principles` | Foundational | 8 h |
| Financial Statement Analysis and Interpretation | OpenLearn | `skill_financial_analysis_reporting` | Foundational | 12 h |
| Assertions and Audit Evidence | OpenTuition | `skill_attention_to_detail` | Foundational | Not published |
| Professional Ethics | OpenTuition | `skill_ethical_judgement` | Foundational | Not published |
| Capital Investment Appraisal | OpenTuition | `skill_cost_benefit_analysis` | Foundational | Not published |
| Work Smarter with Copilot Prompts for Finance Professionals | Microsoft Learn | `skill_financial_analysis_reporting` | AI adaptation | Approx. 28 min |
| Get Started with Finance Agents | Microsoft Learn | `skill_financial_analysis_reporting` | AI adaptation | Approx. 83 min |

Course IDs, live-page links, skill IDs, categories, review dates, estimated durations and relevance notes are maintained in `data/learning_resources.json`. Some materials cover only part of a skill; OpenTuition notes are not the same as a timed course. Unknown hours use `estimated_hours: null` and should display as **â€œDuration variesâ€**, never zero hours.

Training content can be free while professional certification, optional software or Microsoft Copilot product features may have separate charges. These are learning opportunities, not guarantees of Malaysian professional qualification, employment or protection against displacement.

For the Domain 1 reskilling feature, the application still needs to order courses according to the user's skill gaps, show estimated time honestly, and explain why each recommendation fits.

## 7. SDG Mapping

Career-to-SDG tags are in `data/careers.json` and skill-to-SDG tags with rationales are in `data/skills.json`. The existing `data/sdg_mapping.json` contains SDG titles and general rationales; `data_pipeline/sdg_mapping.py` provides access helpers.

| Career | Current project-defined SDG tags | Interpretation |
|---|---|---|
| Software Developer | 4, 8, 9 | Learning, productive work and innovation |
| Accountants and Auditors | 4, 8, 16 | Learning, economic activity and accountability |

Individual skill mappings additionally include other relevant goals where justified. These links are **team-defined interpretations** of possible contributions, **not** official UN classifications, accreditations, or measured social outcomes. Every user-visible SDG recommendation should include its rationale.

## 8. Dataset Files and Validation

| File | Purpose |
|---|---|
| `data/careers.json` | Occupation profiles, required skill weights, source and claim links, AI-impact qualifiers and career SDGs |
| `data/skills.json` | Normalized skill IDs, names, SDG mappings and rationales |
| `data/sources.json` | Source registry, reporting/retrieval details, claim-level evidence, limitations and licence-status metadata |
| `data/occupation_trends.json` | Two real Malaysian Q2 2026 occupation-level job-market observations |
| `data/trends.json` | Explicitly synthetic skill multipliers used for integration testing |
| `data/learning_resources.json` | 19 skill-linked foundational and AI-adaptation learning resources |
| `data/sdg_mapping.json` | SDG titles and explanatory text used by the existing team mapping system |
| `data/Data JMI Q2 2026.xlsx` | Original DOSM workbook, broader occupational-group data; source licence scope warrants review before public redistribution |
| `data/jmi_major_occupation_2025_2026.csv` | Cleaned DOSM major-occupation-group data |
| `data_pipeline/clean_jmi.py` | Workbook cleaning script |
| `data_pipeline/sdg_mapping.py` | Role/skill SDG lookup helpers |
| `data_pipeline/validate_career2.py` | Cross-file data-integrity checks |

**Validation (20 October 2026):** The user's local run of `python data_pipeline/validate_career2.py` reported **413 / 413 checks passed, 0 errors**, with 5 career records (2 evidence-backed and 3 synthetic demo), 19 skills, 10 sources, 19 learning resources, and 2 official occupation observations.

This is **structural validation**: it checks data formats, references and coverage. It does **not** prove that all external source URLs remain live, independently re-verify every claim, test the backend/frontend, or demonstrate an updatable trend-to-matching workflow.

## 9. Assumptions, Limitations, and Next Steps

1. **Weights are estimates:** Required skill weights (1â€“4) were chosen by the team; they are not scores supplied by TalentCorp or ESCO.
2. **Career mappings are approximate:** Software Engineer / Software Developer and GBS finance function / MASCO 2411 are documented approximations.
3. **AI impacts are scoped:** The published classifications apply to particular roles in each TalentCorp report; no uniform future outcome is guaranteed.
4. **Real versus synthetic data must remain separate:** Synthetic demo careers and skill multipliers cannot be shown as verified Malaysian evidence.
5. **DOSM snapshot â‰  trend:** Q2 2026 offerings do not alone establish growth, decline or forecasts; broad occupation CSV must not be mislabelled as role-specific.
6. **Course links and times may change:** Unknown hours stay `null`; course content may cover only part of a required skill.
7. **SDGs are interpretations:** Career and skill SDG tags require meaningful explanations, not decorative icons.
8. **Licence uncertainty must be respected:** Record source attribution and reuse permissions precisely, especially if distributing original reports or workbooks publicly.

**Completed in this data iteration:** two curated Malaysian career profiles; skill-to-course links; occupation snapshots; evidence metadata; individual skill SDG tags; internal cross-file checks.

**Still pending:** confirm backend contract and handling of nullable fields, update this documentation in the repository, synchronize with current `main`, run the team application, verify user-facing evidence and pathways, test a refreshable real trend-signal workflow, and continue building the remaining selected careers.

**ESCO acknowledgement:** This service uses the ESCO classification of the European Commission.
