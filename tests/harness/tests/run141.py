# v0.1.41: board-fetch ends by its 40 s deadline, so both watchdogs wait 50 s;
# a write the watchdog gave up on blocks the next one with a note ("still
# finishing") instead of silently; an unchanged refresh rebuilds no card; the
# refresh icon spins only while the popup is open; the
# sign-out question says it signs glab out on this computer.
# Usage: run141.py <src> [outdir]   (previews: still-finishing, bulk-still-finishing, sign-out-confirm)
import sys, os, json, copy; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import os
os.environ["OGB_SCALE"] = "1.5"
import lib
from lib import *
src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else None
P = "firelink21/phrase41"
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "run134.py")).read().split("ALL = []")[0].split("P = \"firelink21/phrase41\"")[1])
ALL = []
def ok(n, c, e=""): ALL.append(bool(c)); h.ok(n, c, e)
def shot(name):
    QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(80)
    if out: h.grab_card(os.path.join(out, name + ".png"))
h = Harness(src, {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": ["open", "research", "Closed"], "bots": FOUR})
h.ev("panel.availableCardHeight = %d; panel.availableCardWidth = 1460" % DESK)
h.ev("root.opened = true"); h.spin(60); h.answer("board", board()); h.spin(150)
col = lambda name: "root.columns.filter(function(c){ return c.name === %s })[0]" % json.dumps(name)
FINISH = "The last change is still finishing on GitLab. Try again in a moment."

# --- watchdogs above the deadline ----------------------------------------------------
bulk_wd = "(function(){ for (var i = 0; i < bulkBar.data.length; i++) if (bulkBar.data[i].interval !== undefined && bulkBar.data[i].triggered !== undefined && bulkBar.data[i].interval >= 45000) return bulkBar.data[i]; return null })()"
ok("W1 the move watchdog waits 50 s", h.ev("moveWatchdog.interval") == 50000)
ok("W2 the bulk watchdog waits 50 s", h.ev(bulk_wd + ".interval") == 50000)

# --- a move the watchdog gave up on ---------------------------------------------------
h.stop_all()
h.ev("root.moveIssue(%s.issues[0], %s, %s)" % (col("todo"), col("todo"), col("approved"))); h.spin(60)
ok("M1 a move runs", len(h.running("move")) == 1)
h.ev("moveWatchdog.triggered()"); h.spin(80)
h.answer("board", board()); h.spin(80)
ok("M2 the watchdog gave up: no move on screen, its process still running", h.ev("root.move") is None and len(h.running("move")) == 1)
h.ev("root.moveError = ''")
went = h.ev("root.moveIssue(%s.issues[0], %s, %s)" % (col("todo"), col("todo"), col("approved"))); h.spin(60)
ok("M3 the next move is refused with a note, not silently", went is False and h.ev("root.moveError") == FINISH and h.ev("header.status.text") == FINISH, h.ev("header.status.text"))
shot("still-finishing")
ok("M4 nothing else started", len(h.running("move")) == 1)
h.ev("root.moveError = ''")
ok("M4b a drag or Shift+H/L gets the same note", h.ev("root.requestMove(%s.issues[1], %s, %s)" % (col("todo"), col("todo"), col("approved"))) is False and h.ev("root.moveError") == FINISH)
h.ev("root.picked = [root.columns.filter(function(c){ return c.name === 'todo' })[0]].map(function(c){ return Logic.pickKey(c, 21) })"); h.spin(40)
h.ev("bulkBar.armMove(%s, '')" % col("approved")); h.spin(40)
ok("M4c bulk arming gets the note too", h.ev("bulkBar.mode") == "" and h.ev("bulkBar.note") == FINISH, [h.ev("bulkBar.mode"), h.ev("bulkBar.note")])
h.ev("bulkBar.reset(); root.picked = []"); h.spin(40)
h.answer("move", {"state": "ready", "message": "Moved #20 to approved."}); h.spin(80)
h.ev("root.refreshQueued = false"); h.stop_all(); h.answer("board", board()); h.spin(80)
went = h.ev("root.moveIssue(%s.issues[0], %s, %s)" % (col("todo"), col("todo"), col("approved"))); h.spin(60)
ok("M5 once it ended, moves go again", went is True and len(h.running("move")) == 1)
h.answer("move", {"state": "ready", "message": "Moved."}); h.spin(80); h.stop_all(); h.ev("root.refreshQueued = false; root.moveError = ''")
h.ev("root.refresh()"); h.spin(40); h.answer("board", board()); h.spin(120)

# --- a bulk card the watchdog gave up on ----------------------------------------------
h.ev("root.togglePick(%s, 20)" % col("todo")); h.spin(40)
h.ev("bulkBar.armMove(%s, '')" % col("approved")); h.spin(40)
h.ev("bulkBar.confirm()"); h.spin(60)
ok("B1 the run's card is written", len(h.running("move")) == 1 and len(h.ev("root.picked")) == 1, h.ev("root.picked"))
h.ev(bulk_wd + ".triggered()"); h.spin(80)
ok("B2 the watchdog stopped the run: results", h.ev("bulkBar.mode") == "results")
h.ev("bulkBar.done()"); h.spin(40)
h.ev("root.togglePick(%s, 21)" % col("todo")); h.spin(40)
h.ev("bulkBar.armMove(%s, '')" % col("approved")); h.spin(60)
ok("B3 arming again while that card still runs: a note, not armed", h.ev("bulkBar.mode") == "" and h.ev("bulkBar.note") == FINISH and len(h.ev("root.picked")) == 1, [h.ev("bulkBar.mode"), h.ev("bulkBar.note"), h.ev("root.picked")])
ok("B4 the note is on screen", h.ev("bulkBar.visible") and any(it.property("text") == FINISH for it in h.visible(lambda it: it.property("text") is not None)))
shot("bulk-still-finishing")
h.ev("root.moveError = ''")
ok("B5 a single move while that card still runs: the note", h.ev("root.requestMove(%s.issues[2], %s, %s)" % (col("todo"), col("todo"), col("approved"))) is False and h.ev("root.moveError") == FINISH)
h.stop_all(); h.ev("bulkBar.reset(); root.picked = []"); h.spin(40)

# --- an unchanged refresh rebuilds no card ----------------------------------------------
h.ev("root.refreshQueued = false"); h.ev("root.refresh()"); h.spin(40); h.answer("board", board()); h.spin(150)
rootObj = h.ev("root"); changes = []
rootObj.columnsChanged.connect(lambda: changes.append("columns")); rootObj.labelColorsChanged.connect(lambda: changes.append("colors"))
same = board(); same["updatedAt"] = "2026-10-30T15:27:00Z"
h.ev("root.refresh()"); h.spin(40); h.answer("board", same); h.spin(150)
ok("U1 same cards, newer time: columns and colours not replaced, no card rebuilt", changes == [], changes)
ok("U2 the header shows the new time", h.ev("root.updatedAt") == "2026-10-30T15:27:00Z")
h.ev("root.refresh()"); h.spin(40); h.answer("board", board(2)); h.spin(150)
ok("U3 a changed board: columns replaced", "columns" in changes and "colors" not in changes, changes)

# --- the refresh icon spins only while open ----------------------------------------------
# (The placeholder pulse and the issue view's loading bar already stop: they run
# while visible, and KeyboardPanel hides the card when closed.)
h.ev("root.opened = false"); h.spin(40)
h.ev("root.refresh()"); h.spin(60)
rot = lambda: h.ev("header.refreshButton.rotation")
h.until(lambda: rot() % 360 == 0)  # the spin winds down to upright
r0 = rot(); h.spin(300)
ok("A1 a fetch with the popup closed: refresh icon still, upright", h.ev("root.loading") and r0 % 360 == 0 and h.ev("header.refreshButton.rotation") == r0, r0)
ok("A2 the closed card is hidden, so visible-gated pulses stop too", h.ev("panel.visible") is False and h.ev("skeleton.visible") is False)
h.ev("root.opened = true")
ok("A3 open while loading: it spins", h.until(lambda: rot() % 360 != 0))
h.answer("board", board(2)); h.spin(1000)

# --- the one https check -------------------------------------------------------------------
n0 = len(h.launched())
for u in ['https://x/"a', "https://x/<b>", "javascript:alert(1)", "--new-window"]: h.ev("root.openUrl(%s)" % json.dumps(u))
ok("H1 openUrl drops a link the https check refuses", len(h.launched()) == n0, h.launched()[n0:])
h.ev("root.openUrl(\"https://gitlab.com/g/p/-/issues/1?q=it's\")")
ok("H2 and opens one it allows", h.launched()[n0:] == [["omarchy-launch-browser", "https://gitlab.com/g/p/-/issues/1?q=it's"]], h.launched()[n0:])

# --- sign out wording ------------------------------------------------------------------
h.ev("root.showView('settings')"); h.spin(60); h.answer("whoami", {"state": "ready", "message": "", "user": "o_devvy"}); h.spin(60)
h.ev("settingsView.confirming = true"); h.spin(80)
acc = next(it for it in h.walk() if it.objectName() == "" and it.property("text") is not None and "Sign out of glab" in str(it.property("text")))
ok("S1 the question says what it signs out", acc.property("text") == "Sign out of glab on gitlab.com? This also signs glab out in your terminal and scripts on this computer.")
shot("sign-out-confirm")
print("passed", sum(ALL), "failed", len(ALL) - sum(ALL))
