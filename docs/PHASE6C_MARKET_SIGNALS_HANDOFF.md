# Phase 6C — DOSM Six-Career Market Signals (Member 2 + Member 1)

**Baseline:** `skillshift-ai-main member 4 update.zip` supplied 22 October 2026. This branch does **not** include or depend on the previous Phase 6A/6B patches.

## Summary

- Member 4's existing generator and six-career JSON are retained **without edits**.
- `backend/routes/market_signals.py` is the separately supplied Member 4 API file. `backend/main.py` registers it.
- `GET /api/market-signals` loads and validates `data/processed/market_signals_six_careers.json` on each call; it does **not** overwrite the data or modify recommendation scores.
- React's Careers page displays per-career comparisons or an explicit `insufficient_data` state. Synthetic demo careers show "No curated DOSM occupation comparison".
- React's Trends page displays all six sourced career signals **separately** from the existing synthetic skill-multiplier radar. An explicit **Refresh evidence** button makes a fresh request (`cache: 'no-store'`).
- Google/Supabase authentication, learning roadmaps, existing trends and matching are unchanged.

## API contract

`GET /api/market-signals` returns the **unchanged Member 4 JSON**. Important fields:

- `snapshot_id`, `generated_date`, `periods`, `geography`
- `can_directly_adjust_career_scores: false`
- `observed_count: 3`, `insufficient_data_count: 3` (current dataset)
- `career_signals`: exactly six items; each has `career_id`, `data_status`, `previous_period`, `latest_period`, `note`, `source_urls`, etc.
- Status `observed_comparison_available` has numeric `previous_job_offerings`, `latest_job_offerings`, `absolute_change`, and `percent_change`.
- Status `insufficient_data` has `null` for all observation fields, **not zeros**.
- If missing or invalid, returns **503** with a generic error; no invented fallback values.

Observed occupations in current Q1/Q2 snapshot: Software Developer, Accountants and Auditors, Advertising and Marketing Professionals.

Insufficient comparable occupation-level data: Data Professionals, Electrical Engineers, Nursing Professionals.

The base project's public catalog still contains **nine careers** (three synthetic demos, six curated), by design. Phase 6C does **not** silently apply the earlier curated-only catalog change.

## Windows: test and run

Run from the project root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe data_pipeline/validate_careers.py
.\.venv\Scripts\python.exe data_pipeline/test_import_trends_refresh.py
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Check `http://127.0.0.1:8000/api/market-signals` and `http://127.0.0.1:8000/docs`.

In another terminal:

```powershell
cd frontend
npm ci
npm run build
npm run dev
```

Open `http://localhost:5173`, choose a demo or Google login, run career analysis, and inspect **Careers** and **Trends**.

## How to demonstrate a source refresh accurately

1. **Manual source refresh, without fabrication:** When Member 4 has genuine newly checked DOSM figures, update the validated source CSV and documentation first. Rebuild with:

   ```powershell
   .\.venv\Scripts\python.exe data_pipeline/build_six_career_signals.py
   .\.venv\Scripts\python.exe data_pipeline/validate_careers.py
   ```

   Commit the source and regenerated JSON together after review. The builder currently targets **2026-Q1 and Q2**, so it must be extended by Member 4 before using future quarters.

2. The API reads the saved JSON on every request; the backend need not restart after snapshot file replacement.
3. On **Trends** or **Careers**, click **Refresh evidence**; browser fetch uses `cache: 'no-store'`. Observe the new snapshot; skill-readiness scores do **not** change.
4. For an automated **synthetic mechanism test only**, run:

   ```powershell
   .\.venv\Scripts\python.exe -m pytest tests/backend/test_market_signals_integration.py -q
   ```

   `test_source_csv_rebuild_propagates_to_endpoint_without_touching_matching` uses a **temporary CSV copy**, changing Software Developer Q2 from 19,899 to **19,999 for the test only**. It rebuilds to a temp JSON, checks the API, checks scores remain identical, and leaves official source files untouched. **Never present that 19,999 example as a DOSM observation.**

### Member 1 browser acceptance

- [ ] React production build passes locally.
- [ ] Trends shows three observed careers with exact values / source links and three `insufficient_data` cards with no fake percentages.
- [ ] Careers shows the corresponding market observation below each curated matching card; demo careers do not show fabricated source evidence.
- [ ] Switching light/dark mode and mobile layout keeps the cards readable.
- [ ] Simulated API failure displays one clear retry callout; matching and roadmap functions still work.
- [ ] Refresh evidence reads the newly saved JSON (without browser cache), and displayed percentages remain **separate** from readiness scores.
- [ ] Source links open the original DOSM pages. The app never describes market trends as proof of AI causation.

### Member 2 acceptance

- [ ] `GET /api/market-signals` is present in `/docs`, returns HTTP 200.
- [ ] Missing/corrupted snapshot gives HTTP 503 with no invented data.
- [ ] Exactly six role IDs, three observed and three insufficient in current snapshot.
- [ ] `POST /api/analyze` before/after market fetch is byte-for-byte equivalent JSON for a fixed profile.
- [ ] Existing Supabase, RunPod, `trends.json`, scores and scenario behavior are unchanged.
- [ ] Source CSV -> build -> snapshot -> API regression test passes.

## Boundaries and honest limitations

The dataset measures **online job offerings, not unique vacancies or employment totals**. Two quarterly measurements do not establish a persistent trend, and cannot attribute any change to AI. Missing data is not evidence of absent career opportunities. No career-level percentages are inserted into `trends.json` or used to change skill weights. The system **does not fetch new DOSM releases automatically**; 'Refresh evidence' rereads the latest locally published snapshot, not the DOSM website.

The full frontend build must be run on a machine with npm registry access: this packaging environment could parse TS/TSX syntax but could not install Vite/React dependencies. Do not merge until `npm run build` and browser acceptance are successful.
