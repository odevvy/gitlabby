#!/bin/bash
# Mutation checks. Each line of <spec> (tab-separated: name, file, from, to, kind, test)
# replaces the first `from` with `to` in a copy of <plugin-dir> and runs the row's
# test, a path under tests/: run.sh (kind sh), logic.test.js (kind node) or a
# harness test such as harness/tests/run141.py (kind qml). A mutation must make
# its test fail. \n in from/to is a newline. Lines starting with # are notes.
# Usage: mutate.sh <plugin-dir> <spec>...
# PYTHON: an interpreter with PySide6 (python3).
# mutate.sh --check <plugin-dir> <spec>...: only that every row's `from` is still
# in its file and its test exists (no test runs; a second or two), so a row can't
# go stale unnoticed. Prints "stale <spec> <name>" or "notest <spec> <name>".
if [[ $1 == --check ]]; then
  S=$(cd "$2" && pwd); shift 2; bad=0
  for spec in "$@"; do
    while IFS= read -r line; do
      IFS=$'\x1f' read -r name file from _ kind test <<<"${line//$'\t'/$'\x1f'}"
      [[ -z $name || $name == \#* ]] && continue
      src=$(cat "$S/$file" 2>/dev/null) || src=""
      [[ $src == *"${from//\\n/$'\n'}"* ]] || { echo "stale $(basename "$spec") $name"; bad=1; }
      case $kind:$test in
        sh:run.sh|node:logic.test.js) ;;
        qml:harness/tests/*.py) [[ -f $S/tests/$test ]] || { echo "notest $(basename "$spec") $name"; bad=1; } ;;
        *) echo "notest $(basename "$spec") $name"; bad=1 ;;
      esac
    done <"$spec"
  done
  exit $bad
fi
S=$(cd "$1" && pwd); shift; survived=0
w=$(mktemp -d); trap 'rm -rf "$w"' EXIT
for spec in "$@"; do
while IFS= read -r line; do
  # \x1f, not tab, splits: a tab IFS would merge an empty `to` with the next column
  IFS=$'\x1f' read -r name file from to kind test <<<"${line//$'\t'/$'\x1f'}"
  [[ -z $name || $name == \#* ]] && continue
  rm -rf "$w/p"; cp -a "$S" "$w/p"; rm -rf "$w/p/.git"
  F="$from" T2="$to" python3 -c "
import os; p='$w/p/$file'; s=open(p).read(); f=os.environ['F'].replace('\\\\n','\n'); t=os.environ['T2'].replace('\\\\n','\n')
assert f in s; open(p,'w').write(s.replace(f,t,1))" 2>/dev/null || { echo "?? $name: pattern not found"; survived=1; continue; }
  case $kind:$test in
    sh:run.sh) out=$(bash "$w/p/tests/run.sh" 2>&1 | tail -1) ;;
    node:logic.test.js) out=$(cd "$w/p" && node --test tests/logic.test.js 2>&1 | sed -n 's/^ℹ fail \([0-9]*\)$/failed \1/p') ;;
    qml:harness/tests/*.py) out=$("${PYTHON:-python3}" "$S/tests/$test" "$w/p" 2>&1 | grep -E '^passed|LOAD FAILED|Traceback' | head -1) ;;
    *) echo "?? $name: no test for '$kind' '$test'"; survived=1; continue ;;
  esac
  if [[ $out == *"failed 0"* ]]; then echo "SURVIVED $name: $out"; survived=1; else echo "killed $name ($test): ${out:-crashed}"; fi
done <"$spec"
done
exit $survived
