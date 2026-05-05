#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON:-python3}"

echo "==> Backend tests"
cd "$ROOT_DIR/services/api"
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
  "$PYTHON_BIN" -m venv .venv
  # shellcheck source=/dev/null
  source .venv/bin/activate
  PYTHON_BIN="python"
fi
"$PYTHON_BIN" -m pip install -e ".[dev]"
pytest

echo "==> Frontend checks"
cd "$ROOT_DIR/apps/web"
npm install
npm run typecheck
npm run build

echo "==> Local validation finished"
