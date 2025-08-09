#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [ ! -d .venv ]; then
  echo "[dev] venv not found, running setup..."
  bash scripts/setup.sh
fi

# shellcheck disable=SC1091
source .venv/bin/activate
export PYTHONPATH="$PROJECT_ROOT"

HOST="0.0.0.0"
PORT="8000"

if [ "${1:-}" != "" ]; then
  PORT="$1"
fi

echo "[dev] Starting server at http://${HOST}:${PORT}"
exec uvicorn app.main:app --reload --host "$HOST" --port "$PORT"