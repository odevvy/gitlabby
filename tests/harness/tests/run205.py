# v0.1.105: scope tabs are 32 point targets with side padding and a quiet
# hover fill, and take the focus outline (Enter switches the scope); the
# picker's board stars take the outline on their own (Enter stars the board,
# without switching to it).
# Usage: run205.py <src>
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
P = "group/app"
BOARD = {"state": "ready", "project": P, "updatedAt": "2026-10-31T13:20:00Z", "message": "", "labelColors": {}, "boards": [{"id": 1, "name": "Dev"}], "board": {"id": 1, "name": "Dev"}, "fallback": False,
  "columns": [{"name": "Open", "kind": "open", "issues": []}, {"name": "Closed", "kind": "closed", "issues": []}]}
ANS = {"state": "ready", "message": "", "scope": "all", "updatedAt": "2026-10-31T13:20:00Z", "review": [], "mine": []}
h = Harness(sys.argv[1], {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": [], "favorites": [], "serverFavorites": {}})
h.ev("panel.availableCardHeight = 700; panel.availableCardWidth = 1460")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(150)
ev = h.ev
def named(n): return [it for it in h.walk() if it.objectName() == n and it.isVisible()]
def rings(): return named("focusRing")
def tab(): QTest.keyClick(h.win, Qt.Key_Tab); h.spin(30)
def tab_to(pred, n=40):
    for _ in range(n):
        tab()
        if pred(): return True
    return False
S = lambda v: ev("Style.space(%d)" % v)

for view, name in (("mrs", "scopeTab"), ("todos", "todoScopeTab")):
    ev("root.showView('%s')" % view); h.spin(80); h.answer(view, dict(ANS, todos=[])); h.spin(120)
    QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(60)
    tabs = sorted(named(name), key=lambda t: t.mapToScene(QPointF(0, 0)).x())
    h.ok("%s T1 two scope tabs, 32 points high" % view, len(tabs) == 2 and all(abs(t.height() - S(32)) < 0.5 for t in tabs), [t.height() for t in tabs])
    texts = [next(c for c in t.childItems() if c.property("text") == t.property("label")) for t in tabs]
    h.ok("%s T2 side padding: the target is wider than its words" % view, all(t.width() - x.width() >= S(16) - 0.5 for t, x in zip(tabs, texts)))
    a, b = tabs
    h.ok("%s T3 the targets do not overlap" % view, a.mapToScene(QPointF(a.width(), 0)).x() <= b.mapToScene(QPointF(0, 0)).x() + 0.5)
    fills = sorted(named("scopeHover"), key=lambda t: t.mapToScene(QPointF(0, 0)).x())
    h.ok("%s H0 no fill at rest" % view, all(f.property("color").alpha() == 0 for f in fills))
    off = b if a.property("on") else a
    QTest.mouseMove(h.win, h.scene(off)); h.spin(60)
    fill = [f for f in fills if off.isAncestorOf(f)][0]
    h.ok("%s H1 hover: a quiet fill on the other tab" % view, 0 < fill.property("color").alpha() < 40, fill.property("color").alpha())
    QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(60)
    mode0 = ev(("mrsView" if view == "mrs" else "todoView") + ".mode")
    h.ok("%s F1 Tab reaches the other scope tab" % view, tab_to(lambda: ev("root.kbFocus") == off) and len(rings()) == 1)
    h.key(Qt.Key_Return); h.spin(80)
    h.ok("%s F2 Enter switches the scope" % view, ev(("mrsView" if view == "mrs" else "todoView") + ".mode") != mode0)
    ev("root.kbFocus = null")

# Picker, board step: the star is its own Tab stop.
ev("root.showView('board')"); h.spin(60)
ev("root.openPicker()"); h.spin(60)
h.answer("projects", {"state": "ready", "projects": [{"id": 1, "path": "group/app"}]}); h.spin(60)
ev("root.pickProject('group/app')"); h.spin(50)
h.answer("boards", {"state": "ready", "boards": [{"id": 7, "name": "Development"}, {"id": 8, "name": "Ops"}]}); h.spin(100)
ok = tab_to(lambda: ev("root.kbFocus ? root.kbFocus.parent.text : ''") in ("\uf005", "\uf006") and ev("root.kbFocus.parent.parent.name") == "Development")
h.ok("P1 Tab reaches a board's star, one outline", ok and len(rings()) == 1)
proj0 = ev("root.project"); n0 = len(ev("root.saved('favorites', [])") or [])
h.key(Qt.Key_Return); h.spin(80)
h.ok("P2 Enter stars the board without switching", len(ev("root.saved('favorites', [])") or []) == n0 + 1 and ev("root.view") == "picker" and ev("root.project") == proj0)
h.key(Qt.Key_Space); h.spin(80)
h.ok("P3 Space unstars it", len(ev("root.saved('favorites', [])") or []) == n0)
sys.exit(h.finish())
