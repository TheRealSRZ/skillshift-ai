# SkillShift Phase 6E — Security, Acceptance and Replit Handoff

**Baseline:** Phase 6D two-stage roadmap built on Member 4's updated six-career DOSM evidence pipeline. The 3+3 availability semantics, scenario weights and matching code are unchanged.

## 1. Why `/api/roadmap/personalize` is now protected

- `/api/roadmap` remains **public, fast, and GPU-free**.
- `/api/roadmap/personalize` requires a valid Supabase **access token** in `Authorization: Bearer <access-token>`. FastAPI calls Supabase Auth `/auth/v1/user`; it does not trust a profile ID sent from React or decode a JWT without verification.
- No anonymous/guest request can start a RunPod job (HTTP 401). A missing or invalid Supabase configuration returns 503; invalid session returns 401.
- Server-side SQLite allowance (defaults): **3 attempts per authenticated user per UTC day, 30 globally per UTC day, 1 concurrent job globally, 45-second per-user cooldown**. Concurrent requests reserve slots atomically with SQLite `BEGIN IMMEDIATE`; failed AI attempts still count. A `429` response includes `Retry-After`. These values may be changed through the environment limits shown below.
- Local allowance is stored at `instance/ai_quotas.sqlite3` by default. `instance/` and `.sqlite3` are ignored in Git. **This limiter is suitable only for a single deployment with a durable shared filesystem.** Do not deploy multiple autoscaling replicas with different local files: they would have independent GPU budgets, and filesystem resets can reset quotas. For public scalable deployment, replace the allowance store with a centralized, transactional Supabase/Postgres quota function before enabling paid GPU requests. Alternatively leave `AI_ENABLED=false` in production.
- Active jobs are released in `finally`. Stale slots expire after 300 seconds by default; ensure the slot TTL exceeds real provider request durations. After a crash the daily attempt remains counted.
- Auth verification requires a standard `https://*.supabase.co` project URL. Custom domains would require explicit URL trust-configuration changes.
- The existing approved-course validator still prevents invented courses and loss of skill coverage. The frontend does not replace the current roadmap on 503 or 429.

## 2. Critical environment setup

Private backend `.env` (local) or Replit Secrets (deployed):

```dotenv
AI_ENABLED=true
SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_YOUR_KEY
RUNPOD_API_KEY=...
RUNPOD_ENDPOINT_ID=...
RUNPOD_POLL_TIMEOUT=30
AI_DAILY_LIMIT=3
AI_GLOBAL_DAILY_LIMIT=30
AI_MAX_CONCURRENT=1
AI_COOLDOWN_SECONDS=45
# AI_QUOTA_DB_PATH=/persistent/shared/path/ai_quotas.sqlite3
```

If service-role credentials are configured for account deletion, keep them backend-only. Never use `VITE_` for RunPod or service-role secrets.

Public frontend build-time variables (Replit deployment must also provide these **at build time**):

```dotenv
VITE_SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=sb_publishable_YOUR_KEY
VITE_ENABLE_APPLE_AUTH=false
```

Supabase Site URL + Additional Redirect URLs must include your production HTTPS hostname (and `http://localhost:5173` for local development). Google's configured OAuth callback remains the Supabase `/auth/v1/callback` URL.

## 3. Test locally (Windows PowerShell)

```powershell
# Terminal 1, from project root
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe data_pipeline/validate_careers.py
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2
cd frontend
npm ci
npm run build
npm run dev
```

Browser acceptance:

1. Guest demo → Profile → Analyze → Roadmap. Click **Generate approved roadmap**; it must return quickly even with `AI_ENABLED=true`. Guest cannot submit optional AI; a sign-in action is shown.
2. Google sign-in → same steps → click **Personalize with AI**. Verify response is `runpod_validated` only if the model actually succeeds and passes catalog checks; failures leave the initial plan visible.
3. Three AI attempts per user per UTC day (default) → later attempts HTTP 429; verify another account has its own allowance but global cap also applies.
4. Simultaneous requests (two tabs) → only one RunPod reservation at a time; second 429. `429`/`503` should show clear notifications; no raw provider exception or secrets returned.
5. Profile saving/loading after refresh, account isolation, Google logout, six-career DOSM signal panel and its refresh button, light/dark mode and narrow viewport.
6. For an `AI roadmap fallback: ValueError`, inspect the sanitized diagnostic **category** in backend logs. `missing_course_id_array` = model output not matching required JSON list, `invalid_or_duplicate_course_ids` = malformed/unknown selection, `incomplete_skill_coverage` = valid IDs but incomplete skills. Provider logs (queue, cold start, credits) must be checked separately by Member 3. Never log raw prompts or keys.

## 4. Build & publish on Replit

- Replit config now defines `[deployment] build` and `run` separately. Build executes `bash scripts/build_frontend.sh` (npm ci, typecheck/Vite build); run executes `scripts/start.sh` and **fails closed** if `frontend/dist/index.html` is missing. The original root FastAPI entrypoint remains unchanged.
- Configure Python dependencies from `requirements.txt`; ensure Node/npm are available in the Replit build image. Review commands in the Replit Publishing settings because those may override `.replit`.
- Set the actual `PORT` only if Replit doesn't supply one, and choose **one instance** if using the local SQLite allowance file. For autoscale or ephemeral deployments, **keep `AI_ENABLED=false`** until a durable centralized quota is deployed.
- Be aware Replit deployment may have charges or account restrictions. Check the plan before publishing; deployment has not been carried out in this patch.
- After publishing: request `/api/health`, `/api/catalog`, `/api/market-signals`, and open the public `/` to confirm React (not the backend placeholder) is served. Test Google redirect and guest experience on the public origin.

## 5. Member handoff

- **Member 1:** verify sign-in notice, responsive optional AI panel, clarity of 401/429/503 notifications, browser build.
- **Member 2:** own token verification, per-user/global quotas, Replit build, acceptance and account integration.
- **Member 3:** classify worker logs by `IN_QUEUE`/`IN_PROGRESS`/`COMPLETED`, output length, prompt validity, voucher balance; optimize model output for short JSON array only. A `ValueError` is *not* sufficient evidence of exhausted GPU credits.
- **Member 4:** confirm DOSM quarterly evidence and O*NET/OECD annotations remain unchanged.

**Not done automatically:** actual Supabase user validation against your private project, actual RunPod inference, browser E2E on your PC, or live Replit publishing. Do not claim these have passed without completing them.
