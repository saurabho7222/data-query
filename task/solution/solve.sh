#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
INPUT_DB=${INPUT_DB:-/app/input.db}
OUTPUT_JSON=${OUTPUT_JSON:-/app/output.json}

exec python3 "$SCRIPT_DIR/solve.py" --input "$INPUT_DB" --output "$OUTPUT_JSON"
