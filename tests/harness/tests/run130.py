# v0.1.30: while a refresh of the board on screen is in flight (button, r, the
# timer) the header says "Refreshing…" instead of "Updated HH:MM", in the same
# dim color, and the header doesn't move; then "Updated HH:MM" again. A failed
# refresh still says "Couldn't refresh · showing HH:MM" (urgent) and keeps the
# board; a saved copy keeps its own "· updating…"; a move's text wins.
# Usage: run130.py <src> [outdir]   (previews: header-refreshing, header-updated, header-error)
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
out = sys.argv[2] if len(sys.argv) > 2 else None
h = Harness(sys.argv[1], {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": "group/app"})
status = lambda: h.ev("header.status.text")
same = lambda a, b: abs(a.redF() - b.redF()) < 0.01 and abs(a.greenF() - b.greenF()) < 0.01 and abs(a.blueF() - b.blueF()) < 0.01
def shot(name): QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(60); out and h.grab_card(os.path.join(out, name + ".png"))
def geom():  # the header's controls (x in the header: refresh spins): they must not move between states
    return [round(h.ev(("" if n == "header" else "header.") + n + ".x")) for n in ("refreshButton", "keysButton", "gear", "header")] + [round(h.ev("header.width")), round(h.ev("panel.contentWidth"))]
h.ev("root.opened = true"); h.spin(80); h.answer("board", BOARD); h.spin(120)
hhmm = h.ev("new Date(root.updatedAt).toLocaleTimeString(Qt.locale(), 'HH:mm')")
h.ok("U0 loaded: 'Updated HH:MM'", status() == "Updated " + hhmm, status())
g0 = geom(); shot("header-updated")
h.click(h.ev("header.refreshButton")); h.spin(60)
h.ok("F1 the refresh button: 'Refreshing…' while board-fetch runs, quiet like 'Updated'", status() == "Refreshing…" and bool(h.running("board")) and same(h.ev("header.status.color"), h.ev("root.quiet")), status())
h.ok("F2 the header doesn't move or resize", geom() == g0, [g0, geom()])
h.ok("F3 the board stays on screen and usable", h.ev("boardView.visible") and h.ev("root.canMove"))
shot("header-refreshing")
h.answer("board", BOARD); h.spin(80)
h.ok("F4 done: 'Updated HH:MM' again", status().startswith("Updated ") and not h.running("board"), status())
h.key(Qt.Key_R, "r"); h.spin(60)
h.ok("K1 r: 'Refreshing…'", status() == "Refreshing…" and bool(h.running("board")), status())
h.answer("board", BOARD); h.spin(80)
h.ev("refreshTimer.triggered()"); h.spin(60)
h.ok("T0 (v0.1.33) a tick less than an interval after the last fetch: no fetch, 'Updated' stays", status().startswith("Updated ") and not h.running("board"), status())
h.age_feed(); h.ev("refreshTimer.triggered()"); h.spin(60)
h.ok("T1 the 60s timer's refresh: 'Refreshing…' too", status() == "Refreshing…" and bool(h.running("board")), status())
# --- errors: the board stays, the error says so --------------------------------
h.answer("board", {"state": "error", "message": "GitLab did not answer within 30 seconds."}); h.spin(80)
h.ok("E1 a failed refresh: board kept, 'Couldn't refresh · showing HH:MM' in urgent", status().startswith("Couldn't refresh · showing ") and h.ev("boardView.visible") and same(h.ev("header.status.color"), h.ev("root.urgent")), status())
shot("header-error")
h.ev("root.refresh()"); h.spin(60)
h.ok("E2 trying again: 'Refreshing…', quiet (not the old error in red)", status() == "Refreshing…" and same(h.ev("header.status.color"), h.ev("root.quiet")), status())
h.answer("board", {"state": "error", "message": "offline"}); h.spin(80)
h.ok("E3 failing again: the error is back, board still there", status().startswith("Couldn't refresh") and h.ev("boardView.visible") and h.ev("root.refreshError") == "offline", status())
h.ev("root.refresh()"); h.answer("board", BOARD); h.spin(80)
h.ok("E4 then a good refresh clears it", status().startswith("Updated ") and h.ev("root.refreshError") == "", status())
# --- a board with a note (e.g. the fallback board) keeps it -------------------------
h.ev("root.refresh()"); h.answer("board", dict(BOARD, message="No board named Dev; showing Development.")); h.spin(80)
h.ev("root.refresh()"); h.spin(60)
h.ok("M1 a board's note stays while refreshing", status() == "No board named Dev; showing Development.  Refreshing…", status())
h.answer("board", BOARD); h.spin(80)
# --- a saved copy keeps its own note ------------------------------------------------
h.stop_all(); h.ev("root.switchTo('group/app', '7', 'Development')"); h.spin(40)
h.answer("cached", dict(BOARD, cached=True)); h.spin(60)
h.ok("S1 a saved copy while the first fetch runs: 'Saved … · updating…', not 'Refreshing…'", status().endswith("· updating…") and bool(h.running("board")), status())
h.answer("board", BOARD); h.spin(80)
h.ok("S2 fresh board: 'Updated HH:MM'", status().startswith("Updated "), status())
h.finish()
