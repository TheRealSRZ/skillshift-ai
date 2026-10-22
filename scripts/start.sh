#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ "${REQUIRE_FRONTEND_BUILD:-false}" == "true" && ! -f frontend/dist/index.html ]]; then
  echo 'ERROR: frontend/dist is missing; run bash scripts/build_frontend.sh before deployment.' >&2
  exit 1
fi
PORT="${PORT:-8000}"
exec python -m uvicorn backend.main:app --host 0.0.0.0 --port "$PORT" --workers 1
