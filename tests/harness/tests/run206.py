# v0.1.106: a full list section reads "Latest N" (no total) and offers View
# all on GitLab: that list on GitLab, this view's scope, filtered to him,
# opened as Open links in says. Sections under the cap keep their count.
# Usage: run206.py <src>
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
P = "group/app"
BOARD = {"state": "ready", "project": P, "updatedAt": "2026-10-31T13:20:00Z", "message": "", "labelColors": {}, "boards": [{"id": 1, "name": "Dev"}], "board": {"id": 1, "name": "Dev"}, "fallback": False,
  "columns": [{"name": "Open", "kind": "open", "issues": []}, {"name": "Closed", "kind": "closed", "issues": []}]}
def mr(i):
    return {"iid": i, "title": "Change %d" % i, "url": "https://gitlab.com/%s/-/merge_requests/%d" % (P, i), "draft": False, "project": P, "branch": "b%d" % i,
            "updatedAt": "2026-10-31T13:00:00Z", "status": "mergeable", "author": {"username": "alice", "name": "alice", "avatar": ""}, "pipeline": None, "reviewers": []}
MRS = {"state": "ready", "message": "", "scope": "all", "updatedAt": "2026-10-31T13:20:00Z", "review": [mr(i) for i in range(1, 11)], "mine": [mr(i) for i in range(11, 14)]}
def todo(i): return {"id": str(i), "action": "mentioned", "kind": "issue", "iid": i, "title": "T%d" % i, "url": "https://gitlab.com/%s/-/issues/%d" % (P, i), "project": P, "author": {"username": "a", "name": "a"}, "at": "2026-10-31T13:00:00Z"}
def iss(i): return {"iid": i, "title": "I%d" % i, "url": "https://gitlab.com/%s/-/issues/%d" % (P, i), "project": P, "labels": [], "updatedAt": "2026-10-31T13:00:00Z", "notes": 0}
TODOS = {"state": "ready", "message": "", "scope": "all", "updatedAt": "2026-10-31T13:20:00Z", "todos": [todo(i) for i in range(1, 31)], "assigned": [iss(i) for i in range(1, 6)]}
h = Harness(sys.argv[1], {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": []})
h.ev("panel.availableCardHeight = 900; panel.availableCardWidth = 1460")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(150)
ev = h.ev
def named(n): return [it for it in h.walk() if it.objectName() == n and it.isVisible()]
def ys(it): return it.mapToScene(QPointF(0, 0)).y()

ev("root.showView('mrs')"); h.spin(80); h.answer("mrs", MRS); h.spin(150)
counts = sorted(named("mrsCount"), key=ys)
h.ok("M1 the full review section reads Latest 10, Yours keeps its count", [c.property("text") for c in counts] == ["Latest 10", "3"], [c.property("text") for c in counts])
va = named("viewAll")
h.ok("M2 one View all on GitLab, on the full section's heading line", len(va) == 1 and abs(ys(va[0]) + va[0].height() / 2 - (ys(counts[0]) + counts[0].height() / 2)) < 3)
h.ok("M3 it sits at the right", va[0].mapToScene(QPointF(va[0].width(), 0)).x() > ev("mrsView.mapToItem(null, mrsView.width, 0).x") - ev("Style.space(24)"))
h.ok("M4 tabs' badge unchanged (9+ for the slice)", ev("Logic.mrBadge(root.feed.mrs.answers['all'].data)") == "9+")
h.click(va[0]); h.spin(60)
h.ok("V1 username unknown: one whoami first, nothing opened yet", h.running("whoami") and h.launched() == [], h.launched())
h.answer("whoami", {"state": "ready", "message": "", "user": "o_devvy"}); h.spin(80)
h.ok("V2 then the review list on GitLab, all projects, filtered to him, in a browser tab",
     ["omarchy-launch-browser", "https://gitlab.com/dashboard/merge_requests?state=opened&reviewer_username=o_devvy"] in h.launched(), h.launched())
# This project, app window: the project's own list, no second whoami.
ev("root.persist({ openLinks: 'app' })"); ev("root.opened = true"); ev("root.showView('mrs')"); h.spin(60)
ev("mrsView.setMode('project')"); h.spin(60); h.answer("mrs", dict(MRS, scope=P)); h.spin(120)
n = len(h.launched())
h.click(named("viewAll")[0]); h.spin(60)
h.ok("V3 This project: the project's list, in an app window", h.launched()[n:] == [["omarchy-launch-webapp", "https://gitlab.com/group/app/-/merge_requests?state=opened&reviewer_username=o_devvy"]], h.launched()[n:])
# To-do: 30 pending is full (Latest 30); 5 assigned is not.
ev("root.persist({ openLinks: 'browser' })"); ev("root.opened = true"); ev("root.showView('todos')"); h.spin(60)
h.answer("todos", TODOS); h.spin(150)
tc = sorted(named("todoCount"), key=ys)
h.ok("T1 To-dos read Latest 30, Assigned keeps 5", [c.property("text") for c in tc] == ["Latest 30", "5"], [c.property("text") for c in tc])
n = len(h.launched())
for _ in range(30):
    QTest.keyClick(h.win, Qt.Key_Tab); h.spin(20)
    if ev("root.kbFocus") == named("viewAll")[0]: break
h.ok("K1 View all takes the focus outline", ev("root.kbFocus") == named("viewAll")[0])
h.key(Qt.Key_Return); h.spin(60)
h.ok("K2 Enter opens the to-do list", h.launched()[n:] == [["omarchy-launch-browser", "https://gitlab.com/dashboard/todos"]], h.launched()[n:])
sys.exit(h.finish())
