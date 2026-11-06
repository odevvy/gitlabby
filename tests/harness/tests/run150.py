# v0.1.50: a refresh shows. While any refresh runs with the popup open (the
# board, by r, the button or the timer, or the merge-request list on screen),
# a small dot before the status breathes, in the board, issue, MRs and Settings
# views; the cards stay and nothing moves. A refresh you ask for (r, the
# button), the first load and the MR list make the dot accent and spin the
# icon; the timer's only breathes it grey (v0.1.63, which also dropped the bar
# that slid under the header). Usage: run150.py <src> [outdir]   (previews: refresh-{board,issue,mrs,settings})
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else None
ALL = []
def ok(n, c, e=""): ALL.append(bool(c)); h.ok(n, c, e)
h = Harness(src, {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": "group/app", "defaultCollapsed": [], "boardStates": {}, "refreshIntervalSec": 60})
h.ev("panel.availableCardHeight = 900; panel.availableCardWidth = 1460")
nobar = lambda: not any(it.objectName() == "refreshBar" for it in h.walk())
dot = lambda: next(it for it in h.walk() if it.objectName() == "refreshDot")
same = lambda a, c: abs(a.redF() - c.redF()) < 0.01 and abs(a.greenF() - c.greenF()) < 0.01 and abs(a.blueF() - c.blueF()) < 0.01
def breathes():
    a = dot().opacity(); h.spin(200); return dot().isVisible() and dot().opacity() != a
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
ok("R0 nothing running: the icon still, no dot, and no bar under the header", nobar() and not spins() and not dot().isVisible())
under = h.ev("header.mapToItem(null, 0, header.height).y + root.gap")
ok("R0b the board sits a gap under the header", abs(top0 - under) < 0.5, (top0, under))
h.key(Qt.Key_R, "r"); h.spin(60)
ok("R1 r: the icon spins, no bar", spins() and nobar())
d = dot(); st = h.ev("header.status")
ok("R1b ... and an accent dot breathes just before the status", breathes() and same(d.property("color"), h.ev("root.accent"))
   and abs(d.mapToScene(QPointF(d.width(), 0)).x() + h.ev("Style.space(8)") - (st.mapToScene(QPointF(st.width() - st.property("paintedWidth"), 0)).x())) < 1.5
   and abs(d.mapToScene(QPointF(0, d.height() / 2)).y() - st.mapToScene(QPointF(0, st.height() / 2)).y()) < 1.5)
h.ev("root.refresh(true)"); h.spin(60)
ok("R1c opening the popup meanwhile (refresh if due) joins it: still orange and spinning", spins() and same(dot().property("color"), h.ev("root.accent")))
ok("R5 the cards stay and nothing moves", cards() == n0 and n0 > 0 and abs(h.cls("BoardView").mapToScene(QPointF(0, 0)).y() - top0) < 0.5, (n0, cards()))
shot("refresh-board")
h.answer("board", BOARD); h.spin(100); settle()
ok("R6 the answer is in: the dot goes, the icon stops upright", not dot().isVisible() and h.ev("header.refreshButton.rotation") % 360 == 0)
h.age_feed(); h.ev("refreshTimer.triggered()"); h.spin(60)
ok("R7 an automatic refresh (the timer): only a grey dot breathes, the icon stays still", not spins() and breathes() and same(dot().property("color"), h.ev("root.quiet")) and h.running("board") != [])
h.answer("board", BOARD); h.spin(100); settle()
# The issue view
h.ev("root.openIssue(root.columns[1].issues[0])"); h.spin(60); h.stop_all(); h.spin(30)
ok("R8 loading an issue's own data is not a refresh", not h.ev("root.refreshActive"))
h.age_feed(); h.ev("root.refresh()"); h.spin(60)
ok("R9 issue view: the spin", h.ev("root.view") == "issue" and spins())
shot("refresh-issue")
h.answer("board", BOARD); h.spin(100); settle(); h.stop_all()
# The MRs view: its first load is the view's own spinner row (as To-do, 0.1.86); a reload spins the header
h.ev("root.showView('mrs')"); h.spin(60)
ok("R10 MRs view, first load: the spinner row, not the header", h.running("mrs") != [] and not h.ev("root.refreshActive")
   and any(it.objectName() == "mrsMessage" and it.property("spinning") is True for it in h.visible(lambda it: True)), h.running())
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
