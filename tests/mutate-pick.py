#!/usr/bin/env python3
"""Pick the mutation rows a change can affect (mutate.sh --changed).

Usage: mutate-pick.py <plugin-dir> <base> <spec>...  Prints the picked rows.
A row is picked when, against git <base> (commits and the work tree):
- it is a canary (canary-*, must survive: mutate.sh checks the checks);
- its entry in mutations/sh-sections.map is new or changed;
- the row itself is new or changed in its spec;
- its `from` text (where mutate.sh puts the mutant: the first match) touches a
  changed line of its file, or is gone from it (mutate.sh then says so);
- its test changed: the view test file (qml), tests/logic.test.js (node), or
  for sh rows the run.sh sections that mutations/sh-sections.map gives it
  (a row without sections: any change to run.sh).
A change elsewhere that shifts a row's behavior is not seen here; the full
sweep (mutate.sh with no --changed, weekly or before a milestone) covers it.
"""
import os, re, subprocess, sys

src, base, specs = sys.argv[1], sys.argv[2], sys.argv[3:]


def changed_lines():
    """{path: set of changed line numbers in the work tree}; a deletion marks the
    lines on both sides of it."""
    out = subprocess.run(["git", "-C", src, "diff", "-U0", "--no-color", "--relative", base, "--", "."],
                         capture_output=True, text=True, check=True).stdout
    lines, path = {}, None
    for l in out.splitlines():
        if l.startswith("+++ "):
            path = None if l == "+++ /dev/null" else l[6:]
            if path is not None:
                lines.setdefault(path, set())
        elif l.startswith("--- a/"):
            lines.setdefault(l[6:], set())  # a deleted file counts as changed
        elif l.startswith("@@") and path:
            start, count = re.match(r"@@ -\S+ \+(\d+)(?:,(\d+))? @@", l).groups()
            start, count = int(start), 1 if count is None else int(count)
            lines[path] |= set(range(start, start + count)) if count else {start, start + 1}
    return lines


def text(path):
    try:
        return open(f"{src}/{path}").read()
    except OSError:
        return None


def span(path, needle):
    """Line numbers of the first `needle` in path, or None when it is gone."""
    s = text(path)
    if s is None or needle not in s:
        return None
    first = s[: s.index(needle)].count("\n") + 1
    return set(range(first, first + needle.count("\n") + 1))


def sections():
    """{section id: its run.sh line numbers}, and the lines before the first one."""
    out, cur, pre = {}, None, set()
    for n, l in enumerate((text("tests/run.sh") or "").splitlines(), 1):
        if l.startswith("# --- "):
            cur = l.split()[2].rstrip(":")
        (out.setdefault(cur, set()) if cur else pre).add(n)
    return out, pre


ch = changed_lines()
secs, pre = sections()
smap, remapped = {}, set()
mapch = ch.get("tests/mutations/sh-sections.map", set())
for n, l in enumerate((text("tests/mutations/sh-sections.map") or "").splitlines(), 1):
    if "\t" in l and not l.startswith("#"):
        name, ids = l.split("\t", 1)
        smap.setdefault(name, ids.split())
        if n in mapch:
            remapped.add(name)
run_sh = ch.get("tests/run.sh")
for spec in specs:
    rel = os.path.relpath(os.path.abspath(spec), os.path.abspath(src))
    for n, line in enumerate(open(spec).read().splitlines(), 1):
        if not line or line.startswith("#"):
            continue
        name, file, frm, _to, kind, test = (line.split("\t") + [""] * 6)[:6]
        picked = name.startswith("canary-") or name in remapped or n in ch.get(rel, ())
        if not picked and file in ch:
            where = span(file, frm.replace("\\n", "\n"))
            picked = where is None or bool(where & ch[file])
        if not picked and kind == "sh" and run_sh is not None:
            ids = smap.get(name)
            picked = (not ids or bool(run_sh & pre) or any(i not in secs for i in ids)  # unknown id: pick it
                      or any(run_sh & secs[i] for i in ids))
        elif not picked and kind != "sh":
            picked = f"tests/{test}" in ch
        if picked:
            print(line)
