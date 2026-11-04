# v0.1.77 (v177 design A): the To-do tab. The service side: board-fetch todos
# (one GraphQL query: your pending to-dos and the open issues assigned to you)
# runs only when asked (the view opens, its scope changes, or r), never on
# popup open or a timer; an answer under a minute old is reused; one query
# serves both screens; sign-out forgets. Setup as run176 (two screens).
# Usage: run177.py <src>
import sys, os, json, copy, shutil, tempfile, subprocess; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from PySide6.QtGui import QImage, QPainter, QColor
out = sys.argv[2] if len(sys.argv) > 2 else None
O406 = os.environ.get("OMARCHY_PATH", os.path.expanduser("~/.local/share/omarchy"))  # Omarchy 4.0.6 checkout
P = "group/app"
BOTS = {P: {"busyLists": ["in progress", "review"], "bots": [{"name": "App UI", "label": "app-ui"}, {"name": "API", "label": "api"}]}}
SETTINGS = {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": P, "defaultBoardId": "7", "defaultBoardName": "Development", "refreshIntervalSec": 60,
            "bots": BOTS}
def row(i, labels, title=None): return {"iid": i, "title": title or "Card %d" % i, "labels": labels, "url": "https://gitlab.com/%s/-/issues/%d" % (P, i), "createdAt": "2026-10-29T12:00:00Z", "notes": 0, "assignees": []}
def board(todo, prog, review, bid=7, name="Development"):
    cols = [("todo", 11, todo), ("in progress", 12, prog), ("Review", 13, review)]
    return {"state": "ready", "project": P, "updatedAt": "2026-10-30T15:00:00Z", "labelColors": {}, "boards": [{"id": bid, "name": name}], "board": {"id": bid, "name": name}, "fallback": False, "message": "",
            "columns": [{"name": "Open", "kind": "open", "issues": []}] + [{"name": n, "kind": "label", "listId": l, "issues": r} for n, l, r in cols] + [{"name": "Closed", "kind": "closed", "issues": []}]}
A = board([row(1, ["todo"]), row(2, ["todo", "app-ui"])], [row(3, ["in progress", "api"])], [row(4, ["review"])])
B = board([row(1, ["todo"])], [row(3, ["in progress", "api"])], [row(4, ["review"]), row(2, ["review", "app-ui"], "Fix <b> & co")])
C = board([row(1, ["todo"])], [], [row(4, ["review"]), row(2, ["review", "app-ui"], "Fix <b> & co"), row(3, ["review", "api"])])
MAIN = """import QtQuick
import QtQuick.Window
import Quickshell
Item {
  id: top
  BoardService { id: svc; objectName: "svc" }
  component Shell: QtObject {
    property var writes: []
    function serviceFor(id) { return id === "odevvy.gitlab-board" ? svc : null }
    function updateEntryInline(id, s) { writes = writes.concat([s]); return true }
  }
  component Bar: QtObject { property var shell: Shell {} }
  Window { id: w1; objectName: "w1"; width: 1300; height: 760; visible: true; color: "#0b1c30"
    Board { id: a; objectName: "a"; settings: %(s)s
      bar: Bar {} } }
  Window { id: w2; objectName: "w2"; width: 1300; height: 760; visible: true; color: "#0b1c30"
    Board { id: b; objectName: "b"; settings: %(s)s
      bar: Bar {} } }
}
""" % {"s": json.dumps(SETTINGS)}
d = tempfile.mkdtemp(prefix="ogb-h177-"); dst = d + "/app"
shutil.copytree(sys.argv[1], dst, ignore=shutil.ignore_patterns(".git")); open(dst + "/main2.qml", "w").write(MAIN)
eng = QQmlApplicationEngine(); eng.addImportPath(HERE + "/stubs")
warnings = []; eng.warnings.connect(lambda ws: warnings.extend(w.toString() for w in ws))
eng.load(QUrl.fromLocalFile(dst + "/main2.qml"))
if not eng.rootObjects(): print("LOAD FAILED"); print("\n".join(warnings)); sys.exit(1)
wins = {n: next(o for o in QGuiApplication.topLevelWindows() if o.objectName() == n) for n in ("w1", "w2")}
boards = {"a": wins["w1"].findChild(QQuickItem, "a"), "b": wins["w2"].findChild(QQuickItem, "b")}
ctxs = {k: QQmlEngine.contextForObject(v.childItems()[0]) for k, v in boards.items()}
results = []
def ok(name, cond, extra=""):
    results.append(bool(cond)); print(("PASS " if cond else "FAIL ") + name + (("  " + str(extra)) if not cond and extra != "" else ""))
def ev(k, code):
    e = QQmlExpression(ctxs[k], boards[k], code); v = e.evaluate()
    if e.hasError(): print("JSERR", k, code[:90], e.error().toString())
    v = v[0] if isinstance(v, tuple) else v
    return v.toVariant() if isinstance(v, QJSValue) else v
def spin(ms):
    t = QTimer(); t.setSingleShot(True); t.start(ms)
    while t.isActive(): app.processEvents()
SCAN = "(function(f){ var r = []; for (var i = 0; i < f.data.length; i++) { var c = f.data[i]; if (c && c.command !== undefined && c.stdout !== undefined) r.push(c) } return r })"
def running(): return [p for p in ev("a", SCAN + "(root.feed).map(function(p){ return p.running ? p.command : null })") if p]
def answer(data):
    r = ev("a", "(function(){ var p = " + SCAN + "(root.feed).filter(function(p){ return p.running })[0]; if (!p) return false; p.stdout.text = %s; p.stdout.streamFinished(); p.running = false; p.exited(0, 0); return true })()" % json.dumps(json.dumps(data)))
    spin(150); return r
def answer_proc(k, kind, data):
    js = ("(function(){ var ps = [moveProcess, auxProcess, logoutProcess, cacheProcess].filter(function(p){ return p.running && p.command[1] === %s }); var p = ps[0];"
          " if (!p) return false; p.stdout.text = %s; p.stdout.streamFinished(); p.running = false; p.exited(0, 0); return true })()") % (json.dumps(kind), json.dumps(json.dumps(data)))
    r = ev(k, js); spin(150); return r
tickets = lambda: ev("a", "root.feed.tickets")
notes = lambda: [c for c in (ev("a", "Quickshell.launched") or []) if c and c[0] == "omarchy-notification-send"]
def age(): ev("a", "(function(){ var f = root.feed, a = {}; for (var k in f.answers) a[k] = Object.assign({}, f.answers[k], { startedAt: 0 }); f.answers = a })()")
def bg(): t = tickets(); ev("a", "root.feed.background()"); spin(40); return tickets() > t
def headlines(ns): return [n[7] for n in ns]



def todos_running(): return [c for c in running() if c[1] == "todos"]
def answer_todos(data):
    r = ev("a", "(function(){ var p = " + SCAN + "(root.feed).filter(function(p){ return p.running && p.command[1] === 'todos' })[0]; if (!p) return false; p.stdout.text = %s; p.stdout.streamFinished(); p.running = false; p.exited(0, 0); return true })()" % json.dumps(json.dumps(data)))
    spin(150); return r
def td(i, action, kind="issue", title=None):
    return {"id": "gid://gitlab/Todo/%d" % i, "action": action, "kind": kind, "iid": i, "title": title or "Item %d" % i,
            "url": "https://gitlab.com/%s/-/%s/%d" % (P, "issues" if kind == "issue" else "merge_requests", i), "project": P, "author": {"username": "alice", "name": "Alice"}, "at": "2026-11-03T18:00:00Z"}
def asg(i, labels): return {"iid": i, "title": "Card %d" % i, "url": "https://gitlab.com/%s/-/issues/%d" % (P, i), "project": P, "labels": labels, "updatedAt": "2026-11-03T17:00:00Z", "notes": 2}
def tans(todos, assigned, scope="all"): return {"state": "ready", "message": "", "scope": scope, "updatedAt": "2026-11-03T19:00:00Z", "todos": todos, "assigned": assigned}
def stale(): ev("a", "(function(){ var f = root.feed, a = {}; for (var k in f.todoAnswers) a[k] = Object.assign({}, f.todoAnswers[k], { startedAt: 0 }); f.todoAnswers = a })()")
H = lambda: ev("a", "root.feed.helperPath()")
spin(150)
ok("T0 nothing asked at start", todos_running() == [] and ev("a", "Object.keys(root.feed.todoAnswers).length") == 0, running())
ev("a", "root.opened = true"); spin(150)
ok("T1 opening the popup doesn't ask for to-dos", todos_running() == [], running())
while running(): answer(A); spin(40)
ev("a", "root.feed.requestTodos('all', false)"); ev("b", "root.feed.requestTodos('all', false)"); spin(40)
ok("T2 asked from both screens: one todos query, no project", todos_running() == [[H(), "todos", "--hostname", "gitlab.com"]], running())
ok("T3 ... and todoRunning names its scope", ev("a", "root.feed.todoRunning") == "all")
answer_todos(tans([td(31, "mentioned"), td(7, "build_failed", "mr")], [asg(3, ["in progress"])]))
ok("T4 the answer kept for the scope, checked", ev("a", "root.feed.todoAnswers.all.data.todos.length") == 2 and ev("a", "root.feed.todoAnswers.all.data.assigned[0].iid") == 3 and ev("a", "root.feed.todoRunning") == "", ev("a", "JSON.stringify(root.feed.todoAnswers)"))
ev("a", "root.feed.requestTodos('all', false)"); spin(40)
ok("T5 asked again within a minute: reused, nothing runs", todos_running() == [], running())
ev("a", "root.feed.requestTodos('all', true)"); spin(40)
ok("T6 forced (r): runs again", len(todos_running()) == 1, running())
ev("a", "root.feed.requestTodos('all', true)"); spin(40)
ok("T6b r again while it loads: not queued twice", len(todos_running()) == 1 and ev("a", "root.feed.todoPending") is None, ev("a", "JSON.stringify(root.feed.todoPending)"))
ev("a", "root.feed.requestTodos(%s, false)" % json.dumps(P)); spin(40)
ok("T7 another scope while one loads: waits its turn", len(todos_running()) == 1 and ev("a", "root.feed.todoPending.scope") == P, running())
answer_todos(tans([], []))
ok("T8 ... then runs, with the project", todos_running() == [[H(), "todos", "--project", P, "--hostname", "gitlab.com"]], running())
answer_todos(tans([td(31, "mentioned")], [], P))
ok("T9 both scopes kept", sorted(ev("a", "Object.keys(root.feed.todoAnswers)")) == sorted(["all", P]) and ev("a", "root.feed.todoAnswers.all.data.todos.length") == 0)
stale(); ev("a", "root.feed.requestTodos('all', false)"); spin(40)
ok("T10 over a minute old: asked again", len(todos_running()) == 1, running())
ev("a", "root.feed.background()"); spin(40)
ok("T11 a background refresh doesn't ask for to-dos", len(todos_running()) == 1, running())
ev("a", "root.feed.forget()"); spin(40)
answer_todos(tans([td(1, "assigned")], []))
ok("T12 sign out (forget): answers gone, a late answer dropped", ev("a", "Object.keys(root.feed.todoAnswers).length") == 0 and ev("a", "root.feed.todoPending") is None, ev("a", "JSON.stringify(root.feed.todoAnswers)"))
ev("a", "root.feed.requestTodos('all', false)"); spin(40); answer_todos({"state": "logged-out", "message": "Sign in with glab."})
ok("T13 a logged-out answer kept as such", ev("a", "root.feed.todoAnswers.all.data.state") == "logged-out")
ev("a", "root.feed.requestTodos('all', true)"); spin(40); answer_todos("junk")
ok("T14 an unreadable answer: an error state, not raw text", ev("a", "root.feed.todoAnswers.all.data.state") == "error" and ev("a", "root.feed.todoAnswers.all.data.todos.length") == 0)
while running(): answer(A); spin(40)
loops = [w for w in warnings if "oop" in w]
ok("Z no binding-loop warnings", not loops, loops)
ok("Z no QML warnings", not warnings, warnings[:3])
print("passed", sum(results), "failed", len(results) - sum(results))
sys.stdout.flush(); os._exit(0 if all(results) else 1)
