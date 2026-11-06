# v0.1.46: Logic.js is a QML entry over logic/*.js. In the real QML engine every
# name is there and the functions that borrow from another module (use()) work,
# with the same answers node gets from logic/index.js.
# Usage: run146.py <src>
import sys, os, json, subprocess; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
src = sys.argv[1]
ALL = []
def ok(n, c, e=""): ALL.append(bool(c)); h.ok(n, c, e)
h = Harness(src, {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": "a/b"})
names = json.loads(subprocess.run(["node", "-e", "console.log(JSON.stringify(Object.keys(require(process.argv[1]))))", os.path.join(src, "logic", "index.js")], capture_output=True, text=True).stdout)
missing = h.ev("(function(){ return %s.filter(function(n){ return typeof Logic[n] === 'undefined' }) })()" % json.dumps(names))
ok("Q1 QML's Logic has every name node has (%d)" % len(names), len(names) > 90 and missing == [], missing)
# Calls that cross modules, compared with node.
CALLS = [
    ("pickKey", [{"kind": "label", "listId": 5}, 3]),
    ("bulkPlan", [[{"key": "label:5|3", "column": {"kind": "label", "listId": 5, "name": "todo"}, "row": {"iid": 3, "labels": ["todo"]}}], {"kind": "add", "label": "ux"}, "a/b", 7]),
    ("statusLabels", [["Doing"], [{"kind": "label", "name": "Review"}]]),
    ("inline", ["a <b> **c**"]),
    ("byline", [{"author": {"name": "A"}, "created_at": "2026-10-31T10:00:00Z"}, 1793440000000]),
    ("withBot", [{}, "a/b", {"name": "Spec", "label": "spec"}, ["spec"]]),
    ("mrsAnswer", [json.dumps({"state": "ready", "review": [{"iid": 1, "web_url": "https://x/1", "author": {"username": "u", "avatar_url": "javascript:x"}}], "mine": []})]),
    ("accessHint", ["", {"known": True, "level": 10, "scopes": ["api"]}, "a/b", "gitlab.com"]),
    ("withAlert", [{}, "a/b", "review", True]),
    ("notifyArgv", [{"headline": "t <x>", "body": "b & c", "url": "https://x"}]),
    ("alertEvents", [{"state": "ready", "project": "a/b", "columns": [{"kind": "label", "name": "in progress", "issues": [{"iid": 1, "labels": ["spec"]}]}]},
                     {"state": "ready", "project": "a/b", "columns": [{"kind": "label", "name": "in progress", "issues": []}]},
                     {"idle": True, "bots": {"a/b": {"bots": [{"name": "Spec", "label": "spec"}], "busyLists": ["in progress"]}}}]),
]
for name, args in CALLS:
    q = h.ev("JSON.stringify(Logic.%s.apply(null, %s))" % (name, json.dumps(args)))
    n = subprocess.run(["node", "-e", "const L=require(process.argv[1]); console.log(JSON.stringify(L[process.argv[2]].apply(null, JSON.parse(process.argv[3]))))", os.path.join(src, "logic", "index.js"), name, json.dumps(args)], capture_output=True, text=True).stdout.strip()
    ok("Q2 %s: same answer in QML and node" % name, q is not None and q == n and q not in ("undefined", "[]", "null", '""'), [q, n])
print("passed %d failed %d" % (sum(ALL), len(ALL) - sum(ALL)))
h.finish()
