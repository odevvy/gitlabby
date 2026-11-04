#!/bin/bash
# Every harness test against a plugin dir. Usage: all.sh [plugin-dir]
# (default: this checkout). PYTHON: an interpreter with PySide6 (python3).
# The tests are independent (each loads its own copy in a temp dir), so they
# run HARNESS_JOBS at a time (default: the CPU count, at most 4); the report
# keeps the file order.
H=$(cd "$(dirname "$0")" && pwd); S=${1:-$H/../..}
jobs=${HARNESS_JOBS:-$(( $(nproc 2>/dev/null || echo 1) < 4 ? $(nproc 2>/dev/null || echo 1) : 4 ))}
o=$(mktemp -d); trap 'rm -rf "$o"' EXIT
export H S o
printf '%s\0' "$H"/tests/*.py | xargs -0 -P "$jobs" -I{} bash -c '
  t={}; n=$(basename "$t")
  out=$("${PYTHON:-python3}" "$t" "$S" 2>&1); rc=$?
  { echo "== $n $(grep -E "^passed" <<<"$out")"; grep -E "^FAIL|JSERR|LOAD FAILED|Traceback|Error" <<<"$out" | head -10; } > "$o/$n.log"
  [[ $rc == 0 ]] || : > "$o/$n.failed"'
rc=0
for t in "$H"/tests/*.py; do n=$(basename "$t"); cat "$o/$n.log"; [[ -e $o/$n.failed ]] && rc=1; done
exit $rc
