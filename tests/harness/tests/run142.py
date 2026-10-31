# v0.1.42: the issue view reuses the project's labels across its issues for 5
# minutes (one labels read, not one per issue opened); another project or an
# older list reads again; a failed read is not reused.
# Usage: run142.py <src>
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
h = Harness(sys.argv[1], {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": "group/app"})
ALL = []
def ok(n, c, e=""): ALL.append(bool(c)); h.ok(n, c, e)
LABELS = {"state": "ready", "message": "", "status": ["todo", "review"], "labels": [{"name": "bug", "color": "#dc2626", "textColor": None}, {"name": "ux", "color": "#6366f1", "textColor": None}]}
def open_issue(n):
    h.stop_all(); h.ev("root.showView('board')"); h.spin(40)
    h.ev("root.openIssue(root.columns[%d].issues[0])" % n); h.spin(80)
    row = h.ev("root.columns[%d].issues[0]" % n)
    h.answer("issue", {"state": "ready", "message": "", "issue": dict(row, description="", author="dev1", milestone="", assignees=[], createdAt="2026-10-20T12:00:00Z", updatedAt="2026-10-29T12:00:00Z")})
    h.answer("notes", {"state": "ready", "message": "", "iid": row["iid"], "more": False, "notes": []}); h.spin(60)
reads = lambda: len(h.running("labels"))
h.ev("root.opened = true"); h.spin(80); h.answer("board", BOARD)
ok("F0 two issues in two columns", h.ev("root.columns[0].issues.length") >= 1 and h.ev("root.columns[1].issues.length") >= 1)
open_issue(0); h.ev("issueView.editLabels()"); h.spin(60)
ok("L1 first issue: one labels read", reads() == 1)
h.answer("labels", LABELS); h.spin(60)
ok("L2 loaded", h.ev("issueView.labelsState") == "ready" and [l["name"] for l in h.ev("issueView.allLabels")] == ["bug", "ux"])
h.ev("issueView.doneEditing()"); h.spin(40)
open_issue(1); h.ev("issueView.editLabels()"); h.spin(60)
ok("L3 another issue, same project: no read, the labels are there", reads() == 0 and h.ev("issueView.labelsState") == "ready" and h.ev("issueView.editing") and len(h.ev("issueView.addable")) > 0, h.ev("issueView.addable"))
h.ev("issueView.doneEditing()"); h.ev("issueView.labelsAt = Date.now() - 301000")
h.ev("issueView.editLabels()"); h.spin(60)
ok("L4 older than 5 minutes: read again", reads() == 1)
h.answer("labels", {"state": "error", "message": "Could not load labels."}); h.spin(60)
h.ev("issueView.labelsAt = Date.now()")  # even with a recent time, an error is not reused
h.ev("issueView.doneEditing()"); h.ev("issueView.editLabels()"); h.spin(60)
ok("L5 a failed read is not reused", reads() == 1)
h.answer("labels", LABELS); h.spin(60); h.ev("issueView.doneEditing()")
h.ev("issueView.labelsFor = 'other/proj'")  # the labels in hand are another project's
h.ev("issueView.editLabels()"); h.spin(60)
ok("L6 labels of another project: read for this one", reads() == 1 and h.running("labels")[0][3] == "group/app", h.running("labels"))
print("passed", sum(ALL), "failed", len(ALL) - sum(ALL))
