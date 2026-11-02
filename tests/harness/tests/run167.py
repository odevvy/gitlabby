# v0.1.67: calm loading. The picker's spinner row (LoadingRow) is the one
# loading look: the issue view shows it once, only after 250 ms, where the
# description goes and then under Comments, with no bar and no other
# "Loading…"; its state and actions keep their place. A refresh you ask for
# says "Updating…" (at least half a second); the timer's keeps the time.
# Settings, Shortcuts and the issue view fade their bottom edge while there
# is more below. Usage: run167.py <src>
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
h = Harness(sys.argv[1], {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": "group/app", "defaultCollapsed": [], "boardStates": {}, "refreshIntervalSec": 60})
h.ev("panel.availableCardHeight = 900; panel.availableCardWidth = 1460")
cls_is = lambda it, n: it.metaObject().className().startswith(n)
named = lambda n: [it for it in h.walk() if it.objectName() == n]
shown = lambda n: [it for it in named(n) if it.isVisible()]
rows = lambda: h.visible(lambda it: cls_is(it, "LoadingRow"))
spinners = lambda: h.visible(lambda it: cls_is(it, "Spinner"))
loadings = lambda: [it for it in h.visible(lambda it: cls_is(it, "BoardText")) if "Loading" in str(it.property("text") or "")]
same = lambda a, c: abs(a.redF() - c.redF()) < 0.01 and abs(a.greenF() - c.greenF()) < 0.01 and abs(a.blueF() - c.blueF()) < 0.01
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(200)
# --- the picker's loading row, now LoadingRow -----------------------------------------------
h.ev("root.openPicker()"); h.spin(120)
pl = shown("pickerLoading")
h.ok("L1 picker loading: one LoadingRow, its Spinner turning, 'Loading…'", h.running("projects") != [] and len(pl) == 1 and cls_is(pl[0], "LoadingRow") and len(spinners()) == 1 and [t.property("text") for t in loadings()] == ["Loading…"])
lbl = loadings()[0] if loadings() else None
h.ok("L2 ...dim and italic, the spinner just left of it", lbl is not None and len(spinners()) == 1 and lbl.property("font").italic() and same(lbl.property("color"), h.ev("root.dim"))
     and spinners()[0].mapToScene(QPointF(spinners()[0].width(), 0)).x() <= lbl.mapToScene(QPointF(0, 0)).x())
h.answer("projects", {"state": "error", "message": "GitLab said no."}); h.spin(80)
h.ok("L3 a failed list: the same row, the reason, no spinner", len(shown("pickerLoading")) == 1 and spinners() == [] and shown("pickerLoading")[0].property("text") == "GitLab said no.")
h.ev("root.back()"); h.spin(80)
# --- the issue view while loading -------------------------------------------------------------
ISSUE = {"iid": 2, "title": "Second issue", "state": "opened", "labels": ["todo", "bug"], "url": "https://gitlab.com/group/app/-/issues/2",
         "description": "Make the board faster.", "author": "dev1", "milestone": "", "assignees": [], "createdAt": "2026-10-20T12:00:00Z", "updatedAt": "2026-10-29T12:00:00Z"}
NOTES = {"state": "ready", "message": "", "iid": 2, "more": False, "notes": [{"author": {"username": "dev2"}, "body": "On it.", "createdAt": "2026-10-29T12:00:00Z"}]}
iv = h.cls("IssueView"); ic = h.ctx_of(iv); iev = lambda c: h.ev(c, ic, iv)
card = [i for c in h.ev("root.columns") for i in c["issues"] if i["iid"] == 2][0]
card["labels"] = card.get("labels") or ["todo"]; ISSUE["labels"] = list(card["labels"]) + ["bug"]
chip_x = lambda: [it.mapToScene(QPointF(0, 0)).x() for it in h.visible(lambda it: cls_is(it, "LabelChip") and it.property("name") == card["labels"][0])]
h.ev("root.openIssue(%s)" % json.dumps(card)); h.spin(100)
nodesc = lambda: [t for t in h.visible(lambda it: cls_is(it, "BoardText")) if t.property("text") == "No description."]
h.ok("I1 the first 250 ms: nothing says loading (no row, no spinner, no 'Loading…', no 'No description.')", rows() == [] and spinners() == [] and loadings() == [] and nodesc() == [], [t.property("text") for t in loadings()])
h.ok("I2 the comment box keeps its own words, locked", iev("box.placeholderText") == "Write a comment…  (Ctrl+Enter to post)" and iev("box.enabled") is False)
x0 = chip_x()
h.ok("I3 the state and both actions keep their place, unseen", len(shown("editAction")) == 1 and shown("editAction")[0].opacity() == 0 and len(shown("stateAction")) == 1 and shown("stateAction")[0].opacity() == 0)
if shown("editAction"): h.click(shown("editAction")[0])
h.spin(40)
h.ok("I4 ...and do nothing until the issue is in", iev("view.editing") is False)
h.spin(250)
h.ok("I5 past 250 ms: one LoadingRow where the description goes, one spinner, one 'Loading…'", [r.objectName() for r in rows()] == ["issueLoading"] and len(spinners()) == 1 and len(loadings()) == 1, [r.objectName() for r in rows()])
h.answer("issue", {"state": "ready", "message": "", "issue": ISSUE}); h.spin(80)
h.ok("I6 the description is in: the row moves under Comments (still one)", [r.objectName() for r in rows()] == ["notesLoading"] and len(spinners()) == 1 and len(loadings()) == 1, [r.objectName() for r in rows()])
h.answer("notes", NOTES); h.spin(250)
h.ok("I7 all in: no row, no spinner; the state and actions show", rows() == [] and spinners() == [] and shown("editAction")[0].opacity() == 1 and shown("stateAction")[0].opacity() == 1)
h.ok("I8 nothing jumped: the labels sit where they were", x0 != [] and chip_x() == x0, (x0, chip_x()))
h.ok("I9 'No description.' and errors still show when they apply", not [t for t in h.visible(lambda it: cls_is(it, "BoardText")) if t.property("text") == "No description."])
h.ev("root.back()"); h.spin(60)
# A fast answer: nothing in between.
h.ev("root.openIssue(%s)" % json.dumps(card)); h.spin(60)
h.ok("I10a reopened (its description from memory): still nothing in the first 250 ms", rows() == [] and spinners() == [])
h.answer("issue", {"state": "ready", "message": "", "issue": ISSUE}); h.answer("notes", NOTES); h.spin(20)
seen = []
for _ in range(8): h.spin(40); seen += rows() + spinners()
h.ok("I10 a quick load (under 250 ms) never shows the row", seen == [])
h.ev("root.back()"); h.spin(60)
# The description in quickly, the comments slow: still nothing before 250 ms.
other = [i for c in h.ev("root.columns") for i in c["issues"] if i["iid"] != 2][0]
h.ev("root.openIssue(%s)" % json.dumps(other)); h.spin(40)
h.answer("issue", {"state": "ready", "message": "", "issue": dict(ISSUE, iid=other["iid"], title=other["title"])}); h.spin(60)
h.ok("I12 description in fast, comments still out: no row before 250 ms", rows() == [] and spinners() == [])
h.spin(250)
h.ok("I13 ...then the one row under Comments", [r.objectName() for r in rows()] == ["notesLoading"])
h.answer("notes", dict(NOTES, iid=other["iid"])); h.spin(100)
h.ev("root.back()"); h.spin(60)
# A failed issue: the reason, no row.
h.ev("root.openIssue(%s)" % json.dumps(card)); h.spin(300)
h.answer("issue", {"state": "error", "message": "GitLab said no."}); h.answer("notes", NOTES); h.spin(120)
h.ok("I11 a failed issue: its reason, no loading row", rows() == [] and [t for t in h.visible(lambda it: cls_is(it, "BoardText")) if t.property("text") == "GitLab said no."] != [])
h.ev("root.back()"); h.spin(60)
sys.exit(h.finish())
