#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/backend"
if [ ! -f .venv/bin/python ]; then python3 -m venv .venv; fi
source .venv/bin/activate
python -m pip install -r requirements-agent.txt
printf '\nVenture Intelligence starting at http://localhost:8000\nPress Ctrl+C to stop.\n'
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
