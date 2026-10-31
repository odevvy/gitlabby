# v0.1.50: a refresh shows. While any refresh runs with the popup open (the
# board, by r, the button or the timer, or the merge-request list on screen),
# a 2px accent bar slides along a faint track under the header and the refresh
# icon spins, in the board, issue, MRs and Settings views; the cards stay and
# nothing moves. Usage: run150.py <src> [outdir]   (previews: refresh-{board,issue,mrs,settings})
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else None
ALL = []
def ok(n, c, e=""): ALL.append(bool(c)); h.ok(n, c, e)
h = Harness(src, {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": "group/app", "defaultCollapsed": [], "boardStates": {}, "refreshIntervalSec": 60})
h.ev("panel.availableCardHeight = 900; panel.availableCardWidth = 1460")
bar = lambda: next(it for it in h.walk() if it.objectName() == "refreshBar")
shown = lambda: bar().isVisible()
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
ok("R0 nothing running: no bar, the icon still", not shown() and not spins())
under = h.ev("header.mapToItem(null, 0, header.height).y + root.gap")
ok("R0b the bar takes no room: the board sits a gap under the header", abs(top0 - under) < 0.5, (top0, under))
h.key(Qt.Key_R, "r"); h.spin(60)
b = bar(); hb = h.ev("header.mapToItem(null, 0, header.height).y"); by = b.mapToScene(QPointF(0, 0)).y()
ok("R1 r: the bar shows under the header, inside the gap above the board", shown() and hb <= by and by + b.height() <= top0, (hb, by, top0))
ok("R2 it is 2px, as wide as the header, a faint track", abs(b.height() - 2) < 0.5 and abs(b.width() - h.ev("header.width")) < 1, (b.height(), b.width()))
slider = b.childItems()[1]; track = b.childItems()[0]
same = lambda a, c: abs(a.redF() - c.redF()) < 0.01 and abs(a.greenF() - c.greenF()) < 0.01 and abs(a.blueF() - c.blueF()) < 0.01
ok("R3 track faint, slider accent", same(track.property("color"), h.ev("root.faint")) and same(slider.property("color"), h.ev("root.accent")))
x0 = slider.x(); h.spin(200)
ok("R4 the slider moves and the icon spins", slider.x() != x0 and spins(), (x0, slider.x()))
ok("R5 the cards stay and nothing moves", cards() == n0 and n0 > 0 and abs(h.cls("BoardView").mapToScene(QPointF(0, 0)).y() - top0) < 0.5, (n0, cards()))
shot("refresh-board")
h.answer("board", BOARD); h.spin(100); settle()
ok("R6 the answer is in: the bar goes, the icon stops upright", not shown() and h.ev("header.refreshButton.rotation") % 360 == 0)
h.age_feed(); h.ev("refreshTimer.triggered()"); h.spin(60)
ok("R7 an automatic refresh (the timer) shows it too", shown() and h.running("board") != [])
h.answer("board", BOARD); h.spin(100); settle()
# The issue view
h.ev("root.openIssue(root.columns[1].issues[0])"); h.spin(60); h.stop_all(); h.spin(30)
ok("R8 loading an issue's own data is not a refresh", not shown())
h.age_feed(); h.ev("root.refresh()"); h.spin(60)
ok("R9 issue view: the bar and the spin", h.ev("root.view") == "issue" and shown() and spins())
shot("refresh-issue")
h.answer("board", BOARD); h.spin(100); settle(); h.stop_all()
# The MRs view: its own list loading counts
h.ev("root.showView('mrs')"); h.spin(60)
ok("R10 MRs view: the list loading shows it", h.running("mrs") != [] and shown() and spins(), h.running())
ANS = {"state": "ready", "message": "", "scope": "all", "updatedAt": "2026-10-31T13:00:00Z", "review": [], "mine": []}
h.answer("mrs", ANS); h.spin(80); settle()
ok("R11 the list in: no bar", not shown())
h.ev("mrsView.refresh()"); h.spin(60)
ok("R12 r in the MRs view (only the list loads): the bar and the spin", not h.ev("root.loading") and shown() and spins())
shot("refresh-mrs")
h.answer("mrs", ANS); h.spin(80); settle()
# Settings
h.ev("root.showView('settings')"); h.spin(60); h.stop_all(); h.spin(30)
h.age_feed(); h.ev("root.refresh()"); h.spin(60)
ok("R13 Settings: the bar and the spin", shown() and spins())
shot("refresh-settings")
h.ev("root.opened = false"); h.spin(60)
ok("R14 popup closed: no bar, no spin, even while loading", not h.ev("root.refreshActive"))
h.stop_all()
print("passed %d failed %d" % (sum(ALL), len(ALL) - sum(ALL)))
h.finish()
