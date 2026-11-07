# v0.1.103: Tab / Shift+Tab move a focus outline across the popup's controls
# (header, shared buttons); Enter or Space press it; Esc drops it. Ctrl+Tab /
# Ctrl+Shift+Tab switch bar panels.
# Usage: run203.py <src>
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
h = Harness(sys.argv[1], {
    "id": "odevvy.gitlabby", "settingsRevision": 2,
    "defaultProject": "group/app", "defaultBoardId": "7", "defaultBoardName": "Development",
    "defaultCollapsed": [], "boardStates": {}, "refreshIntervalSec": 60,
    "favorites": [], "serverFavorites": {}
})
h.ev("panel.availableCardHeight = 520; panel.availableCardWidth = 1460")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(200)
ev = h.ev
def rings(): return [it for it in h.walk() if it.objectName() == "focusRing" and it.isVisible()]
def tab(n=1, back=False):
    for _ in range(n): QTest.keyClick(h.win, Qt.Key_Backtab if back else Qt.Key_Tab, Qt.ShiftModifier if back else Qt.NoModifier)
    h.spin(40)
def fx(): return ev("root.kbFocus ? root.kbFocus.mapToItem(null, 0, 0).x : -1")
def ftip(): return ev("root.kbFocus ? String(root.kbFocus.tip || root.kbFocus.label || '') : ''")

h.ok("T0 no outline before Tab", rings() == [] and ev("root.kbFocus") is None)
ev("root.moveCursor(0, 1)"); h.spin(40)
tab()
h.ok("T1 Tab outlines the first control (the title), only one", len(rings()) == 1 and ev("root.kbFocus.objectName") == "" and fx() < 40, (len(rings()), fx()))
h.ok("T2 the board cursor gives way", ev("root.cursor") is None)
xs = [fx()]
for _ in range(7): tab(); xs.append(fx())
h.ok("T3 Tab walks the header left to right", all(b > a for a, b in zip(xs, xs[1:])), xs)
h.ok("T4 still one outline", len(rings()) == 1)
tab(back=True)
h.ok("T5 Shift+Tab steps back", abs(fx() - xs[-2]) < 0.5, (fx(), xs[-2]))
n = ev("root.focusOrder().length")
tab(n)
h.ok("T6 Tab wraps around", abs(fx() - xs[-2]) < 0.5)
QTest.keyClick(h.win, Qt.Key_Escape); h.spin(40)
h.ok("E1 Esc drops the outline, the popup stays", rings() == [] and ev("root.opened") is True and ev("root.view") == "board")
last = ev("root.focusOrder()[root.focusOrder().length - 1]")
h.ok("E2a the gear is last, even while refresh spins", ev("root.focusOrder()[root.focusOrder().length - 1].tip") == "Settings (s)")
tab(back=True)
h.ok("E2 Shift+Tab with no outline starts at the last control", ev("root.kbFocus") == last and len(rings()) == 1)
QTest.keyClick(h.win, Qt.Key_Escape); h.spin(40)
# Tab to the gear and press Enter: Settings opens, the outline goes.
tab()
for _ in range(n):
    if ftip() == "Settings (s)": break
    tab()
h.ok("A0 Tab reaches the gear", ftip() == "Settings (s)")
h.key(Qt.Key_Return); h.spin(80)
h.ok("A1 Enter presses it: Settings", ev("root.view") == "settings" and rings() == [])
# Shared buttons take focus too: the view's back glyph (GlyphButton).
for _ in range(40):
    tab()
    if ev("root.kbFocus && root.kbFocus.glyph !== undefined"): break
h.ok("A2 a GlyphButton takes the outline", ev("root.kbFocus && root.kbFocus.glyph !== undefined") is True)
h.key(Qt.Key_Space); h.spin(80)
h.ok("A3 Space presses it", ev("root.view") == "board")
# Arrows go back to the board cursor.
tab(); h.key(Qt.Key_Down); h.spin(40)
h.ok("M1 an arrow drops the outline for the board cursor", rings() == [] and ev("root.cursor") is not None)
# Ctrl+Tab / Ctrl+Shift+Tab: bar panels, focus untouched.
ev("root.switchedPanel = 0"); tab(); f0 = fx()
QTest.keyClick(h.win, Qt.Key_Tab, Qt.ControlModifier); h.spin(40)
h.ok("C1 Ctrl+Tab: next bar panel, outline stays", ev("root.switchedPanel") == 1 and abs(fx() - f0) < 0.5)
QTest.keyClick(h.win, Qt.Key_Backtab, Qt.ControlModifier | Qt.ShiftModifier); h.spin(40)
h.ok("C2 Ctrl+Shift+Tab: previous bar panel", ev("root.switchedPanel") == -1 and abs(fx() - f0) < 0.5)
# An ActionButton takes focus too (the Sign out confirmation).
ev("root.kbFocus = null"); ev("root.showView('settings')"); h.spin(80); ev("settingsView.confirming = true"); h.spin(60)
for _ in range(80):
    tab()
    if ev("root.kbFocus && root.kbFocus.main !== undefined"): break
h.ok("B1 an ActionButton takes the outline", ev("root.kbFocus && root.kbFocus.main !== undefined") is True and len(rings()) == 1, ftip())
sys.exit(h.finish())
