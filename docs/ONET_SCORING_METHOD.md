# SkillShift AI — O*NET skill importance and task evidence method

## Sources and interpretation
- Malaysian role definitions and the six selected skills per role: `data/careers.json` (locally curated; weights 1–4 are team estimates).
- Representative US occupational matches: `data/onet_career_mapping.json` (not an official MASCO–O*NET crosswalk).
- O*NET general Skills importance (IM): `data/processed/onet_occupation_skills.csv`.
- O*NET task importance (IM): `data/processed/onet_occupation_tasks.csv`.
- Distinguish Skills *Level* (LV), task frequency (FT), and *task importance* (IM) from *general skill importance* (IM).

## Proposed SkillShift importance categories (project-defined)
- 1 = supporting
- 2 = relevant
- 3 = important
- 4 = core

For a directly equivalent, unsuppressed O*NET general-skill importance score `x` between 1 and 5, **proposed**, not automatically adopted, `min(4, floor(x))`. Ratings marked Recommend Suppress=Y or Not Relevant=Y are excluded. Record the original numeric value and its measurement date.

## Task evidence handling
`data_pipeline/build_onet_task_evidence.py` contains an explicit (reviewable) list of O*NET task IDs mapped to project skills, validated against the actual occupation-specific task `IM` data. It produces `data/processed/onet_task_skill_evidence.json` with original task descriptions, task ratings, dates and flags for partial overlap. **It never converts task importance to official skill importance**, and it never edits `careers.json`.

Matching task(s) demonstrate that a skill is useful for an occupation. They do **not** prove its exact relative skill weight; tasks may support several skills, and ratings are on different constructs. Where there is no exact task, retain the existing team weight and disclose missing evidence; do not treat `0 tasks` as `0 importance`.

## Scoring policy for Member 2
1. Continue using `careers.json` weights until the team approves versioned changes.
2. Display direct O*NET skill evidence separately from linked task evidence and team weights.
3. Do not combine task averages and skill IM into a fabricated single score.
4. Before adopting proposed direct rating conversions, review balance across the six selected skills, effects on matching, US-to-Malaysia transferability, and sensitivity tests.
5. Do not use US nursing tasks to imply Malaysian legal authority (e.g. prescribing or diagnosing).
6. OECD AI capability exposure must remain separate from skill importance and job replacement probability. DOSM broad-group JMI change must remain separate from individual skill demand.

## Remaining manual checks
- Peer-review all explicit task–skill links and partial-match flags; make changes in the code only when justified by the task wording.
- Check whether specific technology records offer qualitative support for Python, SQL, circuit simulation and digital marketing (no general skill importance inference).
- Add dated source/version and licence attribution to `docs/data_sources.md` when the whole pipeline is complete.
