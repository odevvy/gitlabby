# v0.1.74: an alert notification opens its link as Settings > Open links in says
# (openLinks): an app window (omarchy-launch-webapp) or a browser tab
# (omarchy-launch-browser), https only. Setup as run136 (v0.1.36 desktop alerts).
# Was: v0.1.36: desktop alerts. Two "screens" share one BoardService (as run133);
# the notifier is Quickshell.execDetached, recorded by the stub (the fake
# notifier). Proves: one notification per event for both screens, nothing on
# the first load / a board switch / after a failed refresh / for his own move,
# batched review entries, background refresh only while an alert is on and
# only when due, the exact command Omarchy's bin/omarchy-notification-send
# accepts (run against the real script with busctl faked), Do Not Disturb not
# bypassed (Omarchy's own NotificationLogic.js), the body escaped.
# Usage: run136.py <src> [outdir]   (previews: settings-alerts, settings-alerts-on, notification-review, notification-batch, notification-idle)
import sys, os, json, copy, shutil, tempfile, subprocess; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from PySide6.QtGui import QImage, QPainter, QColor
out = sys.argv[2] if len(sys.argv) > 2 else None
O406 = os.environ.get("OMARCHY_PATH", os.path.expanduser("~/.local/share/omarchy"))  # Omarchy 4.0.6 checkout
P = "group/app"
BOTS = {P: {"busyLists": ["in progress", "review"], "bots": [{"name": "App UI", "label": "app-ui"}, {"name": "API", "label": "api"}]}}
SETTINGS = {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": P, "defaultBoardId": "7", "defaultBoardName": "Development", "refreshIntervalSec": 60,
            "bots": BOTS, "alerts": {P: {"review": True, "idle": False}}, "openLinks": "app"}
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
d = tempfile.mkdtemp(prefix="ogb-h174-"); dst = d + "/app"
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
spin(150)
ok("L0 alerts on, openLinks app: the watched board carries links: app", ev("a", "root.feed.watchers['group/app#7'] && Object.keys(root.feed.watchers['group/app#7']).map(function(o){ return root.feed.watchers['group/app#7'][o].links })") == ["app", "app"])
bg(); answer(A); age(); bg(); answer(B)
n = notes()
ok("L1 App window: a click opens #2 in an app window (omarchy-launch-webapp)", headlines(n) == ["#2 is in review"] and n[0][-3:] == ["--exec", "omarchy-launch-webapp", "https://gitlab.com/group/app/-/issues/2"], n and n[-1])
# Settings > Browser tab on both screens (one saved setting, two copies of the board)
for k in ("a", "b"): ev(k, "root.settings = Object.assign({}, root.settings, { openLinks: 'browser' })")
spin(100)
ok("L2 switched to Browser tab: the watch carries links: browser, the same board still watched", ev("a", "Object.keys(root.feed.watchers['group/app#7']).map(function(o){ return root.feed.watchers['group/app#7'][o].links })") == ["browser", "browser"])
age(); bg(); answer(C)
n = notes()
ok("L3 the switch kept the last answer: only #3 is new, and it opens in a browser tab (omarchy-launch-browser)", headlines(n) == ["#2 is in review", "#3 is in review"] and n[-1][-3:] == ["--exec", "omarchy-launch-browser", "https://gitlab.com/group/app/-/issues/3"], [x[-3:] for x in n])
for k in ("a", "b"): ev(k, "root.settings = Object.assign({}, root.settings, { openLinks: 'webapp' })")
spin(100); age(); bg(); answer(D)
n = notes()
ok("L4 only 'app' is an app window: a saved 'webapp' is a browser tab", headlines(n)[-1] == "#5 is in review" and n[-1][-2] == "omarchy-launch-browser", n and n[-1][-3:])
# The real omarchy-notification-send (busctl faked) and Omarchy's own argv check
fake = tempfile.mkdtemp(prefix="ogb-bus-")
open(fake + "/busctl", "w").write('#!/bin/bash\nprintf "%s\\0" "$@" > "$BUSLOG"\necho "u 1"\n'); os.chmod(fake + "/busctl", 0o755)
log = fake + "/log"; env = dict(os.environ, PATH=fake + ":" + os.environ["PATH"], BUSLOG=log)
argv = ev("a", "Logic.notifyArgv({ headline: '#2 is in review', body: 'b', url: 'https://gitlab.com/group/app/-/issues/2' }, 'app')")
r = subprocess.run([O406 + "/bin/omarchy-notification-send"] + argv[1:], env=env, capture_output=True, text=True)
bus = open(log).read().split("\0")[:-1] if os.path.exists(log) else []
hint = bus[bus.index("omarchy-exec-argv") + 2] if "omarchy-exec-argv" in bus else ""
nl = O406 + "/shell/plugins/notifications/NotificationLogic.js"
res = json.loads(subprocess.run(["node", "-e", "const N = require(%s); console.log(JSON.stringify(N.parseExecArgv(%s)))" % (json.dumps(nl), json.dumps(hint))], capture_output=True, text=True).stdout or "null")
ok("R1 the real script and Omarchy's argv check take the app-window click", r.returncode == 0 and res == ["omarchy-launch-webapp", "https://gitlab.com/group/app/-/issues/2"], (r.returncode, r.stderr, res))
loops = [w for w in warnings if "oop" in w]
ok("Z no binding-loop warnings", not loops, loops)
ok("Z no QML warnings", not warnings, warnings[:3])
print("passed", sum(results), "failed", len(results) - sum(results))
sys.stdout.flush(); os._exit(0 if all(results) else 1)
