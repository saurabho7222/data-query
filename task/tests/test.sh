#!/bin/bash
set -euo pipefail

pytest /tests/test_outputs.py -rA
