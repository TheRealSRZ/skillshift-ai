#!/usr/bin/env bash
# Replit publishing needs *both* Python and the compiled React frontend.
# Install secure Python dependencies in the deployed Python environment.
set -euo pipefail
cd "$(dirname "$0")/.."

python -m pip install -r requirements.txt
# Only upgrade vulnerable httpx2/httpcore2/Pygments if Replit preinstalls them;
# none of those packages is required directly by SkillShift AI.
python scripts/replit_dependency_security.py --upgrade
bash scripts/build_frontend.sh
