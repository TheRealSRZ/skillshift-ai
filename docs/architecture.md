# Architecture

Browser (React/TS) → `backend` FastAPI (/api/*) → `data` JSON evidence and role definitions; backend invokes `ai` for optional grounded explanations. `data_pipeline` refreshes validated snapshots before they are loaded. Replit hosts the built frontend and backend; RunPod hosts inference through a private backend-to-backend call.

- Source evidence must carry source ID, URL, date, geographic coverage, and licensing/terms review.
- Matching score is weighted overlap, **not job probability**.
- Future scenarios are hypothetical multipliers, **not validated future probabilities**.
- Current starter values are synthetic demo only.
- SDG mappings need grounded rationale for each production role/skill.
