# SkillShift AI Phase 6D — Two-stage approved roadmap + optional AI

**Baseline:** Phase 6C built from `skillshift-ai-main member 4 update.zip`. Do not apply the superseded Phase 6A/6B patches.

## What changed

- **Stage 1, always fast:** `POST /api/roadmap` builds a deterministic, Member 4-approved course plan **without RunPod**, regardless of `AI_ENABLED`.
- **Stage 2, opt-in:** `POST /api/roadmap/personalize` is called only after a user clicks **Personalize with AI**. Requires `AI_ENABLED=true`, the RunPod API key and endpoint ID on the backend. Success requires `generation_mode: runpod_validated` and Member 2's course/skill coverage checks. Failure returns `503` (or `422` for invalid input), never a misleading AI success.
- **Member 1 UX:** The approved roadmap remains visible throughout the AI request. If the response times out or fails validation, it remains intact and the user sees a clear inline explanation plus a toast. On success, approved-course selections are updated. Changing career/profile/account invalidates stale responses.
- **No modifications** to Member 4's catalog or DOSM data, RunPod worker/client, Supabase database or career-readiness scoring.

### Important API examples

```powershell
$payload = @{ target_role='role_data_professional'; missing_skills=@('skill_data_analysis','skill_data_cleaning','skill_sql','skill_data_viz','skill_critical_thinking'); scenario='moderate' } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/roadmap -ContentType 'application/json' -Body $payload
# Optional: invokes RunPod when AI_ENABLED=true; may take time and incur charges
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/roadmap/personalize -ContentType 'application/json' -Body $payload
```

If `AI_ENABLED=false`, Stage 1 still returns courses immediately. Stage 2 returns HTTP 503 with a friendly message. A `503` from Stage 2 also covers timeout, failed RunPod output or unsafe/incomplete AI selections, and doesn't delete the Stage 1 result.

## Local setup and acceptance

Backend in repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe data_pipeline/validate_careers.py
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend in a separate PowerShell terminal:

```powershell
cd frontend
npm ci
npm run build
npm run dev
```

Check `/api/health` and `/docs`. In the app, analyze a profile, choose Data Professionals, and select **Generate approved roadmap**. It should return without making a RunPod request even when `AI_ENABLED=true`. Then select **Personalize with AI**; the plan must stay visible during RunPod processing. Turn `AI_ENABLED=false` and restart FastAPI to test the failure state quickly; existing courses must remain unchanged. Repeat with a mocked/working AI response to confirm `runpod_validated` is displayed correctly.

### Critical: live inference and RunPod credits

The standalone `python -m scripts.test_real_roadmap` returning `runpod_ai` proves RunPod succeeded for *that standalone request*, **not** the new protected `POST /api/roadmap/personalize`. Test the real endpoint too, including Data Professionals (5 missing skills). Do not publish API keys, service-role credentials or prompt/user data in screenshots. Member 3 should inspect:

1. Endpoint maximum workers and flex/active workers. `max workers=0` prevents processing; low idle capacity may cause cold starts.
2. Serverless job lifecycle: `IN_QUEUE`, `IN_PROGRESS`, `COMPLETED`, `FAILED`, `TIMED_OUT`, worker unhealthy states, and queue/execution durations.
3. Account/voucher balance, billing status, spend limits and GPU quota—**do not assume** credits are depleted without checking.
4. `RUNPOD_POLL_TIMEOUT` and request timeout settings; the client currently defaults to 30s polling and may spend additional time on HTTP operations. Do not raise limits blindly; record actual timings first.
5. Whether Qwen returned every approved course necessary to cover the missing skills. Successful RunPod completion can still be rejected by SkillShift's trust boundary.

RunPod workers can scale to zero between requests. Current RunPod docs also describe automatic idle-endpoint reductions to max workers after prolonged no-request periods. Always check the console before assigning root cause.

### Cost and production guardrails

The optional AI endpoint is available to demo/guest users and calls a billable GPU service. **Before exposing it on a public URL**, add server-side rate limiting and per-user quotas, budget alerts and concurrency caps. Client-side disabled buttons only prevent accidental double clicks, not API abuse. Never include `RUNPOD_API_KEY` in React, and never log API keys or model prompts. This feature doesn't queue work in the background; the optional request is still synchronous, but Stage 1 stays displayed throughout.

### Test results and limits

Phase 6D Python suite: **121 tests passed**, including baseline/no-AI, 503 on timeouts/invalid outputs, genuine validator handling and both observed/curated careers. Member 4 cross-file validator: **983/983 checks passed**. TypeScript/TSX syntax parsing passed for **23 files**. Full `npm run build` was **not possible in the sandbox** because package download/installation hung; perform it on your Windows PC and inspect the responsive UI before merging. No live RunPod invocation was performed during these tests.
