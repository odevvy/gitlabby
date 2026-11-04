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
# --- The header: Board · Merge requests · To-do, the read-only chip, the badge -------------------
tabs = lambda: [t.property("label") for t in sorted(h.visible(lambda it: it.metaObject().className().startswith("HeadTab")), key=lambda it: it.mapToScene(QPointF(0, 0)).x())]
ok("H1 the To-do tab third, on; the read-only chip shown", tabs() == ["Board", "Merge requests", "To-do"] and h.ev("header.readOnlyView") is True and len(h.visible(lambda it: it.objectName() == "readOnlyChip")) == 1, tabs())
todo_tab = lambda: next(it for it in h.visible(lambda it: it.objectName() == "todoTab"))
badge = lambda: [it.childItems()[0].property("text") for it in h.walk(todo_tab()) if it.objectName() == "todoBadge" and it.isVisible()]
h.click([t for t in named("todoScopeTab") if t.property("label") == "All projects"][0]); h.spin(100)
h.ev("root.showView('board')"); h.spin(150)
ok("H2 on the board: the tabs stay, no chip, the badge: pending to-dos at the last look", tabs() == ["Board", "Merge requests", "To-do"] and h.visible(lambda it: it.objectName() == "readOnlyChip") == [] and badge() == ["1"], badge())
n = len(h.running()); h.spin(100)
ok("H3 the badge asked for nothing", h.running("todos") == [], h.running())
h.click(todo_tab()); h.spin(150)
ok("H4 a click on To-do opens it", h.ev("root.view") == "todos" and badge() == [])
h.ev("root.showView('board')"); h.spin(100)
h.ev("panel.availableCardWidth = 560"); h.spin(300)
ok("H5 short of room: compact, every tab still whole", h.ev("header.compactTabs") is True and tabs() == ["Board", "MRs", "To-do"], tabs())
st = h.ev("header.status")
tabsR = max(t.mapToScene(QPointF(t.width(), 0)).x() for t in h.visible(lambda it: it.metaObject().className().startswith("HeadTab")))
ok("H6 ... the status after the last tab", st.mapToScene(QPointF(0, 0)).x() >= tabsR - 1, (st.mapToScene(QPointF(0, 0)).x(), tabsR))
hd = h.ev("header"); hc = h.ctx_of(hd); bad = []
for view in ("board", "todos"):
  h.ev("root.showView('%s')" % view); h.spin(100)
  for w in range(520, 1040, 20):
    h.ev("panel.availableCardWidth = %d" % w); h.spin(100)
    title_r = h.ev("title.x + Math.min(title.width, title.paintedWidth)", hc, hd); rule_l = h.ev("tabRule.x", hc, hd)
    stat_l = h.ev("status.x + status.width - Math.min(status.width, status.paintedWidth)", hc, hd); tabs_r = h.ev("tabs.x + tabs.width", hc, hd)
    ref_l = h.ev("refreshButton.x", hc, hd); chip_r = h.ev("readOnlyChip.visible ? readOnlyChip.x + readOnlyChip.width : 0", hc, hd)
    if title_r > rule_l - 20 + 1 or stat_l < tabs_r or max(tabs_r, chip_r) > ref_l - 8: bad.append((w, title_r, rule_l, stat_l, tabs_r, ref_l))
ok("H7 at every width: the title, the tabs and the status never overlap", bad == [], bad)
h.ev("panel.availableCardWidth = 1020"); h.spin(300)
# --- Keys: t toggles; j/k, Enter/o, y and r on the lists -------------------------------------------
h.ev("root.showView('board')"); h.spin(100); h.ev("root.focusBoard()"); h.spin(60)
h.key(Qt.Key_T, "t"); h.spin(150)
ok("K1 t opens To-do (the answer under a minute old: nothing asked)", h.ev("root.view") == "todos" and h.running("todos") == [], (h.ev("root.view"), h.running()))
h.ev("root.feed.todos.answers = ({})"); h.ev("todoView.refresh()"); h.spin(60)
h.answer("todos", tans([td(31, "mentioned"), td(77, "review_requested", "mr")], [asg(3, [LABEL])])); h.spin(250); h.ev("root.focusBoard()"); h.spin(60)
h.key(Qt.Key_J, "j"); h.key(Qt.Key_J, "j")
ok("K2 j twice: past the to-dos onto the assigned issue", h.ev("todoView.cursor") == 2 and named("todoFocusBar") and h.ev("todoView.rows[todoView.cursor].iid") == 3)
n = len(h.launched()); h.key(Qt.Key_Y, "y")
ok("K3 y copies its link, Copied #3", since(n) == [["wl-copy", "https://gitlab.com/%s/-/issues/3" % P]] and h.ev("root.copiedNote") == "Copied #3", since(n))
h.key(Qt.Key_K, "k"); n = len(h.launched()); h.key(Qt.Key_Y, "y")
ok("K4 k, y on an MR to-do: Copied !77", since(n) == [["wl-copy", "https://gitlab.com/%s/-/merge_requests/77" % P]] and h.ev("root.copiedNote") == "Copied !77", since(n))
h.key(Qt.Key_R, "r")
ok("K5 r asks again (fresh or not)", len(h.running("todos")) == 1, h.running())
h.answer("todos", tans([td(31, "mentioned"), td(77, "review_requested", "mr")], [asg(3, [LABEL])])); h.spin(200); h.ev("root.focusBoard()"); h.spin(60)
n = len(h.launched()); h.key(Qt.Key_O, "o")
ok("K6 o opens the focused one", since(n) == [["omarchy-launch-browser", "https://gitlab.com/%s/-/merge_requests/77" % P]], since(n))
h.ev("root.opened = true"); h.spin(150); h.ev("root.showView('todos')"); h.spin(150); h.ev("root.focusBoard()"); h.spin(60)
n = len(h.launched()); h.key(Qt.Key_Return, "\r")
ok("K7 Enter opens the focused one too", len(since(n)) == 1 and since(n)[0][0] == "omarchy-launch-browser", since(n))
h.ev("root.opened = true"); h.spin(150); h.ev("root.showView('todos')"); h.spin(150); h.ev("root.focusBoard()"); h.spin(60)
h.key(Qt.Key_T, "t"); h.spin(100)
ok("K8 t again: back to the board", h.ev("root.view") == "board")
h.ev("root.showView('mrs')"); h.spin(100); h.ev("root.focusBoard()"); h.key(Qt.Key_T, "t"); h.spin(100)
ok("K9 t from Merge requests: To-do", h.ev("root.view") == "todos")
sys.exit(h.finish())
