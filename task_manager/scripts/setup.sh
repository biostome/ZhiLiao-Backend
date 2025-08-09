#!/usr/bin/env bash
set -euo pipefail

# Resolve project root (one level up from scripts directory)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

PY=python3

if ! command -v "$PY" >/dev/null 2>&1; then
  echo "python3 not found. Please install Python 3 first." >&2
  exit 1
fi

if [ ! -d .venv ]; then
  echo "[setup] Creating virtualenv .venv";
  "$PY" -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip >/dev/null 2>&1 || true
pip install -r requirements.txt

echo "[setup] Done. Activate with: source .venv/bin/activate"