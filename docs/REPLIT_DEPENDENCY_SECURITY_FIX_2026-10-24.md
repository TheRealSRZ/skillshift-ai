# SkillShift AI: Replit dependency-security fix — 24 October 2026

## Scope and evidence

Replit's screenshot reports 18 issues across four package families, not 18 unique application-code flaws:

| Detected package | Reported version | Remediation floor | Application usage |
|---|---:|---:|---|
| certifi | 2026.7.22 | 2026.10.23 | Indirect dependency of requests/httpx; explicitly secured in `requirements.txt` |
| httpx2 | 2.9.1 | 2.16.0 | **Not** declared or imported by the application; distinct from `httpx` |
| httpcore2 | 2.9.1 | 2.16.0 | **Not** declared or imported by the application; distinct from `httpcore` |
| Pygments | 2.9.0 | 2.20.0 | **Not** a direct application dependency; may be installed by editor/test tooling |

The critical certifi advisory GHSA-6q48-6c7w-9gw2 concerns the compromised emSign certificate authority. `certifi>=2026.10.19` is fixed; the later `2026.10.23` is used here. HTTPX2 has published 2026 HTTP/2, SSE, decompression and WebSocket advisories; at least 2.12.0 fixed those, and 2.16.0 is a later stable release. HTTPCORE2 was upgraded in lockstep with HTTPX2. Pygments 2.20.0 is a later non-vulnerable release.

**Key distinction:** this repository declares `httpx`, NOT `httpx2`. We do not install `httpx2` or `httpcore2` merely to satisfy a scanner. The repair script updates an existing installed package only. If absent, the script leaves it absent.

## Exactly what changed

1. `requirements.txt`: added a minimum patched `certifi>=2026.10.23`.
2. `.replit`: publish build now runs `bash scripts/build_replit.sh` (previously only the frontend build).
3. `scripts/build_replit.sh`: installs backend Python requirements, checks/upgrades vulnerable **existing** versions of four Replit-scanned packages, and builds React.
4. `scripts/replit_dependency_security.py`: reports installed versions with `--check`; with `--upgrade`, updates outdated packages while **not introducing** optional httpx2, httpcore2 or Pygments if absent.
5. Added five tests and updated the deployment wiring regression test. All existing app endpoints and business logic remain unchanged.

## Apply to the Replit development workspace

After pulling the GitHub commit into Replit, open its **Shell** from the project root:

```bash
python -m pip install -r requirements.txt
python scripts/replit_dependency_security.py --check
```

If the report shows outdated packages (the checker intentionally exits 1):

```bash
python scripts/replit_dependency_security.py --upgrade
python scripts/replit_dependency_security.py --check
python -m pip check
```

The `--upgrade` command requires access to PyPI and working permissions to update the Python environment. It does **not** touch your Supabase or RunPod secrets. For diagnosis:

```bash
python -m pip show certifi httpx httpx2 httpcore2 Pygments
python -m pip list --format=freeze | grep -Ei '^(certifi|httpx2?|httpcore2?|pygments)=='
```

If `pip check` reports dependency incompatibilities, **do not** delete packages or force-install incompatible versions. Open the offending dependency details in Replit or consider a fresh isolated app environment. Security scans of the workspace and scans of the production build may assess different Python environments.

## Publish to Replit

1. In GitHub, merge/push the updated files to the branch Replit tracks.
2. In Replit, use **Tools → Git → Pull**, or Shell: `git status`, then `git pull --ff-only origin main`. If Replit has local changes, commit or safely back them up before pulling. Do not reset blindly.
3. Check `.replit` includes `scripts/build_replit.sh` as the deployment build.
4. Review Publishing → deployment secrets (`APP_ENV=production`, exact `ALLOWED_HOSTS`, public Supabase Vite build values, private Supabase service-role key). Do not put credentials in Git.
5. Click **Republish**. Publishing creates a new deployed snapshot; a GitHub push alone is not a guaranteed automatic update of the running website.
6. Verify `https://YOUR-APP.replit.app/api/health`, profile/roadmap/What-If, Supabase login, and Replit's Security Scans. Confirm the new **installed** versions, not just the source files.

## What has and has not been verified

- Baseline: 160/160 Python tests passed before changes.
- Updated: 165/165 Python tests passed, including five additional dependency-upgrade guard tests.
- Shell syntax validated with `bash -n`; Python module compilation passed.
- Replit scanner findings and upstream patched versions were checked against public package advisories.
- **Not performed here:** updating packages in your actual Replit runtime, running its scanner after an upgrade, resolving PyPI packages in a fresh networked runtime, or testing the live published URL. This environment cannot inspect your Replit environment or its secrets.
- Our test suite does not prove all dependencies are vulnerability-free. Existing GitHub Actions runs `pip-audit` for Python and `npm audit` for frontend production dependencies. Check those results after merging.

## Official/public references

- certifi security advisory: https://github.com/certifi/python-certifi/security/advisories/GHSA-6q48-6c7w-9gw2
- certifi patched release: https://pypi.org/project/certifi/2026.10.23/
- HTTPX2 security advisories: https://github.com/pydantic/httpx2/security
- HTTPX2 release: https://pypi.org/project/httpx2/2.16.0/
- HTTPCORE2 release: https://pypi.org/project/httpcore2/2.16.0/
- Pygments versions: https://pypi.org/project/Pygments/
- Replit Git integration: https://docs.replit.com/learn/projects-and-artifacts/version-control
- Replit publishing controls: https://docs.replit.com/references/publishing/monitoring-a-deployment
