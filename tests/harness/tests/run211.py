# v0.1.111: alerts. (1) The bar icon's dot stays for an alert he hasn't seen:
# one the open refresh brings, or one that comes while the popup shows another
# view; one that comes while he watches the board is seen at once. (2) With a
# card or bot alert on, the background looks at the Refresh every setting, not
# the slowed pace. (3) "Last alert: #N in review · HH:MM" in the icon's tip
# and Settings > Alerts, with "Checking every 1 min." and an empty state.
# Two screens, one service (two.py). Usage: run211.py <src>
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import two; P = two.P; two.start({"alerts": {P: {"review": True, "idle": False}}}, "ogb-h211-"); from two import *

dots = lambda: [bool(ev(k, "alertDot.visible")) for k in ("a", "b")]
tips = lambda: [ev(k, "button.tooltipText") for k in ("a", "b")]
def status(k="a"):
    o = two.boards[k].findChild(QQuickItem, "alertStatus")
    return o.property("text") if o is not None and o.property("visible") else ""
def settle(data):
    for _ in range(4):
        if not running(): break
        answer(data); spin(60)
def hhmm(): return ev("a", "new Date(root.feed.lastAlert.at).toLocaleTimeString(Qt.locale(), 'HH:mm')")
D = board([], [], [row(4, ["review"]), row(2, ["review", "app-ui"], "Fix <b> & co"), row(3, ["review", "api"]), row(1, ["review"], "One")])
E = board([], [], [row(4, ["review"]), row(2, ["review", "app-ui"], "Fix <b> & co"), row(3, ["review", "api"]), row(1, ["review"], "One"), row(5, ["review"], "Five")])
F = board([], [], [row(4, ["review"]), row(2, ["review", "app-ui"], "Fix <b> & co"), row(3, ["review", "api"]), row(1, ["review"], "One"), row(5, ["review"], "Five"), row(8, ["review"], "Eight"), row(6, ["review"], "Six"), row(9, ["review"], "Nine")])
spin(150)

# --- (3) empty state ---------------------------------------------------------------------------------
ev("a", "root.opened = true"); spin(60); settle(A); ev("a", "root.showView('settings')"); spin(60)
ok("S0 Settings > Alerts before any alert: the pace and 'No alerts since the shell started.'", status() == "Checking every 1 min. No alerts since the shell started.", (status(), two.boards["a"].findChild(QQuickItem, "alertStatus"), ev("a","root.alerts"), ev("a","root.project")))
ok("S0b the tip has no second line yet", tips() == ["GitLabby · group/app"] * 2, tips())
ev("a", "root.showView('board')"); ev("a", "root.opened = false"); spin(60)

# --- (1) closed: the dot, and (3) the line on both screens -----------------------------------------
bg(); answer(A); spin(60)
age(); bg(); answer(B); spin(80)
ok("C1 popup closed: one notification, the dot on both screens", len(notes()) == 1 and dots() == [True, True], (len(notes()), dots()))
t = hhmm()
ok("C2 the tip: why the dot, then the last alert", tips() == ["GitLabby · group/app · an alert came\nLast alert: #2 in review · " + t] * 2, tips())
ev("b", "root.opened = true"); spin(60); settle(B); ev("b", "root.showView('settings')"); spin(60)
ok("C3 Settings > Alerts on the other screen says it too", status("b") == "Checking every 1 min. Last alert: #2 in review · " + t, status("b"))
ev("b", "root.showView('board')"); ev("b", "root.opened = false"); spin(60)

# --- (1) the open refresh brings an alert: the dot stays ----------------------------------------------
ev("a", "root.opened = true"); spin(80); settle(B); ev("a", "root.opened = false"); spin(60)
ok("O0 opening cleared the earlier one", dots() == [False, False] and ev("a", "root.feed.unseenAlerts") == 0)
age(); ev("a", "root.opened = true"); spin(60)
ok("O1 opening when due fetches", bool(running()))
answer(C); spin(100)
ok("O2 its answer brings an alert: notified, and the dot stays while open", len(notes()) == 2 and dots() == [True, True], (len(notes()), dots()))
ok("O3 the tip names the new one", "Last alert: #3 in review · " in tips()[0], tips())
ev("a", "root.opened = false"); spin(60)
ok("O4 still lit after closing", dots() == [True, True])
ev("a", "root.opened = true"); spin(80); settle(C)
ok("O5 the next opening clears it", dots() == [False, False])

# --- (1) open on the board: a later alert is seen at once ----------------------------------------------
age(); ev("a", "root.refresh(true)"); spin(60); answer(D); spin(100)
ok("B1 watching the board when it comes: notified, no dot", len(notes()) == 3 and dots() == [False, False], (len(notes()), dots()))
# --- (1) open on another view: the dot stays --------------------------------------------------------
ev("a", "root.showView('settings')"); spin(60)
age(); ev("a", "root.refresh(true)"); spin(60); answer(E); spin(100)
ok("V1 open on Settings when it comes: the dot stays", len(notes()) == 4 and dots() == [True, True], (len(notes()), dots()))
ok("V2 and Settings shows it at once", status().startswith("Checking every 1 min. Last alert: #5 in review · "), status())
ev("a", "root.opened = false"); spin(60)
ok("V3 lit after closing", dots() == [True, True])
ev("a", "root.opened = true"); spin(80); settle(E); ev("a", "root.opened = false"); spin(60)

# --- (1) after the open refresh lands, or with nothing to fetch, an alert on the board is seen ---------------
G = board([], [], [row(4, ["review"]), row(2, ["review", "app-ui"], "Fix <b> & co"), row(3, ["review", "api"]), row(1, ["review"], "One"), row(5, ["review"], "Five"), row(7, ["review"], "Seven")])
H = board([], [], [row(4, ["review"]), row(2, ["review", "app-ui"], "Fix <b> & co"), row(3, ["review", "api"]), row(1, ["review"], "One"), row(5, ["review"], "Five"), row(8, ["review"], "Eight")])
age(); ev("a", "root.opened = true"); spin(60)
ok("L0 opening when due fetches", bool(running()))
answer(E); spin(100)
age(); ev("a", "root.refresh(true)"); spin(60); answer(G); spin(100)
ok("L1 the open refresh answered, then an alert on the board: no dot", len(notes()) == 5 and dots() == [False, False], (len(notes()), dots()))
ev("a", "root.opened = false"); spin(60); ev("a", "root.opened = true"); spin(60)
ok("L2 opening again soon fetches nothing", not running())
age(); ev("a", "root.refresh(true)"); spin(60); answer(H); spin(100)
ok("L3 then an alert on the board: no dot", len(notes()) == 6 and dots() == [False, False], (len(notes()), dots()))
ev("a", "root.opened = false"); spin(60)
E = H

# --- (2) no slowdown in the background while a card alert is on ------------------------------------------
ev("a", "var p = {}; p[root.fetchKey] = { sig: 'x', calm: 9, active: false }; root.feed.paces = p"); spin(20)
ok("P0 the pace is slowed (4x)", ev("a", "root.cadence.sec") == 4 * ev("a", "root.refreshIntervalSec"), ev("a", "root.cadence.sec"))
ev("a", "(function(){ var f = root.feed, a = {}; for (var k in f.answers) a[k] = Object.assign({}, f.answers[k], { startedAt: Date.now() - (root.refreshIntervalSec * 1000 + 1000) }); f.answers = a })()")
ok("P1 just past the setting: the background looks", bg())
answer(F); spin(100)
ok("P2 and the cards that came are announced", headlines(notes())[-1] == "2 cards entered review", headlines(notes())[-1:])
ok("P2b the last alert reads as sent", "Last alert: 2 cards entered review · " in tips()[0], tips())
ev("a", "(function(){ var f = root.feed, a = {}; for (var k in f.answers) a[k] = Object.assign({}, f.answers[k], { startedAt: Date.now() - (root.refreshIntervalSec * 1000 - 5000) }); f.answers = a })()")
ok("P3 just under the setting: not yet", not bg())

# --- (3) sign out forgets it ----------------------------------------------------------------------------
ev("a", "root.feed.forget()"); spin(40)
ok("F1 forgotten on sign out or another server: no last alert", ev("a", "root.feed.lastAlert") is None and tips()[0].find("Last alert") == -1, tips())
ev("a", "root.settings = Object.assign({}, root.settings, { alerts: {} })"); spin(60); ev("a", "root.opened = true"); spin(60); settle(F); ev("a", "root.showView('settings')"); spin(60)
ok("F2 no alert on: no status line", status() == "")
loops = [w for w in warnings if "oop" in w]
ok("Z no binding-loop warnings", not loops, loops)
ok("Z no QML warnings", not warnings, warnings[:3])
print("passed", sum(results), "failed", len(results) - sum(results))
sys.stdout.flush(); os._exit(0 if all(results) else 1)
