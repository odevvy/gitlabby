#!/bin/bash
# Every harness test against a plugin dir. Usage: all.sh [plugin-dir]
# (default: this checkout). PYTHON: an interpreter with PySide6 (python3).
H=$(cd "$(dirname "$0")" && pwd); S=${1:-$H/../..}; rc=0
for t in "$H"/tests/*.py; do
  out=$("${PYTHON:-python3}" "$t" "$S" 2>&1) || rc=1
  echo "== $(basename "$t") $(grep -E '^passed' <<<"$out")"
  grep -E '^FAIL|JSERR|LOAD FAILED|Traceback|Error' <<<"$out" | head -10
done
exit $rc
