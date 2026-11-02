# v0.1.70: the refresh pace in plain words. The tip on "Updated" names the
# setting first, then the slowdown (or speed-up) and why, and says when an
# alert also refreshes it with the popup closed; Settings says under
# "Refresh every" that the pace slows while the board is quiet.
# Usage: run170.py <src>
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
P = "group/app"
h = Harness(sys.argv[1], {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": [], "boardStates": {}, "refreshIntervalSec": 120})
h.ev("panel.availableCardHeight = 900; panel.availableCardWidth = 1460")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(300)
# --- the tip on "Updated" -----------------------------------------------------------------
def tip():
    st = h.ev("header.status"); QTest.mouseMove(h.win, h.scene(st, 0.97, 0.5)); h.spin(700)
    t = [str(c.property("text")) for it in h.walk() for c in it.children() if c.metaObject().className().startswith("IconTip") and c.property("visible")]
    QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(60); return t
h.ok("A1 at the setting: just the setting", tip() == ["Every 2 min"], tip())
h.ev("root.setAlert('review', true)"); h.spin(100)
watched = h.ev("root.feed.watchedKeys.indexOf(root.fetchKey) >= 0")
h.ok("A2 an alert on: the board is refreshed while closed too, and the tip says so", watched and tip() == ["Every 2 min · also while closed, for alerts"], (watched, tip()))
h.ev("root.setAlert('review', false)"); h.spin(100)
h.ok("A3 alert off: not watched, the tip drops it", not h.ev("root.feed.watchedKeys.indexOf(root.fetchKey) >= 0") and tip() == ["Every 2 min"], tip())
sys.exit(h.finish())
