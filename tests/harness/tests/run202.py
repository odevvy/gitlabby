# v0.1.102: many starred boards scroll inside a bounded jump menu; Browse all
# projects stays pinned below; keys keep the selected row in view.
# Usage: run202.py <src>
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
favs = [{"project": "group/app", "id": str(100 + i), "name": "Board %d" % i} for i in range(1, 13)]
h = Harness(sys.argv[1], {
    "id": "odevvy.gitlabby", "settingsRevision": 2,
    "defaultProject": "group/app", "defaultBoardId": "7", "defaultBoardName": "Development",
    "defaultCollapsed": [], "boardStates": {}, "refreshIntervalSec": 60,
    "favorites": favs, "serverFavorites": {}
})
h.ev("panel.availableCardHeight = 520; panel.availableCardWidth = 1460")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(200)
ev = h.ev
def one(name): return next((it for it in h.walk() if it.objectName() == name and it.isVisible()), None)
def sy(it): return it.mapToScene(QPointF(0, 0)).y()

ev("root.openJumpMenu()"); h.spin(80)
jm, jl, sb = one("jumpMenu"), one("jumpList"), one("jumpScrollBar")
card = ev("header.parent.height"); card_top = ev("header.parent.mapToItem(null, 0, 0).y")
h.ok("S0 13 boards in the menu", ev("root.jumpBoards.length") == 13)
h.ok("S1 the list is bounded and scrolls", jl is not None and jl.height() < jl.property("contentHeight") and jl.property("interactive") is True, (jl and jl.height(), jl and jl.property("contentHeight")))
h.ok("S2 the menu ends inside the card", sy(jm) + jm.height() <= card_top + card + 0.5, (sy(jm) + jm.height(), card_top + card))
browse = [it for it in h.walk() if it.objectName() == "browseHover" and it.isVisible()][0]
h.ok("S3 Browse is pinned below the list, inside the menu", sy(browse) >= sy(jl) + jl.height() - 0.5 and sy(browse) + browse.height() <= sy(jm) + jm.height() + 0.5)
h.ok("S4 a scroll bar shows", sb is not None)
rows = [it for it in h.walk() if it.objectName() == "jumpHover"]
h.ok("S5 rows keep their full height", all(abs(r.height() - (ev("Style.space(56)") - 2 * ev("Style.space(2)"))) < 0.5 for r in rows))
for _ in range(12): h.key(Qt.Key_Down)
h.spin(80)
h.ok("K1 Down to the last board scrolls it into view", ev("root.menuIndex") == 12 and jl.property("contentY") > 0 and abs(jl.property("contentY") + jl.height() - jl.property("contentHeight")) < 1, jl.property("contentY"))
h.ok("K2 the scroll bar moved to the bottom", abs(sy(sb) + sb.height() - (sy(jl) + jl.height())) < 1.5)
h.key(Qt.Key_Down); h.spin(40)
h.ok("K3 one more Down reaches the pinned Browse", ev("root.menuIndex") == 13 and browse.property("color").alpha() > 0)
for _ in range(13): h.key(Qt.Key_Up)
h.spin(80)
h.ok("K4 Up to the top scrolls back", ev("root.menuIndex") == 0 and jl.property("contentY") == 0)
h.key(Qt.Key_Escape); h.spin(40)
# Few boards: no scrolling, no bar.
ev("root.persist({ favorites: [] })"); h.spin(80)
ev("root.openJumpMenu()"); h.spin(80)
jl2 = one("jumpList")
h.ok("F1 one board: the list fits, no bar", jl2 is not None and abs(jl2.height() - jl2.property("contentHeight")) < 0.5 and one("jumpScrollBar") is None)
sys.exit(h.finish())
