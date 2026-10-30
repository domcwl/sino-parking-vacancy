#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export SINO_API_TOKEN="${SINO_API_TOKEN:-}"
if [[ -z "$SINO_API_TOKEN" && -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi
exec python -m uvicorn main:app --host 0.0.0.0 --port "${PORT:-8765}"
