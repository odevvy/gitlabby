# v0.1.48: the issue view's label editor and comments are their own files
# (IssueLabels.qml, IssueComments.qml); IssueView.qml keeps the state and the
# board-fetch calls. Both get the IssueView as owner; its labelFilter and box
# are theirs; the editor opens and closes, picks and Done reach IssueView; the
# thread shows; Ctrl+Enter posts the box's text.
# Usage: run148.py <src> [issue.png]
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
ALL = []
def ok(n, c, e=""): ALL.append(bool(c)); h.ok(n, c, e)
h = Harness(sys.argv[1], {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": "group/app", "defaultCollapsed": [], "boardStates": {}, "refreshIntervalSec": 60})
h.ev("panel.availableCardHeight = 1000"); h.ev("panel.contentWidth = 790")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(60)
iw = h.cls("IssueView"); ic = h.ctx_of(iw); iev = lambda code: h.ev(code, ic, iw)
le, cm = iev("labelEditor"), iev("comments")
ok("W1 the editor and the comments are IssueLabels and IssueComments inside the issue view",
   le.metaObject().className().startswith("IssueLabels") and cm.metaObject().className().startswith("IssueComments") and iev("labelEditor.owner === view && comments.owner === view"))
ok("W2 labelFilter is the editor's filter field, box the comments' text area",
   iev("labelFilter === labelEditor.field && labelFilter !== null && box === comments.box && box !== null && box.toString().indexOf('TextArea') === 0"), iev("box.toString()"))
h.ev("root.openIssue(root.columns[1].issues[0])"); h.spin(80)
ISSUE = {"iid": 2, "title": "Header palette button", "state": "opened", "labels": ["todo", "frontend"], "url": "https://gitlab.com/group/app/-/issues/2",
         "description": "Hovering shows Background.", "author": "o_devvy", "milestone": "", "assignees": [], "createdAt": "2026-10-29T12:00:00Z", "updatedAt": "2026-10-29T12:00:00Z"}
h.answer("issue", {"state": "ready", "message": "", "issue": ISSUE}); h.spin(60)
NOTES = [{"id": 1, "body": "First note", "createdAt": "2026-10-30T12:00:00Z", "author": {"username": "api", "name": "API"}},
         {"id": 2, "body": "Second note", "createdAt": "2026-10-30T13:00:00Z", "author": {"username": "o_devvy", "name": "odevvy"}}]
h.answer("notes", {"state": "ready", "message": "", "iid": 2, "more": False, "notes": NOTES}); h.spin(80)
texts = lambda: [it.property("text") for it in h.visible(lambda it: it.metaObject().className().startswith("BoardText"))]
ok("C1 the thread shows: the count and both notes", "Comments · 2" in texts() and "First note" in texts() and "Second note" in texts(), [t for t in texts() if "ote" in str(t) or "Comments" in str(t)])
ok("C2 the box opens once the issue and notes are in", iev("view.loaded && box.enabled"))
ok("E0 the editor starts closed", not le.isVisible())
iev("view.editLabels()"); h.spin(60)
ok("E1 Edit labels opens the editor and asks for the project's labels", le.isVisible() and h.running("labels") != [], h.running())
LABELS = [{"name": n, "color": c, "textColor": None} for n, c in [("bug", "#dc2626"), ("docs", "#0ea5e9"), ("frontend", "#16a34a")]]
h.answer("labels", {"state": "ready", "message": "", "labels": LABELS, "status": []}); h.spin(80)
ok("E2 the labels in: the filter has the keys", iev("labelFilter.activeFocus && view.typing"))
h.ev("labelPicker.picked('bug')", h.ctx_of(le), le); h.spin(40)
ok("E3 a pick reaches IssueView: one relabel --add bug", h.running("relabel") and h.running("relabel")[0][-2:] == ["--add", "bug"], h.running())
h.answer("relabel", {"state": "ready", "message": "", "labels": ["todo", "frontend", "bug"]}); h.spin(60)
h.click(h.ev("doneButton", h.ctx_of(le), le)); h.spin(60)
ok("E4 Done closes the editor (IssueView.doneEditing)", not iev("view.editing") and not le.isVisible())
h.stop_all()
iev("view.focusBox()"); h.spin(30)
for ch in "Thanks": h.key(getattr(Qt, "Key_" + ch.upper()), ch)
ok("P1 typing goes into the box", iev("box.text") == "Thanks" and iev("view.typing"), iev("box.text"))
for typ in (QEvent.KeyPress, QEvent.KeyRelease): QGuiApplication.sendEvent(h.win, QKeyEvent(typ, Qt.Key_Return, Qt.ControlModifier, "\r"))
h.spin(60)
ok("P2 Ctrl+Enter posts the box's text: board-fetch comment, the text on stdin", h.running("comment") and h.ev("(function(){ var p = " + h.PROCS + ".filter(function(p){ return p.running && p.command[1] === 'comment' })[0]; return p ? p.written.join('') : '' })()") == "Thanks", h.running())
if len(sys.argv) > 2: h.grab_card(sys.argv[2])
print("passed %d failed %d" % (sum(ALL), len(ALL) - sum(ALL)))
h.finish()
