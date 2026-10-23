# SkillShift AI backend security hardening — 23 October 2026

**Scope:** Audited the uploaded `skillshift-ai-main (1).zip`, not older Phase 6 archives. The local build was exercised with mocked remote services. No penetration test or real RunPod/Supabase verification has been performed.

## Security references used

- OWASP API Security Top 10 **2023** (published edition): https://owasp.org/API-Security/
- OWASP ASVS **5.0.0** (latest stable as of this review): https://asvs.owasp.org/
- FastAPI / Starlette middleware and host validation: https://fastapi.tiangolo.com/advanced/middleware/
- Supabase Auth `getUser()` server identity verification: https://supabase.com/docs/reference/javascript/auth-getuser
- FastAPI trusted proxy guidance: https://fastapi.tiangolo.com/advanced/behind-a-proxy/

## What changed

| Issue | Fix | Caveat |
|---|---|---|
| Unrestricted public request frequency (OWASP API4) | SQLite-backed rolling 60-second IP rate limit for all `/api/` routes other than health, 120/minute by default | **One host / one persistent filesystem only**. Reverse-proxy client IP must be configured by platform. Not a bot/DDOS defense. |
| Unbounded requests (API4) | Maximum API write-body size (32 KiB default), counts bytes even without `Content-Length`; oversized requests return 413 | This is an HTTP application limit, not a network ingress/slowloris defense. |
| Unexpected POST media | JSON-only for analyze/scenarios/roadmap; 415 on other media | Account deletion remains a bearer-authenticated DELETE. |
| Unsafe browser response defaults (API8) | CSP, nosniff, anti-framing, referrer and permissions headers; API responses set `Cache-Control: no-store` | Test CSP with your deployed React build; update `connect-src` for any intentional custom domains. |
| Host-header ambiguity (API8) | Optional `ALLOWED_HOSTS`; production requires a non-wildcard list. OpenAPI/docs disabled in production. | Production must set the real hostname. |
| Strict input validation (API3/API4) | Pydantic bounded skill IDs / interests and `extra="forbid"` on request models | This intentionally rejects undocumented fields. |
| Supabase bearer token validation (API2) | Shared strict parser and origin validation for AI and account deletion | The app still depends on Supabase availability and does not implement local JWT verification. |
| RunPod job path injection / malformed output (API10) | Whitelist endpoint/job ID formats; cap model output, validate structured output and polling timeout | Output still requires Member 3 to consistently return course-ID JSON arrays. |
| GPU slot expiry race (API4/API6) | `AI_SLOT_TTL_SECONDS` must exceed `RUNPOD_POLL_TIMEOUT + 45` seconds | For unusually long worker startup adjust both knobs; verify actual elapsed time. |
| Account deletion privacy | Anonymize user IDs in persistent AI-attempt records after successful Supabase Auth deletion, retaining anonymous global spend totals | Post-delete quota cleanup failures are logged and require operator remediation; auth deletion itself is not rolled back. |
| Dependency/security regression drift | Added dependency audit + Bandit workflow; switched frontend CI to `npm ci` | Audits require network and have not been executed here. Review CI findings rather than blindly suppressing them. |

## Local Windows setup

Keep `.env` private; never place secrets in `VITE_*` variables. Development can use default settings:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe data_pipeline/validate_careers.py
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

The new test fixture gives each test its own request-limit database; repeatedly running pytest will not exhaust the production quota.

To test API throttling manually, issue at least `API_RATE_PER_MINUTE + 1` requests from one trusted client address within a minute. The limit responds with HTTP 429 and `Retry-After`. The `/api/health` endpoint is exempt for uptime checks.

## Production / Replit requirements

```dotenv
APP_ENV=production
ALLOWED_HOSTS=your-actual-hostname.replit.app
API_MAX_BODY_BYTES=32768
API_RATE_PER_MINUTE=120
SECURITY_HSTS_ENABLED=true
AI_ENABLED=false
```

- Only enable `SECURITY_HSTS_ENABLED=true` **after** verifying that the entire public host is HTTPS-only. HSTS influences browsers for a year; avoid on development hosts.
- Configure host allowlist to include every actual public hostname. Do not set `*` in production.
- Replit's HTTPS proxy should pass *correct, trusted* client addresses; do not take `X-Forwarded-For` from arbitrary callers. Uvicorn's forwarded-header trust list needs to match your infrastructure. An incorrect proxy configuration may treat all users as one IP or allow throttling evasion.
- **A local SQLite file does not provide fleet-wide enforcement on autoscaling/ephemeral deployments.** For public multi-instance use, replace both API rate limits and AI quota counters with central durable transactional storage (e.g. a Supabase Postgres RPC with atomic updates) and provider/edge rate limiting. Keep AI disabled on a deployment where paid GPU attempts cannot be enforced reliably.
- If setting `AI_ENABLED=true` in production, `AI_QUOTA_DB_PATH` must be explicitly configured and be on *verified persistent storage*; `API_RATE_DB_PATH` also needs persistent storage for consistent abuse limits. Path configuration **does not prove storage is durable**, so verify the deployment topology.
- Do not add permissive `CORSMiddleware` just to make the frontend work. The deployed frontend should call same-origin `/api`, as it already does.
- `SUPABASE_SERVICE_ROLE_KEY` is server-only and permits destructive administrative operations; rotate it if it was ever included in frontend artifacts/logs. Check Supabase RLS migrations before publishing.
- Observe real RunPod queue, inference and cold-start latency; a 503 does not necessarily mean the GPU failed. Distinguish model output validation errors from provider failures.

## Suggested acceptance probes

| Test | Expected result |
|---|---|
| GET `/api/health` | HTTP 200 |
| POST `/api/analyze` valid JSON | HTTP 200 |
| POST `/api/analyze` with non-JSON Content-Type | HTTP 415 |
| POST JSON larger than `API_MAX_BODY_BYTES` | HTTP 413 |
| Too many `/api/` requests | HTTP 429, `Retry-After` |
| POST `/api/roadmap` as guest | HTTP 200, no RunPod call |
| POST `/api/roadmap/personalize` as guest | HTTP 401 if AI enabled |
| Invalid Supabase access token | HTTP 401 |
| RunPod invalid/timeout/model hallucination | HTTP 503; approved roadmap preserved |
| Wrong host with `ALLOWED_HOSTS` set | HTTP 400 |
| GET `/docs` in production | HTTP 404 |
| Google sign-in, saved profile, account deletion | Real browser and Supabase testing required |

## Remaining risks / must-do before public launch

1. Run `npm ci && npm run build` and test CSP on the real hosted UI. A syntax-only check cannot verify browser CSP.
2. Run `pip-audit`, `bandit`, `npm audit` in CI and triage any findings; lock dependency versions with reviewed lock files/hashes. No vulnerability-free or ASVS-compliant claim is made here.
3. Replace SQLite-backed abuse limits with a centralized rate limiter when scaling beyond a single durable instance; set external RunPod spending caps. Merely setting `AI_DAILY_LIMIT` does not cap *cost per token*.
4. Put an edge reverse proxy / WAF in front of the service to mitigate volumetric attacks and slow clients. Application rate limits alone cannot protect the web server process.
5. Establish an incident response and secret rotation procedure, user data retention policy and access logs without bearer tokens / AI prompts.
6. Run a live authenticated end-to-end test with Member 3's warm RunPod worker. A unit test cannot establish a successful model run.
