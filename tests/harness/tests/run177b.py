# v0.1.77 (v177 design A): the To-do view. Opens on showView("todos") (the
# header tab or t), one todos query then; the first load is one spinner row
# (LoadingRow), no header bar; then "To-dos" with each one's reason and
# "Assigned to you" with its column on this board. A click opens as Open links
# in says, a right-click copies; This project asks with the project; an error
# is the same row, still. Usage: run177b.py <src>
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
P = "group/app"
h = Harness(sys.argv[1], {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": [], "boardStates": {}, "refreshIntervalSec": 60})
h.ev("panel.availableCardHeight = 620; panel.availableCardWidth = 1020")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(400)
def td(i, action, kind="issue", title=None):
    return {"id": "gid://gitlab/Todo/%d" % i, "action": action, "kind": kind, "iid": i, "title": title or "Item %d" % i,
            "url": "https://gitlab.com/%s/-/%s/%d" % (P, "issues" if kind == "issue" else "merge_requests", i), "project": P, "author": {"username": "alice", "name": "Alice"}, "at": "2026-11-03T18:00:00Z"}
def asg(i, labels): return {"iid": i, "title": "Card %d" % i, "url": "https://gitlab.com/%s/-/issues/%d" % (P, i), "project": P, "labels": labels, "updatedAt": "2026-11-03T17:00:00Z", "notes": 2}
def tans(todos, assigned, scope="all"): return {"state": "ready", "message": "", "scope": scope, "updatedAt": "2026-11-03T19:00:00Z", "todos": todos, "assigned": assigned}
def named(n): return sorted(h.visible(lambda it: it.objectName() == n), key=lambda it: (it.mapToScene(QPointF(0, 0)).y(), it.mapToScene(QPointF(0, 0)).x()))
since = lambda n: h.launched()[n:]
LABEL = next(c["name"] for c in h.ev("root.columns") if c.get("kind") == "label")
ok = h.ok
ok("V0 the popup open on the board: no to-dos asked", h.running("todos") == [] and h.ev("root.view") == "board", h.running())
h.ev("root.showView('todos')"); h.spin(150)
ok("V1 the view opens: one todos query", h.running("todos") == [["%s/board-fetch" % h.ev("root.feed.helperPath()").rsplit("/", 1)[0], "todos"]] and h.ev("root.view") == "todos", h.running())
lr = named("todoLoading")
ok("V2 the first load: one spinner row, no header bar or loud dot", len(lr) == 1 and lr[0].property("text") == "Loading your to-dos\u2026" and lr[0].property("spinning") is True
   and h.ev("root.refreshActive") is False and h.ev("root.loudNow") is False, [x.property("text") for x in lr])
h.answer("todos", tans([td(31, "mentioned", title="Login form"), td(77, "review_requested", "mr"), td(76, "build_failed", "mr")], [asg(3, [LABEL, "api"]), asg(9, ["nope"])])); h.spin(300)
ok("V3 answered: the spinner row gone", named("todoLoading") == [])
rows = named("todoRow")
ok("V4 three to-dos then two assigned issues, in order", [r.property("row")["iid"] for r in rows] == [31, 77, 76, 3, 9], [r.property("row") for r in rows])
reasons = [x.property("text") for x in named("todoReason")]
ok("V5 the reasons; an assigned issue's column on this board, else open", reasons == ["mentioned you", "review requested", "pipeline failed", LABEL, "open"], reasons)
ok("V6 pipeline failed in the urgent tone", named("todoReason")[2].property("color").name() == "#ec5941")
subs = [x.property("text") for x in named("todoSubline")]
ok("V7 the sublines: project and who; project and comments", subs[0] == P + "  \u00b7  by Alice" and subs[3] == P + "  \u00b7  2 comments", subs)
counts = [x.property("text") for x in named("todoCount")]
ok("V8 the section counts", counts == ["3", "2"], counts)
read_at = h.ev("Qt.formatTime(new Date(todoView.entry.startedAt), 'HH:mm')")
ok("V9 the status says when the lists were read, not the board", h.ev("header.status.text") == "Updated " + read_at and h.ev("header.status.text") != h.ev("root.showView('board'), header.status.text"), h.ev("header.status.text"))
h.ev("root.showView('todos')"); h.spin(100)
n = len(h.launched()); h.click(rows[1])
ok("V10 a click opens the MR as Open links in says", since(n) == [["omarchy-launch-browser", "https://gitlab.com/%s/-/merge_requests/77" % P]], since(n))
h.ev("root.opened = true"); h.spin(200); h.ev("root.showView('todos')"); h.spin(200)
ok("V10b reopened within a minute: the lists again, nothing asked", h.running("todos") == [] and len(named("todoRow")) == 5, h.running())
n = len(h.launched()); QTest.mouseClick(h.win, Qt.RightButton, Qt.NoModifier, h.scene(named("todoRow")[3])); h.spin(150)
ok("V11 a right-click copies its link; the status says #3", since(n) == [["wl-copy", "https://gitlab.com/%s/-/issues/3" % P]] and h.ev("root.copiedNote") == "Copied #3", since(n))
h.ev("root.showView('board')"); h.spin(60); h.ev("root.showView('todos')"); h.spin(80)
ok("V12 back within a minute: the same lists, nothing asked", h.running("todos") == [] and len(named("todoRow")) == 5, h.running())
h.ev("todoView.refresh()"); h.spin(60)
ok("V13 r with the lists shown: they stay, the header shows the refresh", len(h.running("todos")) == 1 and len(named("todoRow")) == 5 and named("todoLoading") == [] and h.ev("root.refreshActive") is True)
h.answer("todos", tans([td(31, "mentioned")], [])); h.spin(200)
h.click([t for t in named("todoScopeTab") if t.property("label") == "This project"][0]); h.spin(60)
ok("V14 This project: its own query, the project passed", [c[1:] for c in h.running("todos")] == [["todos", "--project", P]], h.running())
h.answer("todos", {"state": "error", "message": "Could not load your to-dos."}); h.spin(200)
lr = named("todoLoading")
ok("V15 an error: the same row, still, and how to retry", len(lr) == 1 and lr[0].property("spinning") is False and lr[0].property("text") == "Could not load your to-dos.  Press r to try again.", [x.property("text") for x in lr])
ok("V16 the merge requests not asked for", h.running("mrs") == [])
sys.exit(h.finish())
