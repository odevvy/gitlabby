# v0.1.75 (v175 design A, alerts only): after an alert, a small accent dot at
# the bar icon's top right, on every screen, until a popup opens; an alert
# while a popup is open never lights it. Settings > General "Keep the bar icon
# unlit" (iconUnlit) turns it off. Setup as run174 / run136 (two screens).
# Usage: run175.py <src>
import sys, os, json, copy, shutil, tempfile, subprocess; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from PySide6.QtGui import QImage, QPainter, QColor
out = sys.argv[2] if len(sys.argv) > 2 else None
O406 = os.environ.get("OMARCHY_PATH", os.path.expanduser("~/.local/share/omarchy"))  # Omarchy 4.0.6 checkout
P = "group/app"
BOTS = {P: {"busyLists": ["in progress", "review"], "bots": [{"name": "App UI", "label": "app-ui"}, {"name": "API", "label": "api"}]}}
SETTINGS = {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": P, "defaultBoardId": "7", "defaultBoardName": "Development", "refreshIntervalSec": 60,
            "bots": BOTS, "alerts": {P: {"review": True, "idle": False}}}
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
d = tempfile.mkdtemp(prefix="ogb-h175-"); dst = d + "/app"
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


D = board([row(1, ["todo"])], [], [row(4, ["review"]), row(2, ["review", "app-ui"], "Fix <b> & co"), row(3, ["review", "api"]), row(5, ["review"], "Five")])
E = board([], [], [row(4, ["review"]), row(2, ["review", "app-ui"], "Fix <b> & co"), row(3, ["review", "api"]), row(5, ["review"], "Five"), row(1, ["review"])])
dots = lambda: [bool(ev(k, "alertDot.visible")) for k in ("a", "b")]
tips = lambda: [ev(k, "button.tooltipText") for k in ("a", "b")]
def settle():
    for _ in range(4):
        if not running(): break
        answer(LAST[0]); spin(60)
LAST = [A]
def feed_answer(data): LAST[0] = data; answer(data)
spin(150)
ok("D0 no alert yet: no dot on either screen", dots() == [False, False] and tips() == ["GitLab board · group/app"] * 2, (dots(), tips()))
bg(); feed_answer(A)
ok("D1 the first load announces nothing: no dot", dots() == [False, False])
age(); bg(); feed_answer(B)
ok("D2 an alert: a dot on both screens, and the tip says why", len(notes()) == 1 and dots() == [True, True] and tips() == ["GitLab board · group/app · an alert came"] * 2, (len(notes()), dots(), tips()))
w, h_, dx, dy, ds = (ev("a", e) for e in ("button.width", "button.height", "alertDot.x", "alertDot.y", "alertDot.width"))
ok("D3 small (5 points), round, at the icon's top right, inside the button", ds == 5 and ev("a", "alertDot.radius") == 2.5 and dx > w / 2 and dx + ds <= w and dy >= 0 and dy + ds < h_ / 2, (w, h_, dx, dy, ds))
ok("D4 in the accent", ev("a", "String(alertDot.color) === String(root.accent)"))
ev("b", "root.opened = true"); spin(120); settle()
ok("D5 opening the popup on one screen clears both", dots() == [False, False] and ev("a", "root.feed.unseenAlerts") == 0 and tips() == ["GitLab board · group/app"] * 2, (dots(), tips()))
age(); ev("b", "root.refresh(true)"); spin(60); feed_answer(C); spin(100)
ok("D6 an alert while a popup is open: no dot", len(notes()) == 2 and dots() == [False, False], (len(notes()), dots()))
ev("b", "root.opened = false"); spin(120)
ok("D7 closing it: still none", dots() == [False, False])
age(); bg(); feed_answer(D)
ok("D8 the next alert with the popups closed: the dot again", len(notes()) == 3 and dots() == [True, True], (len(notes()), dots()))
ev("a", "root.opened = true"); spin(120); settle(); ev("a", "root.opened = false"); spin(80)
loops = [w for w in warnings if "oop" in w]
ok("Z no binding-loop warnings", not loops, loops)
ok("Z no QML warnings", not warnings, warnings[:3])
print("passed", sum(results), "failed", len(results) - sum(results))
sys.stdout.flush(); os._exit(0 if all(results) else 1)
