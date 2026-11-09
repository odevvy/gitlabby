#!/bin/bash
# Mutation checks. Each line of <spec> (tab-separated: name, file, from, to, kind, test)
# replaces the first `from` with `to` in a copy of <plugin-dir> and runs the row's
# test, a path under tests/: run.sh (kind sh), logic.test.js (kind node) or a
# harness test such as harness/tests/run141.py (kind qml). A mutation must make
# its test fail. \n in from/to is a newline. Lines starting with # are notes.
# Usage: mutate.sh <plugin-dir> <spec>...
# PYTHON: an interpreter with PySide6 (python3). MUTATE_STOP=1: stop at the first
# survivor or broken row (exit 1), so a release hears of it in minutes.
# Rows named canary-* (mutations/canary.tsv) must survive, and an sh row counts as
# killed only when run.sh names the check that failed: so a check that fails for
# every mutant, or a crash, can't pass as kills.
# An sh row named in mutations/sh-sections.map (name, run.sh section ids) runs only
# those sections of run.sh (RUN_ONLY), about 3 s instead of the whole file.
# mutate.sh --check <plugin-dir> <spec>...: only that every row's `from` is still
# in its file and its test exists (no test runs; a second or two), so a row can't
# go stale unnoticed. Prints "stale <spec> <name>", "notest <spec> <name>", or
# "dup <spec> <name>" for a name another row already has.
# mutate.sh --changed <base> [--list] <plugin-dir> <spec>...: the per-release run. Only
# the rows the change since git <base> can affect (tests/mutate-pick.py: new or
# changed rows, rows whose code or test sections changed, the canaries); --list
# prints their names and runs nothing. Without --changed every row runs: the
# full sweep, which catches what the picking can't see (run it weekly and before
# a milestone; see README).
if [[ $1 == --changed ]]; then
  base=$2; shift 2; list=0; [[ $1 == --list ]] && { list=1; shift; }
  S=$(cd "$1" && pwd); shift
  sel=$(mktemp); trap 'rm -f "$sel"' EXIT
  python3 "$(dirname "$0")/mutate-pick.py" "$S" "$base" "$@" >"$sel" || { echo "?? not a git checkout or no $base"; exit 2; }
  if ((list)); then cut -f1 "$sel"; exit 0; fi
  echo "$(wc -l <"$sel") rows the change since $base can affect (mutate-pick.py)"
  bash "$0" "$S" "$sel"; exit
fi
if [[ $1 == --check ]]; then
  S=$(cd "$2" && pwd); shift 2; bad=0; declare -A named  # a name picks one row: two rows can't share it
  for spec in "$@"; do
    while IFS= read -r line; do
      IFS=$'\x1f' read -r name file from _ kind test <<<"${line//$'\t'/$'\x1f'}"
      [[ -z $name || $name == \#* ]] && continue
      [[ -n ${named[$name]:-} ]] && { echo "dup $(basename "$spec") $name"; bad=1; }; named[$name]=1
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
bad() { survived=1; [[ -z ${MUTATE_STOP:-} ]]; }  # false: stop now
declare -A clean  # run.sh sections -> yes or no: they pass on clean code
w=$(mktemp -d); trap 'rm -rf "$w"' EXIT
for spec in "$@"; do
while IFS= read -r line; do
  # \x1f, not tab, splits: a tab IFS would merge an empty `to` with the next column
  IFS=$'\x1f' read -r name file from to kind test <<<"${line//$'\t'/$'\x1f'}"
  [[ -z $name || $name == \#* ]] && continue
  rm -rf "$w/p"; cp -a "$S" "$w/p"; rm -rf "$w/p/.git"
  F="$from" T2="$to" python3 -c "
import os; p='$w/p/$file'; s=open(p).read(); f=os.environ['F'].replace('\\\\n','\n'); t=os.environ['T2'].replace('\\\\n','\n')
assert f in s; open(p,'w').write(s.replace(f,t,1))" 2>/dev/null || { echo "?? $name: pattern not found"; bad || break 2; continue; }
  case $kind:$test in
    sh:run.sh) only=$(awk -F'\t' -v n="$name" '$1 == n {print $2; exit}' "$S/tests/mutations/sh-sections.map" 2>/dev/null)
      if [[ -n $only && -z ${clean[$only]:-} ]]; then  # the sections pass on clean code, or the row gets the whole file
        RUN_ONLY=$only bash "$S/tests/run.sh" >/dev/null 2>&1 && clean[$only]=yes || { clean[$only]=no; echo "note: run.sh sections '$only' fail on clean code; their rows run the whole file"; }
      fi
      [[ -n $only && ${clean[$only]} == yes ]] || only=; test="run.sh${only:+ [$only]}"
      out=$(RUN_ONLY=$only RUN_FAILFAST=1 bash "$w/p/tests/run.sh" 2>&1 | tail -1) ;;
    node:logic.test.js) out=$(cd "$w/p" && node --test tests/logic.test.js 2>&1 | sed -n 's/^ℹ fail \([0-9]*\)$/failed \1/p') ;;
    qml:harness/tests/*.py) out=$("${PYTHON:-python3}" "$S/tests/$test" "$w/p" 2>&1 | grep -E '^passed|LOAD FAILED|Traceback' | head -1) ;;
    *) echo "?? $name: no test for '$kind' '$test'"; bad || break 2; continue ;;
  esac
  if [[ $name == canary-* ]]; then  # must survive (mutations/canary.tsv)
    if [[ $out == *"failed 0"* ]]; then echo "canary $name survived ($test)"; else echo "?? canary $name was killed ($test): ${out:-crashed}; a check fails every mutant"; bad || break 2; fi
  elif [[ $out == *"failed 0"* ]]; then echo "SURVIVED $name: $out"; bad || break 2
  elif [[ $kind == sh && $out != *"first: "* ]]; then echo "?? $name: run.sh failed without naming a check: ${out:-crashed}"; bad || break 2
  else echo "killed $name ($test): ${out:-crashed}"; fi
done <"$spec"
done
exit $survived
