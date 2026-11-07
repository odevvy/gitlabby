# v0.1.104: Settings by keyboard. Each segmented control and check box is a
# Tab stop with the focus outline; Left / Right pick a segment, Enter or Space
# toggles a box; Tab scrolls the focused control into view.
# Usage: run204.py <src>
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
h = Harness(sys.argv[1], {
    "id": "odevvy.gitlabby", "settingsRevision": 2,
    "defaultProject": "group/app", "defaultBoardId": "7", "defaultBoardName": "Development",
    "defaultCollapsed": [], "boardStates": {}, "refreshIntervalSec": 60,
    "favorites": [], "serverFavorites": {}
})
h.ev("panel.availableCardHeight = 420; panel.availableCardWidth = 1460")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(200)
ev = h.ev
ev("root.showView('settings')"); h.spin(120)
h.answer("whoami", {"state": "ready", "message": "", "user": "o_devvy"}); h.spin(60)
def rings(): return [it for it in h.walk() if it.objectName() == "focusRing" and it.isVisible()]
def tab(): QTest.keyClick(h.win, Qt.Key_Tab); h.spin(30)
def ring_on(name): return ev("root.kbFocus ? root.kbFocus.objectName : ''") == name and len(rings()) == 1
def tab_to(pred, n=80):
    for _ in range(n):
        tab()
        if pred(): return True
    return False
def flick(): return ev("(function(){ for (var p = root.kbFocus; p; p = p.parent) if (p.flicking !== undefined) return p.contentY; return -1 })()")

h.ok("R0 Tab reaches Refresh every", tab_to(lambda: ring_on("refreshPane")) and len(rings()) == 1)
h.key(Qt.Key_Right); h.spin(40)
h.ok("R1 Right picks the next interval", ev("root.refreshIntervalSec") == 120)
h.key(Qt.Key_Right); h.key(Qt.Key_Right); h.key(Qt.Key_Right); h.key(Qt.Key_Right); h.spin(40)
h.ok("R2 stops at the last", ev("root.refreshIntervalSec") == 900)
h.key(Qt.Key_Left); h.spin(40)
h.ok("R3 Left goes back, the outline stays", ev("root.refreshIntervalSec") == 300 and ring_on("refreshPane"))
for _ in range(6): h.key(Qt.Key_Left)
h.spin(40)
h.ok("R4 stops at the first", ev("root.refreshIntervalSec") == 30)
h.key(Qt.Key_Return); h.spin(40)
h.ok("R5 Enter steps it on", ev("root.refreshIntervalSec") == 60)
h.ok("L0 Tab: Open links in", tab_to(lambda: ring_on("linkPane"), 3))
mode0 = ev("root.linkMode")
h.key(Qt.Key_Right); h.spin(40)
h.ok("L1 Right: App window", ev("root.linkMode") == "app")
h.key(Qt.Key_Left); h.spin(40)
h.ok("L2 Left: Browser tab", ev("root.linkMode") == "browser")
h.key(Qt.Key_Space); h.spin(40)
h.ok("L3 Space switches", ev("root.linkMode") == "app")
tab()
h.ok("C0 next stop: the unlit box", ev("root.kbFocus.parent.objectName") == "unlitRow" and len(rings()) == 1)
u0 = ev("root.iconUnlit")
h.key(Qt.Key_Space); h.spin(40)
h.ok("C1 Space toggles it", ev("root.iconUnlit") == (not u0))
h.key(Qt.Key_Return); h.spin(40)
h.ok("C2 Enter toggles it back", ev("root.iconUnlit") == u0)
tab()
a0 = ev("root.showAvatars")
h.key(Qt.Key_Space); h.spin(40)
h.ok("C3 Show avatars toggles by key", ev("root.kbFocus.parent.objectName") == "avatarsRow" and ev("root.showAvatars") == (not a0))
tab()
c0 = len(ev("root.saved('defaultCollapsed', [])") or [])
h.key(Qt.Key_Space); h.spin(40)
h.ok("C4 a Start collapsed box toggles by key", len(ev("root.saved('defaultCollapsed', [])") or []) == c0 + 1)
# Alerts sit lower: Tab scrolls Settings to them.
ok = tab_to(lambda: ev("root.kbFocus && root.kbFocus.parent && root.kbFocus.parent.modelData !== undefined && root.kbFocus.parent.modelData.kind === 'review'") is True)
h.ok("S1 Tab reaches the first alert box, scrolled into view", ok and flick() > 0, flick())
y = ev("root.kbFocus.mapToItem(settingsView, 0, 0).y"); hh = ev("settingsView.height")
h.ok("S2 the focused box is inside the view", 0 <= y and y + ev("root.kbFocus.height") <= hh + 0.5, (y, hh))
k0 = ev("root.alerts.review === true")
h.key(Qt.Key_Space); h.spin(40)
h.ok("S3 Space toggles the alert", ev("root.alerts.review === true") == (not k0))
sys.exit(h.finish())
