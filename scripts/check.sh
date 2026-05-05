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
CHECK_DATABASE_URL="${CHECK_DATABASE_URL:-sqlite+pysqlite:///./.check.db}"
rm -f .check.db
DATABASE_URL="$CHECK_DATABASE_URL" alembic upgrade head
DATABASE_URL="$CHECK_DATABASE_URL" alembic downgrade -1
DATABASE_URL="$CHECK_DATABASE_URL" alembic upgrade head
pytest

echo "==> Frontend checks"
cd "$ROOT_DIR/apps/web"
npm install
npm run typecheck
npm run build

echo "==> Local validation finished"
