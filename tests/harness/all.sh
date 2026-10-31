#!/bin/bash
# Every harness test against a plugin dir. Usage: all.sh <plugin-dir>
H=$(cd "$(dirname "$0")" && pwd); S=${1:?plugin dir}; rc=0
for t in "$H"/tests/*.py; do
  out=$("$H/../venv/bin/python" "$t" "$S" 2>&1) || rc=1
  echo "== $(basename "$t") $(grep -E '^passed' <<<"$out")"
  grep -E '^FAIL|JSERR|LOAD FAILED|Traceback|Error' <<<"$out" | head -10
done
exit $rc
