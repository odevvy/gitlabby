# v0.1.26: a small accent spinner (Spinner.qml) beside every "…ing" line that
# waits on GitLab: Loading labels… / Saving <label>… in the label editor, the
# comments heading while comments load, and the picker's Loading…. It is gone
# once the wait ends, whether it worked or failed.
# Usage: run126.py <src> [labels-loading.png picker-loading.png]
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
pngs = sys.argv[2:4]
shot = lambda i: len(pngs) > i and h.grab_card(pngs[i])
h = Harness(sys.argv[1], {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": "group/app", "defaultCollapsed": [], "boardStates": {}, "refreshIntervalSec": 60})
h.ev("panel.availableCardHeight = 1000"); h.ev("panel.contentWidth = 790")  # his popup: ~820 wide
cls_is = lambda it, n: it.metaObject().className().startswith(n)
spinners = lambda: h.visible(lambda it: cls_is(it, "Spinner"))
same = lambda a, b: abs(a.redF() - b.redF()) < 0.01 and abs(a.greenF() - b.greenF()) < 0.01 and abs(a.blueF() - b.blueF()) < 0.01
def box(it):  # unrotated: the spinner turns, so map its slot from the parent
    p = it.parentItem().mapToScene(QPointF(it.x(), it.y())); return p.x(), p.y(), p.x() + it.width(), p.y() + it.height()
mid = lambda it: (box(it)[1] + box(it)[3]) / 2
text = lambda t: [it for it in h.visible(lambda it: cls_is(it, "BoardText") and it.property("text") == t)]

h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(60)
h.ok("N0 a loaded board: no spinner anywhere", spinners() == [])
h.ev("root.openIssue(root.columns[1].issues[0])"); h.spin(80)
ISSUE = {"iid": 2, "title": "Header palette button: label it \"Edit background\" like Edit cover", "state": "opened", "labels": ["todo", "frontend"], "url": "https://gitlab.com/group/app/-/issues/2",
         "description": "Hovering the palette button shows \"Background\". It should say \"Edit background\".", "author": "o_devvy", "milestone": "", "assignees": [], "createdAt": "2026-10-29T12:00:00Z", "updatedAt": "2026-10-29T12:00:00Z"}
h.answer("issue", {"state": "ready", "message": "", "issue": ISSUE}); h.spin(300)
cm = text("Comments")
# One spinner for the comments, on the heading's line or the line under it
# (v0.1.67: the loading row under the heading).
h.ok("C1 comments loading: one spinner at the Comments heading", len(spinners()) == 1 and len(cm) == 1 and box(cm[0])[1] - 2 <= mid(spinners()[0]) <= box(cm[0])[3] + (box(cm[0])[3] - box(cm[0])[1]) * 2.5)
h.answer("notes", {"state": "ready", "message": "", "iid": 2, "more": False, "notes": []}); h.spin(60)
h.ok("C2 comments in: no spinner", spinners() == [])

iw = h.cls("IssueView"); ic = h.ctx_of(iw); iev = lambda code: h.ev(code, ic, iw)
h.click(iev("editAction")); h.spin(60)
sp, ln = spinners(), text("Loading labels…")
h.ok("L1 labels loading: one spinner, just left of 'Loading labels…', on its line", len(sp) == 1 and len(ln) == 1 and abs(mid(sp[0]) - mid(ln[0])) < 2
     and 0 <= box(ln[0])[0] - box(sp[0])[2] <= iev("Style.space(8)") and abs(box(sp[0])[0] - box(iev("labelFilter"))[0]) < 1, [box(x) for x in sp + ln])
h.ok("L2 it is the accent, small, and it turns", same(sp[0].property("color"), h.ev("root.accent")) and abs(sp[0].property("font").pixelSize() - iev("Style.font.bodySmall")) < 0.5
     and (lambda a: (h.spin(150), sp[0].property("rotation") != a)[1])(sp[0].property("rotation")))
shot(0)
LABELS = [{"name": n, "color": c, "textColor": None} for n, c in [("bug", "#dc2626"), ("docs", "#0ea5e9"), ("frontend", "#16a34a")]]
h.answer("labels", {"state": "ready", "message": "", "status": ["approved", "in progress", "research", "review", "todo"], "labels": LABELS}); h.spin(60)
h.ok("L3 labels in: the spinner is gone", spinners() == [] and text("Loading labels…") == [])
h.ev("issueView.relabel('add', 'bug')"); h.spin(60)
h.ok("L4 saving a label: the spinner beside 'Saving bug…'", len(spinners()) == 1 and len(text("Saving bug…")) == 1 and abs(mid(spinners()[0]) - mid(text("Saving bug…")[0])) < 2)
h.answer("relabel", {"state": "error", "message": "GitLab refused the label change."}); h.spin(60)
h.ok("L5 the save failed: no spinner, the reason in red", not [s for s in spinners() if s.parentItem() == text("GitLab refused the label change.")[0].parentItem()]
     and same(text("GitLab refused the label change.")[0].property("color"), h.ev("root.urgent")))
h.stop_all(); h.click(iev("editAction")); h.spin(30); h.ev("issueView.labelsAt = 0"); h.click(iev("editAction")); h.spin(60)  # v0.1.42: aged, so it reads again
h.ok("L6 reopened: loading again, spinning", any(s.parentItem() == text("Loading labels…")[0].parentItem() for s in spinners()))
h.ev("issueView.relabel('remove', 'frontend')"); h.spin(30); h.answer("relabel", {"state": "error", "message": "GitLab refused the label change."}); h.spin(60)
h.ok("L6b a failed save while the labels still load: the error shows, no spinner beside it", h.ev("issueView.labelsState") == "loading" and len(text("GitLab refused the label change.")) == 1
     and not [s for s in spinners() if s.parentItem() == text("GitLab refused the label change.")[0].parentItem()])
h.ev("issueView.labelError = ''"); h.spin(30)
h.answer("labels", {"state": "error", "message": "Could not load the project's labels."}); h.spin(60)
h.ok("L7 labels failed: the spinner is gone, the error shows", text("Loading labels…") == [] and len(text("Could not load the project's labels.")) == 1
     and not [s for s in spinners() if s.parentItem() == text("Could not load the project's labels.")[0].parentItem()])

h.stop_all(); h.ev("root.back()"); h.spin(40); h.ev("root.projects = []"); h.ev("root.openPicker()"); h.spin(80)
h.ok("P1 picker loading projects: a spinner beside Loading…", bool(h.running("projects")) and len(spinners()) == 1 and len(text("Loading…")) == 1 and abs(mid(spinners()[0]) - mid(text("Loading…")[0])) < 2)
shot(1)
h.answer("projects", {"state": "ready", "projects": [{"id": 1, "path": "group/app"}]}); h.spin(60)
h.ok("P2 projects in: no spinner", spinners() == [])
h.finish()
