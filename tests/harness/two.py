# Two "screens" (two Windows, one Board each) sharing one BoardService, as the
# shell runs the widget on two monitors. The windows are never exposed, so
# Column layouts do not run here: test a view's rows with lib.Harness instead.
# Usage in a test (run136, run174-run177):
#   import two; two.start({"alerts": {...}}, "ogb-h136-"); from two import *
# start() takes the settings beyond the shared ones (SETTINGS), loads both
# screens, and sets the names a test uses (wins, boards, ctxs, SETTINGS, ...).
import sys, os, json, copy, shutil, tempfile, subprocess, atexit; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from PySide6.QtGui import QImage, QPainter, QColor
out = sys.argv[2] if len(sys.argv) > 2 else None
O406 = os.environ.get("OMARCHY_PATH", os.path.expanduser("~/.local/share/omarchy"))  # Omarchy 4.0.6 checkout
P = "group/app"
BOTS = {P: {"busyLists": ["in progress", "review"], "bots": [{"name": "App UI", "label": "app-ui"}, {"name": "API", "label": "api"}]}}
BASE = {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": P, "defaultBoardId": "7", "defaultBoardName": "Development", "refreshIntervalSec": 60,
            "bots": BOTS}
def row(i, labels, title=None): return {"iid": i, "title": title or "Card %d" % i, "labels": labels, "url": "https://gitlab.com/%s/-/issues/%d" % (P, i), "createdAt": "2026-10-29T12:00:00Z", "notes": 0, "assignees": []}
def board(todo, prog, review, bid=7, name="Development"):
    cols = [("todo", 11, todo), ("in progress", 12, prog), ("Review", 13, review)]
    return {"state": "ready", "project": P, "updatedAt": "2026-10-30T15:00:00Z", "labelColors": {}, "boards": [{"id": bid, "name": name}], "board": {"id": bid, "name": name}, "fallback": False, "message": "",
            "columns": [{"name": "Open", "kind": "open", "issues": []}] + [{"name": n, "kind": "label", "listId": l, "issues": r} for n, l, r in cols] + [{"name": "Closed", "kind": "closed", "issues": []}]}
A = board([row(1, ["todo"]), row(2, ["todo", "app-ui"])], [row(3, ["in progress", "api"])], [row(4, ["review"])])
B = board([row(1, ["todo"])], [row(3, ["in progress", "api"])], [row(4, ["review"]), row(2, ["review", "app-ui"], "Fix <b> & co")])
C = board([row(1, ["todo"])], [], [row(4, ["review"]), row(2, ["review", "app-ui"], "Fix <b> & co"), row(3, ["review", "api"])])
warnings = []; results = []
def start(extra, prefix="ogb-h2s-"):
    global SETTINGS, MAIN, d, dst, eng, wins, boards, ctxs
    SETTINGS = dict(BASE, **extra)
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
    d = tempfile.mkdtemp(prefix=prefix); dst = d + "/app"
    atexit.register(shutil.rmtree, d, True)  # also when a test stops early
    shutil.copytree(sys.argv[1], dst, ignore=shutil.ignore_patterns(".git")); open(dst + "/main2.qml", "w").write(MAIN)
    eng = QQmlApplicationEngine(); eng.addImportPath(HERE + "/stubs")
    eng.warnings.connect(lambda ws: warnings.extend(w.toString() for w in ws))
    eng.load(QUrl.fromLocalFile(dst + "/main2.qml"))
    if not eng.rootObjects(): print("LOAD FAILED"); print("\n".join(warnings)); sys.exit(1)
    wins = {n: next(o for o in QGuiApplication.topLevelWindows() if o.objectName() == n) for n in ("w1", "w2")}
    boards = {"a": wins["w1"].findChild(QQuickItem, "a"), "b": wins["w2"].findChild(QQuickItem, "b")}
    ctxs = {k: QQmlEngine.contextForObject(v.childItems()[0]) for k, v in boards.items()}
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
