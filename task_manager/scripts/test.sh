#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [ ! -d .venv ]; then
  echo "[test] venv not found, running setup..."
  bash scripts/setup.sh
fi

# shellcheck disable=SC1091
source .venv/bin/activate
export PYTHONPATH="$PROJECT_ROOT"

pytest -q -W ignore::DeprecationWarning "$@"