#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)

exec python3 "$REPO_ROOT/task/solution/solve.py" \
  --input "${INPUT_DB:-/app/input.db}" \
  --output "${OUTPUT_JSON:-/app/output.json}" \
  "$@"
