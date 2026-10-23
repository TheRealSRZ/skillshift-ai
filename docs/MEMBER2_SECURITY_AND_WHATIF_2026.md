# Member 2: Security Hardening + Career What-If (23 October 2026)

This is an **additive update** against the security-hardened SkillShift AI version **plus the three-file Bandit CI fix**. It adds no third-party service, paid AI calls, dependency, or new user account requirement. Existing RunPod, Supabase Auth, DOSM and catalog behavior is unchanged.

## Summary

| Area | Implementation | Verification |
|---|---|---|
| GPU-cost guard | Optional AI calls with no eligible approved courses return 422 before account verification/AI slot reservation | Automated Python test |
| Production settings | `APP_ENV` must be `development`, `testing`, or `production`; malformed production host allowlists fail startup | Automated Python tests |
| What-If Simulator | `POST /api/what-if` recomputes readiness from the same catalog, trend snapshot and weights used by `/api/analyze` | Automated Python tests and API smoke test |
| Safe input handling | Strictly-shaped role/skill IDs and rejection of non-text control characters in free-form profile fields | Automated negative-input tests |
| Observability | Server-generated opaque `X-Request-ID` and sanitized status/duration diagnostics; no raw profile/token logs | Automated tests |
| Supabase saved-data limits | Additive SQL migration enforcing bounded JSON, bounded profile arrays and 30 saved analyses/roadmaps per user | SQL reviewed and structurally tested; **must still be applied and live-tested in Supabase** |
| Frontend | One optional panel at bottom of Careers page when a target is selected. Max 5 missing skills, result preview, accessible feedback, light/dark CSS | TS/TSX parsed; **full Vite build on connected machine required** |

## What-If safety/interpretation

1. Sign in or use a guest demo; no authentication is required for the preview.
2. Analyze a profile, visit **Careers**, and choose a target career.
3. Select one to five missing skills and click **Preview readiness**.
4. Review **Current → Hypothetical** plus delta points. The original profile and saved results are never changed.
5. All scores come from `backend.matching.match_roles()`. No RunPod request is made. This is not a hiring probability or verified skill mastery.

Example request:

```json
{
  "profile": {"education": "Student", "skills": ["skill_python", "skill_sql"], "interests": ["data"]},
  "target_role": "role_data_analyst",
  "add_skills": ["skill_power_bi"],
  "scenario": "moderate"
}
```

Endpoint: `POST /api/what-if`. Existing request throttling and request-size middleware apply to this endpoint.

## Install without replacing teammate work

Apply the **changed-files ZIP** over the matching project baseline, preserving paths, or apply the patch to the same baseline. If the code has diverged, use a normal Git merge/review instead of overwriting teammate modifications.

Windows (project root):

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe data_pipeline\validate_careers.py
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
# In another terminal:
cd frontend
npm ci
npm run build
npm run dev
```

Expected suite for this package: **160 Python tests**. A sample what-if calculation for Data Analyst with Python + SQL and adding Power BI is **54.2% → 81.9%** with the bundled snapshot. These are calculated overlap scores, not validated employability statistics.

## Apply Supabase migration (same existing project; no new service)

File: `supabase/migrations/20261023_skillshift_storage_limits.sql`.

**This is NOT automatically applied by extracting the ZIP.** Apply it once, in order, through the team's existing Supabase SQL Editor or migration deployment process, **after** `20261020_skillshift_accounts.sql`. Do not run it twice manually; constraints are not written as idempotent. Ensure you have a schema backup/snapshot and appropriate change approval first.

- Retains existing data and ownership RLS policies.
- Limits *new* saved profile/analysis/roadmap payloads. Existing oversized records remain, because the new CHECK constraints are `NOT VALID` and are not backfilled or deleted.
- Enforces 30 saved analyses and 30 saved roadmaps per account, using advisory transaction locks for concurrent inserts.
- Trigger functions live in the non-API `skillshift_internal` schema, use fixed table names and a fixed `search_path`, and check the authenticated user before counting records.
- The user may delete previous saved entries to free capacity. No automatic deletion/retention timer was added.
- **Live Supabase tests remain necessary:** save/read/delete under two distinct accounts; verify 31st insert fails; unauthorized cross-account writes fail; oversized JSON fails; account deletion cascades; existing app save flow works.
- This migration is not a replacement for RLS or deployment-level authentication configuration.

## Production security notes

`APP_ENV=production` now requires a comma-separated list of exact hostnames in `ALLOWED_HOSTS` (e.g. `your-app.replit.app`), with **no scheme, port, or wildcard**. Using `APP_ENV=prod` fails fast rather than silently running with development controls. Existing protections (CSP, size limits, client-IP throttles, secret placement and AI quotas) remain in place.

No new services are needed, but two existing platform properties **must be verified before paid AI is public**:

1. Replit reverse proxy/client IP behavior: do not blindly trust `X-Forwarded-For`; the current limiter uses ASGI `scope['client']`. If all visitors map to one proxy address, limits may be shared incorrectly. Validate with the actual published environment.
2. The local SQLite request/AI counters require a **single instance and durable disk**. If the Replit plan scales horizontally or uses ephemeral filesystems, keep `AI_ENABLED=false` until shared quotas are available. Code alone cannot enforce a globally correct spend budget across disjoint instances.

`X-Request-ID` is generated server-side for responses. Only status, category, duration and opaque ID are logged for failed API responses; tokens, profile text, raw model output and secrets are not logged.

## Acceptance test checklist

- [ ] 160 Python tests pass on Windows and in GitHub Actions.
- [ ] `npm ci && npm run build` passes on Member 2's/Member 1's PC (not verified in this sandbox due to blocked npm registry).
- [ ] Browser: Careers → select Data Analyst → simulate Power BI → see increased hypothetical score.
- [ ] Switch careers or change profile while preview is pending → no stale result appears.
- [ ] Guest mode still works and uses zero RunPod credits for the What-If feature.
- [ ] Normal approved roadmap and optional authenticated RunPod flow are unchanged.
- [ ] Production startup rejects `APP_ENV=prod`, wildcard hosts, and missing host allowlists.
- [ ] Existing Supabase migration applied and tested by two real accounts.
- [ ] Replit host/proxy behavior checked; AI storage confirmed persistent before publicly enabling paid AI.

## Rollback

Git: revert this patch. The What-If endpoint and panel disappear without modifying user profiles. The new Supabase constraints/triggers **remain** until a separate reviewed database rollback is applied; do not automatically drop the whole `skillshift_internal` schema if other functions were added there later. Back up your database and coordinate rollback before schema changes.

## Scope limitations

- No live production deployment, Supabase policy execution, RunPod requests, npm production build, or penetration test was performed in this environment.
- No claims of full OWASP ASVS compliance are made.
- Do not indiscriminately remove `<`, `>`, quotes, or Unicode from free-form text; React output encoding and contextual allowlist validation are more appropriate. Existing controls exclude dangerous control characters and validate structured IDs.
