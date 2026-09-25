#!/usr/bin/env bash
# Everything CI runs, on every interpreter CI runs it on. Run this before pushing.
set -uo pipefail
cd "$(dirname "$0")"
status=0
for python in "$@"; do
  name="$("$python" -V 2>&1)"
  printf '\n=== %s ===\n' "$name"
  PYTHONPATH=src "$python" -m pytest tests -q || status=1
  PYTHONPATH=src "$python" -m runson.cli --repo . --quiet || status=1
done
exit $status
