# v0.1.20: the issue view's label editor. Status labels are never editable or
# offered; one add or remove at a time through board-fetch relabel.
# v0.1.20b: controls never look like labels: the label row holds only labels,
# "Edit labels" is a text action under it, Done a square button by the filter.
# Usage: run120.py <src> [closed.png open.png error.png]
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
pngs = sys.argv[2:5]
h = Harness(sys.argv[1], {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": "group/app"})
def chips(label=None):
    found = sorted(h.visible(lambda it: True and it.metaObject().className().startswith(("Pill", "LabelChip")) and it.property("label") is not None),
                   key=lambda it: (round(it.mapToScene(QPointF(0, 0)).y()), it.mapToScene(QPointF(0, 0)).x()))
    return [it for it in found if label is None or it.property("label") == label]
    return [it for it in h.visible(lambda it: it.metaObject().className().startswith(("Pill", "LabelChip")) and it.property("label") is not None)
            if label is None or it.property("label") == label]
def chip(label):
    c = chips(label); assert len(c) == 1, (label, [x.property("label") for x in chips()]); return c[0]
labels_text = lambda: [it.property("label") for it in chips() if it.metaObject().className().startswith("LabelChip")]
texts = lambda: [it.property("text") for it in h.visible(lambda it: it.metaObject().className().startswith("BoardText")) if it.property("text")]
field = lambda: [it for it in h.visible(lambda it: it.metaObject().className().startswith("TextField"))]
edit = lambda: h.visible(lambda it: it.metaObject().className().startswith("BoardText") and it.property("text") == "\uf040  Edit labels")
button = lambda label: h.visible(lambda it: it.metaObject().className().startswith("ActionButton") and it.property("label") == label)
row_y = lambda it: round(it.mapToScene(QPointF(0, it.height() / 2)).y())
same = lambda a, b: abs(a.redF() - b.redF()) < 0.01 and abs(a.greenF() - b.greenF()) < 0.01 and abs(a.blueF() - b.blueF()) < 0.01

h.ev("root.opened = true"); h.spin(80); h.answer("board", BOARD)
h.ev("root.openIssue(root.columns[1].issues[0])"); h.spin(80)
ISSUE = {"iid": 2, "title": "Second issue with a longer title", "state": "opened", "labels": ["todo", "bug", "frontend"], "url": "https://gitlab.com/group/app/-/issues/2",
         "description": "Make the board faster on large projects.", "author": "dev1", "milestone": "", "assignees": ["dev1"], "createdAt": "2026-10-20T12:00:00Z", "updatedAt": "2026-10-29T12:00:00Z"}
h.answer("issue", {"state": "ready", "message": "", "issue": ISSUE}); h.answer("notes", {"state": "ready", "message": "", "iid": 2, "more": False, "notes": []})
h.ok("I1 labels shown plainly, no editor until asked", labels_text()[:3] == ["todo", "bug", "frontend"] and not field() and not h.running("labels"), labels_text())
pill_labels = [it.property("label") for it in chips() if it.property("label") != "Open in browser ↗"]
h.ok("L1 the label row holds only the state and labels: no Edit or Done pill", pill_labels[:4] == ["Open", "todo", "bug", "frontend"] and not [l for l in pill_labels if "Edit" in l or l == "Done"], pill_labels)
# v0.1.24: Edit labels sits on the label row, right after the last label.
h.ok("L2 Edit labels: one accent text action right after the labels, same row, no border", len(edit()) == 1 and same(edit()[0].property("color"), h.ev("root.accent"))
     and row_y(edit()[0]) == row_y(chip("frontend")) and edit()[0].mapToScene(QPointF(0, 0)).x() > chip("frontend").mapToScene(QPointF(0, 0)).x())
if pngs: h.grab_card(pngs[0])
h.click(edit()[0])
h.ok("I2 Edit labels: one labels read for the project", h.running("labels") == [[h.ev("root.helperPath()"), "labels", "--project", "group/app"]], h.running())
# v0.1.24: the filter is off (dimmed) until the labels load, then focused.
h.ok("I3 loading line; the filter is off and dimmed, so typing goes nowhere", "Loading labels…" in texts() and not field()[0].property("enabled") and field()[0].property("opacity") < 1 and not h.ev("issueView.typing"))
LABELS = [{"name": n, "color": c, "textColor": None} for n, c in [("bug", "#dc2626"), ("docs", "#0ea5e9"), ("frontend", "#16a34a"), ("needs design", "#f59e0b"),
          ("performance", "#db2777"), ("Review", "#a855f7"), ("ux", "#6366f1")]]
h.answer("labels", {"state": "ready", "message": "", "status": ["approved", "in progress", "research", "review", "todo"], "labels": LABELS})
h.ok("I3b loaded: the filter is on and focused", field()[0].property("enabled") and h.ev("issueView.typing"))
h.ok("I4 issue labels: × on bug and frontend only; todo (a board list) stays plain", labels_text()[:3] == ["todo", "bug  \u00d7", "frontend  \u00d7"]
     and chip("bug  \u00d7").property("clickable") and not chip("todo").property("clickable"), labels_text())
h.ok("I5 offered: project labels not on the issue, never a status label (even 'Review')", labels_text()[3:] == ["+ docs", "+ needs design", "+ performance", "+ ux"], labels_text())
h.ok("I6 chips take the label's own color", chip("+ ux").property("color").name() == "#6366f1" and chip("frontend  \u00d7").property("color").name() == "#16a34a")
h.ok("I7 the drag hint is there", "Board list labels change only by dragging the card." in texts())
done = button("Done")
h.ok("L3 editing: Edit labels hides; Done is a square button beside the filter, same height", not edit() and len(done) == 1 and done[0].property("radius") == 0
     and row_y(done[0]) == row_y(field()[0]) and done[0].x() > field()[0].x() and round(done[0].height()) == round(field()[0].height()) and "Done" not in pill_labels)
h.ok("L4 editing: status labels fade, editable ones don't", chip("todo").property("opacity") == 0.5 and chip("bug  \u00d7").property("opacity") == 1)
h.ok("L5 Post is the same kind of button", len(button("Post")) == 1)
if len(pngs) > 1: h.grab_card(pngs[1])
h.click(chip("+ ux"))
h.ok("A1 + ux runs relabel --add ux for #2", h.running("relabel") == [[h.ev("root.helperPath()"), "relabel", "--project", "group/app", "--iid", "2", "--add", "ux"]], h.running())
h.ok("A2 saving, other chips locked", "Saving ux…" in texts() and not chip("+ docs").property("clickable"))
h.stop_all(); h.ev("issueView.labelBusy = ''"); h.ev("root.boardState = 'ready'")
h.click(chip("+ ux")); h.answer("relabel", {"state": "ready", "message": "Added ux.", "labels": ["todo", "bug", "frontend", "ux"]})
h.ok("A3 done: ux on the issue (removable), gone from the offer, board refreshing", "ux  \u00d7" in labels_text() and "+ ux" not in labels_text() and bool(h.running("board")), labels_text())
h.stop_all()
h.click(chip("bug  \u00d7"))
h.ok("R1 bug × runs relabel --remove bug", h.running("relabel") == [[h.ev("root.helperPath()"), "relabel", "--project", "group/app", "--iid", "2", "--remove", "bug"]], h.running())
h.answer("relabel", {"state": "ready", "message": "Removed bug.", "labels": ["todo", "frontend", "ux"]})
h.ok("R2 bug gone from the issue, offered again", "+ bug" in labels_text() and "bug  \u00d7" not in labels_text(), labels_text())
h.stop_all()
h.click(chip("todo"))
for op, name in [("remove", "todo"), ("remove", "TODO"), ("add", "Review"), ("add", "research"), ("add", "In Progress")]:
    h.ev("issueView.relabel(%r, %r)" % (op, name))
h.ok("G1 status labels: no click, no call, any case", not h.running("relabel"), h.running())
f = field()[0]; f.forceActiveFocus()
for ch in "DES": h.key(getattr(Qt, "Key_" + ch), ch.lower())
h.ok("F1 filter, any case", labels_text()[3:] == ["+ needs design"], labels_text())
h.key(Qt.Key_Return)
h.ok("F2 Enter adds the first match", h.running("relabel") and h.running("relabel")[0][-2:] == ["--add", "needs design"], h.running())
h.answer("relabel", {"state": "error", "message": "GitLab did not answer within 30 seconds. The label change may have gone through."})
err = [it for it in h.visible(lambda it: it.metaObject().className().startswith("BoardText") and "did not answer" in str(it.property("text")))]
h.ok("E1 timeout: friendly message in the urgent color, issue reloads", len(err) == 1 and same(err[0].property("color"), h.ev("root.urgent")) and bool(h.running("issue")))
if len(pngs) > 2: h.grab_card(pngs[2])
h.stop_all()
f.selectAll(); h.key(Qt.Key_Backspace)
h.key(Qt.Key_Escape)
h.ok("K1 Esc closes the editor, keys back to the panel, still on the issue", not h.ev("issueView.editing") and not h.ev("issueView.typing") and h.ev("root.view") == "issue" and not field())
h.ev("issueView.labelsAt = 0")  # v0.1.42: labels are reused for 5 minutes; age them so this read happens
h.click(edit()[0]); h.answer("labels", {"state": "error", "message": "Could not load labels for group/app."})
h.ok("E2 labels read fails: message, nothing offered", "Could not load labels for group/app." in texts() and not [l for l in labels_text() if l.startswith("+ ")])
h.click(button("Done")[0])
h.ok("K3 Done closes the editor; status labels back to full strength", not h.ev("issueView.editing") and not field() and len(edit()) == 1 and chip("todo").property("opacity") == 1)
h.click(edit()[0])
h.ev("root.back()"); h.spin(80); h.ev("root.openIssue(root.columns[1].issues[0])"); h.spin(80)
h.ok("K2 leaving the issue closes the editor", not h.ev("issueView.editing") and not field())
sys.exit(h.finish())
