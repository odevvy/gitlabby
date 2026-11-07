# v0.1.100: a header bots button (md-robot-outline) between columns and
# keyboard toggles the bots row: hidden means no row and no gap, the board
# moves up. Global setting botsHidden; key b; only shown with bots.
# Usage: run200.py <src>
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
from PySide6.QtGui import QFontMetricsF
P = "group/app"
BOTS = {P: {"bots": [{"label": "app-ui", "name": "App UI"}, {"label": "api", "name": "API Engineer"}], "busyLists": []}}
h = Harness(sys.argv[1], {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": [], "boardStates": {}, "refreshIntervalSec": 60, "bots": BOTS})
h.ev("panel.availableCardHeight = 620; panel.availableCardWidth = 1460")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(300)
ev = h.ev
writes = lambda: ev("root.bar.shell.writes") or []
bb = ev("header.botsButton")
g = next(c for c in bb.childItems() if c.objectName() == "headGlyph")
h.ok("B0 bots row shown, button visible", ev("botsRow.visible") is True and bb.isVisible())
h.ok("B1 glyph is md-robot-outline U+F167A", g.property("text") == chr(0xF167A), [hex(ord(c)) for c in g.property("text")])
fm = QFontMetricsF(g.property("font"))
h.ok("B2 the glyph renders (in font, has width)", fm.inFontUcs4(0xF167A) and g.property("implicitWidth") > 4, (fm.inFontUcs4(0xF167A), g.property("implicitWidth")))
x = lambda it: it.mapToScene(QPointF(0, 0)).x()
h.ok("B3 order (v0.1.112): tabs, columns, bots ... refresh, keyboard, settings",
     x(ev("header.tabs")) < x(ev("header.columnsButton")) < x(bb) < x(ev("header.status")) < x(ev("header.refreshButton")) < x(ev("header.keysButton")) < x(ev("header.gear")))
h.ok("B4 lit (accent) while shown", g.property("color") == ev("root.accent") and bb.property("active") is True)
h.ok("B5 tip while shown", bb.property("tip") == "Hide bots (b)")
fw_with = ev("header.fixedWidth")
top_shown = ev("boardView.mapToItem(keyCatcher, 0, 0).y")
n = len(writes())
ev("root.headerMenu = 'jump'")
h.click(bb); h.spin(120)
h.ok("H1 click hides the row (height 0, no gap)", ev("botsRow.visible") is False and ev("botsRow.height") == 0 and ev("botsRow.anchors.topMargin") == 0)
h.ok("H2 the board moves up", ev("boardView.mapToItem(keyCatcher, 0, 0).y") < top_shown, (top_shown, ev("boardView.mapToItem(keyCatcher, 0, 0).y")))
h.ok("H3 persisted botsHidden: true", len(writes()) > n and writes()[-1].get("botsHidden") is True)
h.ok("H4 click clears headerMenu", ev("root.headerMenu") == "")
h.ok("H5 button stays, unlit, tip Show", bb.isVisible() and bb.property("active") is False and g.property("color") != ev("root.accent") and bb.property("tip") == "Show bots (b)")
h.key(Qt.Key_B, "b"); h.spin(120)
h.ok("K1 b shows the row again", ev("botsRow.visible") is True and writes()[-1].get("botsHidden") is False)
h.key(Qt.Key_B, "b"); h.spin(80)
h.ok("K2 b hides it", ev("botsRow.visible") is False)
h.ev("root.showView('settings')"); h.spin(80); h.answer("whoami", {"state": "ready", "message": "", "user": "o_devvy"}); h.spin(60)
ev("root.headerMenu = 'jump'")
h.key(Qt.Key_B, "b"); h.spin(80)
h.ok("K3 b does nothing off the board", ev("root.botsHidden") is True and not bb.isVisible() and ev("root.headerMenu") == "jump")
ev("root.headerMenu = ''")
h.ev("root.showView('board')"); h.spin(100)
h.ok("K4 the key is listed", any(k == "b" for g2 in ev("Logic.keyGroups") for k, a in g2["keys"]))
# No bots: no button, b does nothing
h2 = h
ev("root.persist({ bots: {} })"); h.spin(120)
h.ok("N1 no bots: no button", not bb.isVisible() and ev("root.hasBots") is False)
h.ok("B6 header width sums include the button", abs(fw_with - ev("header.fixedWidth") - (bb.property("implicitWidth") + ev("Style.space(4)"))) < 0.5, (fw_with, ev("header.fixedWidth"), bb.property("implicitWidth")))
n = len(writes()); h.key(Qt.Key_B, "b"); h.spin(60)
h.ok("N2 no bots: b writes nothing", len(writes()) == n)
sys.exit(h.finish())
