# v0.1.76 (v176 design A): Settings > Alerts "A pipeline on my MR finishes".
# While on, each background refresh asks board-fetch pipes (one GraphQL query:
# your open MRs in the project with their head pipelines); with it the only
# alert on, the board itself isn't fetched. A pipeline that was running or
# pending and is now passed or failed, or another one (its id) that ended
# since, is notified; the first answer is a baseline. One query and one
# notification for both screens; the bar icon's dot as for the other alerts.
# Setup as run175 (two screens). Usage: run176.py <src>
import sys, os, json, copy, shutil, tempfile, subprocess; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from PySide6.QtGui import QImage, QPainter, QColor
out = sys.argv[2] if len(sys.argv) > 2 else None
O406 = os.environ.get("OMARCHY_PATH", os.path.expanduser("~/.local/share/omarchy"))  # Omarchy 4.0.6 checkout
P = "group/app"
BOTS = {P: {"busyLists": ["in progress", "review"], "bots": [{"name": "App UI", "label": "app-ui"}, {"name": "API", "label": "api"}]}}
SETTINGS = {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": P, "defaultBoardId": "7", "defaultBoardName": "Development", "refreshIntervalSec": 60,
            "bots": BOTS, "alerts": {P: {"pipeline": True}}}
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
d = tempfile.mkdtemp(prefix="ogb-h176-"); dst = d + "/app"
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


def pipes_running(): return [c for c in running() if c[1] == "pipes"]
def answer_pipes(data):
    r = ev("a", "(function(){ var p = " + SCAN + "(root.feed).filter(function(p){ return p.running && p.command[1] === 'pipes' })[0]; if (!p) return false; p.stdout.text = %s; p.stdout.streamFinished(); p.running = false; p.exited(0, 0); return true })()" % json.dumps(json.dumps(data)))
    spin(150); return r
def mr(i, status, pid=None, title=None):
    return {"iid": i, "title": title or "MR %d" % i, "url": "https://gitlab.com/%s/-/merge_requests/%d" % (P, i),
            "pipeline": None if status is None else {"status": status, "url": "https://gitlab.com/%s/-/pipelines/%s" % (P, pid or i), "id": "gid://gitlab/Ci::Pipeline/%s" % (pid or i)}}
def pans(*mrs): return {"state": "ready", "message": "", "project": P, "updatedAt": "2026-11-03T19:00:00Z", "mrs": list(mrs)}
def page(): ev("a", "(function(){ var f = root.feed, a = {}; for (var k in f.pipeAt) a[k] = 0; f.pipeAt = a })()")
dots = lambda: [bool(ev(k, "alertDot.visible")) for k in ("a", "b")]
spin(150)
ok("P0 the pipeline alert alone watches the board (both screens), the others off", ev("a", "root.watchCfg && root.watchCfg.pipeline === true && !root.watchCfg.review && !root.watchCfg.idle") is True
   and ev("a", "root.feed.watchedKeys.length") == 1, ev("a", "JSON.stringify(root.watchCfg)"))
t0 = tickets(); ev("a", "root.feed.background()"); spin(40)
ok("P1 a background refresh: one pipes query for the project, not the board", tickets() == t0 and pipes_running() == [[ev("a", "root.feed.helperPath()"), "pipes", "--project", P, "--hostname", "gitlab.com"]], running())
answer_pipes(pans(mr(42, "running"), mr(44, "pending"), mr(45, "passed")))
ok("P2 the first answer is a baseline: nothing sent, no dot", notes() == [] and dots() == [False, False], notes())
ev("a", "root.feed.background()"); spin(40)
ok("P3 not due yet (its board's pace): no second query", pipes_running() == [] and tickets() == t0)
page(); ev("a", "root.feed.background()"); spin(40)
ok("P4 due: one query, still no board fetch", len(pipes_running()) == 1 and tickets() == t0, running())
answer_pipes(pans(mr(42, "passed"), mr(44, "pending"), mr(45, "passed")))
n = notes()
ok("P5 running -> passed: one notification, its MR, opened as Open links in says", len(n) == 1 and n[0][7:] == ["Pipeline passed on !42", "!42 MR 42 · " + P, "--exec", "omarchy-launch-browser", "https://gitlab.com/%s/-/merge_requests/42" % P], n)
ok("P6 the bar icon's dot on both screens, as for the other alerts", dots() == [True, True] and ev("a", "root.feed.unseenAlerts") == 1)
page(); ev("a", "root.feed.background()"); spin(40); answer_pipes(pans(mr(42, "passed"), mr(44, "failed", title="Fix <b> & co"), mr(45, "passed")))
n = notes()
ok("P7 pending -> failed: its own notification, the title escaped", len(n) == 2 and n[1][7:9] == ["Pipeline failed on !44", "!44 Fix &lt;b&gt; &amp; co · " + P], n[1:])
page(); ev("a", "root.feed.background()"); spin(40); answer_pipes(pans(mr(42, "passed"), mr(44, "failed"), mr(45, "passed")))
ok("P8 nothing changed: nothing", len(notes()) == 2)
page(); ev("a", "root.feed.background()"); spin(40); answer_pipes(pans(mr(42, "passed", pid=420), mr(44, "running", pid=440), mr(45, "canceled", pid=450)))
ok("P9 a re-run that passed again (another id): notified; canceled: not", [x[7] for x in notes()[2:]] == ["Pipeline passed on !42"], notes()[2:])
page(); ev("a", "root.feed.background()"); spin(40); answer_pipes(pans(mr(42, "failed", pid=421), mr(44, "passed", pid=440), mr(45, "canceled", pid=450)))
n = notes()[3:]
ok("P10 several in one refresh: one, the project's merge requests", len(n) == 1 and n[0][7:] == ["2 pipelines finished", "!42 failed, !44 passed · " + P, "--exec", "omarchy-launch-browser", "https://gitlab.com/%s/-/merge_requests" % P], n)
page(); ev("a", "root.feed.background()"); spin(40); answer_pipes({"state": "error", "message": "Could not load your merge requests."})
ok("P11 a failed query drops the baseline", ev("a", "root.feed.pipeBaselines[%s] === undefined" % json.dumps(P)) is True and len(notes()) == 4)
page(); ev("a", "root.feed.background()"); spin(40); answer_pipes(pans(mr(42, "passed", pid=422)))
ok("P12 ... so the next good one is a baseline again", len(notes()) == 4)
for k in ("a", "b"): ev(k, "root.settings = Object.assign({}, root.settings, { openLinks: 'app' })")
spin(60); page(); ev("a", "root.feed.background()"); spin(40); answer_pipes(pans(mr(42, "passed", pid=423)))
n = notes()[4:]
ok("P13 Open links in: App window, so the click opens an app window", len(n) == 1 and n[0][-3:] == ["--exec", "omarchy-launch-webapp", "https://gitlab.com/%s/-/merge_requests/42" % P], n)
ok("P14 the tip on Updated: no 'also while closed' (only the MR query runs)", "while closed" not in str(ev("a", "root.cadenceText()")), ev("a", "root.cadenceText()"))
for k in ("a", "b"): ev(k, "root.settings = Object.assign({}, root.settings, { alerts: { %s: { pipeline: true, review: true } } })" % json.dumps(P))
spin(60); age(); page(); t0 = tickets(); ev("a", "root.feed.background()"); spin(40)
ok("P15 with a card alert on too: the board and the pipes query", tickets() == t0 + 1 and len(pipes_running()) == 1, running())
ok("P16 ... and the tip says it also refreshes while closed", "also while closed" in str(ev("a", "root.cadenceText()")))
answer_pipes(pans(mr(42, "passed", pid=423))); settle_n = 0
while running() and settle_n < 4: answer(A); settle_n += 1
for k in ("a", "b"): ev(k, "root.settings = Object.assign({}, root.settings, { alerts: { %s: { review: true } } })" % json.dumps(P))
spin(60); age(); page(); ev("a", "root.feed.background()"); spin(40)
ok("P17 pipeline off: no query, its baseline gone", pipes_running() == [] and ev("a", "Object.keys(root.feed.pipeBaselines).length") == 0, running())
while running() and settle_n < 8: answer(A); settle_n += 1
for k in ("a", "b"): ev(k, "root.settings = Object.assign({}, root.settings, { alerts: {} })")
spin(60); page(); ev("a", "root.feed.background()"); spin(40)
ok("P18 every alert off: nothing watched, nothing asked", ev("a", "root.feed.watchedKeys.length") == 0 and running() == [], running())
for k in ("a", "b"): ev(k, "root.settings = Object.assign({}, root.settings, { alerts: { %s: { pipeline: true } } })" % json.dumps(P))
spin(60); page(); ev("a", "root.feed.background()"); spin(40); answer_pipes(pans(mr(42, "running", pid=430)))
ev("a", "root.feed.forget()"); spin(40)
ok("P19 sign out (forget): the pipeline baselines and times go", ev("a", "Object.keys(root.feed.pipeBaselines).length + Object.keys(root.feed.pipeAt).length") == 0)
# --- Settings > Alerts: the box, off by default, and the notes -------------------------------------
for k in ("a", "b"): ev(k, "root.settings = Object.assign({}, root.settings, { alerts: {} })")
spin(60); ev("a", "root.opened = true"); spin(120)
while running(): answer(A); spin(40)
ev("a", "root.showView('settings')"); spin(120)
while running():
    c = running()[0]
    if c[1] == "whoami": answer({"state": "ready", "message": "", "user": "o_devvy"})
    else: answer(A)
    spin(40)
def walk(it):
    yield it
    for c in it.childItems(): yield from walk(c)
sv = ev("a", "settingsView"); items = list(walk(sv))
boxes = lambda: sorted([it for it in walk(sv) if it.isVisible() and it.property("clickable") is not None and isinstance(it.property("modelData"), dict) and it.property("modelData").get("kind") in ("review", "idle", "pipeline")], key=lambda it: it.mapToScene(QPointF(0, 0)).x())
bx = boxes()
ok("S1 Alerts: three boxes, the pipeline one last, all off by default", [b.property("modelData")["label"] for b in bx] == ["A card enters review", "A bot stops working", "A pipeline on my MR finishes"] and not any(b.property("on") for b in bx), [b.property("modelData") for b in bx])
helps = [it.property("text") for it in items if it.isVisible() and isinstance(it.property("text"), str) and it.property("text").startswith("Desktop notifications for")]
ok("S2 the Alerts note: only a card or bot alert refreshes the board in the background", helps == ["Desktop notifications for %s. While a card or bot one is on, the board refreshes in the background." % P], helps)
note = next((it for it in items if it.objectName() == "pipeNote"), None)
ok("S3 under the boxes, what the pipeline one costs", note is not None and note.isVisible() and note.property("text") == "Your open MRs in this project: one small read per refresh, only while this is on."
   and note.mapToScene(QPointF(0, 0)).y() >= bx[2].mapToScene(QPointF(0, bx[2].height())).y(), note and note.property("text"))
fl = next(it for it in walk(sv) if it.metaObject().className().startswith("QQuickFlickable"))
fl.setProperty("contentY", max(0, min(bx[2].mapToItem(fl.property("contentItem"), QPointF(0, 0)).y() - 80, fl.property("contentHeight") - fl.height()))); spin(120)
def click(it):
    c = it.mapToScene(QPointF(it.width() / 2, it.height() / 2)); QTest.mouseClick(wins["w1"], Qt.LeftButton, Qt.NoModifier, QPoint(int(c.x()), int(c.y()))); spin(120)
w0 = len(ev("a", "root.bar.shell.writes") or []); click(boxes()[2])
wr = (ev("a", "root.bar.shell.writes") or [])[w0:]
ok("S4 a click saves pipeline: true for this project, with the other two off; the rest kept", wr and wr[-1].get("alerts") == {P: {"review": False, "idle": False, "pipeline": True}} and wr[-1].get("bots") == BOTS, wr and wr[-1].get("alerts"))
for k in ("a", "b"): ev(k, "root.settings = Object.assign({}, root.settings, { alerts: %s })" % json.dumps(wr[-1].get("alerts")))
spin(80)
ok("S5 ticked once saved; the service watches the board for it", boxes()[2].property("on") is True and ev("a", "root.feed.watchedKeys.length") == 1 and ev("a", "root.watchCfg.pipeline") is True)
click(boxes()[2])
ok("S6 a click again: pipeline off", (ev("a", "root.bar.shell.writes") or [])[-1].get("alerts") == {P: {"review": False, "idle": False, "pipeline": False}})
loops = [w for w in warnings if "oop" in w]
ok("Z no binding-loop warnings", not loops, loops)
ok("Z no QML warnings", not warnings, warnings[:3])
print("passed", sum(results), "failed", len(results) - sum(results))
sys.stdout.flush(); os._exit(0 if all(results) else 1)
