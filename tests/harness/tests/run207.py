# v0.1.107: Sign out says before it runs that it also deletes this server's
# saved board cache (and nothing about settings or favorites); the Sign out
# action is a 32 point target with side padding, a quiet hover fill and the
# focus outline (Enter or Space asks the question).
# Usage: run207.py <src>
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
P = "group/app"
BOARD = {"state": "ready", "project": P, "updatedAt": "2026-10-31T13:20:00Z", "message": "", "labelColors": {}, "boards": [{"id": 1, "name": "Dev"}], "board": {"id": 1, "name": "Dev"}, "fallback": False,
  "columns": [{"name": "Open", "kind": "open", "issues": []}, {"name": "Closed", "kind": "closed", "issues": []}]}
NOTE = "This also deletes this server's saved board cache on this computer."
h = Harness(sys.argv[1], {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": [], "favorites": [], "serverFavorites": {}})
h.ev("panel.availableCardHeight = 700; panel.availableCardWidth = 1460")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(150)
ev = h.ev
def named(n): return [it for it in h.walk() if it.objectName() == n and it.isVisible()]
def link(): return h.visible(lambda it: it.metaObject().className().startswith("BoardText") and it.property("text") == "Sign out")
def texts(): return [str(it.property("text")) for it in h.walk() if it.isVisible() and it.property("text") is not None]
def tab(): QTest.keyClick(h.win, Qt.Key_Tab); h.spin(30)
def tab_to(pred, n=60):
    for _ in range(n):
        tab()
        if pred(): return True
    return False
S = lambda v: ev("Style.space(%d)" % v)

ev("root.showView('settings')"); h.spin(80); h.answer("whoami", {"state": "ready", "message": "", "user": "o_devvy"}); h.spin(80)
QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(60)
lk = link()
h.ok("T1 Sign out is 32 points high", len(lk) == 1 and abs(lk[0].height() - S(32)) < 0.5, [l.height() for l in lk])
h.ok("T2 side padding: wider than its words", len(lk) == 1 and lk[0].property("leftPadding") >= S(12) - 0.5 and lk[0].property("rightPadding") >= S(12) - 0.5
     and lk[0].width() - lk[0].property("contentWidth") >= S(24) - 0.5)
acc = [it for it in h.walk() if it.isVisible() and str(it.property("text") or "").startswith("Signed in as")][0]
r = lambda it: it.mapToScene(QPointF(it.width(), 0)).x()
l = lambda it: it.mapToScene(QPointF(0, 0)).x()
h.ok("T3 the target does not overlap who is signed in", r(acc) <= l(lk[0]) + 0.5)
h.ok("N0 no cache note before asking", NOTE not in texts())

h.ok("F1 Tab reaches Sign out, one outline", tab_to(lambda: ev("root.kbFocus") == lk[0]) and len(named("focusRing")) == 1)
ev("root.kbFocus = null"); h.spin(30)  # scrolled into view by the outline; drop it to see the hover alone
fill = named("signOutHover")
h.ok("H0 no fill at rest", len(fill) == 1 and fill[0].property("color").alpha() == 0)
QTest.mouseMove(h.win, h.scene(lk[0])); h.spin(60)
h.ok("H1 hover: a quiet fill", 0 < fill[0].property("color").alpha() < 40, fill[0].property("color").alpha())
QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(60)
tab_to(lambda: ev("root.kbFocus") == lk[0])
h.key(Qt.Key_Return); h.spin(80)
h.ok("F2 Enter asks first, nothing run", ev("settingsView.confirming") and not h.running("logout"))
h.ok("N1 the question says it deletes this server's saved board cache", NOTE in texts())
h.ok("N2 it does not claim settings or favorites go", not any(("setting" in t.lower() or "favorite" in t.lower()) and "deletes" in t.lower() for t in texts()))
ev("settingsView.confirming = false"); h.spin(40)
lk = link(); ev("root.kbFocus = null"); h.spin(20)
tab_to(lambda: ev("root.kbFocus") == lk[0]); h.key(Qt.Key_Space); h.spin(80)
h.ok("F3 Space asks too", ev("settingsView.confirming"))
yes = h.visible(lambda it: it.metaObject().className().startswith("ActionButton") and it.property("label") == "Yes, sign out")
tab_to(lambda: ev("root.kbFocus") == yes[0]); h.key(Qt.Key_Return); h.spin(40)
h.ok("N3 while signing out the note goes", h.running("logout") and NOTE not in texts(), (len(yes), h.running(), ev("root.signingOut")))
sys.exit(h.finish())
