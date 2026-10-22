#!/usr/bin/env bash
# Install exact lockfile dependencies, then emit frontend/dist for FastAPI.
set -euo pipefail
cd "$(dirname "$0")/../frontend"
npm ci --include=dev --no-audit --no-fund
npm run build
if [[ ! -f dist/index.html ]]; then
  echo 'ERROR: Vite build did not produce frontend/dist/index.html' >&2
  exit 1
fi
