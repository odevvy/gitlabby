# v0.1.50: a refresh shows. While any refresh runs with the popup open (the
# board, by r, the button or the timer, or the merge-request list on screen),
# the refresh icon spins, in the board, issue, MRs and Settings views; the
# cards stay and nothing moves. The bar that slid under the header is gone
# (v0.1.63). Usage: run150.py <src> [outdir]   (previews: refresh-{board,issue,mrs,settings})
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else None
ALL = []
def ok(n, c, e=""): ALL.append(bool(c)); h.ok(n, c, e)
h = Harness(src, {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": "group/app", "defaultCollapsed": [], "boardStates": {}, "refreshIntervalSec": 60})
h.ev("panel.availableCardHeight = 900; panel.availableCardWidth = 1460")
nobar = lambda: not any(it.objectName() == "refreshBar" for it in h.walk())
def spins():
    a = h.ev("header.refreshButton.rotation"); h.spin(120); return h.ev("header.refreshButton.rotation") != a
def shot(name):
    if out: QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(500); h.grab_card(os.path.join(out, name + ".png"))
# Cards: the board's card delegates (they alone carry movable and lifted).
cards = lambda: len(h.visible(lambda it: it.property("movable") is not None and it.property("lifted") is not None))
def settle():  # the answer is in: wait for the icon to finish its turn
    for _ in range(20):
        if not h.ev("header.refreshButton.rotation") % 360: break
        h.spin(100)
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(150); settle()
n0 = cards(); top0 = h.cls("BoardView").mapToScene(QPointF(0, 0)).y()
ok("R0 nothing running: the icon still, and no bar under the header", nobar() and not spins())
under = h.ev("header.mapToItem(null, 0, header.height).y + root.gap")
ok("R0b the board sits a gap under the header", abs(top0 - under) < 0.5, (top0, under))
h.key(Qt.Key_R, "r"); h.spin(60)
ok("R1 r: the icon spins, no bar", spins() and nobar())
ok("R5 the cards stay and nothing moves", cards() == n0 and n0 > 0 and abs(h.cls("BoardView").mapToScene(QPointF(0, 0)).y() - top0) < 0.5, (n0, cards()))
shot("refresh-board")
h.answer("board", BOARD); h.spin(100); settle()
ok("R6 the answer is in: the icon stops upright", h.ev("header.refreshButton.rotation") % 360 == 0)
h.age_feed(); h.ev("refreshTimer.triggered()"); h.spin(60)
ok("R7 an automatic refresh (the timer) spins it too", spins() and h.running("board") != [])
h.answer("board", BOARD); h.spin(100); settle()
# The issue view
h.ev("root.openIssue(root.columns[1].issues[0])"); h.spin(60); h.stop_all(); h.spin(30)
ok("R8 loading an issue's own data is not a refresh", not h.ev("root.refreshActive"))
h.age_feed(); h.ev("root.refresh()"); h.spin(60)
ok("R9 issue view: the spin", h.ev("root.view") == "issue" and spins())
shot("refresh-issue")
h.answer("board", BOARD); h.spin(100); settle(); h.stop_all()
# The MRs view: its own list loading counts
h.ev("root.showView('mrs')"); h.spin(60)
ok("R10 MRs view: the list loading spins it", h.running("mrs") != [] and spins(), h.running())
ANS = {"state": "ready", "message": "", "scope": "all", "updatedAt": "2026-10-31T13:00:00Z", "review": [], "mine": []}
h.answer("mrs", ANS); h.spin(80); settle()
ok("R11 the list in: the icon stops upright", not h.ev("root.refreshActive") and h.ev("header.refreshButton.rotation") % 360 == 0)
h.ev("mrsView.refresh()"); h.spin(60)
ok("R12 r in the MRs view (only the list loads): the spin", not h.ev("root.loading") and spins())
shot("refresh-mrs")
h.answer("mrs", ANS); h.spin(80); settle()
# Settings
h.ev("root.showView('settings')"); h.spin(60); h.stop_all(); h.spin(30)
h.age_feed(); h.ev("root.refresh()"); h.spin(60)
ok("R13 Settings: the spin", spins())
shot("refresh-settings")
h.ev("root.opened = false"); h.spin(60)
ok("R14 popup closed: no spin, even while loading", not h.ev("root.refreshActive"))
h.stop_all()
print("passed %d failed %d" % (sum(ALL), len(ALL) - sum(ALL)))
h.finish()
