#!/bin/bash
# Mutation checks: each line of <spec> (tab-separated: name, file, from, to, sh|qml|node)
# replaces the first `from` with `to` in a copy of <plugin-dir> and runs
# tests/run.sh (sh), tests/logic.test.js (node) or the harness test <qml-test> (qml). A mutation must make
# its test fail. \n in from/to is a newline. Usage: mutate.sh <plugin-dir> <spec> <qml-test>
# PYTHON: an interpreter with PySide6 (python3).
S=$(cd "$1" && pwd); spec=$2; qt=$3; survived=0
w=$(mktemp -d); trap 'rm -rf "$w"' EXIT
while IFS=$'\t' read -r name file from to kind; do
  [[ -z $name || $name == \#* ]] && continue
  rm -rf "$w/p"; cp -a "$S" "$w/p"; rm -rf "$w/p/.git"
  F="$from" T2="$to" python3 -c "
import os; p='$w/p/$file'; s=open(p).read(); f=os.environ['F'].replace('\\\\n','\n'); t=os.environ['T2'].replace('\\\\n','\n')
assert f in s; open(p,'w').write(s.replace(f,t,1))" 2>/dev/null || { echo "?? $name: pattern not found"; survived=1; continue; }
  if [[ $kind == sh ]]; then out=$(bash "$w/p/tests/run.sh" 2>&1 | tail -1)
  elif [[ $kind == node ]]; then out=$(cd "$w/p" && node --test tests/logic.test.js 2>&1 | sed -n 's/^ℹ fail \([0-9]*\)$/failed \1/p')
  else out=$("${PYTHON:-python3}" "$qt" "$w/p" 2>&1 | grep -E '^passed|LOAD FAILED|Traceback' | head -1); fi
  if [[ $out == *"failed 0"* ]]; then echo "SURVIVED $name: $out"; survived=1; else echo "killed $name: ${out:-crashed}"; fi
done <"$spec"
exit $survived
