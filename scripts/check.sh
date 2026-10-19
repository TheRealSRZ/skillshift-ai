#!/usr/bin/env bash
set -euo pipefail
python -m pytest -q
(cd frontend && npm run build)
