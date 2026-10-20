# Malaysian evidence — Member 4

Suggested starting points:
- TalentCorp Malaysia Critical Occupations List (MyCOL): https://www.talentcorp.com.my/
- Department of Statistics Malaysia: https://open.dosm.gov.my/
- OpenDOSM catalogue: https://open.dosm.gov.my/data-catalogue
- MASCO occupational classification: official Malaysian government references

Record source title, URL, report period, access/retrieval date, specific page/table, geography, license and exact skill or trend claim. A periodic report can be imported, but it is **not** a live feed. A single listing snapshot is not evidence of an increasing trend.

`data/*.json` CURRENTLY CONTAINS SYNTHETIC DEMO CONTENT — NOT MALAYSIAN LABOR STATISTICS. Replace with verified data before final submission. The live data pipeline must produce real, dated update signals.

---------------------------------------------------------------------------------------
# Malaysian Evidence — Member 4 - Press Ctrl + Shift + V to view
**Dataset review date:** 20 October 2026 8:45AM

## 1. Dataset Overview

SkillShift AI focuses on helping Malaysian users understand changing career requirements, identify skill gaps, and find relevant learning resources to adapt to AI-driven workplace changes.

The first occupation prepared is **Software Developer (MASCO 2512)** under the Information and Communications Technology (ICT) sector.

The dataset combines Malaysian workforce evidence, international occupational classification references, and verified learning resources.

## 2. Data Sources

| Source | Evidence Used | Reference |
|---|---|---|
| TalentCorp MyCOL 2024/2025 | Identifies Software Developers as a Malaysian critical occupation, with employer-reported skill requirements | Printed pp. 249–250 |
| TalentCorp ICT AI Impact Study (2024) | Six Software Engineer skills and low AI-impact classification | Printed pp. 106–107 |
| ESCO v1.2.1 | Supporting international occupation and skills classification | English CSV dataset |
| DOSM Job Market Insights Q2 2026 | Malaysian online job offerings for Software Developers | Q2 2026 official release |
| Microsoft Learn | Foundational and AI-adaptation learning resources | Individual course pages |
| OpenLearn — The Open University | Software development, critical thinking and innovation learning resources | Individual course pages |

### Official Sources

**TalentCorp MyCOL 2024/2025**

https://www.talentcorp.com.my/images/uploads/publication/204/MyMahir-Malaysia-Critical-Occupations-List-MyCOL20242025-1773385490.pdf

**TalentCorp ICT AI Impact Study**

https://www.talentcorp.com.my/images/uploads/publication/199/Impact-Study-of-Artificial-Intelligence-Digital-and-Green-Economy-on-the-Malaysian-Workforce-Volume-2-Sector-Information-and-Communications-Technology-1747879475.pdf

**ESCO classification**

https://esco.ec.europa.eu/en/use-esco/download

**DOSM Job Market Insights Q2 2026**

https://www.dosm.gov.my/portal-main/release-content/big-data-analytics-job-market-insights-q22026

## 3. Software Developer — Verified Information

- Occupation: Software Developer
- MASCO code: 2512
- Country: Malaysia
- Industry: ICT
- MyCOL status: Included in Malaysia's Critical Occupations List 2024/2025

### Skills from TalentCorp ICT Impact Study

**Specific Skills:**
- Software Configuration
- Software Design
- Software Testing

**Basic Skills:**
- Digital and AI Fluency
- Critical Thinking
- Innovative Thinking

These skills are taken from the TalentCorp ICT study's Software Engineer profile. MyCOL includes Software Engineer among the nominated job titles under Software Developers (MASCO 2512).

The mapping is documented because the two source records are not necessarily identical.

### AI Impact

TalentCorp classifies Software Engineer as a low-impact role in its ICT study.

This classification is specific to the study's assessment of AI, digital and green economy impacts. It does not mean the occupation has low demand or is guaranteed protection from automation.

## 4. Malaysian Job Market Data

DOSM Job Market Insights Q2 2026 reports **19,899 online job offerings for Software Developers**.

This figure is recorded in `data/occupation_trends.json` and references `src_dosm_jmi_q2_2026`.

The raw workbook `Data JMI Q2 2026.xlsx` and cleaned CSV `jmi_major_occupation_2025_2026.csv` contain broader occupational-group statistics across reporting quarters. The cleaned CSV was generated using `data_pipeline/clean_jmi.py`.

The broad-group CSV must not be treated as a Software Developer-specific historical time series.

Online job offerings are not equivalent to total employment or unique job vacancies. They also do not measure individual skill demand.

## 5. Learning Resources

`data/learning_resources.json` contains 12 learning resources:

- 9 foundational resources
- 3 AI-adaptation resources

Learning resources are mapped to existing skills through `skill_ids`.

The `learning_category` field distinguishes:

- `foundational`: Developing general career-related skills.
- `ai_adaptation`: Learning to work effectively with AI tools and evaluate AI-generated outputs.

Learning resources are provided by Microsoft Learn and OpenLearn.

Free learning access does not necessarily include free certification or unrestricted access to optional software tools.

Course recommendations are intended to support skill development and AI adaptation. They do not guarantee employment or prevent job displacement.

## 6. Dataset Files

| File | Purpose |
|---|---|
| `data/careers.json` | Career profiles, skill requirements, occupation mappings and AI impact |
| `data/skills.json` | Skill IDs and skill names |
| `data/sources.json` | Evidence provenance and source metadata |
| `data/occupation_trends.json` | Real Malaysian occupation-level job-market statistics |
| `data/trends.json` | Synthetic skill multipliers for integration testing |
| `data/learning_resources.json` | Skill-linked learning recommendations |
| `data/jmi_major_occupation_2025_2026.csv` | Cleaned DOSM major-occupation-group data |
| `data_pipeline/clean_jmi.py` | DOSM workbook cleaning script |

## 7. Assumptions and Limitations

1. **Skill importance weights (1–4)** are team-defined illustrative values, not official TalentCorp scores.
2. **Skill trend multipliers** in `data/trends.json` remain synthetic test data and must not be presented as measured Malaysian skill-demand changes.
3. **ESCO** is an international classification reference, not Malaysian labour-market evidence. Adapted mappings must be identified.
4. **Software Developer and Software Engineer** are mapped for this prototype, with the difference documented.
5. **DOSM online job-offering statistics** are occupation-level indicators, not measurements of individual skills or future employment guarantees.
6. **Learning resources** are matched according to their published curriculum. Some provide only foundational or partial coverage of a skill.
7. **SDG mappings** are project interpretations, not source-issued certifications.
8. Backend/frontend integration and the team's matching methodology still require final validation.

## 8. Current Progress

Software Developer is ready as an evidence-supported **integration draft**.

Completed:
- Malaysian occupation identification and evidence mapping
- Six TalentCorp skills and AI-impact classification
- Source documentation
- DOSM Q2 2026 occupation-demand record
- Foundational and AI-adaptation learning resources
- JSON syntax and cross-file reference checks

Pending:
- Final review of numerical skill importance weights
- Backend/frontend integration testing
- Replacement or explicit presentation of synthetic skill trend signals
- Expansion to the remaining selected occupations

**ESCO acknowledgement:** This service uses the ESCO classification of the European Commission.