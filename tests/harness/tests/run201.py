# v0.1.101: an open header menu owns the keys. Arrows move its selection,
# Enter or Space chooses it, Escape closes it; nothing reaches the board.
# Usage: run201.py <src>
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
h = Harness(sys.argv[1], {
    "id": "odevvy.gitlabby", "settingsRevision": 2,
    "defaultProject": "group/app", "defaultBoardId": "7", "defaultBoardName": "Development",
    "defaultCollapsed": [], "boardStates": {}, "refreshIntervalSec": 60,
    "favorites": [{"project": "group/wf", "id": "", "name": "Workflow labels"}],
    "serverFavorites": {}
})
h.ev("panel.availableCardHeight = 520; panel.availableCardWidth = 1460")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(200)
ev = h.ev

def lit(name):
    its = [it for it in h.walk() if it.objectName() == name and it.isVisible()]
    its.sort(key=lambda it: it.mapToScene(QPointF(0, 0)).y())  # top to bottom
    return [bool(it.property("color").alpha() > 0) for it in its]

# Jump menu: rows = default, wf favorite, then Browse.
ev("root.cursor = null")
ev("root.openJumpMenu()"); h.spin(60)
h.ok("J0 jump open, 2 boards", ev("root.headerMenu") == "jump" and ev("root.jumpBoards.length") == 2)
h.ok("J1 nothing lit before a key", not any(lit("jumpHover")) and not any(lit("browseHover")))
h.key(Qt.Key_Down); h.spin(40)
h.ok("J2 Down selects row 2 and lights only it", ev("root.menuIndex") == 1 and lit("jumpHover") == [False, True], (lit("jumpHover"), ev("root.menuIndex"), ev("root.menuKeys")))
h.ok("J3 the board cursor did not move", ev("root.cursor") is None)
h.key(Qt.Key_Down); h.spin(40)
h.ok("J4 Down reaches Browse", ev("root.menuIndex") == 2 and lit("browseHover") == [True] and not any(lit("jumpHover")))
h.key(Qt.Key_Down); h.spin(40)
h.ok("J5 stops at the last row", ev("root.menuIndex") == 2)
h.key(Qt.Key_Up); h.key(Qt.Key_Up); h.key(Qt.Key_Up); h.spin(40)
h.ok("J6 Up stops at the first row", ev("root.menuIndex") == 0 and lit("jumpHover") == [True, False])
h.key(Qt.Key_M, "m"); h.key(Qt.Key_X, "x"); h.key(Qt.Key_R, "r"); h.spin(60)
h.ok("J7 letters do not reach the board", ev("root.view") == "board" and ev("root.headerMenu") == "jump" and not h.running("board"))
h.key(Qt.Key_Down); h.key(Qt.Key_Return); h.spin(80)
h.ok("J8 Enter jumps to the selected board", ev("root.headerMenu") == "" and ev("root.project") == "group/wf")
h.answer("board", dict(BOARD, project="group/wf", board={"id": "", "name": "Workflow labels"}, boards=[])); h.spin(80)
ev("root.openJumpMenu()"); h.spin(60)
h.ok("J9 reopening starts at the top, nothing lit", ev("root.menuIndex") == 0 and not any(lit("jumpHover")))
h.key(Qt.Key_Down); h.key(Qt.Key_Down); h.key(Qt.Key_Space); h.spin(80)
h.ok("J10 Space on Browse opens the picker", ev("root.view") == "picker" and ev("root.headerMenu") == "")
ev("root.showView('board')"); h.spin(80)

# Default menu (not on the default board): Go to / Make this your default.
ev("root.openDefaultMenu()"); h.spin(40)
h.ok("D0 default menu open", ev("root.headerMenu") == "default")
h.key(Qt.Key_Down); h.spin(40)
h.ok("D1 Down lights Make", ev("root.menuIndex") == 1 and lit("defHover") == [False, True])
h.key(Qt.Key_Escape); h.spin(40)
h.ok("D2 Escape closes only the menu", ev("root.headerMenu") == "" and ev("root.view") == "board" and ev("root.opened") is True)
ev("root.openDefaultMenu()"); h.spin(40)
h.key(Qt.Key_Return); h.spin(80)
h.ok("D3 Enter with no move chooses the first row (Go to your default)", ev("root.headerMenu") == "" and ev("root.project") == "group/app")
h.answer("board", BOARD); h.spin(80)

# Hover takes the selection back from keys: exactly one lit row.
ev("root.openJumpMenu()"); h.spin(60)
h.key(Qt.Key_Down); h.spin(40)
rows = sorted([it for it in h.walk() if it.objectName() == "jumpHover" and it.isVisible()], key=lambda it: it.mapToScene(QPointF(0, 0)).y())
QTest.mouseMove(h.win, h.scene(rows[0])); h.spin(80)
h.ok("H1 hovering row 1 moves the selection there", ev("root.menuKeys") is False and ev("root.menuIndex") == 0 and lit("jumpHover") == [True, False], lit("jumpHover"))
h.key(Qt.Key_Escape); h.spin(40)
h.ok("H2 Escape closed it", ev("root.headerMenu") == "")
sys.exit(h.finish())
