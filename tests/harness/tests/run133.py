# v0.1.33: one board fetch for every screen. Two "screens" (two windows, a Board
# in each, like Omarchy's bar per screen) share one BoardService, handed over the
# way Omarchy does it (bar.shell.serviceFor(moduleName), PluginShellApi.qml).
# Proves: one board-fetch per interval and per manual refresh for both, both show
# the same answer, both refreshing (a dot; "Refreshing…" before v0.1.63) while it runs, moves and sign out still
# right, different boards kept apart; without serviceFor a Board uses its own.
# Usage: run133.py <src> [outdir]   (previews: two-screens-refreshing, two-screens-updated)
import sys, os, json, copy, shutil, tempfile; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
from PySide6.QtGui import QImage, QPainter, QColor
out = sys.argv[2] if len(sys.argv) > 2 else None
SETTINGS = {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": "group/app", "defaultBoardId": "7", "defaultBoardName": "Development", "refreshIntervalSec": 60}
MAIN = """import QtQuick
import QtQuick.Window
Item {
  id: top
  BoardService { id: svc; objectName: "svc" }
  // bar.shell as Omarchy gives a third-party widget under the built-in bar: own service only.
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
d = tempfile.mkdtemp(prefix="ogb-h2-"); dst = d + "/app"
shutil.copytree(sys.argv[1], dst, ignore=shutil.ignore_patterns(".git")); open(dst + "/main2.qml", "w").write(MAIN)
eng = QQmlApplicationEngine(); eng.addImportPath(HERE + "/stubs")
warnings = []; eng.warnings.connect(lambda ws: warnings.extend(w.toString() for w in ws))
eng.load(QUrl.fromLocalFile(dst + "/main2.qml"))
if not eng.rootObjects(): print("LOAD FAILED"); print("\n".join(warnings)); sys.exit(1)
top = eng.rootObjects()[0]
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
# Every board-fetch process anywhere: the shared service, and each Board's private one.
SCAN = "(function(f){ var r = []; for (var i = 0; i < f.data.length; i++) { var c = f.data[i]; if (c && c.command !== undefined && c.stdout !== undefined) r.push(c) } return r })"
def fetching(): return [c for c in (ev("a", SCAN + "(root.feed).concat(" + SCAN + "(localFeed))") or []) + (ev("b", SCAN + "(localFeed)") or []) if c]
def running(): return [p for p in ev("a", "(" + SCAN + "(root.feed).concat(" + SCAN + "(localFeed))).map(function(p){ return p.running ? p.command : null })") + ev("b", SCAN + "(localFeed).map(function(p){ return p.running ? p.command : null })") if p and p[1] != "access"]  # 0.1.39: the once-per-project access check is not a board fetch
def answer(data):
    r = ev("a", "(function(){ var p = " + SCAN + "(root.feed).filter(function(p){ return p.running })[0]; if (!p) return false; p.stdout.text = %s; p.stdout.streamFinished(); p.running = false; p.exited(0, 0); return true })()" % json.dumps(json.dumps(data)))
    spin(150); return r
def answer_proc(k, kind, data):  # a Board's own process (move, aux)
    js = ("(function(){ var ps = [moveProcess, auxProcess, logoutProcess, cacheProcess].filter(function(p){ return p.running && p.command[1] === %s }); var p = ps[0];"
          " if (!p) return false; p.stdout.text = %s; p.stdout.streamFinished(); p.running = false; p.exited(0, 0); return true })()") % (json.dumps(kind), json.dumps(json.dumps(data)))
    r = ev(k, js); spin(150); return r
tickets = lambda: ev("a", "root.feed.tickets")
status = lambda k: ev(k, "header.status.text")
iids = lambda k: ev(k, "root.columns.map(function(c){ return c.name + ':' + (c.issues || []).map(function(i){ return i.iid }).join(',') }).join(' ')")
def age(): ev("a", "(function(){ var f = root.feed, a = {}; for (var k in f.answers) a[k] = Object.assign({}, f.answers[k], { startedAt: 0 }); f.answers = a })()")
def grab(k, w):
    spin(200); img = wins[w].grabWindow(); s = img.width() / wins[w].width()
    card = next(it for it in [boards[k]] + list(boards[k].window().contentItem().childItems()) if it.metaObject().className().startswith("KeyboardPanel"))
    return img.copy(QRect(int(card.x() * s) - 2, int(card.y() * s) - 2, int((card.width() + 4) * s), int((card.height() + 4) * s)))
def shot(name):
    if not out: return
    ia, ib = grab("a", "w1"), grab("b", "w2"); gap = 24
    im = QImage(ia.width() + ib.width() + gap, max(ia.height(), ib.height()) + 30, QImage.Format_ARGB32); im.fill(QColor("#0b1c30"))
    p = QPainter(im); p.setPen(QColor("#e8d5b0")); p.drawText(8, 18, "screen 1 (DP-1)"); p.drawText(ia.width() + gap + 8, 18, "screen 2 (HDMI-A-1)")
    p.drawImage(0, 30, ia); p.drawImage(ia.width() + gap, 30, ib); p.end(); im.save(os.path.join(out, name + ".png"))
B1 = copy.deepcopy(BOARD); B1["updatedAt"] = "2026-10-30T15:00:00Z"
B2 = copy.deepcopy(BOARD); B2["updatedAt"] = "2026-10-30T15:01:00Z"
B2["columns"][1]["issues"] = B2["columns"][1]["issues"] + [{"iid": 6, "title": "New on GitLab", "labels": ["todo"], "url": "https://gitlab.com/group/app/-/issues/6", "createdAt": "2026-10-30T15:00:30Z", "notes": 0, "assignees": []}]

# --- one service for both screens -------------------------------------------------
ok("D1 both screens use the one service from bar.shell.serviceFor, not their own", ev("a", "root.feed === root.sharedFeed && root.feed !== localFeed") and ev("b", "root.feed !== localFeed") and ev("a", "root.feed") == ev("b", "root.feed"))
spin(200)
ok("D2 shell start: no board-fetch yet (only the saved copies, no GitLab call)", tickets() == 0 and not running())
ev("a", "root.opened = true"); spin(80)
ok("D3 popup opened on screen 1: one board-fetch, run by the service", tickets() == 1 and len(running()) == 1 and running()[0][1] == "board", running())
ok("D4 screen 2's widget (popup closed) knows its board is loading", ev("b", "root.loading"))
answer(B1)
ok("D5 the one answer reaches both screens", iids("a") == iids("b") and ev("a", "root.updatedAt") == ev("b", "root.updatedAt") == "2026-10-30T15:00:00Z", (iids("a"), iids("b")))
ev("b", "root.opened = true"); spin(80)
ok("D6 opening screen 2 within the interval: no second fetch; same board, same 'Updated'", tickets() == 1 and not running() and status("a") == status("b") and status("b").startswith("Updated "), (tickets(), status("a"), status("b")))
# --- the interval: ticks on both screens, one fetch -------------------------------
ev("b", "refreshTimer.triggered()"); ev("a", "refreshTimer.triggered()"); spin(60)
ok("I1 both timers tick within the interval: no fetch", tickets() == 1 and not running())
age()
ev("a", "refreshTimer.triggered()"); spin(40); ev("b", "refreshTimer.triggered()"); spin(60)
ok("I2 an interval later both tick: one board-fetch", tickets() == 2 and len(running()) == 1, (tickets(), running()))
ok("I3 'Updated' stays on both screens while it runs (v0.1.63: the dot says it)", status("a").startswith("Updated ") and status("a") == status("b") and ev("a", "root.refreshing") and ev("b", "root.refreshing"), (status("a"), status("b")))
ok("I4 refresh icon spins on both", ev("a", "root.loading") and ev("b", "root.loading"))
shot("two-screens-refreshing")
answer(B2)
ok("I5 both show the new answer: #6 in todo, same 'Updated HH:MM'", "todo:2,6" in iids("a") and iids("a") == iids("b") and status("a") == status("b") and status("a").startswith("Updated "), (iids("a"), status("a"), status("b")))
shot("two-screens-updated")
# --- manual refresh: one fetch, both screens ---------------------------------------
QTest.mouseClick(wins["w2"], Qt.LeftButton, Qt.NoModifier, ev("b", "header.refreshButton").mapToScene(QPointF(4, 4)).toPoint()); spin(60)
ok("R1 Refresh on screen 2 fetches although the last one is fresh", tickets() == 3 and len(running()) == 1)
ev("a", "root.refresh()"); spin(40)
QTest.keyClick(wins["w1"], Qt.Key_R, Qt.NoModifier); spin(40)
ok("R2 Refresh and r on screen 1 meanwhile join it: still one", tickets() == 3 and len(running()) == 1, (tickets(), running()))
ok("R3 refreshing on both, 'Updated' stays", ev("a", "root.refreshing") and ev("b", "root.refreshing") and status("a").startswith("Updated ") and status("a") == status("b"))
answer(B1); ok("R4 both done, same board", iids("a") == iids("b") and status("a") == status("b") and not ev("a", "root.loading") and not ev("b", "root.loading"))
# --- a move on screen 1 ------------------------------------------------------------
ev("a", "root.moveIssue(root.columns[1].issues[0], root.columns[1], root.columns[2])"); spin(60)
ok("M1 the move runs from screen 1 (its own write), no board fetch yet", ev("a", "moveProcess.running") and tickets() == 3)
ev("b", "root.refresh()"); spin(40)
ok("M2 screen 2 refreshes meanwhile: one fetch", tickets() == 4)
moved = copy.deepcopy(B1); moved["columns"][2]["issues"] = moved["columns"][1]["issues"]; moved["columns"][1]["issues"] = []
answer_proc("a", "move", {"state": "ready", "message": "Moved #2 to review."}); spin(120)
ok("M3 move done while that fetch (started before the write) is out: screen 1 is refreshing, no second fetch yet", tickets() == 4 and ev("a", "root.refreshing") and status("a").startswith("Updated "), (tickets(), status("a")))
ev("a", "root.refresh()"); spin(40)
ok("M3 Refresh on screen 1 now doesn't join that older fetch: a newer one waits", tickets() == 4 and ev("a", "root.feed.queue.length") == 1, (tickets(), ev("a", "root.feed.queue.length")))
answer(B1); spin(60)
ok("M4 screen 1 keeps its moved card (that answer predates the move); screen 2 shows it", "review:2" in iids("a") and "todo:2" in iids("b"), (iids("a"), iids("b")))
ok("M4 then one fetch for the board as GitLab has it", tickets() == 5 and len(running()) == 1, (tickets(), running()))
answer(moved)
ok("M5 both screens show #2 in review", "review:2" in iids("a") and iids("a") == iids("b"), (iids("a"), iids("b")))
# --- different boards stay apart, also in the same project; the queue ------------------
ev("a", "root.switchTo('group/app', '8', 'Lean')"); spin(60)
ok("K1 screen 1 switches board: a fetch for it; screen 2 isn't loading", tickets() == 6 and ev("a", "root.loading") and not ev("b", "root.loading"))
ev("b", "root.refresh()"); spin(20); ev("b", "root.refresh()"); spin(20)
ok("Q1 screen 2 refreshes twice meanwhile: its board waits once, and counts as loading", ev("a", "root.feed.queue.length") == 1 and ev("b", "root.loading") and tickets() == 6, (ev("a", "root.feed.queue.length"), ev("b", "root.loading")))
ev("a", "root.feed.request('group/third', '', false, 0, 0)")
ok("Q2 the newest request goes first", ev("a", "root.feed.queue.map(function(q){ return q.key }).join(' ')") == "group/third# group/app#7")
lean = dict(copy.deepcopy(BOARD), board={"id": 8, "name": "Lean"}); lean["columns"] = [{"name": "Doing", "kind": "label", "listId": 9, "issues": []}]
answer(lean)
ok("K2 screen 2 keeps its board (same project, other board)", "review:2" in iids("b") and ev("b", "root.boardName") == "Development" and iids("a") == "Doing:", (iids("a"), iids("b")))
ok("Q3 then the waiting ones run, newest first", running() and running()[0][3] == "group/third", running())
answer(dict(copy.deepcopy(BOARD), project="group/third")); answer(moved)
ok("Q4 screen 2 gets its board; nothing else waits", "review:2" in iids("b") and not running() and ev("a", "root.feed.queue.length") == 0)
ev("a", "root.switchTo('group/app', '7', 'Development')"); spin(40); answer(moved)
# --- an answer while a card is held on screen 1 --------------------------------------
t0 = tickets(); ev("a", "boardView.holding = true"); ev("a", "root.refresh()"); spin(40)
ok("H0 Refresh on screen 1 while a card is held there waits: no fetch", tickets() == t0 and not running(), (tickets(), t0))
ev("b", "root.refresh()"); spin(40); answer(B2)
ok("H1 held on screen 1: screen 2 shows the answer, screen 1 waits", "todo:2,6" in iids("b") and "todo:2,6" not in iids("a"))
ev("a", "boardView.holding = false"); spin(120)
ok("H2 let go: screen 1 shows that same answer, no new fetch", "todo:2,6" in iids("a") and tickets() == t0 + 1 and not running(), (iids("a"), tickets(), t0))
# --- the move watchdog: the board is fetched again --------------------------------------
ev("a", "root.moveIssue(root.columns[1].issues[0], root.columns[1], root.columns[2])"); spin(40)
ev("b", "root.refresh()"); spin(40); answer(B1)  # started during the move: may predate the write
t0 = tickets(); ev("a", "moveWatchdog.triggered()"); spin(120)
ok("W1 no answer to a move in 30 s: the board is fetched (not the saved answer)", tickets() == t0 + 1 and len(running()) == 1, (tickets(), t0))
answer(B1); ev("a", "moveProcess.running = false")
# --- sign out on screen 1 -----------------------------------------------------------
ev("b", "root.refresh()"); spin(40)
ev("a", "root.signOut()"); spin(40); answer_proc("a", "logout", {"state": "logged-out", "message": "Signed out of gitlab.com."})
gen = ev("a", "root.feed.generation")
answer(B2)
ok("S1 an answer started before sign-out reaches no screen", "todo:2,6" not in iids("b") and gen == 1 and ev("a", "root.setup") == "logged-out", (iids("b"), gen))
ok("S2 the service keeps no board after sign-out", ev("a", "Object.keys(root.feed.answers).length") == 0)
# --- private fallback ---------------------------------------------------------------
ok("P1 no private fetch ever ran on either screen", ev("a", "localFeed.tickets") == 0 and ev("b", "localFeed.tickets") == 0)
loops = [w for w in warnings if "oop" in w]
ok("Z no binding-loop warnings", not loops, loops)
ok("Z no QML warnings", not warnings, warnings[:3])
print("QML warnings:", len(warnings)); print("\n".join(warnings[:20]))
print("passed", sum(results), "failed", len(results) - sum(results))
shutil.rmtree(d, ignore_errors=True)
sys.exit(0 if all(results) else 1)
